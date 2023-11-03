from womutils.elastic import es_client, retrieve_all_documents
from people import queries, preprocessing, people_store
from people.types import Person, WebPage, MergedPerson
from people.ner import extract_people_from_plaintext
from people.table_analysis import extract_people_from_table
from elasticsearch import NotFoundError
from womutils.exceptions import IgnoreThisPageException
from womutils.Progress import Progress
from typing import List
from lxml.etree import XMLSyntaxError
from urllib.parse import urljoin
from womutils.hashes import sha256
import copy
from time import perf_counter

import logging
log = logging.getLogger(__name__)


def create_index(name: str):
    es = es_client()
    # Delete index to start fresh
    if es.indices.exists(index=name):
        es.indices.delete(index=name)

    es.indices.create(index=name, mappings={
        # Don't allow new fields https://www.elastic.co/guide/en/elasticsearch/reference/8.8/dynamic.html
        # https://www.elastic.co/guide/en/elasticsearch/reference/8.8/mapping-types.html
        # https://www.elastic.co/guide/en/elasticsearch/reference/8.8/keyword.html#wildcard-field-type
        "dynamic": 'strict',
        "properties": {
            "name":          {"type": "text"},
            "title":         {"type": "text"},
            "email":         {"type": "wildcard"},
            "found_in":      {"type": "wildcard"},
            "source":        {"type": "wildcard"},
            "homepages":     {"type": "wildcard"},
            # Filled later by keyword search
            "doc.keywords":         {"type": "text"},
            "doc.keywords_weights": {"type": "half_float"},
        }
    }, settings={
        # Intentionally empty since there are not settings yet
    })


# We use urljoin from urllib.parse instead
# def normalize_homepage(p:Person, url):
    """Normalizes the homepage of a person to absolute URLs and non-obfuscating email addresses"""

    # TODO does not work on
    # - https://www.pe.ruhr-uni-bochum.de/erziehungswissenschaft/personen.html.de
    # - https://www2.wiwi.rub.de/en/chair-projects/team/

    # Resolve relative homepage
    # if p.homepage.startswith("/"):
    #     # Remove leading / if already present in url
    #     p.homepage = url + p.homepage[1:] if url.endswith("/") else url + p.homepage


def extract_people(document:WebPage) -> List[Person]:
    """Returns all people in the passed document (plaintext and XML provided)"""

    # Start with table extraction
    people : List[Person] = []
    try:
        people += extract_people_from_table(document)
    except XMLSyntaxError:
        log.warning(f"Malformed HTML in {document.url}")
    except Exception as e:
        log.warning(f"Exception for HTML processing in {document.url}: " + str(e))

    # Add potential missing people not covered by the tables
    for person_from_txt in extract_people_from_plaintext(document):
        if person_from_txt not in people:
            people.append(person_from_txt)    

    # Ignore pages with too few names
    if len(people) < 3:
        # TODO This may lead to too many ignored pages
        #      We search for tables / overviews - not for detail pages
        raise IgnoreThisPageException("Too few names")
    
    for p in people:
        if p.homepage:
            p.homepage = urljoin(document.url, p.homepage)

    return people


def index_person(p:MergedPerson, university):
    """Indexes a single person"""
    saved_doc = {
        "name": p.name,
        "title": p.title,
        "email": p.email,
        "found_in": p.found_in,
        "source": p.source,
        "homepages": p.homepage,
    }
    es_client().index(index="people-" + university, document=saved_doc)


