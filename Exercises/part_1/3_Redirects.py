# To implement redirections

import socket
import ssl

redirect_statuses = [300, 301, 302, 303, 304, 307, 308]
MAX_REDIRECT = 10

class URL:
    def __init__(self, url):
        self.scheme, url = url.split("://", 1)
        if "/" not in url:
            url = url + "/"
        self.host, url = url.split("/", 1)
        self.path = "/" + url

        if self.scheme == "http":
            self.port = 80
        elif self.scheme == "https":
            self.port = 443
        
        if ":" in self.host:
            self.host, port = self.host.split(":", 1)
            self.port = int(port)
    
    # Creating a socket (Request and Response)
    def request(self):
        i=0
        while (True):
            s = socket.socket(
                family=socket.AF_INET,
                type = socket.SOCK_STREAM,
                proto = socket.IPPROTO_TCP,
            )
            s.connect((self.host, self.port))

            if self.scheme == "https":
                ctx = ssl.create_default_context()
                s = ctx.wrap_socket(s, server_hostname=self.host)
            
            headers = {
                "Host": self.host
            }

            request = "GET {} HTTP/1.1\r\n".format(self.path)

            for header, value in headers.items():
                request += f"{header}: {value}\r\n"
            request += "\r\n"
            s.send(request.encode("utf8"))

            response = s.makefile("r", encoding="utf8", newline="\r\n")
            statusline = response.readline()
            version, status, explanation = statusline.split(" ", 2)
            status = int(status)
            
            response_headers = {}
            while True:
                line = response.readline()
                if line == "\r\n": break
                header, value = line.split(":", 1)
                response_headers[header.casefold()] = value.strip()

            if status in redirect_statuses:
                redirect_url = response_headers["location"]
                if "://" in redirect_url:
                    self.scheme, url = redirect_url.split("://", 1)
                    self.host, url = url.split("/", 1)
                    self.path = "/" + url
                elif redirect_url.startswith("/"):
                    redirect_url = redirect_url[1:]
                    self.path = redirect_url
                elif not redirect_url.startswith("/"):
                    directory, _= self.path.rsplit("/", 1)
                    self.path = directory + "/" + redirect_url

                if self.scheme == "http":
                    self.port = 80
                elif self.scheme == "https":
                    self.port = 443

                if ":" in self.host:
                    self.host, port = self.host.split(":", 1)
                    self.port = int(port)
            
            content = response.read()
            s.close()

            i+=1
            if not (status in redirect_statuses) and (i < 10):
                break
        return content
    
def show(body):
    if "<html" in body.lower():
        in_tag = False
        for c in body:
            if c == "<":
                in_tag=True
            elif c == ">":
                in_tag=False
            elif not in_tag:
                print(c, end="")
    else:
        print(body)
def load(url):
    body = url.request()
    show(body)

if __name__ == "__main__":
    import sys
    load(URL(sys.argv[1]))