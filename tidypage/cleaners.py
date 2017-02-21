import sys
from bs4 import BeautifulSoup,Comment

def clean_tag(doc):
    for tag in doc.find_all(["style", "script","form", "textarea", "input", "iframe", "select","frame", "link"]):
        tag.extract()
    comments = doc.findAll(text=lambda text:isinstance(text, Comment))
    [comment.extract() for comment in comments]

def is_ad_block(elem):
    link_num = 0
    link_text_len = 0
    text_len = 0
    g = elem.recursiveChildGenerator()
    while True:
        try:
            tag = g.next()
            if not isinstance(tag,unicode):
                if tag.name == "a":
                    link_num += 1
                    link_text_len += len(tag.text.strip())
            else:
                text_len += len(tag)
        except StopIteration:
            break
    link_density = float(link_text_len) / max(text_len, 1)
    if link_density >= 0.5:
        #print "tag<%s> class:%s\t%f\t%d" %(elem.name,elem.attrs, link_density, text_len)
        return True
    elif text_len - link_num < 30:
        #print "tag<%s> class:%s\t%f\t%d" %(elem.name, elem.attrs, link_density, text_len)
        return True
    else:
        return False

def no_block_children(tag):
    if tag.name == "div" or tag.name == "section":
        g = tag.find_all(["div", "dl", "ul", "table", "section"])
        if len(g) == 0:
            return True
        else:
            return False
    else:
        return True

def clean_spam(doc):
    """clean the ad block and link block"""
    for tag in doc.find_all(["div","ol", "dl", "ul", "table", "section"]):
        if no_block_children(tag) and is_ad_block(tag):
            tag.extract()
