#-*- coding: UTF-8 -*-
from bs4 import BeautifulSoup
import logging
import sys
import re
from .cleaners import clean_tag
from .cleaners import clean_spam
import StringIO, gzip
log = logging.getLogger("tidypage.extractor")

TEXT_TAG_COLLECTION = {"p":5, "span":4, "font":3, "i":2, "b":1, "pre": 1}

REGEXES = {
    'positiveRe': re.compile('article|body|content|entry|hentry|main|page|pagination|post|text|blog|story', re.I),
    'negativeRe': re.compile('combx|comment|com-|contact|foot|footer|footnote|masthead|media|meta|outbrain|promo|related|scroll|shoutbox|sidebar|sponsor|shopping|tags|tool|widget|recommend|clearfix', re.I),
}

class Document:
    """Class to build a dom tree from html."""
    def __init__(self, html,isForeign = True, url=None):
        """Generate the document
        :param html: string of the html content.
        :param url: url of the html
        """
        self.url = url
        self.html = html
        self.link_num = 0
        self.link_text_len = 0
        self.total_text_tag_num = 0
        self.total_text_len = 0
        self.text_tag_num = 0
        self.text_tag_text_len = 0
        self.is_foreign = isForeign
        
        self.doc = self._parse(self.html)
        clean_tag(self.doc)

    def _parse(self, html):
        soup = BeautifulSoup(html, "lxml")
        return soup

    def html_title(self):
        """Returns document title"""
        return self.doc.title.string

    def prettify(self):
        """Returns prettify document"""
        return self.doc.prettify("utf-8")


    def get_dom(self):
        return self.doc

    def content(self):
        """get the content of html page"""
        clean_spam(self.doc)
        candidates = self.get_candidates()
        best_node = self.best_candidates(candidates)
        if best_node:
            return self.purify(best_node["elem"])
        else:
            return None

    def is_index_page(self):
        """estimate the page is index page or not"""
        link_density = self.get_link_tag_density(self.doc)
        mean_text_block = float(self.text_tag_text_len) / max(self.text_tag_num, 1)
        if link_density > 0.45:
            return True
        elif link_density > 0.30:
            """the foreign language page is different from chinese page"""
            if self.is_foreign and mean_text_block < 30:
                return True
            elif not self.is_foreign and mean_text_block < 20:
                return True
            else:
                return False
        else:
            return False

    def walk(self):
        """walk the dom tree and get the info of the page"""
        g = self.doc.recursiveChildGenerator()
        while True:
            try:
                tag = g.next()
                if not isinstance(tag,unicode):
                    if tag.name == "a" and ((self.is_foreign and len(tag.text) > 10) or (not self.is_foreign and len(tag.text) > 4)):
                        self.link_num += 1
                        self.link_text_len += len(tag.getText())
                    elif TEXT_TAG_COLLECTION.has_key(tag.name):
                        tag_text = tag.contents[0] if len(tag.contents) > 0 and isinstance (tag.contents[0], unicode) else ""
                        if len(tag_text) > 0:
                            self.text_tag_num += 1
                            self.text_tag_text_len += len(tag_text)
                else:
                    self.total_text_len += len(tag)
            except StopIteration:
                break

    def content_block_len(self):
        block_size = 3
        block_array = map(len, self.doc.strings)
        block_set = []
        for i in range(0, len(block_array) - block_size):
            block_text_len = 0
            for j in range(i, i + block_size):
                block_text_len += (block_array[j] - 1)
            block_set.append(block_text_len)
        blk_num = len(block_set)
        start = -1
        end = -1
        max_text_len = 0
        cur_text_len = 0
        i = 0
        
        while i < blk_num:
            if block_set[i] == 0:
                if cur_text_len > max_text_len:
                    max_text_len = cur_text_len
                    start = tmp
                    end = i - 1
                cur_text_len = 0
                i += 1
                continue
            if cur_text_len == 0:
                tmp = i
            cur_text_len += block_set[i]
            i += 1
        
    
    def text_weight(self, elem):
        content_score = 1
        long_text_line = 0
        block_size = 3
        inner_text = ""
        for string in elem.stripped_strings:
            if (self.is_foreign and len(string) > 100) or (not self.is_foreign and len(string) > 50):
                long_text_line += 1
                inner_text += string
            else:
                inner_text += string
        """for punch"""
        if len(inner_text) > 0:
            if self.is_foreign:
                splits = re.split(u",|\.|\?", inner_text)
                content_score += len(splits)
            else:
                splits = re.split(u"|，|。|？", inner_text)
                content_score += len(splits)
        """for text len"""
        if self.is_foreign:
            content_score += min((len(inner_text) / 100), 5)
        else:
            content_score += min((len(inner_text) / 20), 5)

        """for text block"""
        block_array = map(len, elem.strings)
        block_set = []
        for i in range(0, len(block_array) - block_size):
            block_text_len = 0
            for j in range(i, i + block_size):
                block_text_len += (block_array[j] - 1)
            block_set.append(block_text_len)
        short_block = 0
        blk_text_len = 0
        for block in block_set:
            blk_text_len += block
            if (self.is_foreign and block < 50) or (not self.is_foreign and block < 10):
                short_block += 1
        short_block_ratio = float(short_block) / max(len(block_set), 1)
        if short_block_ratio > 0.3:
            content_score -= 10
        return content_score
    
    def class_weight(self, elem):
        weight = 0
        for feature in [elem.get('class', None), elem.get('id', None)]:
            try:
                if feature:
                    if REGEXES['negativeRe'].search(feature):
                        weight -= 25

                    if REGEXES['positiveRe'].search(feature):
                        weight += 25
            except:
                continue
        return weight

    def node_weight(self, elem):
        content_score = 0
        name = elem.name
        if name == "div":
            content_score += 5
        elif name in ["pre", "td", "blockquote"]:
            content_score += 3
        elif name in ["address", "ol", "ul", "dl", "dd", "dt", "li", "form"]:
            content_score -= 3
        elif name in ["h1", "h2", "h3", "h4", "h5", "h6", "th"]:
            content_score -= 5
        return content_score

    def score_node(self, elem):
        class_score = self.class_weight(elem)
        node_score = self.node_weight(elem)
        content_score = class_score + node_score
        return {
            'score': content_score,
            'elem': elem
        } 

    def get_candidates(self):
        candidates = {}
        g = self.doc.recursiveChildGenerator()
        while True:
            try:
                tag = g.next()
                #text node
                if isinstance(tag,unicode):
                    if (self.is_foreign and len(tag) > 40) or (not self.is_foreign and len(tag) > 20):
                        text_tag = tag.parent
                        if text_tag is None:
                            continue
                        if text_tag.name not in ["p", "span", "td", "pre", "i", "b"]:
                            continue
                        parent_node = text_tag.parent
                        if parent_node is not None and parent_node not in candidates:
                            candidates[parent_node] = self.score_node(parent_node)
                            candidates[parent_node]['score'] += self.text_weight(parent_node)
                            link_density = self.get_link_tag_density(parent_node)
                            candidates[parent_node]['score'] *= (1 - link_density)
                        
                        grand_parent_node = parent_node.parent
                        if grand_parent_node is not None and grand_parent_node not in candidates:
                            candidates[grand_parent_node] = self.score_node(grand_parent_node)
                            candidates[grand_parent_node]['score'] += self.text_weight(grand_parent_node) / 2.0
                            link_density = self.get_link_tag_density(grand_parent_node)
                            candidates[grand_parent_node]['score'] *= (1 - link_density)

                    else:
                        continue
            except StopIteration:
                break
        return candidates
        
    def get_link_tag_density(self, elem):
        """get the link tag density"""
        return float(self.link_text_len) / max(self.total_text_len, 1)

    def best_candidates(self, candidates):
        if not candidates:
            return None

        sorted_candidates = sorted(
            candidates.values(), 
            key=lambda x: x['score'],
            reverse=True
        )
        for candidate in sorted_candidates[:3]:
            elem = candidate['elem']
            log.info("Top 3 : %6.3f %s" % (
                candidate['score'],
                (elem)))

        best_candidate = sorted_candidates[0]
        return best_candidate 

    def purify(self, best_elem):
        del best_elem['class']
        del best_elem['id']
        g = best_elem.recursiveChildGenerator()
        while True:
            try:
                tag = g.next()
                if tag is None:
                    break
                #text node
                if not isinstance(tag,unicode) and tag is not None:
                    if tag.name == 'a':
                        tag.unwrap()
                    elif tag.name == 'img':
                        img_src = tag.get('src')
                        data_src = tag.get('data-src')
                        if img_src is None and data_src is None:
                            tag.extract()
                        else:
                            if data_src is not None:
                                if data_src.startswith("http"):
                                    img_src = data_src
                                else:
                                    img_src = self.domain + data_src
                            else:
                                if not img_src.startswith("http"):
                                    img_src = self.domain + img_src
                        attr_names = [attr for attr in tag.attrs]
                        for attr in attr_names:
                            del tag[attr]
                        tag['src'] = img_src
                    del tag['class']
                    del tag['id']
                    continue
            except StopIteration:
                break
        return best_elem.prettify("utf-8")


