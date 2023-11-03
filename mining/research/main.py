import logging
import re
import xml.etree.ElementTree as ET
import sys
sys.path.append('../mining')
from research.summarizer import summarize
from research.util import calculate_num_batches, document_exists, get_last_timestamp, get_num_documents, contains_keyword
from datetime import datetime

from womutils.elastic import es_client
from womutils.exceptions import IgnoreThisPageException

log = logging.getLogger(__name__)

# Mining logic
# Get Document with *project* *projekt* *research* or *forschung* in title or in url
search_query = {
    "query": {"bool": {
        "should": [{"regexp": {"title": ".*project.*"}}, {"regexp": {"title": ".*projekt.*"}},
                    {"regexp": {"title": ".*research.*"}}, {"regexp": {"title": ".*forschung.*"}},
                    {"regexp": {"url": ".*project.*"}}, {"regexp": {"url": ".*projekt.*"}},
                    {"regexp": {"url": ".*research.*"}}, {"regexp": {"url": ".*forschung.*"}},

                    # To retrieve documents that do not necessarily have project in their url or title
                    {"regexp": {"content_txt": ".*projektbeschreibung.*"}},
                    {"regexp": {"content_txt": ".*projektleitung.*"}},
                    {"regexp": {"content_txt": ".*projektkoordination.*"}},
                    {"regexp": {"content_txt": ".*projektförderung.*"}},
                    {"regexp": {"content_txt": ".*projektlaufzeit.*"}},
                    {"regexp": {"content_txt": ".*Projektbearbeiter.*"}},

                    {"regexp": {"content_txt": ".*project description.*"}},
                    {"regexp": {"content_txt": ".*project management.*"}},
                    {"regexp": {"content_txt": ".*project coordination.*"}},
                    {"regexp": {"content_txt": ".*project funding.*"}},
                    {"regexp": {"content_txt": ".*project duration.*"}}
                    ],
    }
    },
    "fields": ["title", "url"]
}


# Extract Preprocessing data page from Elastic
def reformat_content(txt):
    if txt is None:
        return ''
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
            'title': hit['_source'].get('title', 'no_title'),
            'content_txt': reformat_content(hit['_source'].get('content_txt', '')),  # content_txt
            'lang': hit['_source'].get('lang', ''),
            # 'keywords': hit['_source']['keywords'],
            'content_xml': hit['_source'].get('content_xml', ''),
            'person_names': hit['_source'].get('person_names', []),
        }

        yield extracted_data, hit


def should_be_ignored(data):
    # 1 - First ignore publications
    # List of keywords to check
    to_exclude_keywords = ["pdf", "prof", "download", "publication", "publikation", "archiv", "promov", "team", "talks",
                           "vortraege", "associate", "Stellenausschreibung", "job", "meldungen", "presseinformationen",
                           "presse", "campus", "impressum", "datenschutz", "ansprechpartner", "kontakt", "inhalt",
                           "student", "hilfskraft", "assistenz", "mitarbeiter", "angebote", "forum", "elnrw", "termin",
                           "neuigkeit", "arbeitsgruppe", "dr.", "research group", "working group", "theme", "coop",
                           "koop", "office", "secretary", "contact", "news", "semester", "winter", "sommer",
                           "veroeffen", "bachelor", "master", "database", "school"
                           ]

    # In - URL
    if contains_keyword(to_exclude_keywords, data['url']):
        return True

    # In - Title
    if contains_keyword(to_exclude_keywords, data['title']):
        return True
    # In - XML content
    root = ET.fromstring(data['content_xml'])
    h1_elements = root.findall(".//head[@rend='h1']")
    h2_elements = root.findall(".//head[@rend='h2']")
    if h1_elements:
        for h1_element in h1_elements:
            h1_text = h1_element.text.lower()
            if contains_keyword(to_exclude_keywords, h1_text):
                return True
    if h2_elements:
        for h2_element in h2_elements:
            if h2_element.text is not None:
                h2_text = h2_element.text.lower()
                if contains_keyword(to_exclude_keywords, h2_text):
                    return True
    return False


def init_elastic(research_project_index):
    es = es_client()
    es.indices.create(index=research_project_index,
                      mappings={
                          "dynamic": 'strict',
                          "properties": {
                              "id": {"type": "text"},
                              "url": {"type": "wildcard"},
                              "title": {"type": "text",
                                        "fields": {"keyword": {"type": "keyword", "ignore_above": 512}}},
                              "type": {"type": "text"},
                              "lang": {"type": "keyword", "ignore_above": 5},
                              "last_update": {"type": "text",
                                              "fields": {"keyword": {"type": "keyword", "ignore_above": 512}}},
                              "content": {"type": "text"},
                              "person_names": {"type": "text"},
                              # "keywords": {"type": "text"},
                              "summary": {"type": "text"},
                          }
                      },
                      ignore=400)  # ignore 400 Index Already Exists exception
    return es


def process_batch(es, index_pre, research_project_index, batch_size, last_timestamp, university):
    log.info(f"last_timestamp={last_timestamp}")
    for data, doc in extract_data_from_index(es, index_pre, search_query, last_timestamp):
        last_timestamp = doc['sort']
        id = 'research_miner' + '_' + university + '_' + doc['_id']
        if document_exists(es, research_project_index, id):
            log.info(f"Document with this URL -> {data['url']} already exists")
        else:
            if should_be_ignored(data):
                log.info(f"Ignore doc with ID={doc['_id']} - URL={data['url']}, reason: Document has not passed filter criteria")
                continue
            else:
                if data['content_txt'] == '':
                    log.exception(f"Could not index the document with ID={doc['_id']} - URL={data['url']}, ,reason: Content is empty")
                    continue
                research_data = {
                    'id': id,
                    'url': data['url'],
                    'title': data['title'],
                    'type': 'research projects',
                    'lang': data['lang'],
                    'content': data['content_txt'],
                    'last_update': datetime.utcnow().isoformat(timespec='milliseconds') + "Z",
                    'person_names': data['person_names'],
                    'summary': summarize(data['content_txt'])
                }
            es.index(index=research_project_index, body=research_data, id=research_data['id'])
    return last_timestamp


def start(batch_size: int, university: str, timestamp: int):
    # Miner Configuration
    index_pre = "preprocessing-" + university
    research_project_index = "research_project-" + university

    # Create Elasticsearch instance with the research project index
    es = init_elastic(research_project_index=research_project_index)

    # Get the total number of documents in the preprocessing index
    num_documents = get_num_documents(es, index_pre)

    # Calculate the number of batches based on the total number of documents and batch size
    num_batches = calculate_num_batches(num_documents, batch_size)

    last_timestamp = get_last_timestamp(timestamp)

    # Iterate over each batch
    for batch_number in range(num_batches):
        # Process the batch and update the last timestamp
        last_timestamp = process_batch(es, index_pre, research_project_index, batch_size, last_timestamp, university)

