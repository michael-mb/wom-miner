"""
Does several preprocessing steps for the documents:
- Language detection
- Plain content extraction
- Stopwords removal
"""

from womutils.elastic import es_client, retrieve_all_documents
from womutils.exceptions import IgnoreThisPageException
from womutils.ShutdownHandler import ShutdownHandler
from womutils.Progress import Progress
from womutils import state_service
from preprocessing.ner import recognize_names
from elastic_transport import ConnectionTimeout

import trafilatura

from langdetect import LangDetectException
from bs4 import BeautifulSoup, Comment
from elasticsearch import Elasticsearch
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import langdetect
from datetime import datetime
import re
import logging

log = logging.getLogger(__name__)
es : Elasticsearch = None


def process_html_text(html_text:str, id:str):
    """Uses beautifulSoup to extract cleaned HTML, XML and plaintext from a HTML content"""

    # Remove header, head, nav, scripts and footer
    soup = BeautifulSoup(html_text, 'html.parser')

    # References:
    # - https://beautiful-soup-4.readthedocs.io/en/latest/#a-list
    # - https://beautiful-soup-4.readthedocs.io/en/latest/#calling-a-tag-is-like-calling-find-all
    # - https://beautiful-soup-4.readthedocs.io/en/latest/#extract

    main_tag = soup.find('main')
    if main_tag:
        # Start with main tag if found
        soup = main_tag
        
    # Remove garbage tags
    for not_wanted in soup(['head', 'header', 'nav', 'footer', 'script', 'pre', 'code']):
        not_wanted.decompose()
    
    div = soup.find('div')
    if not div:
        # we expect that all (useful) pages have at least one div element
        # TODO discussion, e.g. https://www.ruhr-uni-bochum.de/elektrobiochemie/Homeenglish.html
        raise IgnoreThisPageException("No div in HTML")
    
    # Remove comments in HTML (source: https://stackoverflow.com/a/23299678)
    for element in div(text=lambda text: isinstance(text, Comment)):
        element.extract()

    cleaned_html = soup.prettify()

    # Extract plaintext if possible
    try:
        extracted_text = trafilatura.extract(html_text, output_format="txt", include_formatting=False,
                                             include_images=False,
                                             include_comments=False, include_links=False)
    except Exception:
        log.warn(f"Trafilatura failed (plaintext), ID={id}", exc_info=1)
        extracted_text = ""

    # Extract XML if possible
    try:
        extracted_xml = trafilatura.extract(html_text, output_format="xml", include_comments=False, include_links=True)
    except Exception:
        log.warn(f"Trafilatura failed (XML), ID={id}", exc_info=1)
        extracted_xml = ""

    return cleaned_html, extracted_text, extracted_xml


def detect_language(text, id):
    """Returns 'de' or 'en', depending on the language of the passed text"""
    try:
        language = langdetect.detect(text)
    except LangDetectException:
        log.warn(f"Language detection failed, ID={id}", exc_info=1)
        # Note that we don't simply ignore the page. Instead, we return an empty language to still process this document.
        # Uncomment the following line if this behavior should be changed
        # raise IgnoreThisPageException("Language detection failed.")
        return ""
    
    # TODO You may add other supported languages
    if language not in ['de', 'en']:
        raise IgnoreThisPageException("Unsupported language: " + language)
    return language


def remove_stopwords(text, lang):
    """Removes stopwords from the passed plaintext"""

    # Tokenize the text into individual words via NLTK
    tokens = word_tokenize(text)

    # Get the list of stop words for the specified language
    if lang == 'en':
        stop_words = set(stopwords.words('english'))
    elif lang == 'de':
        stop_words = set(stopwords.words('german'))
    else:
        return ""
        # See comment in detect_language
        # raise ValueError("Unsupported language. Please choose 'english' or 'german'.")

    # Remove the stop words from the text
    filtered_tokens = [word for word in tokens if word.casefold() not in stop_words]

    # Join the filtered tokens back into a single text
    filtered_text = ' '.join(filtered_tokens)

    return filtered_text


def validate_content(content:str):
    """Raises IgnoreThisPageException if the page should be ignored due to not enough content"""

    if not content or not content.strip():
        raise IgnoreThisPageException("Empty")
    
    # Continue the process with html content only - Remove xml, bibtex, json, sql ...
    # TODO discussion, e.g. https://memiserf.medmikro.ruhr-uni-bochum.de/nrz/index.html
    if not "!doctype html" in content.lower():
        # print(content.lower())
        raise IgnoreThisPageException("No doctype HTML")
    
    # Detect pages with too few information with a simple heuristic that removes special characters and then counts the words
    content = re.sub(r'[^a-zA-Z0-9\s\n]', '', content)
    if len(content.split()) < 30:
        raise IgnoreThisPageException("Too few words")


