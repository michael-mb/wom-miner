"""Common methods that can be used across all spiders"""

from datetime import datetime
import hashlib
import os
from pathlib import Path
import re
import tomllib
from urllib.parse import urlsplit
from scrapy.spiders import CrawlSpider
from scrapy.http import Response


def calculate_sha256(text: str):
    """Returns the sha256 checksum of the passed string"""

    sha256_hash = hashlib.sha256()
    sha256_hash.update(text.encode('utf-8'))
    return sha256_hash.hexdigest()


def has_content_changed(html_content, hash_value):
    return calculate_sha256(html_content) != hash_value


def parse_config(university_conf: str):
    """Returns a dictionary with the content of the university config file. Raises Exceptions on bad input."""

    # Open the file
    if not university_conf:
        raise ValueError("University not provided")
    filename = Path(f"../config/{university_conf}.toml")
    if not os.path.isfile(filename):
        raise ValueError(f"University '{university_conf}' has no configuration")
    with open(filename, mode="rb") as f:
        conf = tomllib.load(f)
    
    # Go into the "[crawler]" section
    if not "crawler" in conf:
        raise ValueError("Config does not contain crawler settings")
    conf = conf['crawler']

    # Check that all required values are present
    if not "entrypoint" in conf:
        raise ValueError("Entry point not provided")
    if not "domains" in conf:
        raise ValueError("Domains not provided")
    if not "deny-urls" in conf and not "allow-urls" in conf:
        raise ValueError("URL filter not provided")
    if "deny-urls" in conf and "allow-urls" in conf:
        raise ValueError("URL filter is ambiguous")
    return conf


def should_visit_page(spider: CrawlSpider, url):
    """Returns true if the passed url is allowed by the spider; false otherwise"""

    # NOTE: This is a "hack" for manipulating the config files AFTER the crawler has already been started.
    #       We simply concatenate the regexes into a big regex for performance improvevments
    # see https://stackoverflow.com/a/33406382. Lookahead is important, otherwise the lookup performance is very very slow.
    # Note: For other spiders like "ground_truth_people" the spider does not have these attributes
    if hasattr(spider, "denied_urls") and spider.denied_urls:
        return not re.findall(r"(?=(" + '|'.join(spider.denied_urls) + r"))", url)
    elif hasattr(spider, "allowed_urls") and spider.allowed_urls:
        return bool(re.findall(r"(?=(" + '|'.join(spider.allowed_urls) + r"))", url))
    
    return True # all URLs allowed


def get_metadata(spider: CrawlSpider, response: Response):
    """Returns metadata for a response from a CrawlSpider"""

    # Parse URL
    domain = urlsplit(response.url).hostname
    # Remove leading 'www' which is a common subdomain for web pages
    # This is because we don't distinguish between 'www' and not-www versions
    if domain.startswith("www."):
        domain = domain[4:]

    extracted_links = spider.link_extractor.extract_links(response)
    # This extracts only the "url" attribute, but there are more (text, fragment, ...), see https://docs.scrapy.org/en/2.8/topics/link-extractors.html#module-scrapy.link

    return {
        "url": response.url,
        "domain": domain,
        "title": response.xpath('/html/head/title/text()').get(),

        # NOTE: We have to save datetime with suffix 'Z' to indicate UTC time. For Kibana we must save time in UTC.
        # https://stackoverflow.com/a/56074397, https://discuss.elastic.co/t/no-results-match-your-search-criteria-error-while-there-is-data/195753/14
        "timestamp": datetime.utcnow().isoformat(timespec='milliseconds') + "Z",

        "url_hash": calculate_sha256(response.url),  # Hash will change if the URL changes !
        "content_hash": calculate_sha256(response.text),  # Hash will change if the content changes !

        "links": [{"target": l.url, "text": l.text, "fragment": l.fragment} for l in extracted_links],

        # "content_length": response.headers.get('Content-Length'), # "Content-Length" is not always sent
        # the following line is more accurate than "Content-Length" since the latter can be the compressed file for transmission
        "content_size": len(response.body),
        
        "content_type": response.headers.get('Content-Type').decode('utf-8'),
        "referer": response.request.headers.get('Referer', '').decode('utf-8'),  # but may not help because only domain
        # "html_head_tag": html_head_tag
        # dates of publication / modification
        # author
        # meta description
        # keywords
    }
