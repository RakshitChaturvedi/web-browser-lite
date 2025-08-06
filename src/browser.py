from src.url_loader import URL
import tkinter
import tkinter.font
from src.html_parser import Text, Element, HTMLParser      

WIDTH, HEIGHT = 800, 600 # Width and height of the console
HSTEP, VSTEP = 13, 18 # Width and Height of the characters
SCROLL_STEP = 100 
FONTS = {}

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

class Layout:
    def __init__(self, tree):
        self.display_list= []

        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.weight = "normal"
        self.style = "roman"
        self.size = 16

        self.line = []
        self.recurse(tree)
        self.flush()

    def recurse(self, tree):
        if isinstance(tree, Text):
            for word in tree.text.split():
                self.word(word)
        else:
            self.open_tag(tree.tag)
            for child in tree.children:
                self.recurse(child)
            self.close_tag(tree.tag)

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
    
    def word(self, word): # Add word to current line and manage cursor position
        font = get_font(self.size, self.weight, self.style)
        w = font.measure(word)      
        if self.cursor_x + w >= WIDTH - HSTEP:
            self.flush()
        self.line.append((self.cursor_x, word, font))
        self.cursor_x += w + font.measure(" ")
    
    def flush(self): # Align words, Add to display list, update cursor_x and y fiels.
        if not self.line: return
        metrics = [font.metrics() for x, word, font in self.line]
        max_ascent = max([font.metrics("ascent")        
                          for x, word, font in self.line])  
        baseline = self.cursor_y + 1.25 * max_ascent    # adjusts the baseline
        for x, word, font in self.line:
            y = baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font))
        max_descent = max([metric["descent"] for metric in metrics])

        # update cursor_x, cursor_y and line
        self.cursor_x = HSTEP
        self.cursor_y = baseline + 1.25*max_descent
        self.line = []

class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window,
            width=WIDTH,
            height=HEIGHT            
        )
        self.canvas.pack()

        self.scroll = 0
        self.window.bind("<Down>", self.scrolldown)
        self.window.bind("<Up>", self.scrollup)

    def scrolldown(self, e):
        self.scroll += SCROLL_STEP
        self.draw()
    
    def scrollup(self, e):
        self.scroll -= SCROLL_STEP
        self.draw()
    
    def load(self, url):
        body = url.request()
        self.nodes = HTMLParser(body).parse()
        self.display_list = Layout(self.nodes).display_list
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        for x, y, word, font in self.display_list:
            if y > self.scroll + HEIGHT: continue
            if y + font.metrics("linespace") < self.scroll: continue
            self.canvas.create_text(x, y - self.scroll, text=word, font=font, anchor="nw")

if __name__ == "__main__":
    import sys
    Browser().load(URL(sys.argv[1]))
    tkinter.mainloop()
        