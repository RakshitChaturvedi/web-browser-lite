from src.url_loader import URL
import tkinter
import tkinter.font
         
WIDTH, HEIGHT = 800, 600 # Width and height of the console
HSTEP, VSTEP = 13, 18 # Width and Height of the characters
SCROLL_STEP = 100 
FONTS = {}

class Text:
    def __init__(self, text):
        self.text = text

class Tag:
    def __init__(self, tag):
        self.tag = tag

def lex(body):
    out = []
    buffer = "" # stores either text or tag before they can be used 
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
            if buffer: out.append(Text(buffer))
            buffer = ""
        elif c == ">":
            in_tag = False
            out.append(Tag(buffer))
            buffer=""
        else:
            buffer += c
    if not in_tag and buffer:
        out.append(Text(buffer))
    return out

    """
    If the text is inside <> tags, ignore them, if not, add them to text and return them.
    """

# Caching fonts to avoid repeat creation
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
    def __init__(self, tokens):
        self.display_list= []
        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.weight = "normal"
        self.style = "roman"
        self.size = 16
        self.line = []
        for tok in tokens:
            self.token(tok)
        self.flush()

    def token(self, tok):
        if isinstance(tok, Text):
            for word in tok.text.split():
                self.word(word)
        elif tok.tag == "i":
            style = "italic"
        elif tok.tag == "/i":
            style = "roman"
        elif tok.tag == "b":
            weight = "bold"
        elif tok.tag == "/b":
            weight = "normal"
        elif tok.tag == "small":
            self.size -= 2
        elif tok.tag == "/small":
            self.size += 2
        elif tok.tag == "big":
            self.size += 4
        elif tok.tag == "/big":
            self.size -= 4
        elif tok.tag == "br":
            self.flush()
        elif tok.tag == "/p":
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
        tokens = lex(body)
        self.display_list = Layout(tokens).display_list
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
        