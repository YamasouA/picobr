def urlparse(url):
    # とりあえず、httpのみを取り扱う
    # assert url.startswith("http://")
    scheme, url = url.split("://", 1)
    assert scheme in ["http", "https", "file"], "Unknown scheme {}".format(scheme)
    # url = url[len("http://"):]
    host, path = url.split("/", 1)
    if host == "" and scheme == "file":
        host = "localhost"
    path = "/" + path
    print("scheme: ", scheme)
    print("host: ", host)
    print("path: ", path)

    return scheme, url, host, path