def create_index(name:str):
    """Creates the required index for preprocessing, if not already exists"""
    if es.indices.exists(index=name):
        return # nothing to do
    
    es.indices.create(index=name, mappings={
        # Don't allow new fields https://www.elastic.co/guide/en/elasticsearch/reference/8.7/dynamic.html
        # https://www.elastic.co/guide/en/elasticsearch/reference/8.7/mapping-types.html
        # https://www.elastic.co/guide/en/elasticsearch/reference/8.7/keyword.html#wildcard-field-type
        "dynamic": 'strict',
        "properties": {
            "id":                             {"type": "text"},
            "url":                            {"type": "wildcard"},
            "title":                          {"type": "text", "fields": {"keyword": {"type": "keyword", "ignore_above": 512}}},
            "timestamp":                      {"type": "date", "format": "strict_date_time"},
            "content_html":                   {"type": "text"},
            "content_xml":                    {"type": "text"},
            "content_txt":                    {"type": "text"},
            "content_txt_without_stopwords":  {"type": "text"},
            "lang":                           {"type": "keyword", "ignore_above": 5},
            "keywords":                       {"type": "text"},
            "keywords_weights":               {"type": "half_float"},
            "person_names":                   {"type": "text"},
        }
    }, settings={
        # No settings yet
    })


def preprocess(doc):
    """Pre-processes the passed document"""

    # 0. Metadata
    result = {
        "id": doc['_id'],
        "url": doc['fields']["url"][0],
        "timestamp": datetime.utcnow().isoformat(timespec='milliseconds') + "Z",
    }
    if "title" in doc['fields']:
        result["title"] = doc['fields']["title"][0]

    # 1. Processing with Trafilatura
    (result['content_html'], result['content_txt'], result['content_xml']) = process_html_text(doc['fields']['content'][0], doc['_id'])
    
    # 2. Language detection
    if result['content_txt']:
        result['lang'] = detect_language(result['content_txt'], doc['_id'])

    if result["content_txt"] and result["lang"]:
        # 3. Remove stopwords
        result['content_txt_without_stopwords'] = remove_stopwords(result['content_txt'], result['lang'])
        # 4. Perform NER
        try:
            result["person_names"] = recognize_names(result["content_txt"], result["lang"])
        except Exception as e:
            log.warn("NER failed", exc_info=1)
    
    return result


def start(batch_size:int, university:str, state:str, only_update:bool):
    """Starts the preprocessing and executes the preprocessing loop"""

    if only_update:
        log.warn("Preprocessing was configured with 'only_update=True'. This will keep pre-existing fields that are not updated during Preprocessing.")

    # Create required indices
    source_index = "crawl-rawdata-" + university
    target_index = "preprocessing-" + university
    global es
    es = es_client()
    create_index(target_index)

    # Configure and read state (if configuration was passed)
    state_service.configure(state)
    last_timestamp = state_service.read()

    if last_timestamp:
        # If we start at a specific timestamp, don't process earlier documents
        # Note that because we use 'gte' instead of 'gt', the next pass overlaps by one document.
        # But this is intentional, in case an error occurred during the exit and the document was not sent properly to Elastic.
        query = { "bool": { "filter": [ { "range": { "timestamp": { "gte": last_timestamp }}} ]} }
    else:
        # If not, the empty query will be automatically handled as 'return all documents'
        query = None
    
    fields = ["title", "content", "url", "title", "title.keyword"]
    if state:
        # If we want to track the state, include the document timestamp in the query
        fields.append("timestamp")
    
    interrupted = False

    total_documents = es.count(index=source_index, query=query)["count"]
    progress = Progress(total_documents, batch_size)

    for doc in retrieve_all_documents(source_index, batch_size, fields=fields, query=query, source=False):

        with ShutdownHandler() as shutdownHandler:

            # log.info("Document no. " + str(i) + " with id=" + str(doc['_id']))
            try:
                # Execute preprocessing
                validate_content(doc['fields']['content'][0])
                result = preprocess(doc)

                # Index the document
                try:
                    if not only_update:
                        # Overwrite the whole document with 'result'. Previously existing fields may be deleted if they are not present in 'result'
                        es.index(id=doc['_id'], index=target_index, document=result)
                    else:
                        # Update the fields which are present in 'result', but otherwise keep existing fields
                        # Cited from docs: https://elasticsearch-py.readthedocs.io/en/v8.8.2/api.html#elasticsearch.Elasticsearch.update :
                        #   "doc_as_upsert=True = If the document does not already exist, the contents of 'result' are inserted as a new document."
                        es.update(id=doc['_id'], index=target_index, doc=result, source=False, doc_as_upsert=True)

                except ConnectionTimeout as e:
                    log.exception("Timeout while indexing " + doc['_id'])
                if state:
                    last_timestamp = doc['fields']['timestamp'][0]

            except IgnoreThisPageException as e:
                log.info(f"Ignore doc with ID={doc['_id']}, reason: {str(e)}")
                progress.ignore()
            except Exception as e:
                log.exception(f"Could not pre-process document with ID={doc['_id']}")
            
            progress.next()
            
            # return # ONLY FOR DEBUGGING

            if shutdownHandler.interrupted:
                # Don't continue with the outer loop
                interrupted = True
                break
    
    
    progress.finish()

    if not state:
        log.info("Preprocessing ended with no state information.")
    elif interrupted:
        state_service.write(last_timestamp)
        log.info("Preprocessing interrupted, next document to process: " + str(last_timestamp))
    else:
        # Note that we still save the state. This allows us to resume the preprocessing after new documents were crawled
        # state_service.clear()
        state_service.write(last_timestamp)
        log.info("Preprocessing ended regularly, no more documents to process. However, state will be saved to continue with new crawled documents: " + str(last_timestamp))
