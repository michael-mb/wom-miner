'''This modul is used to evaluate the performance of the keybased project mining.'''
from main import should_be_ignored, init_elastic, reformat_content, search_query as keybased_search_query
import numpy as np
from sklearn.metrics import classification_report
import logging 
import re

from womutils.elastic import configure_elastic_from_config, es_client, retrieve_all_documents_without_sort
log = logging.getLogger(name=__name__, level=logging.DEBUG)

def extract_data(hit, label):
    if label != 4:
        label = 0
    return {
        'url': hit['_source']['url'],
        'title': hit['_source'].get('title', 'no_title'),
        'content': reformat_content(hit['_source'].get('content', '')),  # content
        'lang': hit['_source'].get('lang', ''),
        # 'keywords': hit['_source']['keywords'],
        'content_xml': hit['_source'].get('content_xml', ''),
        'person_names': hit['_source'].get('person_names', []),
        'label' : label
    }

def get_total_docs(es, index, query):
    # Get the total count of documents in the source index
    total_docs_response = es.search(index=index, body={"query": query, "size": 0})
    return total_docs_response["hits"]["total"]["value"]

def load_complett_dataset_key_based(es, test_data_index):
    query = { "bool": { "must_not": [ { "bool": { "should": [ { "bool": { "must_not": { "exists": { "field": "content" } } } }, { "bool": { "must_not": { "exists": { "field": "url" } } } } ] } } ] } } 
    total_docs = get_total_docs(es=es, index=test_data_index, query=query)
    ret = []
    while True:
        for hit in retrieve_all_documents_without_sort(index=test_data_index, batch_size=100, query=query, source=["label", "url"]):
            ret.append(hit)
        if len(ret) >= total_docs:
            logging.info(f'Current number of handled pages: {len(ret)}')
            break
    log.info(f'Get {len(ret)} documents from test data index.')
    return ret

# Regular expressions from the original search query


def match_all_regex(input_dict):
    
    regex_expressions_titel = [
    ".*project.*", ".*projekt.*", ".*research.*", ".*forschung.*"
    ]
    if match_regex(regex_expression=regex_expressions_titel, input_dict=input_dict):
        return True

    regex_expressions_ur = [
        ".*project.*", ".*projekt.*", ".*research.*", ".*forschung.*"
        ]
    if match_regex(regex_expression=regex_expressions_ur, input_dict=input_dict):
        return True
    
    regex_expressions_content = [
        ".*project description.*", ".*project management.*", ".*project coordination.*",
        ".*project funding.*", ".*project duration.*", ".*projektbeschreibung.*",
        ".*projektleitung.*", ".*projektkoordination.*", ".*projektförderung.*",
        ".*projektlaufzeit.*", ".*Projektbearbeiter.*"
    ]
    if match_regex(regex_expression=regex_expressions_content, input_dict=input_dict):
        return True
    return False

# Function to match the regular expressions against dictionary values
def match_regex(regex_expression, input_dict):
    for regex_exp in regex_expression:
        pattern = re.compile(regex_exp, re.IGNORECASE)
        if pattern.search(input_dict['title']):
            return True

    return False  # Return False if no match is found


def load_test_dataset_key_based(es, test_data_index):
    # TODO 
    query["query"]["bool"]["filter"] = { "bool": {
         "must": [ {"exists": {  "field": "content"} },
                   {"exists": {  "field": "url"} }
         ]
    }
    }
    query = query["query"]
    query["_source"] = ["label", "url"]
    total_docs =  get_total_docs(es=es, index=test_data_index, query=query)
    ret = []
    while True:
        for hit in retrieve_all_documents_without_sort(index=test_data_index, batch_size=100, query=query, source=["label", "url"]):
            ret.append(hit)
        if len(ret) >= total_docs:
            logging.info(f'Current number of handled pages: {len(ret)}')
            break

    log.info(f'There are {len(ret)} test documetns')
    log.info(f'Get {len(ret)} documents from test data index.')
    return ret


