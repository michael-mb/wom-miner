"""Performs handcrafted Name Recognition on HTML"""
from people.types import Person, TableConfiguration, WebPage
from typing import List
from people.name_analysis import possible_title_candidates, possible_title_candidates_long, compute_title
from people.html_analysis import normalize, innertext
from people import html_analysis, email_analysis
import re
from lxml.etree import _Element

# NOTE: Python's XPath implementation does not support some syntax in this file
#       If you get inexplicable or confusing error messages like "SyntaxError: invalid predicate",
#       please use ".xpath()" instead of ".find()" or ".findall()"
from lxml.etree import Element
from lxml import etree

import logging
log = logging.getLogger(__name__)

xpath_content_rows = ".//tr[not(.//th) and not(.//td[@colspan])]"
"""XPath for iterating over all content rows (does not contain th) and skiping cells with colspan"""

xpath_hyperlink = "//a/@href" # HTML Version
# xpath_hyperlink = "//ref/@target" # Trafilatura XML Version
"""XPath for searching for a hyperlink"""

def xpath_nth_column(col_index:int):
    """XPath for going from a row into the n-th column"""
    # Note that position is not 0-based
    return f".//td[position() = {(col_index+1)}]"


def string_contains_word_in_list(str, list):
    """Returns true if the string contains one of the listed words"""
    return any([list_item in str for list_item in list])


def get_column_index_of_interesting_text(table:_Element, interesting_texts:List[str], include_content:bool, exclusions:List[str] = []):
    """Returns the column index where one of the 'interesting_texts' values appears first. Returns None if not found.
    :param table: The table where to search
    :param interesting_texts: For what texts we search
    :param include_content: Wether the content of a table is included (td elements) or only the header (th elements)
    :param exclusions: Optional exclusions when a match does not count"""
    rows = table.findall(".//tr")

    # TODO In case of misspelled words, we can discuss if we consider a distance metric (e.g. Levenshtein)
    #      see e.g. https://www.uni-due.de/agbovensiepen/people.php ("Fist name")
    #               https://www.uni-due.de/philosophie/staff
    
    # Normalize strings
    interesting_texts = [s.lower() for s in interesting_texts]
    exclusions = [s.lower() for s in exclusions]

    # Iterate over all cells and return the first index where a column matches the interesting word
    for row in rows:

        search_in = row.findall(".//th")
        if include_content:
            # Look also in content rows
            search_in += table.findall(".//td")

        for idx, col in enumerate(search_in):
            # print(f"{idx}, {col}")
            # print(innertext(col))
            inner = innertext(col).lower()
            if string_contains_word_in_list(inner, interesting_texts) and not string_contains_word_in_list(inner, exclusions):

                # Offset by the number of columns
                # Try first with number of head:
                number_of_columns = len(table.findall(".//th"))
                if number_of_columns == 0:
                    # Fallback: use number of columns in first row
                    number_of_columns = len(table.xpath(".//tr[position()=1]//td"))
                if number_of_columns == 0:
                    # Malformed tables, not supported
                    return None
                return idx % number_of_columns
    return None


def find_link_for_person(row:_Element, tc:TableConfiguration):
    """Returns a hyperlink found in one of the name columns to the detail page of the person"""

    link = ""
    if tc.i_firstname is not None:
        link = row.xpath(xpath_nth_column(tc.i_firstname) + xpath_hyperlink + "[1]")
    if not link and tc.i_lastname is not None:
        link = row.xpath(xpath_nth_column(tc.i_lastname) + xpath_hyperlink + "[1]")
    return next(iter(link),"")


def find_email_for_person(row:_Element, tc:TableConfiguration):
    """Returns a hyperlink found in the email column"""

    address = "" # TODO Hier ist was falsch. Die Mailadressen sind immer gleich.
    search_in = []
    # Try to make email as followed:
    if tc.i_email is not None:
        # 1) from href in email column
        for href in row.xpath(xpath_nth_column(tc.i_email) + xpath_hyperlink):
            search_in.append(href)
        # 2) from text in email column
        search_in.append(normalize(innertext(row.xpath(xpath_nth_column(tc.i_email))[0])))
    # 3) from href in full row
    for href in row.xpath("." + xpath_hyperlink):
        search_in.append(href)
    # 4) from text in full row
    search_in.append(normalize(innertext(row)))

    for text in search_in:
        address = email_analysis.extract_first_email_address(text) # TODO Performance? extract_first... beim ersten direkt abbrechen lassen statt die ganze Liste durchzugehen
        if address:
            break

    return address


