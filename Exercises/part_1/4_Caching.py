# To implement HTTP 1.1, which adds 2 new headers, connection and user-agent.

import socket
import ssl
import time

CACHE = {}

class URL:
    def __init__(self, url):
        self.url = url
        self.scheme, url = url.split("://", 1)
        assert self.scheme in ["http", "https"]

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
        if self.url in CACHE:
            content, entry_time, max_age = CACHE[self.url]
            if time.time() < entry_time + max_age:
                return content
            else:
                del CACHE[self.url]

        s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )
        s.connect((self.host, self.port))

        if self.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)
        
        headers = {
            "Host": self.host,
            "Connection": "close",
            "User-Agent": "MyBrowser",
        }

        # Sending the Request
        request = "GET {} HTTP/1.1\r\n".format(self.path) # \r\n: \r means go to the start of current line, \n means go to the next line.
        for header, value in headers.items():
            request += f"{header}: {value}\r\n" 
        request += "\r\n" # add blank line at end of request, if not, the other computer keeps waiting.
        s.send(request.encode("utf8"))

        # Recieving the Response
        response = s.makefile("r", encoding="utf8", newline="\r\n") # makefile returns file-like obj containing every byte we recieve from server

        statusline = response.readline()
        version, status, explanation = statusline.split(" ", 2)

        response_headers = {}
        while True:
            line = response.readline()
            if line == "\r\n": break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()

        content = response.read() # Everything after the headers      
        s.close()

        # Caching logic 
        if request[:4].strip() == "GET" and status == 200:
            if "cache-control" in response_headers:
                cache_control = response_headers["cache-control"]
                if "no-cache" in cache_control:
                    pass
                elif "max-age=" in cache_control:
                    parts = cache_control.split(",")
                    for part in parts:
                        if "max-age=" in part:
                            try:
                                max_age = int(part.strip(). split("=")[1])
                                CACHE[self.url] = (content, time.time(), max_age)
                            except ValueError:
                                pass
        return content
    
def show(body):
    in_tag = False
    for c in body:
        if c == "<":
            in_tag=True
        elif c == ">":
            in_tag=False
        elif not in_tag:
            print(c, end="")

def load(url):
    body = url.request()
    show(body)

if __name__ == "__main__":
    import sys
    load(URL(sys.argv[1]))