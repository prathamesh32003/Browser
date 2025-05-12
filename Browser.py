import socket
import ssl

class URL:
    def __get_scheme(self, url):
        self.scheme, url = url.split(":", 1)
        if url[:2] == "//":
            url = url[2:]
        return url

    def __init__(self, url):
        url = self.__get_scheme(url)
        assert self.scheme in ["http", "https", "file", "data", "view-source"]

        if self.scheme in ["http", "https", "view-source"]:
            if self.scheme == "view-source":
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

    def request(self):
        if self.scheme in ["http", "https", "view-source"]:
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
            request += "Connection: close\r\n"
            request += "User-Agent: Mozilla/5.0\r\n"
            request += "\r\n"
            s.send(request.encode("utf8"))

            response = s.makefile("r", encoding="utf8", newline="\r\n")

            statusline = response.readline()
            version, status, explanation = statusline.split(" ", 2)

            response_headers = {}
            while True:
                line = response.readline()
                if line == "\r\n": break
                header, value = line.split(":", 1)
                response_headers[header.casefold()] = value.strip()

            assert "transfer-encoding" not in response_headers
            assert "content-encoding" not in response_headers

            content = response.read()
            s.close()

            return content

        if self.scheme == "file":
            file = open(self.path, 'r')
            content = file.read()
            file.close()
            return content

        if self.scheme == "data":
            return self.body

def show(scheme, body):
    if scheme in ["http", "https"]:
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

    elif scheme in ["file", "data", "view-source"]:
        print(body)

def load(url):
    body = url.request()
    show(url.scheme, body)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        load(URL(sys.argv[1]))
    else:
        load(URL("file:///home/knight/Documents/Projects/Browser/README.md"))
