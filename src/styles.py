import os
from src.layout import Element
from src.constants import INHERITED_PROPERTIES

class TagSelector:
    def __init__(self, tag):
        self.tag = tag
        self.priority = 1

    def matches(self, node):    # test whether selector matches an element
        return isinstance(node, Element) and self.tag == node.tag
    
    def __repr__(self):
        return f"TagSelector('{self.tag}')"
    
class DescendantSelector:
    def __init__(self, ancestor, descendant):
        self.ancestor = ancestor
        self.descendant = descendant
        self.priority = ancestor.priority + descendant.priority

    # check if node matches the descendant part of selector, 
    # and if any of its ancestors match ancestor selector
    def matches(self, node): 
        if not self.descendant.matches(node): return False      # if node isnt the kind of element the descendant targets, return false
        while node.parent:                                      # walk up the dom tree
            if self.ancestor.matches(node.parent): return True  # if any parent matches the ancestor selector, return True
            node = node.parent                                  # go one level up and repeat
        return False                                            # if no ancestor matches after traversing up, return false
    
    def __repr__(self):
        return f"DescendantSelector({self.ancestor}, {self.descendant})"
    
class CSSParser:
    def __init__(self, s):
        self.s = s          # string
        self.i = 0          # indentation
    
    # Increment the index i past every whitespace character ( no parsed data for whitespaces )
    def whitespace(self):   
        while self.i < len(self.s) and self.s[self.i].isspace():
            self.i += 1

    # String tokenizer
    def word(self):        
        start = self.i
        # Loop over the string, char by char, accept alphanumeric and #-,% special character. 
        # Stops when a strange character encountered
        while self.i < len(self.s):
            if self.s[self.i].isalnum() or self.s[self.i] in "#-.%":
                self.i += 1
            else:
                break
        # If self.i never moved forward, throw an error
        if not (self.i > start):
            raise Exception("Parsing error")
        # Return the slice of string from start to end of the while loop
        return self.s[start:self.i]
    
    # Check whether next character in input string is exactly whats expected 
    # (a literal char like :, {, {, ; etc. whatever we pass as arguement),
    # If yes, increment the index.
    def literal(self, literal):
        if not (self.i < len(self.s) and self.s[self.i] == literal):
            raise Exception("Parsing error")
        self.i += 1
        """
        example string: color: red;
        after parsing "color" with word(), you call -> self.literal(':')
        this verifies that next char is :
        at last, call self.literal(';') to confirm end of rule.
        """

    def pair(self):
        prop = self.word()
        self.whitespace()
        self.literal(":")
        self.whitespace()
        val = self.word()
        return prop.casefold(), val
    
        """
        Example: "color : red ; "
        i= 0
        prop = self.word() --> prop = color, i comes at end of word color
        self.whitespace() --> i is at the literal : now
        self.literal(":") --> checks if current char is :, true, i is at whitespace before red now
        self.whitespace() --> i is at char r of word red
        val = self.word() --> val = red
        return prop.casefold ("color") and val ("red")
        """
    
    # Uses the pair function and also checks for the ";" at the end of rule. 
    # Create a dictiionary of key value pairs.
    def body(self): 
        pairs = {}
        while self.i < len(self.s) and self.s[self.i] != "}":
            try:
                prop, val = self.pair()
                pairs[prop.casefold()] = val
                self.whitespace()
                self.literal(";")
                self.whitespace()
            except Exception:
                why = self.ignore_until([";", "}"])
                if why == ";":
                    self.literal(";")
                    self.whitespace()
                else:
                    break
        return pairs
    
    # Error recovery mechanism
    # Skips over char in i/p string self.s until it finds one of char listed in chars.
    def ignore_until(self, chars):
        while self.i < len(self.s):
            if self.s[self.i] in chars:
                return self.s[self.i]
            else:
                self.i += 1
        return None 
        # Used when parser encounters invalid / unexpected i/p 
        # and wants to resume parsing at a known boundary
    
    def selector(self):
        # .word() parses first tag name (div in div p span) 
        # TagSelector wraps it in a selector object and checks for nodes with this tag
        out = TagSelector(self.word().casefold())
        self.whitespace()
        while self.i < len(self.s) and self.s[self.i] != "{":   # keep looping until { is hit
            tag = self.word()                                   # parse the tag name, first iteration, tag = div
            descendant = TagSelector(tag.casefold())            # wrap in tagselector, which checks if current node has the current tag
            out = DescendantSelector(out, descendant)           # nests the prev selector inside a new descendantselector
            self.whitespace()                                   # indents over whitespaces.
        return out
        """
        Example: div p span { color: red; }
        DescendantSelector(
            ancestor = DescendantSelector(
                ancestor = TagSelector("div"),
                descendant = TagSelector("p")
            ),
            descendant = TagSelector("span")
        )
        """
    
    def parse(self):
        rules = []
        while self.i < len(self.s):
            try:
                self.whitespace()
                selector = self.selector()
                self.literal("{")
                self.whitespace()
                body = self.body()
                self.literal("}")
                rules.append((selector, body))
            except Exception:
                why = self.ignore_until(["}"])
                if why == "}":
                    self.literal("}")
                    self.whitespace()
                else:
                    break
        return rules

script_dir = os.path.dirname(os.path.abspath(__file__))
css_path = os.path.join(script_dir, "browser.css")
DEFAULT_STYLE_SHEET = CSSParser(open(css_path).read()).parse()

def style(node, rules):
    node.style= {}
    for property, default_value in INHERITED_PROPERTIES.items():
        if node.parent:
            node.style[property] = node.parent.style[property]
        else:
            node.style[property] = default_value
    for selector, body in rules:
        if not selector.matches(node): continue
        for property, value in body.items():
            node.style[property] = value

    # If its an html element with style, use CSSParser to parse the style string. 
    # Store the parsed properties in node.style
    if isinstance(node, Element) and "style" in node.attributes:
        pairs = CSSParser(node.attributes["style"]).body()
        # recursively do it for all child nodes
        for property, value in pairs.items():   
            node.style[property] = value

    # If font sizes are in percentages
    if node.style["font-size"].endswith("%"):
        # if node has parent, use its font size, if not,fallback to default
        if node.parent:
            parent_font_size = node.parent.style["font-size"]
        else:
            parent_font_size = INHERITED_PROPERTIES["font-size"]
        node_pct = float(node.style["font-size"][:-1]) / 100            # if 120%, strip % -> 120, / 100 -> 1.2
        parent_px = float(parent_font_size[:-2])                        # if parent_px 16px, strip px -> 16 -> 16.0
        node.style["font-size"] = str(node_pct * parent_px) + "px"      # 1.2 * 16 = 19.2, final font size = 19.2px
        
    for child in node.children:
        style(child, rules)
    """
    Example: <div style="color: red"> <span style = "font-size: 20px">Text</span> </div>
    after style(root_node):
        root_node.style == {"color": "red"}
        root_node.children[0].style == {"font-size": "20px"}
    """
    
def cascade_priority(rule):
    selector, body = rule
    return selector.priority