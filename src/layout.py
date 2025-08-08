from src.constants import WIDTH, HEIGHT, HSTEP, VSTEP, BLOCK_ELEMENTS, get_font, DrawRect, DrawText, DrawOutline, DrawLine, Rect
from src.html_parser import Text, Element
from src.styles import style

class DocumentLayout:
    def __init__(self, node):
        self.node = node            # Root of DOM tree (e.g., <html>)
        self.parent = None          # No parent, as this is the document root
        self.children = []          # List of block children
    
    def layout(self):
        # Begin layout from the root node using BlockLayout
        child = BlockLayout(self.node, self, None)
        self.children.append(child)

        self.width = WIDTH - 2*HSTEP    # Available horizontal space
        self.x = HSTEP                  # Start x position
        self.y = VSTEP                  # Start y position
        child.layout()                  # Recursively lay out all elements
        self.height = child.height or 0 # Total height from child
    
    def paint(self):
        return []       # No painting for the document node itself

class LineLayout:
    def __init__(self, node, parent, previous):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []
        self.x = None
        self.y = None
        self.width = None
        self.height = None

    def layout(self):
        self.width = self.parent.width
        self.x = self.parent.x

        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y

        for word in self.children:
            word.layout()

        if not self.children:
            return
        max_ascent = max([word.font.metrics("ascent") for word in self.children])
        baseline = self.y + 1.25*max_ascent
        for word in self.children:
            word.y = baseline - word.font.metrics("ascent")
        max_descent = max([word.font.metrics("descent") for word in self.children])
        self.height = 1.25*(max_ascent + max_descent)

    def paint(self):
        return []

class TextLayout:
    def __init__(self, node, word, parent, previous):
        self.node = node
        self.word = word
        self.children = []
        self.parent = parent
        self.previous = previous
        self.x = None
        self.y = None
        self.width = None
        self.height = None
        self.font = None

    def layout(self):
        weight = self.node.style["font-weight"]
        style = self.node.style["font-style"]
        if style == "normal": style = "roman"
        size = int(float(self.node.style["font-size"][:-2])*.75)
        self.font = get_font(size, weight, style)
        self.width = self.font.measure(self.word)
        if self.previous:
            space = self.previous.font.measure(" ")
            self.x = self.previous.x + space + self.previous.width
        else:
            self.x = self.parent.x
        self.height = self.font.metrics("linespace")
    
    def paint(self):
        color = self.node.style["color"]
        return [DrawText(self.x, self.y, self.word, self.font, color)]

class BlockLayout:
    def __init__(self, node, parent, previous):        
        self.node = node                # Current DOM node
        self.parent = parent            # Parent BlockLayout
        self.previous = previous        # Previous sibling
        self.children = []              # Nested BlockLayouts if block mode

        self.x = None
        self.y = None
        self.width = None
        self.height = None

    def layout_mode(self):
        # Decide whether to use block or inline layour for this node
        if isinstance(self.node, Text):
            return "inline"
        elif any([isinstance(child, Element) and child.tag in BLOCK_ELEMENTS for child in self.node.children]):
            return "block"
        elif self.node.children:
            return "inline"
        else:
            return "block"

    def layout(self):
        # Set position and dimensions based on parent
        self.x = self.parent.x
        self.width = self.parent.width
        self.height = 0

        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y

        mode = self.layout_mode()
        if mode == "block":
            previous = None
            for child in self.node.children:
                next = BlockLayout(child, self, previous)
                self.children.append(next)
                previous = next
        else:
            self.new_line()
            self.recurse(self.node)

        for child in self.children:
            child.layout()

        self.height = sum([child.height for child in self.children if child.height is not None])

    def recurse(self, node):
        # Recursively lay out inline text nodes and apply tags
        if isinstance(node, Text):
            for word in node.text.split():
                self.word(node,word)
        else:
            if node.tag == "br":
                self.new_line()
            for child in node.children:
                self.recurse(child)

    # Add word to current line and manage cursor position
    def word(self, node, word): 
        color = node.style["color"]
        weight = node.style["font-weight"]
        style = node.style["font-style"]
        if style == "normal": style = "roman"
        size = int(float(node.style["font-size"][:-2]) * .75)
        font = get_font(size, weight, style)

        w = font.measure(word)      
        if self.cursor_x + w > self.width:
            self.new_line()
        line = self.children[-1]                                        # fetches most recent LineLayout that has been added to current BlockLayout
        previous_word = line.children[-1] if line.children else None    # determine the previous word if any
        text = TextLayout(node, word, line, previous_word)              # creates new TextLayout object for current word
        line.children.append(text)                                      # Adds TextLayout to current line's list of children
        self.cursor_x += w + font.measure(" ")
    
    # start a new line in an inline layout context,
    # and append it to the list of children of current BlockLayout
    def new_line(self):
        self.cursor_x = 0                                           
        last_line = self.children[-1] if self.children else None    # get the most recently added line(i.e line that just got flushed)
        new_line = LineLayout(self.node, self, last_line)           # create new LineLayout object
        self.children.append(new_line)                              # add the new LineLayout to list of block's children

    def paint(self):
        cmds = []
        bgcolor = self.node.style.get("background-color", "transparent")
        if bgcolor != "transparent":
            rect = DrawRect(self.self_rect(), bgcolor)
            cmds.append(rect)
        return cmds

    def self_rect(self):
        return Rect(self.x, self.y, self.x + self.width, self.y + self.height)
    
"""
Example: <html><body><b>Hello <i>World!</i></b></body></html>

1. Parsing builds the DOM tree:
    Element(tag='html', children=[
        Element(tag='body', children=[
            Element(tag='b', children=[
                Text('Hello '),
                Element(tag='i', children=[
                    Text('World!')
                ])
            ])
        ])
    ])

2. DocumentLayout is initialized with the root <html> node:
    -> layout = DocumentLayout(<html>)

3. Calling layout() triggers layout_mode() on <html>:
    -> Because <html> has children like <body> which are block-level
    -> Mode is set to "block"

4. In block layout mode:
    -> Each child is wrapped in a BlockLayout and layout() is called recursively

5. <body> and <b> are also block elements:
    -> <b> is block, but contains only inline content
    -> Switch to inline layout mode for <b>

6. Inline layout mode:
    -> Recursively walks through <b>'s children:
        - open_tag("b") applies bold style
        - Text("Hello ") added to display list
        - Element("i") triggers:
            -> open_tag("i") applies italic
            -> Text("World!") added with bold+italic
            -> close_tag("i")
        - close_tag("b")
    -> Text is positioned word-by-word using cursor_x / cursor_y

7. Heights are computed bottom-up:
    -> Each BlockLayout returns its height to the parent
    -> Final document height bubbles up to DocumentLayout

8. Display list is constructed:
    -> Contains DrawText entries like:
        - DrawText(x, y, "Hello", font=bold)
        - DrawText(x+dx, y, "World!", font=bold+italic)

9. This display list is then passed to the painter:
    -> Rendered onto the screen as text with correct position and styling
"""