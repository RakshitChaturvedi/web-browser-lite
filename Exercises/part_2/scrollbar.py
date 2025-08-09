from Exercises.part_2.url import URL
import tkinter

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100

def lex(body):
    text = ""
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            text += c
    return text

def layout(text):
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP

    for c in text:
        display_list.append((cursor_x, cursor_y, c))
        cursor_x += HSTEP
        if cursor_x + HSTEP >= WIDTH:
            cursor_y += VSTEP
            cursor_x = HSTEP
    
    return display_list

class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window, 
            width= WIDTH,
            height= HEIGHT
        )
        self.canvas.pack(fill="both", )

        self.scroll = 0
        self.display_list = []

        self.window.bind("<Down>", self.scrolldown)
        self.window.bind("<Up>", self.scrollup)
        self.window.bind("<MouseWheel>", self.mouse_scroll)

    def draw(self):
        self.canvas.delete("all")
        if not self.display_list: return
        doc_height = self.display_list[-1][1] + VSTEP

        if doc_height > HEIGHT:
            scrollbar_height = HEIGHT * (HEIGHT / doc_height)
            scrollbar_y = HEIGHT * (self.scroll / doc_height)
            self.canvas.create_rectangle(
                WIDTH - 10,     # x1: 10px from right edge
                scrollbar_y,    # y1: top of scrollbar
                WIDTH,          # x2: right edge
                scrollbar_y + scrollbar_height, # y2: bottom of scrollbar
                fill = "blue",  # color
                width = 0       # no border
            )
        for x,y,c in self.display_list:
            if y > self.scroll + HEIGHT: continue
            if y + VSTEP < self.scroll: continue
            self.canvas.create_text(x, y - self.scroll, text=c)
    
    def load(self, url):
        body = url.request()
        text = lex(body)
        self.display_list = layout(text)
        self.draw()
    
    def scrolldown(self, e):
        if not self.display_list: return
        max_y = self.display_list[-1][1] + VSTEP - HEIGHT # y position of last char + one line height, minus window height
        self.scroll = min(self.scroll + SCROLL_STEP, max_y)
        self.draw()
    
    def scrollup(self, e):
        self.scroll = max(0, self.scroll - SCROLL_STEP)
        self.draw()

    def mouse_scroll(self, e):
        if not self.display_list: return
        max_y = self.display_list[-1][1] + VSTEP - HEIGHT
        new_scroll = self.scroll - e.delta
        self.scroll = max(0, min(new_scroll, max_y))
        self.draw()
            
if __name__ == "__main__":
    import sys

    Browser().load(URL(sys.argv[1]))
    tkinter.mainloop()