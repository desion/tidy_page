import os
import unittest
from tidypage import Document

HTMLS = os.path.join(os.path.dirname(__file__), 'htmls')

class TestArticleContent(unittest.TestCase):
    def test_best_elem_is_root_and_passing(self):
        html = open(os.path.join(HTMLS, "aleyna-tilki-basrol-oynamaya-hazirlaniyor.html")).read()
        doc = Document(html, True, "http://www.test.com/test.html")
        print doc.content()


