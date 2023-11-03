import argparse
import re
import tomllib
import os
import time
import spacy
import xml.etree.ElementTree as ET
from elasticsearch import Elasticsearch
from pathlib import Path
from datetime import datetime
from transformers import BartTokenizer, BartForConditionalGeneration
from svm_classification import SVM_Page_classifier
import logging

log = logging.getLogger(name=__name__)

parser = argparse.ArgumentParser()
parser.add_argument('--config', type=str, help='Path to the configuration file')
parser.add_argument('--model', type=str, help='Path to the classification model file')
parser.add_argument('--log_level', type=str, help='Set log level DEBUG, INFO WARNING etc.')
args = parser.parse_args()
config_path = args.config
if not config_path:
    config_path = "./config/elastic.toml"

model_path = args.model
if not model_path:
    model_path = "./page_classification_model_700_250.pkl"

log_level = args.log_level
if not log_level:
    log_level = "INFO"

level = logging.getLevelName(log_level)
log.setLevel(level)


log.info('connect to elastic')
with open(Path(config_path), "rb") as f:
    config = tomllib.load(f)

# Miner Configuration
index_pre = config['pre_index']
batch_size = config['batch_size']
research_project_index = config['research_project_index']

log.info('connect to elastic')
# Elastic connection

disable_security = config.get('disable_security', False)
es = Elasticsearch(
    config['instance'],
    basic_auth=(config['username'], config['password']),
    verify_certs=not disable_security,
    ssl_show_warn=not disable_security
)

if not es:
    raise RuntimeError("Could not configure Elasticsearch instance")
if not es.ping():
    raise RuntimeError("Elasticsearch instance not available")



# create index if not exist
es.indices.create(index=research_project_index, ignore=400)  # ignore 400 Index Already Exists exception

# Bart summarization
model_name = 'facebook/bart-large-cnn'
tokenizer = BartTokenizer.from_pretrained(model_name)
model = BartForConditionalGeneration.from_pretrained(model_name)
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'


def preprocess_text(text):
    return tokenizer.batch_encode_plus(
        [text],
        max_length=1024,
        truncation=True,
        return_tensors='pt'
    )


def generate_summary(inputs):
    summary_ids = model.generate(
        inputs['input_ids'],
        attention_mask=inputs['attention_mask'],
        num_beams=4,
        length_penalty=2.0,
        max_length=1024,
        min_length=200,
        no_repeat_ngram_size=3
    )
    return tokenizer.decode(summary_ids[0], skip_special_tokens=True)


def summarize(input_text):
    start_time = time.time()
    inputs = preprocess_text(input_text)
    summary = generate_summary(inputs)
    end_time = time.time()
    print("Summary time elapsed: ", end_time - start_time)
    return summary


# Extract Preprocessing data page from Elastic

def reformat_content(txt):
    txt = txt.replace("http", "   http")
    txt = txt.replace("mailto", "   mailto")
    txt = txt.replace("](/", " ")

    # Regular expression pattern to match URLs
    url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')

    # Remove URLs from the text
    txt = re.sub(url_pattern, '', txt)

    # Regular expression pattern to match PDF filenames
    pdf_filename_pattern = re.compile(r'\b[\w-]+\.pdf\b', re.IGNORECASE)

    # Remove PDF filenames from the text
    txt = re.sub(pdf_filename_pattern, '', txt)

    return txt


def extract_data_from_index(elastic, name_input, query, last_sort_index):
    if last_sort_index == 0:
        search_result = elastic.search(index=name_input, body=query, sort=[{"timestamp": "asc"}])
    else:
        search_result = elastic.search(index=name_input, body=query, search_after=last_sort_index,
                                       sort=[{"timestamp": "asc"}])

    for hit in search_result['hits']['hits']:
        extracted_data = {
            'url': hit['_source']['url'],
            'title': hit['_source']['title'],
            'content': reformat_content(hit['_source']['content_txt']),  # content_txt
            'language': hit['_source']['lang'],
            'extracted_from': hit['_source'].get('extracted_from', ''),
            'content_xml': hit['_source']['content_xml'],
            'person_names': hit['_source']['person_names'],
        }

        yield extracted_data, hit


