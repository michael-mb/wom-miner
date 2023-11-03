import argparse
import logging
from svm_classification import SVM_Page_classifier
import sys
from tqdm import tqdm
from datetime import datetime
sys.path.append('../mining')
from womutils import elastic 
from womutils.log import configure_logging
from womutils.config import ensure_config_exists, read_config
from womutils.elastic import configure_elastic_from_config
from womutils.elastic import es_client

import warnings
# Ignore DeprecationWarnings from elastic
warnings.filterwarnings("ignore", category=DeprecationWarning)

def extract_data(doc):
     data = {
                    #'id': 'research_miner' + '_' + university + '_' + doc['_id'],
                    'url': doc['_source']['url'],
                    'title': doc['_source']['title'],
                    'type': 'research projects',
                    'lang': doc['_source']['lang'],
                    'content': doc['_source']['content'],
                    'last_update': datetime.utcnow().isoformat(timespec='milliseconds') + "Z",
                    'person_names': doc['_source']['person_names'],
                    # 'keywords': data['keywords'],
                    'summary': doc['_source']['summary']
                }
     return data

def check_doc_already_exists(doc, es, result_index):
    search_result = es.search(index=result_index, body={"query": { "match": {  "url" : doc['_source']['url'] }}, "_source": ["url"] })
    if search_result['hits']['total']['value'] > 0:
        return True
    return False

def get_total_docs(es, source_index):
    total_docs = 0  
    # Get the total count of documents in the source index
    total_docs_query = {"match_all": {}}
    total_docs_response = es.search(index=source_index, body={"query": total_docs_query, "size": 0})
    return total_docs_response["hits"]["total"]["value"]

def save_doc(doc, es, result_index):
    if check_doc_already_exists(doc=doc, es=es, result_index=result_index):
        log.warn(f"Document with url {doc['_source']['url']} already exists. Skip this document.")
    else:
        data = extract_data(doc=doc)
        if data:
            es.index(index=result_index, body=data)
        else:
            log.error('Document is none. This should not happen.')

def run(batch_size, es, result_index, source_index, svm):
    counter = 0 
    total_docs = get_total_docs(es=es, source_index=source_index)  # Variable to track the total number of documents in the source index
    with tqdm(total=total_docs, desc="Handle pages", unit="page") as pbar:
        for doc in elastic.retrieve_all_documents_without_sort(index=source_index, batch_size=batch_size):
            counter += 1
            # Check if the document is predicted as a project

            if svm.predict(page=doc) == 4:
                log.debug(f'Doc with {doc["_source"]["url"]} is a project')
                save_doc(doc=doc, es=es, result_index=result_index)
            else:
                log.debug(f'Doc with {doc["_source"]["url"]} is not a project')
            pbar.update()
        return True, counter
                
def main(batch_size: int, svm_model: str, university: str, source_index=None, result_index=None):
    # Miner Configuration
    if not source_index:
        source_index = "research_project-" + university
    if not result_index:
        result_index = "research-project-svm-" + university

    es = es_client()
    es.indices.create(index=result_index,
                      mappings={
                          "dynamic": 'strict',
                          "properties": {
                              "id": {"type": "text"},
                              "url": {"type": "wildcard"},
                              "title": {"type": "text",
                                        "fields": {"keyword": {"type": "keyword", "ignore_above": 512}}},
                              "type": {"type": "text"},
                              "lang": {"type": "keyword", "ignore_above": 5},
                              "last_update": {"type": "text", "fields": {"keyword": {"type": "keyword", "ignore_above": 512}}},
                              "content": {"type": "text"},
                              "person_names": {"type": "text"},
                              "summary": {"type": "text"},
                          }
                      },
                      ignore=400) 
    
    svm = SVM_Page_classifier(model_path=svm_model)
    counter = 0
    err_counter = 0
    while(True):
        try:
            reached_end, ret_counter = run(es=es, batch_size=batch_size, result_index=result_index, source_index=source_index, svm=svm)
            counter += ret_counter
            if reached_end:
                break
            err_counter = 0
        except Exception as e:
            if err_counter > 10:
                break
            err_counter += 1
            log.error(f'An error occurs try again ({err_counter})', exc_info=True)

    log.info(f'Handle {counter} documents')
    log.info(f'Finish')

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument('university', help='The university e.g. "rub". Used to identify the indices.')
    parser.add_argument('elastic', help='The elastic instance configuration e.g. "local".')
    parser.add_argument('--logfile', help='Path to a logfile (optional)')
    parser.add_argument('--timestamp', help='last timestamp to continue the execution (optional)')
    parser.add_argument('--model', help='Path to svm model')
    parser.add_argument('--result_index', help='Index for saving the result')
    parser.add_argument('--source_index', help='Index for loading the sources.')
    
    args = parser.parse_args()
    # Configure logging, university and elastic
    configure_logging(args.logfile)
    log = logging.getLogger(__name__)
    ensure_config_exists(args.university) # If university config does not exist, there is no chance that this will work
    configure_elastic_from_config(args.elastic)

    svm_model = args.model
    if not svm_model:
        svm_model = './page_classification_model.pkl'
    log.info('Start project classification')
    # Using preprocessing config for reading batch_size
    cfg = read_config("preprocessing")
    main(batch_size=cfg['batch_size'],svm_model=svm_model,  university=args.university, result_index=args.result_index, source_index=args.source_index)
