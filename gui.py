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
'''
def lex(body):
    tmp = ""
    in_angle = False
    in_body = False
    is_entity = False
    if body[0] == "&":
        in_body = True
    text = ""
    body_tag = ["body", "/body"]
    for c in body:
        if in_angle or is_entity:
            if c == "\n":
                continue
            tmp += c
            #print("text: ", text)
            #print("in_angle: ", in_angle)
            #print("is_entity: ", is_entity)
        if c == "<":
            in_angle = True
            continue
        elif c == ">":
            in_angle = False
            tmp = tmp[:-1]
            tag = tmp.split(' ')[0]
            #print("=== tag ===")
            #print(tag)
            if tag in body_tag:
                in_body = not in_body
            tmp = ""
            continue
        elif c == "&" and (not in_angle):
            is_entity = True
            #print("c: ",c)
            continue
        if tmp!= "" and (is_entity and c == ";"):
            tmp = tmp[:-1]
            # print(entities[tmp], end="")
            text += entities[tmp]
            is_entity = False
            tmp = ""
        elif in_body and not in_angle and not is_entity:
            # print(c, end="")
            text += c

    return text
'''

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
'''
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
'''
class Layout:
    def __init__(self, tokens):
        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.weight = "normal"
        self.style = "roman"
        self.size = 16
        self.display_list = []
        for tok in tokens:
            self.token(tok)

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

    def text(self, tok):
        font = tkinter.font.Font(
            size=self.size,
            weight = self.weight,
            slant = self.style,
        )
        for word in tok.text.split():
            w = font.measure(word)
            if self.cursor_x + w > WIDTH - HSTEP:
                self.cursor_y += font.metrics("linespace") * 1.25
                self.cursor_x = HSTEP
            self.display_list.append((self.cursor_x, self.cursor_y, word, font))
            self.cursor_x += w + font.measure(" ")

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

        print(tkinter.font.families())
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
        self.display_list= layout(self.tokens)
        self.draw()

    def change_font_size_plus(self, e):
        global HSTEP
        global VSTEP
        global FONT_SIZE
        FONT_SIZE *= 2
        HSTEP *= 2
        VSTEP *= 2
        self.canvas.delete("all")
        self.display_list= layout(self.tokens)
        self.draw()

    def configure(self, e):
        #print(e)
        global HEIGHT
        HEIGHT = e.height
        global WIDTH
        WIDTH = e.width
        #print(self.HEIGHT, self.WIDTH)
        self.display_list = layout(self.tokens)
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
