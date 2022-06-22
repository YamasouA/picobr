import socket
from urlparse import urlparse
import ssl
import gzip
import io
import datetime

entities = {"lt": "<", "gt": ">", "amp": "&", "quot": "\"", "#39": "\'", "copy": "©", "ndash": "–", "#8212": "—", "#187": "»", "hellip": "…"}

def load(url):
    headers, body, show_type = request(url)
    if show_type:
        show_all(body)
    else:
        show(body)

def transform(body):
    text = ""
    for c in body:
        if c == "<":
            text += "&lt;"
        elif c == ">":
            text += "&gt;"
        elif c == "&":
            # "&"を&ampに書き換えることで、元が&lt;などが&amp;ltとなり、
            # showの時にソースコード通りに出力できる
            text += "&amp;"
        elif c == "\"":
            text += "&quot;"
        else:
            text += c
    #print(text)
    return text

def show_all(body):
    for c in body:
        print(c, end="")

def show(body):
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
            text += c
            #print("text: ", text)
            #print("in_angle: ", in_angle)
            #print("is_entity: ", is_entity)
        if c == "<":
            in_angle = True
            continue
        elif c == ">":
            in_angle = False
            text = text[:-1]
            tag = text.split(' ')[0]
            #print("=== tag ===")
            #print(tag)
            if tag in body_tag:
                in_body = not in_body
            text = ""
            continue
        elif c == "&" and (not in_angle):
            is_entity = True
            #print("c: ",c)
            continue
        '''
        print("=== text = ", text)
        print("in_angle: ", in_angle)
        print("in_body: ", in_body)
        print("is_entity: ", is_entity)
        '''
        if text != "" and (is_entity and c == ";"):
            text = text[:-1]
            #print(text)
            print(entities[text], end="")
            is_entity = False
            text = ""
        elif in_body and not in_angle and not is_entity:
            print(c, end="")
    '''
    for c in body:
        print(c, end="")
    '''

def chunked_text(body):
    text = b""
    #print(body)
    cnt = 0
    while 1:
        n_txt = b""
        #r_flag = False
        #n_flag = False
        #print("\n\n\n\n\n\n\n\n\n\n")
        for b in body:
            b = bytes([b])
            #print(b)
            '''
            if b == b'\r':
                r_flag = True
                continue
            elif b == b'\n':
                n_flag = True
            if r_flag and n_flag:
                break
            '''
            n_txt += b
            if b == b'\n':
                n_txt = n_txt[:-2]
                break
            #print("n_text: ", n_txt)
        '''
        print("n_txt: ", n_txt)
        print("len(body)1: ", len(body))
        print("body: ", body[:len(n_txt)+2])
        print("len(body)2: ", len(body))
        print("body: ", body[:len(n_txt)+4])
        print("len(body)3: ", len(body))
        print("body: ", body[:len(n_txt)+6])
        print("len(body)4: ", len(body))
        '''
        if n_txt == b'':
            break
        #print("n_txt: ", n_txt)
        #print("len(n_txt): ", len(n_txt))
        #print("len(body): ", len(body))
        #print("body: ", body[:len(n_txt)+2])
        n = int(n_txt, 16)
        if n == 0:
            #text += b'\r\n'
            break
        print("n: ", n)
        #print(n)
        #print("body1: ", body[:10])
        body = body[len(n_txt) + 2:]
        #print("len(body)5: ", len(body))
        print("body here: ", body[:len(n_txt)+6])
        #print("len(body)6: ", len(body))
        if body[:n] != b'':
            text += body[:n]
        #print(text)
        #print(body[n-2:n+1])
        #print("body10: ", body[:2])
        body = body[n + 2:]
        #print("body100: ", body[:2])
        #if body == b"":
        #    break
    #print("end chuncked")
    #print(text)
    return text
    #print(text)

def request(url):
    cache_age = {}
    cache_body = {}
    cache_header = {}
    # リダイレクトの制限
    for i in range(10):
        is_view_source = False
        scheme, url, host, path = urlparse(url)
        if url in cache_age:
            if cache_age[url] > datetime.datetime.now():
                return cache_body[url], cache_header[url], 0
        if scheme == "view-source":
            is_view_source = True
            scheme, url, host, path = urlparse(url)
        elif scheme == "data":
            mtype = "text/pain"
            base = "charset=US-ASCII"

            tmp = url.split(",", maxsplit=1)
            if len(tmp) == 2:
                mtype =  tmp[0]
                if len(mtype.split(";")) == 2:
                    base = mtype.split(";")[1]
            data_body = tmp[1]
            print("mtype: ", mtype)
            data_body = url.split(",")[1]
            print("data_body: ", data_body)
            return {}, data_body, 1

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
        #request_headers["Connection"] = "keep-alive"
        request_headers["Connection"] = "close"
        request_headers["User-Agent"] = "picobr"
        request_headers["Accept-Encoding"] = "gzip"
        request_header = "{} {} {}\r\n".format(method, path, http_ver)
        for key, value in request_headers.items():
            tmp_str = "{}: {}\r\n".format(key, value)
            request_header += tmp_str
        request_header = (request_header + "\r\n").encode("utf-8")
        print("request_header: ", request_header)
        #print(request_header)
        #print(type(request_header))
        
        s.send(request_header)
        
        #response = s.makefile("r", encoding="utf8", newline="\r\n")
        response = s.makefile("rb", newline="\r\n")
        print("response type: ", type(response))

        # HTTP Version, Response Code(status), Response Description(ex OK)のような形で帰ってくる
        statusline = response.readline()
        print("statusline: ", type(statusline))
        print("statusline: ", statusline)
        version, status, explanation = statusline.split(b" ", 2)
        print("version: ",version, " status: ", status, " exp: ", explanation)
        version = version.decode('utf-8')
        status = status.decode('utf-8')
        explanation = explanation.decode('utf-8')
        print("version: ",version, " status: ", status, " exp: ", explanation)
        assert status == "200" or status == "301", "{}: {}".format(status, explanation)

        # ステータス行の次のヘッダーの処理
        headers = {}
        while True:
            line = response.readline().decode('utf-8')
            if line == "\r\n":
                break
            header, value = line.split(":", 1)
            headers[header.lower()] = value.strip()

        # アクセスしようとするデータが通常とは異なる方法で送信されていることを示すヘッダーがないかを確認
        #assert "transfer-encoding" not in headers
        #assert "content-encoding" not in headers

        print(headers)
        if status == "301":
            url = headers["location"]
            print("======")
            print("url: ", url)
            #scheme, url, host, path = urlparse(url)
            #path = "/index.html"
            #print("path: ", path)
            #print("======")
            continue
        body = response.read()
        #print(body)
        if "content-encoding" in headers and headers["content-encoding"] == "gzip":
            #body = gzip.decompress(body)
            if "transfer-encoding" in headers:
                body = chunked_text(body)
            body = gzip.decompress(body)
        body = body.decode("utf-8")
        #print(body)
        if is_view_source:
            body = transform(body)

        # キャッシュする
        if "cache-control" in headers and headers["cache-control"] == "max-age":
            cache_body[url] = body
            cache_headers[url] = headers
            cache_age[url] = datetime.datetime.now() + datetime.timedelta(seconds=headers["cache-control"])
        elif "cache-control" in headers and headers["cache-control"] == "no-store":
            pass

        break

    s.close()
    return headers, body, 0
