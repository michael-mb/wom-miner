"""
Methods for retrieving documents from Elasticsearch
"""

from elasticsearch import Elasticsearch
import logging
from womutils.config import read_config

# this is a pointer to the module object instance itself.
# DON'T USE the pointer directly. Call "es_client()" instead!
es: Elasticsearch = None

log = logging.getLogger(__name__)

def configure_elastic(instance: str, username: str, password: str, disable_security: bool):
    """Inits the elasticsearch instance from parameters"""
    global es
    es = Elasticsearch(
        instance,
        basic_auth=(username, password),
        verify_certs=not disable_security,
        ssl_show_warn=not disable_security,
        retry_on_timeout=True,
        max_retries=5,
        request_timeout=60
    )

    if not es:
        raise RuntimeError("Could not configure Elasticsearch instance")
    if not es.ping():
        raise RuntimeError("Elasticsearch instance not available")
    log.info("Elasticsearch instance successfully connected")

def configure_elastic_from_config(name:str):
    """Inits the elasticsearch instance from a config name (elastic.name.toml).
    The file must contain 'instance', 'username', 'password' and could contain 'disable_security'"""
    config = read_config("elastic." + name)
    configure_elastic(config['instance'], config['username'], config['password'], config.get('disable_security', False))

def retrieve_all_documents(index:str, batch_size:int, fields = [], query = {"match_all": {}}, sort=[{"timestamp": "asc"}], source=True):
    """Returns all documents found by the query. If 'query' is not given, all documents in the index are accessed"""

    # Build query depending on requested fields
    if fields:
        search_query = {"query": query, "size": batch_size, "fields": fields}
    else:
        search_query = {"query": query, "size": batch_size}
    log.info("Starting iteration with query: " + str(search_query))

    # We use search_after for pagination as recommended by Elasticsearch
    # see https://www.elastic.co/guide/en/elasticsearch/reference/current/paginate-search-results.html#search-after
    last_sort = 0

    while True:
        # Fetch result from elastic
        if last_sort == 0:
            result = es.search(index=index, body=search_query, sort=sort, source=source)
        else:
            result = es.search(index=index, body=search_query, search_after=last_sort, sort=sort, source=source)
        
        if not result['hits']['hits']:
            break # No result, end loop

        for hit in result['hits']['hits']:
            yield hit
            last_sort = hit['sort']

def retrieve_all_documents_without_sort(index: str, batch_size: int, fields=[], query={"match_all": {}}, source=True):
    """Returns all documents found by the query. If 'query' is not given, all documents in the index are accessed"""

    # Build query depending on requested fields
    if fields:
        search_query = {"query": query, "size": batch_size, "fields": fields}
    else:
        search_query = {"query": query, "size": batch_size}
    log.info("Starting iteration with query: " + str(search_query))

    # Perform initial search with scroll
    response = es.search(index=index, body=search_query, scroll='1m', source=source)
    scroll_id = response['_scroll_id']
    hits = response['hits']['hits']
    
    while hits:
        for hit in hits:
            yield hit

        # Perform scroll request to get next batch of results
        response = es.scroll(scroll_id=scroll_id, scroll='1m')
        hits = response['hits']['hits']

    # Clear the scroll context
    es.clear_scroll(scroll_id=scroll_id)


def es_client() -> Elasticsearch:
    """Returns the Elasticsearch client"""
    return es
