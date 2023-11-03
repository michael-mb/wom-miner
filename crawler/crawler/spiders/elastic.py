import os
import tomllib
from pathlib import Path
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.http import Response
from crawler.spiders.common import *
from elasticsearch import Elasticsearch


class ElasticSpider(CrawlSpider):
    """Crawler that saves the crawled web pages into an Elasticsearch Index"""
    name = "elastic"
    link_extractor = LinkExtractor()
    allowed_urls = []
    denied_urls = []
    page_index_name:str
    client:Elasticsearch

    def __init__(self, university=None, elastic=None, *args, **kwargs):

        # Process university config
        conf = parse_config(university)
        self.page_index_name = "crawl-rawdata-" + university

        self.allowed_domains = conf["domains"]
        self.start_urls = [conf["entrypoint"]]
        if "allow-urls" in conf:
            self.allowed_urls = conf["allow-urls"]
            self.rules = (Rule(LinkExtractor(allow=conf["allow-urls"]), callback="parse_page", follow=True),)
        else:
            self.denied_urls = conf["deny-urls"]
            self.rules = (Rule(LinkExtractor(deny=conf["deny-urls"]), callback="parse_page", follow=True),)
        
        # Process elastic config
        elastic_config_path = Path(f"../config/elastic.{elastic}.toml")
        if not elastic or not os.path.isfile(elastic_config_path):
            raise ValueError(f"Error in Elasticsearch configuration: '{elastic}'")
        with open(elastic_config_path, "rb") as f:
            elastic_config = tomllib.load(f)
        
        disable_security = elastic_config.get('disable_security', False)
        self.client = Elasticsearch(
            elastic_config['instance'],
            basic_auth=(elastic_config['username'], elastic_config['password']),
            verify_certs=not disable_security,
            ssl_show_warn=not disable_security,
            retry_on_timeout=True,
            max_retries=5,
            request_timeout=60
        )
        if not self.client:
            raise RuntimeError("Could not configure Elasticsearch instance")
        if not self.client.ping():
            raise RuntimeError("Elasticsearch instance not available")
        print(self.client.info())
        
        self.create_index()

        super(ElasticSpider, self).__init__(*args, **kwargs)

    def create_index(self):
        """Creates a page index for the university, if necessary"""
        if self.client.indices.exists(index=self.page_index_name):
            return # nothing to do
        
        self.client.indices.create(index=self.page_index_name, mappings={
            # Don't allow new fields https://www.elastic.co/guide/en/elasticsearch/reference/8.7/dynamic.html
            # https://www.elastic.co/guide/en/elasticsearch/reference/8.7/mapping-types.html
            # https://www.elastic.co/guide/en/elasticsearch/reference/8.7/keyword.html#wildcard-field-type
            "dynamic": 'strict',
            "properties": {
                "url":          {"type": "wildcard"},
                "domain":       {"type": "keyword", "ignore_above": 128},
                # Page title, extracted from HTML, see https://stackoverflow.com/a/69630261 for composed data-type
                "title":        {"type": "text", "fields": {"keyword": {"type": "keyword", "ignore_above": 512}}},                               
                "timestamp":    {"type": "date", "format": "strict_date_time"},
                "links": {
                    # Target URL, URL text (<a> content) and an (optional) additional fragment
                    "properties": {
                        "target":   {"type": "wildcard"},
                        "text":     {"type": "text", "fields": {"keyword": {"type": "keyword", "ignore_above": 512}}},
                        "fragment": {"type": "wildcard"}
                    }
                },
                # HTML content, hash, size and Content-Type header
                "content":      {"type": "text"},
                # TODO Do we need the following fields?
                "url_hash":     {"type": "text"},
                "content_hash": {"type": "text"},
                "content_size": {"type": "integer"},
                "content_type": {"type": "keyword", "ignore_above": 64},
                "referer":      {"type": "wildcard"}
            }
        }, settings={
            # TODO maybe add some settings, maybe not :-)
        })

    def parse_page(self, response:Response):

        # Create the document
        doc = get_metadata(self, response)
        doc['content'] = response.text

        self.client.index(id=doc['url_hash'], index=self.page_index_name, document=doc)

        return {} 
