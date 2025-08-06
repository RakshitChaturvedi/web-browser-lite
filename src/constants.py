import tkinter
import tkinter.font

WIDTH, HEIGHT = 800, 600 # Width and height of the console
HSTEP, VSTEP = 13, 18 # Width and Height of the characters
SCROLL_STEP = 100 
FONTS = {}
BLOCK_ELEMENTS = [
    "html", "body", "article", "section", "nav", "aside",
    "h1", "h2", "h3", "h4", "h5", "h6", "hgroup", "header",
    "footer", "address", "p", "hr", "pre", "blockquote",
    "ol", "ul", "menu", "li", "dl", "dt", "dd", "figure",
    "figcaption", "main", "div", "table", "form", "fieldset",
    "legend", "details", "summary"
] 

# CACHING FONTS
def get_font(size, weight, style):
    key = (size, weight, style) # unique identifier for a font style

    # if font doesnt exist, create it
    if key not in FONTS:
        font = tkinter.font.Font(size=size, weight=weight, slant=style)
        label = tkinter.Label(font=font)
        FONTS[key] = (font, label)

    # return only font, not label
    return FONTS[key][0]

class DrawText:
    def __init__(self, x1, y1, text, font):
        self.top = y1
        self.left = x1
        self.text = text
        self.font = font
        self.bottom = y1 + font.metrics("linespace")

    def execute(self, scroll, canvas):
        canvas.create_text(
            self.left, self.top - scroll,
            text = self.text,
            font = self.font, 
            anchor = 'nw'
        )

class DrawRect:
    def __init__(self, x1, y1, x2, y2, color):
        self.top = y1
        self.bottom = y2
        self.left = x1
        self.right = x2

        self.color = color

    def execute(self, scroll, canvas):
        canvas.create_rectangle(
            self.left, self.top - scroll,
            self.right, self.bottom - scroll,
            width = 0,
            fill = self.color
        ) 

def paint_tree(layout_object, display_list):
    display_list.extend(layout_object.paint())

    for child in layout_object.children:
        paint_tree(child, display_list)