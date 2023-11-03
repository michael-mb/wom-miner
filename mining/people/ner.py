"""Performs Named Entity Recognition with SpaCy on a plaintext"""

import spacy
from spacy.language import Language
from spacy.tokens import Doc, Span
from womutils.exceptions import IgnoreThisPageException
import re
from people import name_analysis, html_analysis, email_analysis
from people.types import Person, WebPage
from typing import List
from preprocessing.ner import get_english_model, get_german_model
from lxml.etree import _Element
from lxml import etree

import logging
log = logging.getLogger(__name__)

def nlp(text:str, lang:str|None) -> Doc:
    """Performs a Named Entity Recognition on the given text"""

    # we reuse the model methods from Preprocessing
    if lang == "de":
        model = get_german_model()
    elif lang == "en":
        model = get_english_model()
    else:
        raise IgnoreThisPageException("Illegal language: " + str(lang))
    return model(text)


def should_ignore_whole_line(line:str):
    """Returns True if the whole name should be excluded from NER"""

    # Ignore mostly empty lines (lesser than 5 characters and lesser than 2 words)
    # We expect at least one firstname and one lastname
    # The shortest possible name is something like "Li Li" which has 5 characters
    if len(line.strip()) < 5 or len(line.split()) < 2:
        return True

    # Ignore lines with years: These are strong indicators for publications
    # We look for names that stand alone to identify a single person working at somewhere
    if re.findall(r"\d{4}", line):
        return True

    # SpaCy can only handle 1GB text
    if len(line) >= 1_000_000:
        return True

    return False


def should_ignore_named_entity(name:Span):
    """Returns True if the passed Named Entity (found by NER) is invalid"""

    # Still require at least 2 words for a name
    # Note that len(span) actually counts words
    if len(name) < 2:
        return True
    
    # Ignore names not matching a specific pattern for firstname, lastname and middle name
    if not name_analysis.is_normalized_name(name.text):
        return True
    
    return False


def find_link_for_person(root:_Element, name:str, url:str) -> str:
    """Returns a hyperlink found in the name of the person"""
    # try:
    #     root = html_analysis.parse_html(html)
    # except etree.XMLSyntaxError:
    #     log.warning(f"NER/Find link: Malformed HTML in {url}")
    #     return ""
    # except Exception as e:
    #     log.warning(f"NER/Find link: Exception for HTML processing in {url}: " + str(e))
    #     return ""
    # return root.xpath(f".//a[//*[contains(text(),{name})]]/@href")
    # return root.xpath(f".//a[.//*[contains(text(),{name})]]/@href")
    # log.debug(name)

    # Note because names can contain ' e.g. Luca Dall'Ava (https://esaga.uni-due.de/marc.levine/ERC/Members/)
    # Therefore we must use " in xpath
    hyperlinks = root.xpath(f'.//a[contains(normalize-space(.),"{name}")]/@href')
    return next(iter(hyperlinks), "")


def assign_email_addresses(people:List[Person], html:str):
    """Selects the best email address for each passed person and saves it into the person object"""
    # Note that technically "extract_email_addresses" takes plaintext, but it also works with HTML strings
    mails = email_analysis.extract_email_addresses(html)
    log.debug(mails)
    log.debug([p.name for p in people])

    cursor = -1
    for p in people:
        # Since 'people' is sorted by the occurrence and 'mails' also, we have a good chance
        # that we find the correct addresses if we search sequentially. This is implemented
        # as a cursor placed in the 'mails' list after the last successful match.

        # Select the first occurrence where the email is a match
        # Only iterate over the mail elements _after_ the cursor
        start_with_index = cursor+1
        log.debug(f"Will iterate over {mails[start_with_index:]}")
        mail_index, mail = next(((idx,mail) for idx,mail in enumerate(mails[start_with_index:], start=start_with_index) if email_analysis.email_match_name(p.name, mail)), (None, None))
        if mail_index is not None and mail:
            log.debug(f"Found mail {mail} for {p.name} at index {mail_index}")
            p.email = mail
            cursor = mail_index
        else:
            log.debug(f"Did not found mail for {p.name}")


def extract_people_from_plaintext(page:WebPage) -> List[Person]:
    """Returns all people found by Named Entity Recognition over the plaintext"""

    # Split table separators from Trafilatura
    # txt = txt.replace("|", "\n")

    people = []
    log.debug(page.txt.splitlines())
    for line in page.txt.splitlines():

        if should_ignore_whole_line(line):
            continue

        # Cut off "Dr." and "Prof.". Otherwise SpaCy's DE model won't recognize these names
        # Titles are added later
        if page.lang == 'de':
            line = line.replace("Dr.", "")
            line = line.replace("Prof.", "")

        doc = nlp(line.strip(), page.lang)
        # "doc.ents" returns a list of Spans (https://spacy.io/api/span)
        # Note that SpaCy counts the position word-wise

        # Filter person names
        # PER is for the German model, PERSON for the English model
        named_entities = list(filter(lambda ne: (ne.label_ == 'PER' or ne.label_ == 'PERSON'), doc.ents))

        for named_entity in named_entities:

            if should_ignore_named_entity(named_entity):
                continue

            p = Person(named_entity.text, "txt")
            p.title = name_analysis.compute_title(page.txt, p.name)
            p.homepage = find_link_for_person(page.root, p.name, page.url)

            people.append(p)
        # log.info(f"\n{line}\n->{','.join(names)}")
    
    assign_email_addresses(people, page.html)
    
    return people


    