def process_document(doc:WebPage, university, csv):
    """Processes a single document"""

    people = extract_people(doc)

    # Set missing attributes and add person to store
    for p in people:
        p.found_in = doc.url
        people_store.add_person(p)

    # with open(f"./people/results/rawpage_{id}.txt", "w") as f:
    #     f.write(doc_processed['_source']["content_html"])
    #     f.write("------------------------------------------------------------------------------------------------------------------------")
    #     f.write(doc_processed['_source']["content_txt"])
    # Append lines

    # if csv:
    # CSV always active to compare results directly

    # Write the recognized people into a CSV file
    with open(f"./people/results/people-{university}.csv", "a", encoding="utf-8") as f:
        # f.write(doc["fields"]["url"][0])
        # f.write("\n")
        for person in people:
            f.write('"')
            f.write('","'.join([person.title,person.name,person.email,person.source,person.homepage,person.found_in]))
            f.write('"\n')

        # f.write("\n".join(str(s) for s in names))
        # f.write("\n")

    
    # else:
    
    # if not csv:
    #     # Save the people into an Elasticsearch index
    #     for p in people:

    #         # See comment in "duplicate_manager.py"
    #         log.info("H E R E")
    #         if not duplicate_manager.skip_name(person.name):
    #             duplicate_manager.add_name(person.name)

    #             saved_doc = {
    #                 "name": p.name,
    #                 "title": p.title,
    #                 "email": p.email,
    #                 "in.url": p.found_in,
    #                 "in.hash": sha256(p.found_in),
    #                 "homepage.url": p.homepage,
    #                 "homepage.hash": sha256(p.homepage)
    #             }
    #             es_client().index(index="people-" + university, document=saved_doc)
    
    # TODO Jetzt ist das Dokument fertig und doc.root kann gelöscht werden
    #      (Besser noch ein wenig früher!)


# def process_document(doc:WebPage, university, csv):
#     """Processes a single document"""
#     # Ignore documents where no plaintext is available since we heavily rely on this
#     if not 'content_txt' in doc['fields']:
#         raise IgnoreThisPageException("Plaintext missing")

#     # Note that we use content_html instead of content_xml as Trafilatura sometimes skips rows or even whole tables
#     people = extract_people(doc['fields']['content_txt'][0], doc['fields']['content_html'][0], doc['fields']['lang'][0], doc["fields"]["url"][0])

#     # Set "found_in" attributes
#     for p in people:
#         p.found_in_id = doc["_id"]
#         p.found_in_url = doc["fields"]["url"][0]

#     # with open(f"./people/results/rawpage_{id}.txt", "w") as f:
#     #     f.write(doc_processed['_source']["content_html"])
#     #     f.write("------------------------------------------------------------------------------------------------------------------------")
#     #     f.write(doc_processed['_source']["content_txt"])
#     # Append lines

#     if csv:
#         # Write the recognized people into a CSV file
#         with open(f"./people/results/people-{university}.csv", "a", encoding="utf-8") as f:
#             # f.write(doc["fields"]["url"][0])
#             # f.write("\n")
#             for person in people:
#                 f.write('"')
#                 f.write('","'.join([person.title,person.name,person.email,person.source,person.homepage,person.found_in_url]))
#                 f.write('"\n')
#             # f.write("\n".join(str(s) for s in names))
#             # f.write("\n")
    
#     else:
#         target_index = "people-" + university
#         create_index(target_index)
#         # Save the people into an Elasticsearch index
#         for p in people:
#             doc = {
#                 "name": p.name,
#                 "title": p.title,
#                 "email": p.email,
#                 "in.url": p.found_in,
#                 "in.hash": sha256(p.found_in),
#                 "homepage.url": p.homepage,
#                 "homepage.hash": sha256(p.homepage)
#             }
#             es_client().index(index=target_index, document=doc)
            


def start_single(url, university):
    """Processes one single document and prints the result on the console"""
    # prep_index = "preprocessing-" + university
    crawl_index = "crawl-rawdata-" + university
    # fields = ["title", "url", "content_txt", "content_html", "lang"]
    fields = ["title", "url", "content"]
    query = copy.deepcopy(queries.staff_page_by_title) # Note: We may call this method twice so we need to create a copy, see https://stackoverflow.com/a/2465932
    # Append a URL search to the query
    query['bool']['must'].append({"match": {"url": url}})

    result = es_client().search(index=crawl_index, fields=fields, query=query, source=False)
    cnt = result["hits"]["total"]["value"]
    if cnt == 0:
        log.error(f"Page {url} was not found in {crawl_index} or search criteria don't match")
        return
    if cnt > 1:
        log.error(f"Multiple pages were found in {crawl_index}, this should not be possible")
        return
    
    doc = result["hits"]["hits"][0]

    url = doc['fields']['url'][0]
    content = doc['fields']['content'][0]
    webPage = WebPage(doc["_id"], url, content)
    preprocessing.extract_web_page(webPage)
    
    # people = extract_people(doc['fields']['content_txt'][0], doc['fields']['content_html'][0], doc['fields']['lang'][0],doc["fields"]["url"][0])
    people = extract_people(webPage)

    print("Title                          │ Name                                          │ Email                                                        │ Source │ Homepage")
    print("───────────────────────────────┼───────────────────────────────────────────────┼──────────────────────────────────────────────────────────────┼────────┼────────────────────────────────────────────────")
    for p in people:
        # Print person to console
        print(f"{p.title:<30} │ {p.name:<45} │ {p.email:<60} │ {p.source:<6} │ {p.homepage}")


