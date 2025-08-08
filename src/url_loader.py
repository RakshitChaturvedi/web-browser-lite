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
        request = "GET {} HTTP/1.0\r\n".format(self.path)   # \r\n: \r means go to the start of current line, \n means go to the next line.
        request += "Host: {}\r\n".format(self.host) 
        request += "\r\n"                                   # add blank line at end of request, if not, the other computer keeps waiting.
        s.send(request.encode("utf8"))

        """
        the request looks like this for a url of http://example.org/homepage :
        GET /homepage HTTP/1.0
        Host: example.org

        """

        # Recieving the Response. 
        # Makefile returns file-like obj containing every byte we recieve from server
        response = s.makefile("r", encoding="utf8", newline="\r\n") 
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

    def resolve(self, url):
        if not url: return None

        url = url.strip()
        url = url.strip('"')
        print(f"DEBUG: URL IS -> {url}")
        
        if "://" in url: return URL(url)

        if url.startswith("#") or url.startswith("javascript:"):
            return None

        """
        if not url.startswith("/"):
            dir, _ = self.path.rsplit("/", 1)
            while url.startswith("../"):
                _, url = url.split("/", 1)            
                if "/" in dir: 
                    dir, _ = dir.rsplit("/", 1)
            url = dir + "/" + url 
        """

        if url.startswith("/"):
            return URL(f"{self.scheme}://{self.host}:{self.port}{url}")

        if url.startswith("//"):
            return URL(self.scheme + "://" + self.host + ":" + str(self.port) + url)  
        
        dir, _ = self.path.rsplit("/", 1)
        while url.startswith("../"):
            url = url[3:] # strip leading../
            if "/" in dir:
                dir, _ = dir.rsplit("/", 1)
        
        full_path = f"{dir}/{url}"
        return URL(f"{self.scheme}://{self.host}:{self.port}{full_path}")
        """
        First if statement:
            --> handles already complete urls
            --> returns the url as is

        Second if statement: (parent or host relative)
            --> Handle relative paths that don't start with a slash (e.g. "another-page.html") 
            --> These are relative to the *current directory* of the URL
            1) get dir part of current path. e.g if self.path is "/articles/tech/index.html", dir = "/articles/tech"
            2) while loop: (for parent relatives)
                --> handles "go up one dir" paths like "../style.css". For each "../" at the start of URL...
                1) remove the "../" from url
                2) go one level up in dir path
                    --> e.g if dir is "/articles/tech" it becomes "/articles"
            3) combine dir path and relative URL to make full path 
                --> e.g. if dir = "/articles" and url = "style.css", url becomes "/articles/style.css

        Third if statement: (for protocol relatives)
            --> handles urls starting with "//" (e.g: "//example.com/image.png) 
            --> uses same scheme (http or https) as current page
            1) rebuild url from its components 
        """
         