def main():
    VERBOSITY = {
        1: logging.WARNING,
        2: logging.INFO,
        3: logging.DEBUG
    }

    from optparse import OptionParser
    parser = OptionParser(usage="%prog: [options] [file]")
    parser.add_option('-v', '--verbose', action='count', default=0)
    parser.add_option('-u', '--url', default=None, help="use URL instead of a local file")
    parser.add_option('-l', '--log', default=None, help="save logs into file (appended)")
    parser.add_option('-f', '--foreign', default=False, action='store_true', help="the html language is foreign or not")
    (options, args) = parser.parse_args()

    if options.verbose:
        logging.basicConfig(level=VERBOSITY[options.verbose], filename=options.log,
            format='%(asctime)s: %(levelname)s: %(message)s (at %(filename)s: %(lineno)d)')
    if not (len(args) == 1 or options.url):
        parser.print_help()
        sys.exit(1)

    html_fp = None
    if options.url:
        headers = {'User-Agent': 'Mozilla/5.0'}
        if sys.version_info[0] == 3:
            import urllib.request, urllib.parse, urllib.error, http.cookiejar
            request = urllib.request.Request(options.url, None, headers)
        else:
            import urllib2, cookielib
            request = urllib2.Request(options.url, None, headers)
    else:
        html_fp = open(args[0], 'rt')
    
    try:
        if options.url:
            if sys.version_info[0] == 3:
                opener = urllib.build_opener(urllib2.HTTPCookieProcessor(cookielib.CookieJar()))
            else:
                opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.CookieJar()))
            conn = opener.open(request)
            html_str = conn.read()
            if conn.headers.get('html-Encoding') == 'gzip' or conn.headers.get('Content-Encoding') == 'gzip':
                stream = StringIO.StringIO(html_str)
                gzipper = gzip.GzipFile(fileobj=stream)
                html_str = gzipper.read()
        else:
            html_str = html_fp.read()
        doc = Document(html_str, options.foreign, url=options.url)
        doc.walk()
        doc.content()
    finally:
        if html_fp:
            html_fp.close()

if __name__ == '__main__':
    main()
