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

class Text:
    def __init__(self, text):
        self.text = text

class Tag:
    def __init__(self, tag):
        self.tag = tag

def lex(body):
    out = []
    text = ""
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
            if text:
                out.append(Text(text))
            text = ""
        elif c == ">":
            in_tag = False
            out.append(Tag(text))
            text = ""
        else:
            text += c
    if not in_tag and text:
        out.append(Text(text))
    return out

# スクロールできるように各文字の位置を保持する
def layout(tokens):
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    print("HSTEP: ", HSTEP)
    print("VSTEP: ", VSTEP)
    for c in text:
        display_list.append((cursor_x, cursor_y, c))
        cursor_x += HSTEP
        if c == "\n":
            cursor_y += NLSTEP
            cursor_x = HSTEP
            continue
        if cursor_x >= WIDTH - HSTEP:
            cursor_y += VSTEP
            cursor_x = HSTEP
    weight = "normal"
    style = "roman"
    for tok in tokens:
        # tokがText型か、（そうでなければ、Tag型）
        if isinstance(tok, Text):
            font = tkinter.font.Font(
                size=FONT_SIZE,
                weight = weight,
                slant = style,
            )
            for word in tok.text.split():
                w = font.measure(word)
                if cursor_x + w > WIDTH - HSTEP:
                    cursor_y += font.metrics("linespace") * 1.25
                    cursor_x = HSTEP
                display_list.append((cursor_x, cursor_y, word, font))
                cursor_x += w + font.measure(" ")
        elif tok.tag == "i":
            style = "italic"
        elif tok.tag == "/i":
            style = "roman"
        elif tok.tag == "b":
            weight = "bold"
        elif tok.tag == "/b":
            weight = "normal"

    return display_list

class Layout:
    def __init__(self, tokens):
        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.weight = "normal"
        self.style = "roman"
        self.size = FONT_SIZE
        self.display_list = []
        self.line = []
        for tok in tokens:
            self.token(tok)
        self.flush()

    def flush(self):
        if not self.line: return
        metrics = [font.metrics() for x, word, font in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        baseline = self.cursor_y + 1.25 * max_ascent

        for x, word, font in self.line:
            y = baseline - font.metrics("ascent")
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
            self.cursor_y += VSTEP #段落が変わるときは空白を少し広げる

    def text(self, tok):
        font = tkinter.font.Font(
            size=self.size,
            weight = self.weight,
            slant = self.style,
        )
        for word in tok.text.split():
            #w = font.measure(word)
            tmp = ""
            is_entitie = False
            for i in range(len(word)):
                if word[i] == "&":
                    if tmp != "":
                        w = font.measure(tmp)
                        if self.cursor_x + w > WIDTH - HSTEP:
                            self.flush()
                        self.line.append((self.cursor_x, tmp, font))
                        self.cursor_x += w
                        tmp = ""
                    is_entitie = True
                elif word[i] == ";" and is_entitie:
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
        tokens = lex(body)
        self.tokens = tokens
        self.display_list = Layout(tokens).display_list
        self.draw()

if __name__ == "__main__":
    import sys
    Browser().load(sys.argv[1])
    # 再描画プロセスを開始
    tkinter.mainloop()
