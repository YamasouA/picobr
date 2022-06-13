import socket
from urlparse import urlparse
import ssl

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

def send_text(header_list):
    ret =""
        

def request(url):
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
    s.close()

    return headers, body
