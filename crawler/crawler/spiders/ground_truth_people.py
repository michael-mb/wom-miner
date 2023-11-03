"""This Spider collects all employees from UDE"""

# scrapy crawl GroundTruthPeople

import logging
import scrapy
import re
from pathlib import Path

out = Path("../mining/people/results/ground_truth.csv")

class GroundTruthPeopleSpider(scrapy.Spider):
    name = "GroundTruthPeople"

    def __init__(self, university=None, *args, **kwargs):
        self.allowed_urls = ["https://www.uni-due.de/person"]
        self.denied_urls = []
        super(GroundTruthPeopleSpider, self).__init__(*args, **kwargs)

    def start_requests(self):

        with open(out, "w", encoding="utf-8") as f:
            f.write("sep=,\n")
        
        # Traverse over all person pages (there is no person with a 6-digits ID)
        r = range(1, 99999)
        for n in r:
            yield scrapy.Request(url=f"https://www.uni-due.de/person/{n}", callback=self.parse, meta={"id": n})
    
    def parse(self, response):
        found = response.css(".card-body > p::text").get()
        if found == "Es wurden 0 Personen gefunden.":
            # No person found
            return
        elif not found == "Es wurde 1 Person gefunden.":
            # Since we provided a unique ID, it is not possible to get more than 1 person
            logging.warn("Missing found message")
            return
        
        name = response.css(".card-header a::text").get()
        if name:
            # Normalize name (i.e. cut off multiple spaces / whitespace characters)
            name = " ".join(name.split())
        else:
            logging.warn("No name 1")
            return
        
        if not name:
            logging.warn("No name 2")
            return
        
        # Search for mailto links, institute and functions
        mail = response.css(".card-body").xpath(".//a[starts-with(@href, 'mailto:')]/@href").get() or ""
        mail = mail.replace("mailto:", "")
        institute = response.css(".card-body > .tab-content > div > .row > div > h3::text").get() or ""

        functions = response.css(".card-body > .tab-content > div > .row > div > ul > li > h3::text").getall() or []
        # Some functions are trash (they must be not empty, must not be too short and must contain letters)
        functions = map(lambda s: s.strip().strip(",").strip(), functions)
        functions = filter(lambda s: len(s) > 3 and re.search(r"[A-Za-z]", s), functions)

        if functions:
            # functions = ',"' + '","'.join(functions) + '"'
            functions = " ; ".join(functions)
        else:
            functions = ""
        
        # Search for the second column in a row containing "Webseite"
        website = response.css(".card-body .row").xpath(".//*[div[contains(text(),'Webseite')]]/div[2]//a/@href").get() or ""

        # Escape " to ""
        name = name.replace('"', '""')
        mail = mail.replace('"', '""')
        website = website.replace('"', '""')
        institute = institute.replace('"', '""')
        functions = functions.replace('"', '""')
        
        with open(out, "a", encoding="utf-8") as f:
            # f.write(f'"{response.meta.get("id")}","{name}","{mail}","{website}","{institute}"{functions}\n')
            f.write(f'"{response.meta.get("id")}","{name}","{mail}","{website}","{institute}","{functions}"\n')
