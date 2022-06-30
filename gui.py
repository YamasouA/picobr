import tkinter
import tkinter.font
from socket_utils import request

entities = {"lt": "<", "gt": ">", "amp": "&", "quot": "\"", "#39": "\'", "copy": "©", "ndash": "–", "#8212": "—", "#187": "»", "hellip": "…"}

HSTEP, VSTEP = 13, 18
NLSTEP = 25
HEIGHT = 600
WIDTH = 800
SCROLL_STEP = 100
FONT_SIZE = 16
FONTS = {}

class Text:
    def __init__(self, text, parent):
        self.text = text
        # text nodeは基本的に子ノードを持たないが、TextとElement両方に
        # childrenフィールドを追加することで、isinstanceの呼び出しを回避する
        self.children = []
        self.parent = parent
    def __repr__(self):
        return repr(self.text)

class Element:
    def __init__(self, tag, attributes,  parent):
        self.tag = tag
        self.attributes = attributes
        self.children = []
        self.parent = parent
    def __repr__(self):
        return "<" + self.tag + ">"

class HTMLParser:
    HEAD_TAGS = [
        "base", "basefont", "bgsound", "noscript",
        "link", "meta", "title", "style", "script",
    ]

    SELF_CLOSING_TAGS = [
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr",
    ]
    def __init__(self, body):
        self.body = body
        self.unfinished = []

    def add_text(self, text):
        if text.isspace(): return
        self.implicit_tags(None)
        parent = self.unfinished[-1]
        node = Text(text, parent)
        parent.children.append(node)

    def get_attributes(self, text):
        parts = text.split()
        tag = parts[0].lower()
        attributes = {}
        for attrpair in parts[1:]:
            if "=" in attrpair:
                key, value = attrpair.split("=", 1)
                # 引用符を取り除く
                if len(value) > 2 and value[0] in ["'", "\""]:
                    value = value[1:-1]
                attributes[key.lower()] = value
            else:
                attributes[attrpair.lower()] = ""
        return tag, attributes

    def add_tag(self, tag):
        tag, attributes = self.get_attributes(tag)
        # !doctypeはこのブラウザでは捨てる
        if tag.startswith("!"): return
        self.implicit_tags(tag)
        if tag.startswith("/"):
            if len(self.unfinished) == 1: return
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        elif tag in self.SELF_CLOSING_TAGS:
            parent = self.unfinished[-1]
            node = Element(tag, attributes, parent)
            parent.children.append(node)
        else:
            parent = self.unfinished[-1] if self.unfinished else None
            # parentは開始タグの段階で情報を与える
            node = Element(tag, attributes, parent)
            self.unfinished.append(node)

    def implicit_tags(self, tag):
        while True:
            open_tags = [node.tag for node in self.unfinished]
            if open_tags == [] and tag != "html":
                self.add_tag("html")
            elif open_tags == ["html"] and tag not in ["head", "body", "/html"]:
                if tag in self.HEAD_TAGS:
                    self.add_tag("head")
                else:
                    self.add_tag("body")
            elif open_tags == ["html", "head"] and tag not in ["/head"] + self.HEAD_TAGS:
                self.add_tag("/head")
            else:
                break

    def finish(self):
        if len(self.unfinished) == 0:
            self.add_tag("html")
        # 終了していないノードを強制的に終わらせる
        while len(self.unfinished) > 1:
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        # unfinishedの最後の一つはルートノード
        return self.unfinished.pop()
    
    def parse(self):
        text = ""
        in_tag = False
        comment_text = ""
        is_comment = False
        for c in self.body:
            if c == "<":
                in_tag = True
                if text:
                    self.add_text(text)
                text = ""
                comment_text += c
            elif c == ">":
                in_tag = False
                comment_text += c
                if not is_comment:
                    self.add_tag(text)
                #print(comment_text)
                #print(comment_text[-3:])
                if len(comment_text) >= 7 and comment_text[-3:] == "-->":
                    comment_text = ""
                    is_comment = False
                text = ""
            else:
                if comment_text != "":
                    comment_text += c
                    if comment_text == "<!--":
                        is_comment = True
                        text = text[:-3]
                if not is_comment:
                    text += c
        if not in_tag and text:
            self.add_text(text)
        return self.finish()

def print_tree(node, indent=0):
    print(" " * indent, node)
    for child in node.children:
        print_tree(child, indent + 2)


def get_font(size, weight, slant):
    key = (size, weight, slant)
    if key not in FONTS:
        font = tkinter.font.Font(size=size, weight=weight, slant=slant)
        FONTS[key] = font
    return FONTS[key]


