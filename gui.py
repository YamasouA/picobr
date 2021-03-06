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

BLOCK_ELEMENTS = [
    "html", "body", "article", "section", "nav", "aside",
    "h1", "h2", "h3", "h4", "h5", "h6", "hgroup", "header",
    "footer", "address", "p", "hr", "pre", "blockquote",
    "ol", "ul", "menu", "li", "dl", "dt", "dd", "figure",
    "figcaption", "main", "div", "table", "form", "fieldset",
    "legend", "details", "summary"
]
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
        self.syntax_highlight = ""
    def __repr__(self):
        return "<" + self.tag + ">"

def layout_mode(node):
    if isinstance(node, Text):
        return "inline"
    elif node.children:
        for child in node.children:
            if isinstance(child, Text): continue
            if child.tag in BLOCK_ELEMENTS:
                return "block"
        return "inline"
    else:
        return "block"

class BlockLayout:
    def __init__(self, node, parent, previous):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []

    def layout(self):
        # self, previous, nextはlayout tree.
        # node はHTML tree
        previous = None
        self.width = self.parent.width
        self.x = self.parent.x
        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y
        for child in self.node.children:
            if layout_mode(child) == "inline":
                next = InlineLayout(child, self, previous)
            else:
                next = BlockLayout(child, self, previous)
            self.children.append(next)
            previous = next
        for child in self.children:
            child.layout()
        # 高さは子ノードが全て入る必要があるから、子ノードを全て計算してから計算する
        self.height = sum([child.height for child in self.children])

    def paint(self, display_list):
        for child in self.children:
            child.paint(display_list)


class DocumentLayout:
    def __init__(self, node):
        self.node = node
        self.parent = None
        self.children = []

    def layout(self):
        child = BlockLayout(self.node, self, None)
        self.children.append(child)
        self.width = WIDTH - 2 * HSTEP
        self.x = HSTEP
        self.y = VSTEP
        child.layout()
        self.height = child.height + 2 * VSTEP

    def paint(self, display_list):
        for child in self.children:
            child.paint(display_list)


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
        self.is_script = False
        self.is_quote = False

    def add_text(self, text):
        if text.isspace(): return
        self.implicit_tags(None)
        parent = self.unfinished[-1]
        node = Text(text, parent)
        parent.children.append(node)

    def get_attributes(self, text):
        is_quote = False
        is_key = True
        is_value = False
        parts = text.split(' ', 1)
        print("parts")
        print(parts)
        tag = parts[0].lower()
        attributes = {}
        text = ""
        key = ""
        value = ""
        if len(parts) == 1:
            return tag, attributes
        for attr in parts[1]:
            if attr == "\"":
                is_quote = not is_quote
            elif attr == "=":
                is_key = not is_key
                is_value = not is_value
                #key, value = attrpair.split("=", 1)
                # 引用符を取り除く
                #if len(value) > 2 and value[0] in ["'", "\""]:
                #    value = value[1:-1]
                #attributes[key.lower()] = value
            elif is_key and attr == " " and not is_quote:
                attributes[key.lower()] = ""
                key = ""
            elif is_value and attr == " " and not is_quote:
                attributes[key.lower()] = value
                key = ""
                value = ""
                is_key = not is_key
                is_value = not is_value
            elif is_key:
                key += attr
            elif is_value:
                value += attr
        if key != "":
            attributes[key.lower()] = value
        print(attributes)
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
        script_text = ""
        for c in self.body:
            if c == "<" and not self.is_script:
                in_tag = True
                if text:
                    self.add_text(text)
                text = ""
                comment_text += c
            elif c == ">":
                in_tag = False
                comment_text += c
                if text == "script":
                    print("script on")
                    self.is_script = True
                elif self.is_script and script_text[-8:] == "</script":
                    print("script off")
                    self.is_script = False
                    print(script_text[:-8])
                    self.add_text(script_text[:-8])
                elif self.is_script:
                    script_text += c
                elif not is_comment:
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
                if self.is_script:
                    script_text += c
                elif not is_comment:
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


