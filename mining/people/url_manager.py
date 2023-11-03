"""Manages a list of processed URLs. The purpose is that similar URLs are ignored."""
from Levenshtein import distance
from urllib.parse import urlsplit

# see https://maxbachmann.github.io/Levenshtein/levenshtein.html#hamming

processed_urls = []

def clear():
    """Clears the list of URLs"""
    processed_urls.clear()

def add_url(url):
    """Appends the passed URL to the lists of URLs"""
    processed_urls.append(url)


def compute_domain(url):
    # Parse URL
    domain = urlsplit(url).hostname
    if domain.startswith("www."):
        # Don't distinguish between 'www' and non-www versions
        return domain[4:]
    return domain


def skip_url(toCheck:str):
    """Returns true if the passed URL should be skipped because another similar URL was already processed"""

    toCheck_domain = compute_domain(toCheck)
    
    for url in processed_urls:
        if compute_domain(url) != toCheck_domain:
            # Pages must be different because of different domain
            continue
        if distance(url, toCheck) < 4:
            # Similar page found
            return True
        if toCheck.startswith(url):
            # Don't go deeper where a URL was already processed
            # e.g. if "x.de/lehrstuhl/team" was already processed, skip "x.de/lehrstuhl/team/personXYZ"
            return True
    return False


# def processor(s:str):
#     """Pre-processor for URLs before the distance metric is applied"""
#     return s.replace("http://", "").replace("https://")