def build_person_from_row(row:_Element, tc:TableConfiguration) -> Person:
    """Builds a Person object from a row and the interesting indices"""

    # Start with the name
    name = normalize(innertext(row.xpath(xpath_nth_column(tc.i_lastname))[0])) # type: ignore - i_lastname is present when the method is called
    # Swap if needed
    if tc.swap_lastname:
        split = name.split(",")
        name = normalize(f"{split[1]} {split[0]}")
    # Insert firstname
    if not tc.i_firstname is None:
        name = normalize(innertext(row.xpath(xpath_nth_column(tc.i_firstname))[0])) + " " + name
    
    # Now the person has a name and we can create the object
    p = Person(name, "table")
    
    if not tc.i_title is None:
        # Title can be directly set
        p.title = normalize(innertext(row.xpath(xpath_nth_column(tc.i_title))[0]))

    # Check if a title is in the name
    title_match = normalize(compute_title(p.name))
    if title_match:
        # Overwrite the title with a better one
        # e.g. in https://math.ruhr-uni-bochum.de/fakultaet/arbeitsbereiche/numerik/team/ the title column is not found correctly
        p.title = title_match
        # Cut-off found title
        p.name = normalize(p.name.replace(p.title, ""))
    
    # Sometimes job title is after or before the name in parentheses
    p.name = normalize(re.sub(r"\(.*\)", "", p.name))

    # Extract homepage and email
    p.homepage = find_link_for_person(row, tc)
    p.email = find_email_for_person(row, tc)

    # Validation

    # Filter illegal titles (email addresses, (telephone) numbers)
    if re.search(r"[0-9+@]|\.de", p.title):
        log.debug(f"Illegal title: {p.title}")
        p.title = ""
    
    # Title must contain an actual title
    if p.title and not string_contains_word_in_list(p.title, possible_title_candidates + possible_title_candidates_long):
        log.debug(f"Unrecognized title: {p.title}")
        p.title = ""
    
    # Filter illegal names (email addresses, (telephone) numbers)
    if re.search(r"[0-9+@:]|\.de", p.name):
        log.debug(f"Illegal name: {p.name}")
        p.name = "" # caller will handle this as "skip"
    
    # Swap name if it still contains a comma
    if p.name.count(",") == 1:
        log.debug(f"Split afterwards: {p.name}")
        split = p.name.split(",")
        p.name = normalize(f"{split[1]} {split[0]}")
    
    # Name must contain at least two words and 5 characters
    # TODO deactivated, see e.g. https://www.uni-due.de/agbovensiepen/people.php ("Fist name")
    # if len(p.name) < 5 or len(p.name.split()) < 2:
    #     log.debug(f"Name too small: {p.name}")
    #     p.name = "" # caller will handle this as "skip"

    return p


def all_columns_contain_string_once(table:_Element, col_index:int, string:str):
    """Returns True if all cells at the passed column index contains a passed string exactly once"""
    for row in table.xpath(xpath_content_rows + "/" + xpath_nth_column(col_index)):
        inner = innertext(row)
        if inner.count(string) != 1:
            return False
    return True


def extract_people_from_table(doc:WebPage) -> List[Person]:
    """Returns all people found by Table analysis"""

    root = doc.root

    # Search for tables first
    people = []
    # print(root.findall(".//table"))
    for table in root.findall(".//table"):

        tc = TableConfiguration()

        log.debug("TABLE")
        
        # Lookup where the interesting columns are
        tc.i_title = get_column_index_of_interesting_text(table, ["Titel", "Title", "Grade", "Grad", "Degree"], False)
        if tc.i_title is None:
            # Try to search for titles inline
            tc.i_title = get_column_index_of_interesting_text(table, possible_title_candidates, True)
        tc.i_firstname = get_column_index_of_interesting_text(table, ["Vorname", "Firstname", "First Name"], False)
        tc.i_lastname = get_column_index_of_interesting_text(table, ["Nachname", "Lastname", "Surname", "Familyname", "Family Name", "Name"], False, ["First", "Vorname"])
        tc.i_email = get_column_index_of_interesting_text(table, ["Email", "E-Mail"], False)

        # if not tc.i_title is None:
        #     log.debug(f"Found title in column {tc.i_title}")
        # if not tc.i_firstname is None:
        #     log.debug(f"Found firstname in column {tc.i_firstname}")
        # if not tc.i_lastname is None:
        #     log.debug(f"Found lastname in column {tc.i_lastname}")
        # if not tc.i_email is None:
        #     log.debug(f"Found email in column {tc.i_email}")
        
        if tc.i_lastname is None:
            # Require at least one field for the lastname or the whole name
            log.debug("Table is useless")
            continue

        if tc.i_firstname == tc.i_lastname:
            # First and lastname are the same column
            log.debug("Firstname and lastname same column")
            tc.i_firstname = None
        
        if not tc.i_title is None and (tc.i_title in [tc.i_firstname, tc.i_lastname, tc.i_email]):
            # No extra title-column
            log.debug("No extra title column")
            tc.i_title = None
        
        if tc.i_firstname is None:
            # If there is a comma in all lastname columns, swap the parts between and after the comma
            tc.swap_lastname = all_columns_contain_string_once(table, tc.i_lastname, ",")
        
        # if tc.swap_lastname:
        #     log.debug("Swap lastname")
        
        # print(table.xpath(xpath_content_rows))
        log.debug(tc)

        for idx, row in enumerate(table.xpath(xpath_content_rows)):
            # print("row")
            try:
                p = build_person_from_row(row, tc)
            except IndexError:
                # It is possible that a row is incomplete and cells are missing. In this case we get an IndexError
                # We simply ignore these rows
                # see e.g. https://www.uni-due.de/agfarle/team/now_deu.php for such a malformed page
                log.debug(f"Index error in row {idx}", exc_info=1)
                continue
            if p and p.name:
                people.append(p)
    
    # print(people)
    return people
