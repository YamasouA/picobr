import tkinter
from socket_utils import request

entities = {"lt": "<", "gt": ">", "amp": "&", "quot": "\"", "#39": "\'", "copy": "©", "ndash": "–", "#8212": "—", "#187": "»", "hellip": "…"}

HSTEP, VSTEP = 13, 18
NLSTEP = 25
HEIGHT = 600
WIDTH = 800
SCROLL_STEP = 100

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
        '''
        print("=== tmp = ", tmp)
        print("in_angle: ", in_angle)
        print("in_body: ", in_body)
        print("is_entity: ", is_entity)
        '''
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

# スクロールできるように各文字の位置を保持する
def layout(text):
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
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
    return display_list

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
        self.text = "" # body内容
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

    def configure(self, e):
        #print(e)
        global HEIGHT
        HEIGHT = e.height
        global WIDTH
        WIDTH = e.width
        #print(self.HEIGHT, self.WIDTH)
        self.display_list = layout(self.text)
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
        for x, y, c in self.display_list:
            # 画面より下
            #if y > self.scroll + self.HEIGHT: continue
            if y > self.scroll + HEIGHT: continue
            # 画面より上
            #if y + self.VSTEP < self.scroll: continue
            if y + VSTEP < self.scroll: continue
            self.canvas.create_text(x, y - self.scroll, text=c)

    def load(self, url):
        headers, body, show_flag = request(url)
        text = lex(body)
        self.text = text
        self.display_list = layout(text)
        self.draw()

if __name__ == "__main__":
    import sys
    Browser().load(sys.argv[1])
    # 再描画プロセスを開始
    tkinter.mainloop()
