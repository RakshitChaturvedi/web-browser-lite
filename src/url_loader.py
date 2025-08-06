import socket
import ssl

class URL:
    def __init__(self, url):
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
        
        """
        website url: https://en.wikipedia.org/wiki/OpenAI
        scheme = https
        host = en.wikipedia.org/
        path = /wiki/OpenAI
        """
    
    # Creating a socket (Request and Response)
    def request(self):
        s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )
        s.connect((self.host, self.port))

        if self.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)

        # Sending the Request
        request = "GET {} HTTP/1.0\r\n".format(self.path) # \r\n: \r means go to the start of current line, \n means go to the next line.
        request += "Host: {}\r\n".format(self.host) 
        request += "\r\n" # add blank line at end of request, if not, the other computer keeps waiting.
        s.send(request.encode("utf8"))

        """
        the request looks like this for a url of http://example.org/homepage :
        GET /homepage HTTP/1.0
        Host: example.org

        """

        # Recieving the Response
        response = s.makefile("r", encoding="utf8", newline="\r\n") # makefile returns file-like obj containing every byte we recieve from server
        """
        Example response:
        HTTP/1.0 200 OK\r\n
        Content-Type: text/html; charset=UTF-8\r\n
        Content-Length: 44\r\n
        \r\n
        <html><body>Hello World!</body></html>
        """

        statusline = response.readline()
        version, status, explanation = statusline.split(" ", 2)
        """
        statusline = HTTP/1.0 200 OK
        version = HTTP/1.0
        status = 200
        explanation = OK
        """

        response_headers = {}
        while True:
            line = response.readline()
            if line == "\r\n": break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()
        """
        line = 
            Content-Type: text/html; charset=UTF-8\r\n
            Content-Length: 44\r\n
        header = 
            "Content-Type"
            "Content-Length"
        value = 
            " text/html; charset=UTF-8"
            " 44"
        response_headers = {
            "content-type": "text/html; charset=UTF-8",
            "content-length": "44"
        }
        """

        assert "transfer-encoding" not in response_headers
        assert "content-encoding" not in response_headers

        content = response.read() # Everything after the headers
        s.close()
        """
        content = <html><body>Hello World!</body></html>
        """

        return content            