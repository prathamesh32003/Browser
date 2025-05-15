import socket
import ssl
import os
import hashlib

class URL:
    redirects = 0
    MAX_REDIRECTS = 5
    def __get_scheme(self, url):
        self.scheme, url = url.split(":", 1)
        if url[:2] == "//":
            url = url[2:]
        return url

    def __init__(self, url):
        if not os.path.exists(".cache"):
            os.makedirs(".cache")
        url = self.__get_scheme(url)
        self.view_source = False
        assert self.scheme in ["http", "https", "file", "data", "view-source"]

        if self.scheme in ["http", "https", "view-source"]:
            if self.scheme == "view-source":
                self.view_source = True
                self.scheme, url = url.split("://", 1)
            if not "/" in url:
                url = url + "/"
            self.host, url = url.split("/", 1)
            self.path = "/" + url

            if ":" in self.host:
                self.host, port = self.host.split(":", 1)
                self.port = int(port)

        elif self.scheme in ["file"]:
            self.path = url

        elif self.scheme in ["data"]:
            type, self.body = url.split(",", 1)

    def write_cache(self, response_headers, content):
        if "no-store" in response_headers or "max-age" in response_headers:
            key = f"{self.host}{self.path}".encode()
            key = hashlib.md5(key).hexdigest() + ".cache"
            path = os.path.join(".cache", key)
            with open(path, 'w') as f:
                f.write(content)

    def request(self):
        if self.scheme in ["http", "https", "view-source"]:
            if self.scheme != "view-source":
                key = f"{self.host}{self.path}".encode()
                key = hashlib.md5(key).hexdigest() + ".cache"
                print("From cache")
                path = os.path.join(".cache", key)
                with open(path, 'r') as f:
                    return f.read()

            s = socket.socket(
                family=socket.AF_INET,
                type=socket.SOCK_STREAM,
                proto=socket.IPPROTO_TCP,
            )
            if self.scheme == "http":
                self.port = 80
            elif self.scheme == "https":
                self.port = 443
            s.connect((self.host, self.port))

            if self.scheme == "https":
                ctx = ssl.create_default_context()
                s = ctx.wrap_socket(s, server_hostname=self.host)

            request = "GET {} HTTP/1.0\r\n".format(self.path)
            request += "Host: {}\r\n".format(self.host)
            request += "Connection: keep-alive\r\n"
            request += "User-Agent: Mozilla/5.0\r\n"
            request += "\r\n"
            s.send(request.encode("utf8"))

            response = s.makefile("rb", encoding="utf8", newline="\r\n")

            statusline = response.readline()
            statusline = statusline.decode("utf-8")
            version, status, explanation = statusline.split(" ", 2)

            response_headers = {}
            while True:
                line = response.readline()
                line = line.decode("utf-8")
                if line == "\r\n": break
                header, value = line.split(":", 1)
                response_headers[header.casefold()] = value.strip()

            assert "transfer-encoding" not in response_headers
            assert "content-encoding" not in response_headers

            print(response_headers)
            length = int(response_headers["content-length"]) if "content-length" in response_headers else -1
            content = response.read(length)

            if 'cache-control' in response_headers:
                self.write_cache(response_headers['cache-control'], content.decode("utf-8"))

            if 'location' in response_headers:
                URL.redirects += 1;
                if URL.redirects < URL.MAX_REDIRECTS:
                    if response_headers['location'][:1] == "/":
                        url = self.scheme + "://" + self.host + response_headers['location']
                    else:
                        url = response_headers['location']
                    load(URL(url))
                    return False
                else:
                    return "Max Redirects reached"
            else:
                URL.redirects = 0
                return content.decode("utf-8")

 
        if self.scheme == "file":
            file = open(self.path, 'r')
            content = file.read()
            file.close()
            return content

        if self.scheme == "data":
            return self.body

def show(view_source, scheme, body):
    if scheme in ["http", "https"] and not view_source:
        in_tag = False
        content = ""

        for c in body:
            if c == "<":
                in_tag = True
            elif c == ">":
                in_tag = False
            elif not in_tag:
                content += c

        content = content.replace("&lt;", "<")
        content = content.replace("&gt;", ">")
        print(content)

    elif scheme in ["file", "data"] or view_source:
        print(body)

def load(url):
    body = url.request()
    if body:
        show(url.view_source, url.scheme, body)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        load(URL(sys.argv[1]))
    else:
        load(URL("file:///home/knight/Documents/Projects/Browser/README.md"))