def load_preprocessed_dataset(es, train_dataset, pre_index_rub, pre_index_ude):
    ret = []
    counter = 0
    for train_doc in train_dataset:
        counter += 1
        search_query = {"query": {"match": {"url": train_doc['_source']['url']}}, '_source': ['url', 'title', 'content_txt', 'lang', 'person_names']}
        docs_hits_ude = es.search(index=pre_index_ude, body=search_query)
        if docs_hits_ude['hits']['total']['value'] > 0:
            if docs_hits_ude['hits']['total']['value'] > 1:
                log.warning(f'There is more then one results for the doc with the url: {train_doc["_source"]["url"]}. This should not happen.')
            ret.append(extract_data(hit=docs_hits_ude['hits']['hits'][0], label=train_doc['_source']['label'])) # there should only be one result 

        else:
            docs_hits_rub = es.search(index=pre_index_rub, body=search_query)
            #  print('====== rub result =======')
            #   print(docs_hits_ude)
            if docs_hits_rub['hits']['total']['value'] > 0:
                if docs_hits_rub['hits']['total']['value'] > 1:
                    log.warning(f'There is more then one results for the doc with the url: {train_doc["_source"]["url"]}. This should not happen.')
                ret.append(extract_data(docs_hits_rub['hits']['hits'][0], label=train_doc['_source']['label'])) # there should only be one result
            else:
                log.warning(f'No document with url {train_doc["_source"]["url"]} found. Skip this document')
    return ret


def get_y_test(dataset):
    y_test = []
    for data in dataset:
        y_test.append(data['label'])
    return np.array(y_test)


def load_data(es, pre_index_ude, pre_index_rub, test_data_index):
    log.info('Load test data.')
    # get all from train index
    train_dataset_complett = load_complett_dataset_key_based(es=es, test_data_index=test_data_index)
    # train_dataset_filtered = load_test_dataset_key_based(es=es, test_data_index=test_data_index)
    # get documents with a specific url from ude
    # get documents with a specific url from rub if not in ude
    # ignore if not in rub or ude
    # transform data for handling
    return load_preprocessed_dataset(es=es, train_dataset=train_dataset_complett, pre_index_rub=pre_index_rub, pre_index_ude=pre_index_ude)
 

def do_evaluation(y_test: np.array, y_pred:np.array):
    # Make predictions on the test dataset
    label_names = ['other: 0', 'project: 4']
    print('')
    print('========= results =========')
    print('')
    print(classification_report(y_test, y_pred, target_names=label_names))


def is_url_in_filtered_dataset(url, dataset_filtered):
    log.debug(f'Is {url} in the dataset obtained with the keyword based search query?')
    for data in dataset_filtered:
        if data['url'] == url:
            log.debug('Yes')
            return True
    log.debug('No')
    return False


def predict(dataset):
    y_pred = []
    for data in dataset:
        if match_all_regex(input_dict=data):
            y_pred.append(4) # is a project
        else:
            y_pred.append(0) # is not a project
    return np.array(y_pred)


def main():
    log.info('Start keybased project mining evaluation.')
    test_data_index: str = "classification_train_index-ude"  
    pre_index_ude: str = "preprocessing-ude"
    pre_index_rub: str = "preprocessing-rub"

    # Create Elasticsearch instance with the research project index
    configure_elastic_from_config('remote')
    es = es_client()

    dataset = load_data(es=es, pre_index_ude=pre_index_ude, pre_index_rub=pre_index_rub, test_data_index=test_data_index)
    print(f'Length of full train dataset: {len(dataset)}')
    # print(f'Length of full filtered dataset: {len(dataset_filtered)}')
    y_test: np.array = get_y_test(dataset=dataset)
    y_pred: np.array = predict(dataset)
    do_evaluation(y_test=y_test, y_pred=y_pred)

if __name__ == "__main__":
    main()