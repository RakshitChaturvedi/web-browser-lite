from src.constants import WIDTH, HEIGHT, HSTEP, VSTEP, BLOCK_ELEMENTS, get_font, DrawRect, DrawText
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

class BlockLayout:
    def __init__(self, node, parent, previous):
        self.display_list= []           # What gets drawn to screen
        
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
            self.cursor_x = 0
            self.cursor_y = 0
            self.weight = "normal"
            self.style = "roman"
            self.size = 12

            self.line = []
            self.recurse(self.node)
            self.flush()
            self.height = self.cursor_y

        for child in self.children:
            child.layout()

        if mode == "block":
            self.height = sum([child.height for child in self.children])
        else:
            self.height = self.cursor_y

    def recurse(self, node):
        # Recursively lay out inline text nodes and apply tags
        if isinstance(node, Text):
            for word in node.text.split():
                self.word(node,word)
        else:
            if node.tag == "br":
                self.flush()
            for child in node.children:
                self.recurse(child)

    def open_tag(self, tag):
        if tag == "i":
            self.style = "italic"
        elif tag == "b":
            self.weight = "bold"
        elif tag == "small":
            self.size -= 2
        elif tag == "big":
            self.size += 4
        elif tag == "br":
            self.flush()

    def close_tag(self, tag):
        if tag == "i":
            self.style = "roman"
        elif tag == "b":
            self.weight = "normal"
        elif tag == "small":
            self.size += 2
        elif tag == "big":
            self.size -= 4
        elif tag == "p":
            self.flush()
            self.cursor_y += VSTEP
    
    # Align words, Add to display list, update cursor_x and y fiels.
    def flush(self): 
        if not self.line: return
        metrics = [font.metrics() for x, word, font , color in self.line]
        max_ascent = max([font.metrics("ascent") for x, word, font, color in self.line])  
        baseline = self.cursor_y + 1.25 * max_ascent    # adjusts the baseline
        for x, word, font, color in self.line:
            x = self.x + x
            y = self.y + baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font, color))
        self.cursor_x = 0
        self.line = []
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent

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
            self.flush()
        self.line.append((self.cursor_x, word, font, color))
        self.cursor_x += w + font.measure(" ")

    def paint(self):
        cmds = []
        bgcolor = self.node.style.get("background-color", "transparent")

        if bgcolor != "transparent":
            x2, y2 = self.x + self.width, self.y + self.height
            rect = DrawRect(self.x, self.y, x2, y2, bgcolor)
            cmds.append(rect)

        if self.layout_mode() == "inline":
            for x, y, word, font, color in self.display_list:
                cmds.append(DrawText(self.x + x, self.y + y, word, font, color))
        return cmds
    
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