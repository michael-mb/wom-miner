import asyncio
import sys
import time
import logging
import argparse

#to run the keyword extraction, open the keywords folder and type "python main.py" in the command line
sys.path.append('../')

# from apscheduler.schedulers.asyncio import AsyncIOScheduler

from womutils.elastic import es_client, retrieve_all_documents, configure_elastic_from_config
from meta_extractor import keyword_batch_extractor, clean_text

log = logging.getLogger(__name__)


query_doc_without_keyword = {"bool": {"must_not": {"exists": {"field": "keywords_weights"}}}}
batch_size = 10

def process_docs(index):
    """Appends keywords to documents in index."""
    es = es_client()
    content_list = []
    documents_list = []
    lang_list = []
    log.info(f"Extracting keywords for documents in index {index}. Batch size: {batch_size} documents.")

    documents = retrieve_all_documents(index, batch_size=batch_size)#, query=query_doc_without_keyword)
    doc_count = 0
    batch_count = 0

    for document in documents:
        

        if "content_txt_without_stopwords" not in document["_source"]:
            print(f"Document with ID {document['_id']} has no 'content_txt_without_stopwords'. Skipping.")
            continue
        
        content_text = document["_source"]["content_txt_without_stopwords"]
        lang = document["_source"]["lang"]
        content_list.append(content_text)
        documents_list.append(document)
        lang_list.append(lang)
        doc_count += 1

        if doc_count % batch_size == 0:
            start_time = time.time()
            batch_count += 1
            keyword_lists = keyword_batch_extractor(content_list, lang_list=lang_list, index=index, connection=es)
            for doc, doc_keywords in zip(documents_list, keyword_lists):
                doc_id = doc["_id"]
                if not doc_keywords:
                    doc_keywords = [("null", 0.0)]
                keywords = [keyword for keyword, weight in doc_keywords]
                weights = [weight for keyword, weight in doc_keywords]
                doc = {"keywords": keywords, "keywords_weights": weights}
                es.update(
                    index=index,
                    id=doc_id,
                    doc_as_upsert=True,
                    doc=doc
                )
            content_list = []
            documents_list = []
            end_time = time.time()
            elapsed_time = end_time - start_time
            start_time = time.time()
            print(f"Batch: {batch_count} | Seconds/doc: {round(elapsed_time/batch_size, 2)}")
    log.info("Finished keyword extraction for all documents.")

def keyword_is_person(keyword, person_names):
    """Checks if a keyword occurs in the person_names field"""
    names= ' '.join(person_names)
    names = clean_text(names)
    person_names = names.split()
    if keyword in person_names:
        return True
    return False

#from the mining/keywords folder exedcute: python preprocessing_keywords.py --env production --unis ude rub
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Configure and process documents for universities.")
    parser.add_argument("--env", default="production", help="Environment setting (e.g., 'production', 'local')")
    parser.add_argument("--unis", nargs="+", help="List of universities (e.g., 'ude', 'rub')")
    args = parser.parse_args()
    env = args.env
    unis = args.unis if args.unis else ["ude", "rub"]
    configure_elastic_from_config(env)
    for uni_name in unis:
        process_docs(f"preprocessing-{uni_name}")