class Layout:
    def __init__(self, tree):
        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.weight = "normal"
        self.style = "roman"
        self.size = FONT_SIZE
        self.display_list = []
        self.line = []
        self.is_sup = False
        self.is_pre = False
        #for tok in tokens:
        #    self.token(tok)
        self.recurse(tree)
        self.flush()

    def open_tag(self, tag):
        if tag == "i":
            self.style = "italic"
        if tag == "b":
            self.weight = "bold"
        if tag == "small":
            self.size -= 2
        if tag == "big":
            self.size += 4 
        if tag == "br":
            self.flush()
        if tag == "sup":
            self.size = int(self.size/2)
            self.is_sup = True
        if tag == "pre":
            self.is_pre = True

    def close_tag(self, tag):
        if tag == "i":
            self.style = "roman"
        if tag == "b":
            self.weight = "normal"
        if tag == "small":
            self.size += 2
        if tag == "big":
            self.size -= 4
        if tag == "p":
            self.flush()
        if tag == "sup":
            self.size *= 2
            self.is_sup = False
        if tag == "pre":
            self.is_pre = False
        if tag == "h1":
            self.flush()
        if tag == "h2":
            self.flush()

    def recurse(self, tree):
        if isinstance(tree, Text):
            self.text(tree)
        else:
            #print(tree)
            self.open_tag(tree.tag)
            for child in tree.children:
                self.recurse(child)
            self.close_tag(tree.tag)

    def flush(self):
        if not self.line: return
        metrics = [font.metrics() for x, word, font in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        if self.is_sup:
            baseline = self.cursor_y
        else:
            baseline = self.cursor_y + 1.25 * max_ascent

        for x, word, font in self.line:
            y = baseline #- font.metrics("ascent")
            self.display_list.append((x, y, word, font))

        self.cursor_x = HSTEP
        self.line = []
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent

    def token(self, tok):
        if isinstance(tok, Text):
            self.text(tok)
        elif tok.tag == "i":
            self.style = "italic"
        elif tok.tag == "/i":
            self.style = "roman"
        elif tok.tag == "b":
            self.weight = "bold"
        elif tok.tag == "/b":
            self.weight = "normal"
        elif tok.tag == "small":
            self.size -= 2
        elif tok.tag == "/small":
            self.size += 2
        elif tok.tag == "big":
            self.size += 4
        elif tok.tag == "/big":
            self.size -= 4
        elif tok.tag == "br":
            self.flush()
        elif tok.tag == "/p":
            self.flush()
        elif tok.tag == "sup":
            self.size = int(self.size/2)
            self.is_sup = True
        elif tok.tag == "/sup":
            self.size *= 2
            self.is_sup = False
        elif tok.tag == "pre":
            self.is_pre = True
        elif tok.tag == "/pre":
            self.is_pre = False
        #elif tok.tag == "h1 class=\"title\"":
        
            self.cursor_y += VSTEP #段落が変わるときは空白を少し広げる

    def text(self, tok):
        font = get_font(size=self.size, weight = self.weight, slant = self.style)
        if self.is_pre:
            tmp = ""
            is_entitie = False
            for i in range(len(tok.text)):
                if tok.text[i] == "&":
                    if tmp != "":
                        w = font.measure(tmp)
                        if self.cursor_x + w >WIDTH - HSTEP:
                            self.flush()
                        self.line.append((self.cursor_x, tmp, font))
                        self.cursor_x += w
                        tmp = ""
                    is_entitie = True
                elif tok.text[i] == ";" and is_entitie:
                    entitie = entities[tmp]
                    w = font.measure(entitie)
                    if self.cursor_x + w > WIDTH - HSTEP:
                        self.flush()
                    self.line.append((self.cursor_x, entitie, font))
                    self.cursor_x += w
                    is_entite = False
                    tmp = ""
                elif tok.text[i] == "\n":
                    w = font.measure(tmp)
                    self.line.append((self.cursor_x, tmp, font))
                    self.cursor_x += w
                    self.flush()
                    tmp = ""
                else:
                    tmp += tok.text[i]
            if tmp != "":
                self.line.append((self.cursor_x, tmp, font))
                w = font.measure(tmp)
                self.cursor_x += w
                self.flush()
        else:    
            for word in tok.text.split():
                #w = font.measure(word)
                tmp = ""
                is_entitie = False
                for i in range(len(word)):
                    if word[i] == "&":
                        #print(word[i])
                        if tmp != "":
                            w = font.measure(tmp)
                            if self.cursor_x + w > WIDTH - HSTEP:
                                self.flush()
                            self.line.append((self.cursor_x, tmp, font))
                            self.cursor_x += w
                            tmp = ""
                        is_entitie = True
                    elif word[i] == ";" and is_entitie:
                        print(tmp)
                        entitie = entities[tmp]
                        w = font.measure(entitie)
                        if self.cursor_x + w > WIDTH - HSTEP:
                            self.flush()
                        self.line.append((self.cursor_x, entitie, font))
                        self.cursor_x += w
                        is_entitie = False
                        tmp = ""
                    else:
                        tmp += word[i]
                if tmp != "":
                    w = font.measure(tmp)
                    if self.cursor_x + w > WIDTH - HSTEP:
                        self.flush()
                    self.line.append((self.cursor_x, tmp, font))
                    self.cursor_x += w
                
                #w = font.measure(word)
                #if self.cursor_x + w > WIDTH - HSTEP:
                #    self.flush()
                #self.line.append((self.cursor_x, word, font))
                #self.cursor_x += w + font.measure(" ")
                self.cursor_x += font.measure(" ")

class Browser:
    def __init__(self):
        # ウィンドウ作成
        self.window = tkinter.Tk()
        # ウィンドウ内にキャンバスを作成
        # 引数にwindowを渡して、キャンバスを表示する場所を認識
        #self.HEIGHT = 600
        #self.WIDTH = 800
        #self.HSTEP = 13
        #self.VSTEP = 18
        #self.SCROLL_STEP = 100
        self.tokens = [] 
        self.nodes = []
        self.font = tkinter.font.Font(family="Times", size=FONT_SIZE)
        self.canvas = tkinter.Canvas(
            self.window,
            width=WIDTH,
            height=HEIGHT
        )
        # キャンバスをウィンドウ内に配置
        #self.canvas.pack()
        self.canvas.pack(expand=1, fill=tkinter.BOTH)
        self.scroll = 0
        self.window.bind("<Down>", self.scrolldown)
        self.window.bind("<Up>", self.scrollup)
        self.window.bind("<MouseWheel>", self.mousehandler)
        self.window.bind("<Configure>", self.configure)
        self.window.bind("<KeyPress-+>", self.change_font_size_plus)
        self.window.bind("<KeyPress-minus>", self.change_font_size_minus)

        #print(tkinter.font.families())
        bi_times = tkinter.font.Font(
            family="Times",
            size=16,
            weight="bold",
            slant="italic",
        )

    def change_font_size_minus(self, e):
        global HSTEP
        global VSTEP
        global FONT_SIZE
        FONT_SIZE = int(FONT_SIZE/2)
        HSTEP = int(HSTEP/2)
        VSTEP = int(VSTEP/2)
        self.canvas.delete("all")
        self.display_list= Layout(self.tokens).display_list
        self.draw()

    def change_font_size_plus(self, e):
        global HSTEP
        global VSTEP
        global FONT_SIZE
        FONT_SIZE *= 2
        HSTEP *= 2
        VSTEP *= 2
        self.canvas.delete("all")
        self.display_list= Layout(self.tokens).display_list
        self.draw()

    def configure(self, e):
        #print(e)
        global HEIGHT
        HEIGHT = e.height
        global WIDTH
        WIDTH = e.width
        #print(self.HEIGHT, self.WIDTH)
        self.display_list = Layout(self.tokens).display_list
        self.canvas.delete("all")
        self.draw()

    def mousehandler(self, e):
        if e.delta > 0:
            self.scrollup(e)
        else:
            self.scrolldown(e)

    def scrolldown(self, e):
        endline = self.display_list[-1 ][1]
        #print(endline)
        #if self.scroll + self.HEIGHT < endline:
        if self.scroll + HEIGHT < endline:
            self.canvas.delete("all")
            self.scroll += SCROLL_STEP
            self.draw()

    def scrollup(self, e):
        startline = self.display_list[0][1]
        #print(startline)
        #if self.scroll - self.SCROLL_STEP >= 0:
        if self.scroll - SCROLL_STEP >= 0:
            self.canvas.delete("all")
            #self.scroll -= self.SCROLL_STEP
            self.scroll -= SCROLL_STEP
            self.draw()

    def draw(self):
        #print(self.display_list)
        for x, y, c, font in self.display_list:
            # 画面より下
            #if y > self.scroll + self.HEIGHT: continue
            if y > self.scroll + HEIGHT: continue
            # 画面より上
            #if y + self.VSTEP < self.scroll: continue
            if y + VSTEP < self.scroll: continue
            self.canvas.create_text(x, y - self.scroll, text=c, font=font, anchor='nw')

    def load(self, url):
        headers, body, show_flag = request(url)
        self.nodes = HTMLParser(body).parse()
        self.display_list = Layout(self.nodes).display_list
        #print_tree(nodes)
        #tokens = lex(body)
        #self.tokens = tokens
        #self.display_list = Layout(tokens).display_list
        self.draw()

if __name__ == "__main__":
    import sys
    Browser().load(sys.argv[1])
    # 再描画プロセスを開始
    tkinter.mainloop()
