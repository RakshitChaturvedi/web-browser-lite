from src.url_loader import URL
import tkinter
import tkinter.font
from src.html_parser import HTMLParser, Element, Text
from src.layout import DocumentLayout   
from src.constants import WIDTH, HEIGHT, VSTEP, SCROLL_STEP, paint_tree, tree_to_list, get_font, DrawRect, DrawText, Rect, DrawLine, DrawOutline
from src.styles import style, DEFAULT_STYLE_SHEET, CSSParser, cascade_priority

class Tab:
    def __init__(self, tab_height):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window,
            width=WIDTH,
            height=HEIGHT,
            bg="white",           
        )
        self.canvas.pack()
        self.tab_height = tab_height
        self.url = None
        self.scroll = 0

    def draw(self, canvas, offset):
        for cmd in self.display_list:
            if cmd.top > self.scroll + self.tab_height: continue
            if cmd.bottom < self.scroll: continue
            cmd.execute(self.scroll - offset, canvas)

    def load(self, url):
        self.url = url
        body = url.request()
        self.nodes = HTMLParser(body).parse()

        rules = DEFAULT_STYLE_SHEET.copy()
        links = [node.attributes["href"]
                 for node in tree_to_list(self.nodes, [])
                 if isinstance(node, Element)
                 and node.tag == "link"
                 and node.attributes.get("rel") == "stylesheet"
                 and "href" in node.attributes]
        for link in links:
            style_url = url.resolve(link)
            try:
                body = style_url.request()
            except:
                continue
            rules.extend(CSSParser(body).parse())


        style(self.nodes, sorted(rules, key=cascade_priority))

        self.document = DocumentLayout(self.nodes)
        self.document.layout()
        self.display_list = []
        
        paint_tree(self.document, self.display_list)

    def scrolldown(self):
        max_y = max(self.document.height + 2*VSTEP - self.tab_height, 0)
        self.scroll = min(self.scroll + SCROLL_STEP, max_y)
    
    def scrollup(self):
        self.scroll -= SCROLL_STEP

    def click(self, x, y):
        y += self.scroll
        objs = [obj for obj in tree_to_list(self.document, [])
                if obj.x <= x < obj.x + obj.width
                and obj.y <= y < obj.y + obj.height]
        if not objs: return
        elt = objs[-1].node
        while elt:
            if isinstance(elt, Text):
                pass
            elif elt.tag == "a" and "href" in elt.attributes:
                if self.url is not None:
                    url = self.url.resolve(elt.attributes["href"])
                    return self.load(url)
            elt = elt.parent

class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window,
            width=WIDTH,
            height=HEIGHT,
            bg="white",           
        )
        self.canvas.pack()

        self.scroll = 0
        self.window.bind("<Down>", self.handle_down)
        self.window.bind("<Up>", self.handle_up)
        self.window.bind("<Button-1>", self.handle_click)

        self.tabs = []
        self.active_tab = None
        self.chrome = Chrome(self)

    def new_tab(self, url):
        new_tab = Tab(HEIGHT - self.chrome.bottom)
        new_tab.load(url)

        self.active_tab = new_tab
        self.tabs.append(new_tab)
        self.draw()

    def handle_down(self, e):
        if self.active_tab:
            self.active_tab.scrolldown()
            self.draw()
    
    def handle_up(self, e):
        if self.active_tab:
            self.active_tab.scrollup()
            self.draw()
    
    def handle_click(self, e):
        if e.y < self.chrome.bottom:
            self.chrome.click(e.x, e.y)
        elif self.active_tab:
            tab_y = e.y - self.chrome.bottom
            self.active_tab.click(e.x, tab_y)
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        if self.active_tab:
            self.active_tab.draw(self.canvas, self.chrome.bottom)
        for cmd in self.chrome.paint():
            cmd.execute(0, self.canvas)

class Chrome:
    def __init__(self, browser):
        self.browser = browser
        self.font = get_font(20, "normal", "roman")
        self.font_height = self.font.metrics("linespace")
        self.padding = 5
        self.tabbar_top = 0
        self.tabbar_bottom = self.font_height + 2*self.padding
        self.bottom = self.tabbar_bottom
        
        plus_width = self.font.measure("+") + 2*self.padding
        self.newtab_rect = Rect(
            self.padding,
            self.padding,
            self.padding + plus_width,
            self.padding + self.font_height
        )

    def paint(self):
        cmds = []
        cmds.append(DrawRect(
            Rect(0, 0, WIDTH, self.bottom),
            "white"
        ))
        cmds.append(DrawLine(
            0, self.bottom, WIDTH,
            self.bottom, "black", 1
        ))
        cmds.append(DrawOutline(self.newtab_rect, "black", 1))
        cmds.append(DrawText(
            self.newtab_rect.left + self.padding,
            self.newtab_rect.top,
            "+",
            self.font,
            "black"
        )) 

        for i, tab in enumerate(self.browser.tabs):
            bounds = self.tab_rect(i)
            cmds.append(DrawLine(
                bounds.left, 0, bounds.left, bounds.bottom,
                "black", 1
            ))       
            cmds.append(DrawLine(
                bounds.right, 0, bounds.right, bounds.bottom,
                "black", 1
            ))
            cmds.append(DrawText(
                bounds.left + self.padding,
                bounds.top + self.padding,
                "Tab {}".format(i),
                self.font,
                "black"
            ))

            if tab == self.browser.active_tab:
                cmds.append(DrawLine(
                    0, bounds.bottom, bounds.left, bounds.bottom,
                    "black", 1
                ))
                cmds.append(DrawLine(
                    bounds.right, bounds.bottom, WIDTH, bounds.bottom,
                    "black", 1
                ))
        return cmds
    
    def click(self, x, y):
        if self.newtab_rect.containsPoint(x, y):
            self.browser.new_tab(URL("https://browser.engineering/"))
        else:
            for i, tab in enumerate(self.browser.tabs):
                if self.tab_rect(i).containsPoint(x, y):
                    self.browser.active_tab = tab
                    break
    
    def tab_rect(self, i):
        tabs_start = self.newtab_rect.right + self.padding
        tab_width = self.font.measure("Tab X") + 2*self.padding
        return Rect(
            tabs_start + tab_width * i,
            self.tabbar_top,
            tabs_start + tab_width * (i+1),
            self.tabbar_bottom
        )