class InlineLayout:
    def __init__(self, node, parent, previous):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []
        self.width = self.parent.width

    def layout(self):
        #self.cursor_x = HSTEP
        #self.cursor_y = VSTEP
        self.width = self.parent.width
        self.x = self.parent.x
        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y
        self.cursor_x = self.x
        self.cursor_y = self.y
        self.weight = "normal"
        self.style = "roman"
        self.size = FONT_SIZE
        self.display_list = []
        self.line = []
        self.is_sup = False
        self.is_pre = False
        self.is_script = False
        #for tok in tokens:
        #    self.token(tok)
        self.recurse(self.node)
        self.flush()
        self.height = self.cursor_y - self.y

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
        if tag == "script":
            self.is_script = True

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
        if tag == "script":
            self.is_script = False
        if tag == "h1":
            self.flush()
        if tag == "h2":
            self.flush()

    def recurse(self, tree):
        if isinstance(tree, Text):
            self.text(tree)
        else:
            #print(tree)
            #if isinstance(tree, list):
            #    return
            self.open_tag(tree.tag)
            for child in tree.children:
                self.recurse(child)
            self.close_tag(tree.tag)

    def flush(self):
        if not self.line: return
        metrics = [font.metrics() for x, word, font, color in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        if self.is_sup:
            baseline = self.cursor_y
        else:
            baseline = self.cursor_y + 1.25 * max_ascent

        for x, word, font, color in self.line:
            y = baseline #- font.metrics("ascent")
            self.display_list.append((x, y, word, font, color))

        #self.cursor_x = HSTEP
        self.cursor_x = self.x
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
            self.cursor_y += VSTEP #段落が変わるときは空白を少し広げる
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
        

    def text(self, tok):
        font = get_font(size=self.size, weight = self.weight, slant = self.style)
        color = "black"
        if self.is_pre:
            tmp = ""
            is_entitie = False
            in_anc = False
            is_attr = False
            is_quote = False
            for i in range(len(tok.text)):
                #print(tok.text[i])
                if tok.text[i] == "&":
                    if tmp != "":
                        w = font.measure(tmp)
                        if self.cursor_x + w >WIDTH - HSTEP:
                            self.flush()
                        self.line.append((self.cursor_x, tmp, font, color))
                        self.cursor_x += w
                        tmp = ""
                    print("is_entite on")
                    is_entitie = True

                elif tok.text[i] == ";" and is_entitie:
                    if tmp == "lt":
                        in_anc = True
                        color = "blue"
                    entitie = entities[tmp]
                    w = font.measure(entitie)
                    if self.cursor_x + w > WIDTH - HSTEP:
                        self.flush()
                    self.line.append((self.cursor_x, entitie, font, color))
                    self.cursor_x += w
                    print("is_entite off")
                    is_entitie = False
                    if tmp == "gt":
                        in_anc = False
                        color = "black"
                    tmp = ""
                elif tok.text[i] == "\n":
                    w = font.measure(tmp)
                    self.line.append((self.cursor_x, tmp, font, color))
                    self.cursor_x += w
                    self.flush()
                    tmp = ""
                else:
                    tmp += tok.text[i]
            if tmp != "":
                self.line.append((self.cursor_x, tmp, font, color))
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
                            self.line.append((self.cursor_x, tmp, font, color))
                            self.cursor_x += w
                            tmp = ""
                        is_entitie = True
                    elif word[i] == ";" and is_entitie:
                        print(tmp)
                        entitie = entities[tmp]
                        w = font.measure(entitie)
                        if self.cursor_x + w > WIDTH - HSTEP:
                            self.flush()
                        self.line.append((self.cursor_x, entitie, font, color))
                        self.cursor_x += w
                        is_entitie = False
                        tmp = ""
                    else:
                        tmp += word[i]
                if tmp != "":
                    w = font.measure(tmp)
                    if self.cursor_x + w > WIDTH - HSTEP:
                        self.flush()
                    self.line.append((self.cursor_x, tmp, font, color))
                    self.cursor_x += w
                
                #w = font.measure(word)
                #if self.cursor_x + w > WIDTH - HSTEP:
                #    self.flush()
                #self.line.append((self.cursor_x, word, font))
                #self.cursor_x += w + font.measure(" ")
                self.cursor_x += font.measure(" ")


    def paint(self, display_list):
        display_list.extend(self.display_list)

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
        for x, y, c, font, color in self.display_list:
            # 画面より下
            #if y > self.scroll + self.HEIGHT: continue
            if y > self.scroll + HEIGHT: continue
            # 画面より上
            #if y + self.VSTEP < self.scroll: continue
            if y + VSTEP < self.scroll: continue
            self.canvas.create_text(x, y - self.scroll, text=c, font=font, anchor='nw', fill=color)

    def load(self, url):
        headers, body, show_flag = request(url)
        self.nodes = HTMLParser(body).parse()
        self.document = DocumentLayout(self.nodes)
        self.document.layout()
        self.display_list = []
        self.document.paint(self.display_list)
        self.draw()
        #self.display_list = Layout(self.nodes).display_list
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
