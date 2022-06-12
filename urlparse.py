def urlparse(url):
    # とりあえず、httpのみを取り扱う
    # assert url.startswith("http://")
    scheme, url = url.split("://", 1)
    assert scheme in ["http", "https"], "Unknown scheme {}".format(scheme)
    # url = url[len("http://"):]
    host, path = url.split("/", 1)
    path = "/" + path

    return scheme, url, host, path
