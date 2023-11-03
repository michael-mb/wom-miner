import sys
import logging
import time
import csv
from operator import itemgetter
import re
from functools import lru_cache
import json
from urllib.parse import quote

sys.path.append('../')

from womutils.elastic import es_client, retrieve_all_documents, configure_elastic_from_config
from meta_extractor import keyword_batch_extractor
from keywords_common import clean_text

log = logging.getLogger(__name__)

import os
import csv
from urllib.parse import quote

def write_entities_to_csv(miner_type, uni, entities):
    csv_filename = f"eval_results/csv/{miner_type}_{uni}_entities.csv"
    write_header = not os.path.exists(csv_filename)
    
    with open(csv_filename, mode='a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ["uni", "miner", "name", "title", "email", "found_in", "source", "homepages", "keywords", "google_query", "useful_keywords", "quality_score"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore', delimiter=';')
        if write_header:
            writer.writeheader()
        for entity in entities:
            source = entity["_source"]
            row = {"uni": uni, "miner": miner_type}
            for key, value in source.items():
                lower_key = key.lower()
                if lower_key == "doc":
                    keywords = value.get("keywords", [])
                    row["keywords"] = "[" + ", ".join(keywords) + "]"
                else:
                    row[lower_key] = value

            if "research_project" in miner_type.lower():
                name_or_title = row['title']
            else:
                name_or_title = row['name']

            site_param = ""
            if uni == "ude":
                site_param = "site:uni-due.de"
            elif uni == "rub":
                site_param = "site:ruhr-uni-bochum.de"

            google_query = f"https://www.google.com/search?q={quote(name_or_title)}+{quote(uni_to_full_name(uni))}+{site_param}"
            row["google_query"] = google_query

            useful_keywords = []
            for keyword in keywords:
                user_input = input(f"{keyword: <40} <- (# + ENTER if userfull/ENTER if not): ")
                if user_input.lower() == "#":
                    useful_keywords.append(keyword)

            total_keywords = len(keywords)
            quality_score = len(useful_keywords) / total_keywords if total_keywords > 0 else 0
            row["useful_keywords"] = useful_keywords
            row["quality_score"] = quality_score

            writer.writerow(row)


def uni_to_full_name(uni):
    if uni == "ude":
        return "Universität Duisburg-Essen"
    elif uni == "rub":
        return "Ruhr Universität Bochum"
    else:
        return uni

if __name__ == "__main__":
    configure_elastic_from_config("production")
    miners = ["people", "research_project", "org"]
    unis = ["ude", "rub"]
    es = es_client()
    for uni in unis:
        for miner in miners:
            entity_index = f"{miner}-{uni}"
            query = {
                "query": {
                    "function_score": {
                        "query": {
                            "bool": {
                                "must": {"exists": {"field": "doc.keywords_weights"}}
                            }
                        },
                        "random_score": {},
                        "boost_mode": "replace"
                    }
                },
                "size": 1
            }
            response = es.search(index=entity_index, body=query)
            entity_docs = response["hits"]["hits"]

            write_entities_to_csv(miner, uni, entity_docs)