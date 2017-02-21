import os
import unittest
from tidypage import Document

HTMLS = os.path.join(os.path.dirname(__file__), 'htmls')

class TestContentOnly(unittest.TestCase):
    def test_content_parser(self):
        html = open(os.path.join(HTMLS, "aleyna-tilki-basrol-oynamaya-hazirlaniyor.html")).read()
        doc = Document(html, True, "http://www.test.com/test.html")
        doc.content()


