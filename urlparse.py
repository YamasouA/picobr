def urlparse(url):
    # とりあえず、httpのみを取り扱う
    # assert url.startswith("http://")
    scheme, url = url.split(":", 1)
    assert scheme in ["http", "https", "file", "data", "view-source"], "Unknown scheme {}".format(scheme)
    # url = url[len("http://"):]
    if url[:2] == "//":
        url = url[2:]
    host, path = url.split("/", 1)
    if host == "" and scheme == "file":
        host = "localhost"
    path = "/" + path
    print("scheme: ", scheme)
    print("url: ", url)
    print("host: ", host)
    print("path: ", path)

    return scheme, url, host, path


if __name__ == "__main__":
    import sys
    url = sys.argv[1]
    urlparse(url)
