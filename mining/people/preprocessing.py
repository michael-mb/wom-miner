"""Does preprocessing on the rawdata HTML pages"""

from people.types import WebPage
from womutils.exceptions import IgnoreThisPageException
import lxml.html
from lxml.etree import Element
from lxml.html import HtmlElement
from lxml import etree
from langdetect import detect_langs
from langdetect.language import Language
import re

import logging
log = logging.getLogger(__name__)

def clean_html(doc:WebPage):
    """Extracts and cleans HTML """

    # see https://stackoverflow.com/a/38244227
    xml_declaration = bool(re.findall(r'<\?xml[^>]*encoding=".*?".*?>', doc.html))

    # Using a special parser for HTML
    # https://lxml.de/api/lxml.etree.HTMLParser-class.html
    # https://lxml.de/lxmlhtml.html#html-element-methods
    # https://lxml.de/api/lxml.html.HtmlElement-class.html

    # Parse HTML into a HtmlElement tree
    # parser = etree.HTMLParser(recover=True, no_network=True, remove_blank_text=True, remove_comments=True, remove_pis=True, collect_ids=False, encoding="utf-8")
    try:
        # print(doc.html[0:100])
        # If the HTML includes an XML encoding declaration, we must load the document in byte mode
        # see https://stackoverflow.com/a/38244227
        root = lxml.html.document_fromstring(doc.html if not xml_declaration else bytes(bytearray(doc.html, encoding="utf-8"))) # ,parser DOES NOT WORK
    except Exception:
        log.exception("Error while parsing HTML")
        raise IgnoreThisPageException("Error while parsing HTML")
    
    # print(type(root))

    doc.root = root

    root = root.find("body")
    if root is None:
        raise IgnoreThisPageException("No body")
    if root.find(".//div") is None:
        raise IgnoreThisPageException("No div in HTML")
    
    # print(type(root))

    # print("\n".join([s.strip() for s in root.xpath("//text()")]))
    
    # Drop unwanted tags, see https://www.w3schools.com/TAGS/default.asp
    for not_wanted in ['header', 'nav', 'footer', 'script', 'pre', 'code', 'canvas', "dialog", "iframe", "noscript", "source", "svg", "video", "track", "style", "link"]:
        for elem in root.findall(".//" + not_wanted):
            # print(type(elem))
            log.debug(f"{not_wanted} was dropped from tree")
            elem.drop_tree()
    
    # print("\n".join([s.strip() for s in root.xpath("//text()")]))

    # Remove formatting tags, but keep content. See e.g.
    # - https://www.uni-due.de/anglistik/applied_linguistics_didactics/teachers
    # - https://www.mikro.wiwi.uni-due.de/team/
    # - https://www.uni-due.de/zmb/members/index.php

    # TODO Dies führt zu mehr nicht erkannten Namen, siehe https://www.uni-due.de/ekfg/mitglieder.shtml
    # for drop in ["strong", "i", "emph", "span"]:
    #     for elem in root.findall(".//" + drop):
    #         # print(type(elem))
    #         # Add spaces between the removed tag
    #         # TODO https://cinch.uni-due.de/team/mitglieder/ Dies führt zu nicht mehr erkannten Titeln
    #         # if elem.text:
    #         #     elem.text=" " + str(elem.text) + " "
    #         elem.drop_tag()

    main_tag = root.find(".//main")
    if main_tag is not None:
        root = main_tag
    
    if root is None:
        raise IgnoreThisPageException("No interesting content in HTML")

    doc.root = root


def extract_txt(doc:WebPage):
    """Extracts plaintext for people recognition and write the plaintext back to the document object"""
    if doc.root is None:
        raise RuntimeError("Cannot extract txt without a root")

    # Only consider non-empty lines ...
    texts = [s.strip() for s in doc.root.xpath("//text()")]
    # print("\n".join(texts))
    # ... and lines that contain at least 4 letters
    # (every name is at least 5 letters long, e.g. "Li Li")
    texts = list(filter(lambda s: len(s) > 5 and len(re.sub("[^a-zA-ZöäüßÖÄÜ]", "", s)) > 4, texts))
    # Normalize whitespaces
    texts = [" ".join(s.split()).strip() for s in texts]
    # print(list(texts))
    doc.txt = "\n".join(texts)
    # log.debug(doc.txt)


def detect_language(doc:WebPage):
    """Performs a language detection and write the best language back to the document object"""

    # https://pypi.org/project/langdetect/#description
    langs = detect_langs(doc.txt)
    log.debug("Languages: " + str(langs))

    # No result
    if not langs:
        doc.lang = ""
        log.warning(f"No language recognized: {doc.url}")
        return
    
    # More results
    langs_filtered = list(filter(lambda x: x.lang == 'de' or x.lang == 'en', langs))

    # No result after filtering
    if not langs_filtered:
        doc.lang = ""
        log.warning(f"Language unsupported, recognized {langs_filtered}: {doc.url}")
        return
    
    # One result
    if len(langs_filtered) == 1:
        doc.lang = langs_filtered[0].lang
        if langs_filtered[0].prob < 0.5:
            log.warning(f"Language uncertain: {langs}, choosed {doc.lang}: {doc.url}")
        return
    
    # Many results: Choose best
    # Since we filtered for DE and EN, we only can get 2 results
    doc.lang = langs_filtered[0].lang if langs_filtered[0].prob >= langs_filtered[1].prob else langs_filtered[1].lang
    log.warning(f"Language uncertain: {langs}, choosed {doc.lang}: {doc.url}")


def extract_web_page(doc:WebPage):
    """Fills the WebPage object with preprocessing data"""
    clean_html(doc)
    extract_txt(doc)
    detect_language(doc)
    log.debug(f"lang={doc.lang}")

