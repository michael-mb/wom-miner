from lxml.etree import ElementTree, _Element
from lxml import etree
from lxml.html import document_fromstring, HtmlElement
import re

import logging
log = logging.getLogger(__name__)

# This was a fragment of the old parsing algorithm from preprocessing index.
# Now we have our own preprocessing.

# def parse_html(html) -> _Element:
#     # If the HTML includes an XML encoding declaration, load the document in byte mode
#     xml_declaration = re.findall(r'<\?xml[^>]*encoding=".*?".*?>', html)
#     if xml_declaration:
#         # see https://stackoverflow.com/a/38244227
#         html = bytes(bytearray(html, encoding="utf-8"))

#     parser = etree.XMLParser(ns_clean=True, recover=True, encoding="utf-8")
#     root = etree.fromstring(html, parser=parser)

#     if root is None:
#         raise RuntimeError("Malformed or empty document")
#     return root


def innertext(elem:_Element):
    # source: https://stackoverflow.com/a/18114318
    return (elem.text or '') + ' ' + ' '.join(innertext(e) for e in elem) + ' ' + (elem.tail or '')


def normalize(s:str):
    # Due to the split logic, we must also strip leading/trailing commas
    return " ".join(s.split()).strip().strip(",")