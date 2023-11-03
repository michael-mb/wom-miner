import logging
import os
from pathlib import Path
from urllib.parse import SplitResult, urlsplit
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from crawler.spiders.common import *

def convert_to_valid_path(s: Path):
    """Replaces all non-alphanumeric characters with an underscore"""
    # see https://stackoverflow.com/a/27647178 and https://stackoverflow.com/a/31976060
    # TODO This does not work on Unix-based systems because '/' is the path separator.
    # Don't filter '\\' as this is the path separator
    map = dict((ord(char), "_") for char in '|<>:"|?*')
    s = str(s).translate(map)
    # s = s.replace(u'\u200b', '') # TODO I don't know why there are \u200b in the string (https://stackoverflow.com/a/31527338)
    return s

def create_folder_and_file(domain: str, url: SplitResult, html_content):
    """Creates a file for the html content"""

    # Make folder for domain
    folder = Path(f"crawled_content/{domain}")
    if not os.path.isdir(folder):
        os.makedirs(folder)

    # Save the file
    if not url.path:
        # Path is empty => requested file was 'index.html'
        file_path = folder / "index.html"
    elif not "/" in url.path:
        # No sub-folder
        file_path = folder / url.path
    else:
        # sub-folder
        last_index_of_sep = url.path.rfind("/")
        folder = Path(f"crawled_content/{domain}/{url.path[0:last_index_of_sep]}") # Construct a path until the last occurrence of "/"
        if not os.path.isdir(folder):
            os.makedirs(folder)

        suffix = url.path[last_index_of_sep + 1:] # All other trailing characters after the separator are the filename
        if not suffix:
            # Path is empty => requested file was 'path/.../index.html'
            file_path = folder / "index.html"
        else:
            # Path is not empty => a 'real' file was requested (e.g. 'path/.../file.html')
            file_path = folder / suffix

    # Append query and fragment if present
    if url.query:
        file_path = str(file_path) + "?" + url.query
    if url.fragment:
        file_path = str(file_path) + "#" + url.fragment
    file_path = convert_to_valid_path(file_path) # TODO Scheint noch nicht zu funktionieren, z.B. mit https://www.uni-due.de/de/presse/meldung.php?id=9162

    if os.path.isfile(file_path):
        logging.warning("File already exists and will be overridden: " + file_path)
        os.remove(file_path)

    # # TODO Why there is non-visible white-space???
    # if u'\u200b' in html_content:
    #     print("WARNING: THE HTML CONTENT CONTAINS u200b")
    #     print(html_content)
    #     return
    # if u'\u200b' in file_path:
    #     print("WARNING: THE FILE PATH CONTAINS u200b")
    #     print(file_path)
    #     return
    html_content = html_content.replace(u'\u200b', '')

    # TODO in https://www.uni-due.de/zim/datenschutzerklaerung.php there is '\u0308'
    # Solution: https://stackoverflow.com/a/42495690
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(html_content)


class FilesystemSpider(CrawlSpider):
    """Crawler that saves the crawled web pages into the file-system"""
    name = "filesystem"
    link_extractor = LinkExtractor()
    allowed_urls = []
    denied_urls = []

    def __init__(self, university=None, *args, **kwargs):
        conf = parse_config(university)

        self.allowed_domains = conf["domains"]
        self.start_urls = [conf["entrypoint"]]
        if "allow-urls" in conf:
            self.allowed_urls = conf["allow-urls"]
            self.rules = (Rule(LinkExtractor(allow=conf["allow-urls"]), callback="parse_page", follow=True),)
        else:
            self.denied_urls = conf["deny-urls"]
            self.rules = (Rule(LinkExtractor(deny=conf["deny-urls"]), callback="parse_page", follow=True),)

        super(FilesystemSpider, self).__init__(*args, **kwargs)

    def parse_page(self, response):

        metadata = get_metadata(self, response)

        # print(metadata)

        create_folder_and_file(metadata['domain'], urlsplit(response.url), response.text)

        return {} # prevents the metadata from shown in the logs
