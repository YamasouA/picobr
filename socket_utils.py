import socket
from urlparse import urlparse
import ssl

entities = {"lt": "<", "gt": ">", "amp": "&", "quot": "\""}

def load(url):
    headers, body = request(url)
    show(body)

def transform(body):
    text = ""
    for c in body:
        if c == "<":
            text += "&lt;"
        elif c == ">":
            text += "&gt;"
        elif c == "&":
            text += "&amp;"
        elif c == "\"":
            text += "&quot;"
        else:
            text += c
    #print(text)
    return text
        

def show(body):
    in_angle = False
    in_body = False
    is_entity = False
    if body[0] == "&":
        in_body = True
    print(body)
    text = ""
    body_tag = ["body", "/body"]
    for c in body:
        if in_angle or is_entity:
            text += c
        if c == "<":
            in_angle = True
            continue
        elif c == ">":
            in_angle = False
            text = text[:-1]
            if text in body_tag:
                in_body = not in_body
            text = ""
            continue
        elif c == "&":
            is_entity = True
            continue
        #print("in_angle, in_body, is_entity, text")
        #print(in_angle, in_body, is_entity, text)
        if in_body and text != "" and (is_entity and c == ";"):
            text = text[:-1]
            print(entities[text], end="")
            is_entity = False
            text = ""
        elif in_body and not in_angle and not is_entity:
            print(c, end="")
    '''
    for c in body:
        print(c, end="")in_angle = False
    '''
def send_text(header_list):
    ret =""
        

def request(url):
    is_view_source = False
    scheme, url, host, path = urlparse(url)
    if scheme == "view-source":
        is_view_source = True
        scheme, url, host, path = urlparse(url)
    s = socket.socket(
        family=socket.AF_INET,
        type=socket.SOCK_STREAM,
        proto=socket.IPPROTO_TCP,
    )
    # HTTPSは443ポートを使う
    if scheme == "http":
        port = 80
    elif scheme == "https":
        port = 443
    elif scheme == "file":
        port = 8000
    if scheme == "https":
        ctx = ssl.create_default_context()
        s = ctx.wrap_socket(s, server_hostname=host)

    # カスタムポート
    if ":" in host:
        host, port = host.split(":", 1)
        port = int(port)
    #host = "localhost"
    s.connect((host, port))
    #print(s)
    # 改行には\r\nを用いる
    # リクエストの最後に空行を入れる
    # データ送信時はバイトとして送るからエンコードが必要

    # リクエストヘッダーを作成
    method = "GET"
    http_ver = "HTTP/1.1"
    request_headers = {}
    request_headers["Host"] = host
    request_headers["Connection"] = "close"
    request_headers["User-Agent"] = "picobr"
    request_header = "{} {} {}\r\n".format(method, path, http_ver)
    for key, value in request_headers.items():
        tmp_str = "{}: {}\r\n".format(key, value)
        request_header += tmp_str
    request_header = (request_header + "\r\n").encode("utf-8")
    #print(request_header)
    #print(type(request_header))
    
    s.send(request_header)
    
    response = s.makefile("r", encoding="utf8", newline="\r\n")

    # HTTP Version, Response Code(status), Response Description(ex OK)のような形で帰ってくる
    statusline = response.readline()
    version, status, explanation = statusline.split(" ", 2)
    assert status == "200", "{}: {}".format(status, explanation)

    # ステータス行の次のヘッダーの処理
    headers = {}
    while True:
        line = response.readline()
        if line == "\r\n":
            break
        header, value = line.split(":", 1)
        headers[header.lower()] = value.strip()

    # アクセスしようとするデータが通常とは異なる方法で送信されていることを示すヘッダーがないかを確認
    assert "transfer-encoding" not in headers
    assert "content-encoding" not in headers

    body = response.read()
    if is_view_source:
        body = transform(body)
    s.close()

    return headers, body
