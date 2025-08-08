import tkinter
from src.gui import Browser
from src.url_loader import URL

if __name__ == "__main__":
    import sys
    Browser().new_tab(URL(sys.argv[1]))
    tkinter.mainloop()
        