def start(batch_size: int, university: str, csv):
    people_store.clear()
    # The previously search from preprocessing index was commented out
    
    target_index = "people-" + university
    if not csv:
        create_index(target_index)

    # prep_index = "preprocessing-" + university
    crawl_index = "crawl-rawdata-" + university

    # Overwrite files once to clear it
    with open(f"./people/results/people-{university}.csv", "w") as f:
        f.write("sep=,\n")
    with open(f"./people/results/people-{university}-cleaned.csv", "w") as f:
        f.write("sep=,\n")
    
    # cnt = es_client().count(index=prep_index, query=queries.staff_page_by_title)['count']
    cnt = es_client().count(index=crawl_index, query=queries.staff_page_by_title)['count']
    progress = Progress(cnt, batch_size)

    # Look for pages with words in the title indicating that this is a staff page
    # fields = ["title", "url", "content_txt", "content_html", "lang"]
    fields = ["title", "url", "content"]
    # We sort in deterministic order
    # Sorting by URL is very convenient, since this first visits pages like "/team" and then "/team/concrete-person"
    # sort = [{"lang": "asc"},{"url": "asc"}]
    sort = [{"url": "asc"}]
    # for doc in retrieve_all_documents(prep_index, batch_size, fields=fields, query=queries.staff_page_by_title, source=False, sort=sort):
    # i = 0
    for doc in retrieve_all_documents(crawl_index, batch_size, fields=fields, query=queries.staff_page_by_title, source=False, sort=sort):

        # print(doc)

        # TODO Erst nachher prüfen und dann schauen, auf welcher Seite wurden mehr Namen gefunden
        #      oder gar keine Duplikate rausfiltern
        # if url_manager.skip_url(doc['fields']['url'][0]):
        #     log.info(f"Skipped {doc['fields']['url'][0]} due to URL policy")
        #     progress.next()
        #     continue

        try:
            url = doc['fields']['url'][0]
            content = doc['fields']['content'][0]
            webPage = WebPage(doc["_id"], url, content)

            # Do preprocessing
            start = perf_counter()
            preprocessing.extract_web_page(webPage)
            diff = round(perf_counter() - start, 3)
            if diff > 1.5:
                log.warning(f"Preprocessing took long: {diff}s for {url}")

            # Extract people
            start = perf_counter()
            process_document(webPage, university, csv)
            diff = round(perf_counter() - start, 3)
            if diff > 1.5:
                log.warning(f"People extraction took long: {diff}s for {url}")

        except IgnoreThisPageException as e:
            log.warning(f"Ignore {url}, reason: {str(e)}")
            progress.ignore()
        except Exception as e:
            log.exception(url)
            # return

        progress.next()
        
        # This is for debugging (limiting the number of documents)
        # i += 1
        # if i > 500:
        #     break
        
        # return # ONLY DEBUGGING

    # TODO 2. Look for pages where the title indicates a person detail view
    #         e.g. pages where the title starts with "Prof."

    progress.finish()

    log.info("Finished with mining. Next step is duplicate removal.")

    # Now clean the duplicates
    people_cleaned = people_store.aggregate_people()
    
    progress = Progress(len(people_cleaned), batch_size)

    # Write cleaned people into a CSV file
    with open(f"./people/results/people-{university}-cleaned.csv", "a", encoding="utf-8") as f:
        for person in people_cleaned:
            f.write('"')
            source = ",".join(list(dict.fromkeys(person.source)))
            homepage = "" if len(person.homepage) == 0 else person.homepage[0] if len(person.homepage) == 1 else "multiple"
            found_in = person.found_in[0] if len(person.found_in) == 1 else "multiple"
            f.write('","'.join([person.title,person.name,person.email,source,homepage,found_in]))
            f.write('"\n')

            # If there is no argument indicating that the search is CSV-only, save the person in the index
            if not csv:
                index_person(person, university)
                progress.next()
         
    if not csv:       
        progress.finish()

