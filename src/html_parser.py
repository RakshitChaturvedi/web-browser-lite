class Text:
    def __init__(self, text, parent):
        self.text = text
        self.children = [] # text nodes dont have children, but kept for consistency
        self.parent = parent
        self.style = {}

    def __repr__(self):
        return repr(self.text)

class Element:
    def __init__(self, tag, attributes, parent):
        self.tag = tag                  # tag name, e.g., "div", "body", "html" etc
        self.attributes = attributes    # dictionary of html attributes
        self.children = []              # list of children, element or text
        self.parent = parent            # pointer to parent element
        self.style = {}

    def __repr__(self):
        return "<" + self.tag + ">"

def print_tree(node, indent=0):
    print(" " * indent, node)           # print the current node with indentation
    for child in node.children:
        print_tree(child, indent+2)     # recursively print children, more indented

class HTMLParser:
    SELF_CLOSING_TAGS = [
        "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr",
    ]
    HEAD_TAGS = [
        "base", "basefont", "bgsound", "noscript",
        "link", "meta", "title", "style", "script",
    ]

    def __init__(self, body):
        self.body = body                # raw html as string
        self.unfinished = []            # stack of open (unfinished) elements

    def parse(self):
        text = ""
        in_tag = False
        for c in self.body:
            if c == "<":
                in_tag = True
                if text: self.add_text(text)
                text = ""
            elif c == ">":
                in_tag = False
                self.add_tag(text)
                text = ""
            else:
                text += c
        if not in_tag and text:
            self.add_text(text)
        return self.finish()
    """
    Example input = <html><body>Hello World!</body></html>
    char        in_tag      action
     <          True        Start of tag -> flush text
     >          False       End of tag -> process tag
     other      False       Build up tag name or text
    """

    def get_attributes(self, text):
        parts = text.split()
        tag = parts[0].casefold()
        attributes = {}

        for attrpair in parts[1:]:
            if "=" in attrpair:
                key, value = attrpair.split("=", 1)
                if len(value) > 2 and value[0] in ["'", "/"]:
                    value = value[1:-1]
                attributes[key.casefold()] = value
            else: 
                attributes[attrpair.casefold()] = ""
        return tag, attributes
    """
    Example input: <a href="https://example.org" target="_blank">
    tag = 'a'
    attributes = {
        'href': 'https://example.org',
        'target': '_blank'
    }
    """

    def add_text(self, text):
        if text.isspace(): return
        self.implicit_tags(None)

        parent = self.unfinished[-1]
        node = Text(text, parent)
        parent.children.append(node)

    def add_tag (self, tag):
        tag, attributes = self.get_attributes(tag)
        if tag.startswith("!"): return
        self.implicit_tags(tag)

        # Close tag finishes the last unfinished node by adding it to the prev unfinished node in list
        if tag.startswith("/"): 
            if len(self.unfinished) == 1: return # to prevent stack overflow / malformed tree, as its likely root node
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        elif tag in self.SELF_CLOSING_TAGS:
            parent = self.unfinished[-1]
            node = Element(tag, attributes, parent)
            parent.children.append(node)
        else:   # Open tags adds an unfinished node to the end of the list
            parent = self.unfinished[-1] if self.unfinished else None
            node = Element(tag, attributes, parent)
            self.unfinished.append(node)

    def implicit_tags(self, tag):
        while True:
            open_tags = [node.tag for node in self.unfinished]
            if open_tags == [] and tag != "html":
                self.add_tag("html")
            elif open_tags == ["html"] and tag not in ["head", "body", "/html"]:
                if tag in self.HEAD_TAGS:
                    self.add_tag("head")
                else:
                    self.add_tag("body")
            elif open_tags == ["html", "head"] and tag not in ["/head"] + self.HEAD_TAGS:
                self.add_tag("/head")
            else:
                break

    def finish(self):
        if not self.unfinished:
            self.implicit_tags(None)
        while len(self.unfinished) > 1:
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        return self.unfinished.pop()
    

    """
    Example: <html><body><b>Hello <i>World!</i></b></body></html>

    intial state: unfinished = []
    1) <html> -> add_tag("html")
        -> new Element("html") created, no parent (since unfinished is empty)
        -> unfinished = [html]

        2) <body> -> add_tag("body")
            -> new Element("body", parent=html)
            -> unfinished = [html, body]

            3) <b> -> add_tag("b")
                -> new Element("b, parent = body)
                -> unfinished = [html, body, b]

                4) Text "Hello " -> add_text("Hello ")
                    -> text.isspace() is false
                    -> parent = b
                    -> create Text("Hello ", parent= b)
                    -> append Text("Hello ") to b.children

                    5) <i> -> add_tag("i")
                        -> new Element("i", parent = b)
                        -> unfinished = [html, body, b, i]
                        
                        6) Text "World!" -> add_text("World!)
                            -> text.isspace() is false
                            -> create Text("World!", parent =i)
                            -> append Text("World!") to i.children
                            
                    7) </i> -> add_tag("/i")
                        -> node = i (popped from unfinished)
                        -> parent = b (unfinished[-1])
                        -> append i (along with its children) to b.children
                        -> unfinished = [html, body, b]

            8) </b> -> add_tag("/b")
                -> node = b (popped from unfinished)
                -> parent = body (unfinished[-1])
                -> append b (along with its children) to body.children
                -> unfinished = [html, body]

        9) </body> -> add_tag("/body")
            -> node = body (popped from unfinished)
            -> parent = html (unfinished[-1])
            ->  append body (along with its children) to html.children
            -> unfinished = [html]
    10) </html> -> add_tag("/html")
        -> prevented by if len(unfinished) == 1: return 
    """