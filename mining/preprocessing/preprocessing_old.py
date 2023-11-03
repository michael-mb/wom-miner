# NOTE: This is currently unstable. Use "preprocessing.py"

import tomllib
import nltk
import trafilatura
import hashlib
import time

from langdetect import LangDetectException
from bs4 import BeautifulSoup
from elasticsearch import Elasticsearch
from elasticsearch.helpers import scan, bulk
from pathlib import Path
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from langdetect import detect
from datetime import datetime

# 0 - Elastic connection

# Init NLTK
nltk.download('stopwords')
nltk.download('punkt')

with open(Path(f"./config/elastic.toml"), "rb") as f:
    config = tomllib.load(f)

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

# Preprocessing Configuration
index_name_input = config['index_name']
batch_size = config['batch_size']
index_pre = config['pre_index']

# create index if not exist
es.indices.create(index=index_pre, ignore=400)  # ignore 400 Index Already Exists exception


# 1 - Extract HTML page from Elastic Function
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
            'content': hit['_source']['content'],
        }
        yield extracted_data, hit


# 2 - Use beautifulSoup to extract HTML Content
def process_html_text(html_text):
    # Continue the process with html content only - Remove xml, bibtex, json, sql ...
    if not (("!DOCTYPE html" in html_text) or ("!DOCTYPE HTML" in html_text) or ("!doctype html" in html_text) or (
            "!doctype HTML" in html_text)):
        return ""

    # Remove header, head, nav, scripts and footer
    soup = BeautifulSoup(html_text, 'html.parser')

    main_tag = soup.find('main')
    if not main_tag:
        header = soup.find('header')
        head = soup.find('head')
        nav = soup.find('nav')
        footer = soup.find('footer')
        if header:
            header.decompose()
        if head:
            head.decompose()
        if nav:
            nav.decompose()
        if footer:
            footer.decompose()
        for script in soup("script"):
            script.decompose()
        for pre in soup("pre"):
            pre.decompose()
        for code in soup("code"):
            code.decompose()
    else:
        soup = main_tag

    cleaned_html = soup.prettify()

    try:
        extracted_text = trafilatura.extract(html_text, output_format="txt", include_formatting=False,
                                             include_images=False,
                                             include_comments=False, include_links=True)
    except Exception:
        extracted_text = ""
    try:
        extracted_xml = trafilatura.extract(html_text, output_format="xml", include_comments=False, include_links=True)
    except Exception:
        extracted_xml = ""

    return cleaned_html, extracted_text, extracted_xml


# 3 - Remove Stopwords
def remove_stopwords(text, lang):
    # Tokenize the text into individual words
    tokens = word_tokenize(text)

    # Get the list of stop words for the specified language
    if lang == 'en':
        stop_words = set(stopwords.words('english'))
    elif lang == 'de':
        stop_words = set(stopwords.words('german'))
    else:
        raise ValueError("Unsupported language. Please choose 'english' or 'german'.")

    # Remove the stop words from the text
    filtered_tokens = [word for word in tokens if word.casefold() not in stop_words]

    # Join the filtered tokens back into a single text
    filtered_text = ' '.join(filtered_tokens)

    return filtered_text


# 4 - Helpers
def validate_content(content):
    # remove ponctuations
    if content is None:
        return False

    punctuations = '''!()-[]{};:'"\,<>./?@#$%^&*_~'''
    for char in punctuations:
        content = content.replace(char, "")

    # Divide the text into words and return the number of words
    if len(content.split()) < 30:
        return False

    return True


def delete_document(es_index, identifier):
    response = es.delete(index=es_index, id=identifier)
    if response['result'] == 'deleted':
        print("Document successfully removed.")
    else:
        print("Failed to remove document.")


def calculate_sha256(text: str):
    """Returns the sha256 checksum of the passed string"""

    sha256_hash = hashlib.sha256()
    sha256_hash.update(text.encode('utf-8'))
    return sha256_hash.hexdigest()


def main():
    # 5 - preprocessing logic
    search_query = {"query": {"match_all": {}}, "size": batch_size}

    # Get the number of documents in the index
    num_documents = es.count(index=index_name_input)['count']
    print("num_documents:", num_documents)

    # Calculate the number of batches
    num_batches = (num_documents + batch_size - 1) // batch_size
    print("num_batches:", num_batches)

    # Last Sort
    # last_sort = [1684957263464]
    last_sort = 0
    index = 1

    start_time = time.perf_counter()

    for batch_number in range(num_batches):
        print("last_sort", last_sort)
        for data, raw_data in extract_data_from_index(es, index_name_input, search_query, last_sort):

            try:
                (extracted_cleaned_html, extracted_content, extracted_content_xml) = process_html_text(data['content'])
                if not validate_content(extracted_content):
                    delete_document(es_index=index_name_input, identifier=raw_data['_id'])
                else:

                    # Language detection
                    try:
                        language = detect(extracted_content)
                    except LangDetectException:
                        print("No features in text.")
                        language = "no-lang"

                    # Delete index if not in german or english
                    if language not in ['de', 'en']:
                        delete_document(es_index=index_name_input, identifier=raw_data['_id'])
                        continue
                    ret_data = {}
                    # Crawler ID + nonce ("preprocessing")
                    ret_data['id'] = raw_data['_id']
                    ret_data['language'] = language
                    # TODO wird das Feld von jemandem verwendet? Ich würde das gerne raus lassen, da es unsere Dokumente viel größer macht.
                    # ret_data['cleaned_html'] = extracted_cleaned_html
                    ret_data['content'] = extracted_content
                    ret_data['content_without_stopwords'] = remove_stopwords(extracted_content, language)
                    ret_data['extracted_xml'] = extracted_content_xml
                    ret_data['extracted_from'] = index_name_input
                    ret_data['timestamp'] = datetime.utcnow().isoformat(timespec='milliseconds') + "Z"
                    es.index(index=index_pre, body=ret_data)

                last_sort = raw_data['sort']

                index += 1
                if index % 10000 == 0:
                    end_time = time.perf_counter()
                    elapsed_time = end_time - start_time
                    print(f"Time elapsed : {elapsed_time:.2f} seconds")

                    # reset start time
                    start_time = time.perf_counter()
            except ValueError:
                print("Extraction Error *****")
                print("data url:", data['url'])
                print("data title:", data['title'])
                # ignore
                # delete_document(es_index=index_name_input, identifier=raw_data['_id'])


if __name__ == "__main__":
    main()
