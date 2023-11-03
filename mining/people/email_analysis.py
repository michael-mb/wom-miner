import re
from pathlib import Path
from typing import List
import Levenshtein

# Extract all possible Top Level Domains
# We use this to exclude very many false-positive email addresses
tlds = []
with open(Path("people/top-level-domains.txt"), "r") as f:
    for line in f.readlines():
        if len(line) > 1 and not line.startswith("#") and not "--" in line:
            tlds.append(line.lower().strip())
tlds = "(" + "|".join(tlds) + ")"
    

# We are using named groups here
# see https://datatracker.ietf.org/doc/html/rfc5322#section-3.4.1 for full specification, but we only support a subset for covering the most email patterns at universities
# There are also internationalized email addresses (see https://datatracker.ietf.org/doc/html/rfc5336#section-2)
# Explanation: We look for x@y where
# - x is the local part of an email address (alpha-nummeric with the following special characters: .+-_ but must not start with a dot)
# - @ may be also at, ät, - at -, ...
# - y is the domain (left and right part min 2 characters, alpha-nummeric wiht the special characters as above or digits)
# Note also that - must be escaped in a character group if it is NOT the last character
email_local = r"(?P<local>[a-zA-Z0-9äöüÄÖÜß+_-][a-zA-Z0-9äöüÄÖÜß+_.-]*)"
email_at = r"([\s()\[\]-]{0,3}@[\s()\[\]-]{0,3}|\s{0,3}[()\[\]-]\s{0,3}[aAäÄ][tT]\s{0,3}[()\[\]-]\s{0,3})"
email_domain = r"(?P<domain>[a-zA-Z0-9äöüÄÖÜß+_-][a-zA-Z0-9äöüÄÖÜß+_.-]*\.TLD_DOMAINS)".replace("TLD_DOMAINS", tlds)

def extract_first_email_address(txt:str) -> str:
    """Extracts the first found email address from a String or empty string"""
    return next(iter(extract_email_addresses(txt)), "")


def extract_email_addresses(txt:str) -> List[str]:
    """Extracts all possible email addresses from a String"""

    r = re.compile(email_local + email_at + email_domain)
    addresses = []
    for match in r.finditer(txt):
        addresses.append(match.group("local") + "@" + match.group("domain"))
    return addresses

def email_match_name(name:str, mail:str) -> bool:
    """Returns True if the email fits to a name"""
    # TODO May add more heuristics
    mail = mail.lower()
    words = name.lower().split()

    if words[0] in mail and words[-1] in mail:
        # Exact name match for the first and the last name
        return True
    
    if Levenshtein.distance(mail.partition("@")[0], name) < 4:
        # Strong similarity between mail and name
        # TODO Check for false positives
        return True
    
    words = [s.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss") for s in words]
    if words[0] in mail and words[-1] in mail:
        # Match first and last name without umlauts
        return True
    
    words = [re.sub("[^a-zA-Z]", "", s) for s in words]
    if words[0] in mail and words[-1] in mail:
        # Match first and last name without further special characters removed
        return True
    
    # print(f"{name} does not match {mail}")
    return False
    
