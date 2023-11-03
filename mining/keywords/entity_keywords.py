import sys
import logging
import time
from operator import itemgetter
import re
from functools import lru_cache  
import argparse

sys.path.append('../')

from womutils.elastic import es_client, retrieve_all_documents, configure_elastic_from_config
from meta_extractor import keyword_batch_extractor
from keywords_common import clean_text

log = logging.getLogger(__name__)


def aggregate_keywords(document, entity_name, uni, es=None):
    query = {
        "query": {
            "bool": {
                "must": [
                    {
                        "match_phrase": {
                            "content_txt": entity_name.lower()
                        }
                    },
                    {
                        "exists": {
                            "field": "keywords_weights"
                        }
                    }
                ]
            }
        }
    }
    index = "preprocessing-" + uni

    response = es.search(index=index, body=query, size=1000)

    preprocessing_documents = response["hits"]["hits"]
    preprocessing_documents = preprocessing_documents[:20] + preprocessing_documents[20::4]

    aggregated_keywords = {}
    for preprocessing_doc in preprocessing_documents:
        keywords = preprocessing_doc["_source"].get("keywords", [])
        weights = preprocessing_doc["_source"].get("keywords_weights", [])
        for keyword, weight in zip(keywords, weights):
            if not common_keyword(index, keyword, connection=es):
                if keyword in aggregated_keywords:
                    aggregated_keywords[keyword] += weight
                else:
                    aggregated_keywords[keyword] = weight

    sorted_keywords = sorted(aggregated_keywords.items(), key=lambda x: x[1], reverse=True)
    top_keywords = dict(sorted_keywords[:20])

    specific_keywords = {k: v for k, v in top_keywords.items() if not common_keyword(index, k, connection=es)}

    total_weight = sum(specific_keywords.values())
    normalized_weights = {k: round(v / total_weight, 3) for k, v in specific_keywords.items()}

    document["keywords"] = list(normalized_weights.keys())
    document["keywords_weights"] = list(normalized_weights.values())

    return document["keywords"], document["keywords_weights"]

@lru_cache(maxsize=None) 
def common_keyword(index, search_keyword, connection=None):
    """Returns True if search_keyword is common in the keywords list of index."""
    es = connection

    query = {
        "query": {
            "bool": {
                "must": [
                    {
                        "match": {
                            "keywords": search_keyword
                        }
                    }
                ]
            }
        },
        "size": 1
    }

    response = es.search(index=index, body=query)
    count = response['hits']['total']['value']
    return count > 500

#from the mining/keywords folder exedcute: python entity_keywords.py --env production --unis ude rub
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Configure and process documents for universities.")
    parser.add_argument("--env", default="production", help="Environment setting (e.g., 'production', 'local')")
    parser.add_argument("--unis", nargs="+", help="List of universities (e.g., 'ude', 'rub')")
    args = parser.parse_args()
    env = args.env
    unis = args.unis if args.unis else ["ude", "rub"]
    configure_elastic_from_config(env)
    for _ in range(1000):
        miners=["people","research_project", "org"]

        es = es_client()
        for uni in unis:
            for miner in miners:
                entity_index = f"{miner}-{uni}"
                print(f"Keyword processing for {entity_index}..")
                field_name = "title" if "project" in entity_index else "name"
                query = {
                    "query": {
                        "bool": {
                            "must_not": {"exists": {"field": "doc.keywords_weights"}}
                        }
                    }
                }
                batch_size = 1000

                response = es.search(index=entity_index, size=batch_size, body=query)
                entity_docs = response["hits"]["hits"]

                for entity in entity_docs:
                    try:
                        entity_name = entity["_source"][field_name]
                        k, w = aggregate_keywords(entity, entity_name, es=es, uni=uni)
                        doc = {"doc": {
                            "keywords": k,
                            "keywords_weights": w
                        }}
                        print(f"document: {entity['_id']}, keywords: {k}, weights: {w} name/title: {entity_name}")
                        es.update(index=entity_index, id=entity["_id"], doc=doc)
                    except Exception as e:
                        log.error(f"Error processing document {entity['_id']}: {str(e)}")


