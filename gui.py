import tkinter
from socket_utils import request

entities = {"lt": "<", "gt": ">", "amp": "&", "quot": "\"", "#39": "\'", "copy": "©", "ndash": "–", "#8212": "—", "#187": "»", "hellip": "…"}

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
    HSTEP, VSTEP = 13, 18
    HEIGHT = 600
    WIDTH = 800
    cursor_x, cursor_y = HSTEP, VSTEP
    for c in text:
        display_list.append((cursor_x, cursor_y, c))
        cursor_x += HSTEP
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
        self.HEIGHT = 600
        self.WIDTH = 800
        self.HSTEP = 13
        self.VSTEP = 18
        self.canvas = tkinter.Canvas(
            self.window,
            width=self.WIDTH,
            height=self.HEIGHT
        )
        # キャンバスをウィンドウ内に配置
        self.canvas.pack()
        self.scroll = 0

    def draw(self):
        for x, y, c in self.display_list:
            self.canvas.create_text(x, y - self.scroll, text=c)

    def load(self, url):
        headers, body, show_flag = request(url)
        text = lex(body)
        self.display_list = layout(text)
        self.draw()
        #print(text)
        #HEIGHT = 600
        #WIDTH = 800
        # ウィンドウ作成
        #self.window = tkinter.Tk()
        # ウィンドウ内にキャンバスを作成
        # 引数にwindowを渡して、キャンバスを表示する場所を認識
        #self.canvas = tkinter.Canvas(
        #    self.window,
        #    width = WIDTH,
        #    height = HEIGHT
        #)
        # キャンバスをウィンドウ内に配置
        #self.canvas.pack()
        # self.canvas.create_rectangle(10, 20, 400, 300)
        # self.canvas.create_oval(100, 100, 150, 150)
        
        #HSTEP, VSTEP = 13, 18
        #cursor_x, cursor_y = HSTEP, VSTEP
        #for c in text:
        #    self.canvas.create_text(cursor_x, cursor_y, text=c)
        #    cursor_x += HSTEP
        #    #print(cursor_x)
        #    if cursor_x >= self.WIDTH - HSTEP:
        #        cursor_y += VSTEP
        #        cursor_x = HSTEP

if __name__ == "__main__":
    import sys
    Browser().load(sys.argv[1])
    # 再描画プロセスを開始
    tkinter.mainloop()