# Helpers
def contains_keyword(keywords, text):
    for keyword in keywords:
        pattern = r"\b" + re.escape(keyword) + r"\w*\b"
        if re.search(pattern, text, flags=re.IGNORECASE):
            return True

    return False


def should_be_ignored(data):
    # 1 - First ignore publications

    # List of keywords to check
    keywords = ["pdf", "prof", "download", "publication", "publikation", "archiv", "promov", "team", "talks",
                "vortraege", "associate",
                "meldungen", "office", "secretary",
                "student", "hilfskraft", "assistenz", "mitarbeiter", "angebote", "forum", "elnrw", "termin",
                "neuigkeit", "arbeitsgruppe", "dr.", "research group", "working group", "theme", "coop", "koop"]

    # In - URL
    if contains_keyword(keywords, data['url']):
        log.debug(f'Page titel contains keyword that should be ignored. Ignore page. {data["url"]}')
        return True
    
    # In - XML content
    root = ET.fromstring(data['content_xml'])
    h1_elements = root.findall(".//head[@rend='h1']")
    h2_elements = root.findall(".//head[@rend='h2']")
    
    if h1_elements:
        for h1_element in h1_elements:
            h1_text = h1_element.text.lower()
            if contains_keyword(keywords, h1_text):
                return True

    if h2_elements:
        for h2_element in h2_elements:
            if h2_element.text is not None:
                h2_text = h2_element.text.lower()
                if contains_keyword(keywords, h2_text):
                    return True

    # should have this in text
    # {"text": ".", "min": 2, "max": None } Should have sentence in the text
    must_have_keywords_text = [{"text": ".", "min": 2, "max": None}]
    for condition in must_have_keywords_text:
        if condition['min']:

            if data['content'].count(condition["text"]) <= condition["min"]:
                return True
        if condition['max']:
            if data['content'].count(condition["text"]) > condition["max"]:
                return True

    return False


def main():
    # Mining logic
    # Get Document with *project* *projekt* *research* or *forschung* in title or in url
    search_query = {
        "query": {"bool": {
            "should": [{"regexp": {"title": ".*project.*"}}, {"regexp": {"title": ".*projekt.*"}},
                       {"regexp": {"title": ".*research.*"}}, {"regexp": {"title": ".*forschung.*"}},
                       {"regexp": {"url": ".*project.*"}}, {"regexp": {"url": ".*projekt.*"}},
                       {"regexp": {"url": ".*research.*"}}, {"regexp": {"url": ".*forschung.*"}},
                       ],
        }
        },
        "fields": ["title", "url"]
    }

    # Get the number of documents in the index
    num_documents = es.count(index=index_pre)['count']
    print("num_documents:", num_documents)

    # Calculate the number of batches
    num_batches = (num_documents + batch_size - 1) // batch_size
    print("num_batches:", num_batches)

    # Last Sort
    last_sort = 0

    svm = SVM_Page_classifier(model_path=model_path)
    
    # Only for test: limit definition
    # index = 1

    for batch_number in range(num_batches):
        #print("last_sort", last_sort)

        for data, raw_data in extract_data_from_index(es, index_pre, search_query, last_sort):
            last_sort = raw_data['sort']
            # print("document_number --> ", index)

            if should_be_ignored(data):
                # print("Filtering - Ignore this page: -- ", data['url'])
                print("nothing")
            else:
                prediction = svm.predict(page=data)
                if prediction and prediction == 4:
                    research_data = {
                        'id': data['extracted_from'] + '_' + raw_data['_id'],
                        'url': data['url'],
                        'title': data['title'],
                        'type': 'research projects',
                        'language': data['language'],
                        'last_update': datetime.utcnow().isoformat(timespec='milliseconds') + "Z",
                        'extracted_from': data.get('extracted_from', ''),
                        'person_names': data['person_names']
                        # 'summary': summarize(data['content'])
                    }
                    print("project url: -- ", data['url'])
                    input("Enter for next ")
                    #es.index(index=research_project_index, body=research_data)
                else:
                    log.debug(f'Fitler document. The SVM classifier classified the page with the url {data["url"]} as not project.')
                    input("Enter for next ")
            #index += 1

if __name__ == "__main__":
    main()