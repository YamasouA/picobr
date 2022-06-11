from socket_utils import request

def main():
    url = "http://example.org/index.html"
    headers, body = request(url)
    print("===== headers =====")
    print(headers)
    print("===== body =====")
    print(body)

if __name__ == "__main__":
    main()
