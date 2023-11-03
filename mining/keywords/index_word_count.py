import os
import logging
import asyncio
import sys
from functools import lru_cache  

log = logging.getLogger(__name__)


@lru_cache(maxsize=None) 
def common_string(index, search_string, connection=None):
    """Returns True if search_string is a common string in index."""
    es = connection

    query = {
        "query": {
            "bool": {
                "must": [
                    {
                        "match": {
                            "content_txt_without_stopwords": search_string
                        }
                    }
                ]
            }
        },
        "size": 1
    }

    response = es.search(index=index, body=query)
    count = response['hits']['total']['value']
    return count > 700
