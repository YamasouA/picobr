import socket
from urlparse import urlparse

def load(url):
    headers, body = request(url)
    show(body)

def show(body):
    in_angle = False
    for c in body:
        if c == "<":
            in_angle = True
        elif c == ">":
            in_angle = False
        elif not in_angle:
            print(c, end="")

def request(url):
    url, host, path = urlparse(url)
    s = socket.socket(
        family=socket.AF_INET,
        type=socket.SOCK_STREAM,
        proto=socket.IPPROTO_TCP,
    )

    s.connect((host, 80))
    # 改行には\r\nを用いる
    # リクエストの最後に空行を入れる
    # データ送信時はバイトとして送るからエンコードが必要
    s.send("GET {} HTTP/1.0\r\n".format(path).encode("utf8") + "Host: {}\r\n\r\n".format(host).encode("utf8"))
    
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
    s.close()

    return headers, body
