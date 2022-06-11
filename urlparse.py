def urlparse(url):
    # とりあえず、httpのみを取り扱う
    assert url.startswith("http://")
    url = url[len("http://"):]
    host, path = url.split("/", 1)
    path = "/" + path
    return url, host, path
