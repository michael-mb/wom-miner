import logging
from elasticsearch import NotFoundError
import re

log = logging.getLogger(__name__)

def document_exists(es, index, id):
    """
    Check if a document with the given ID exists in the specified index.
    """
    try:
        es.get(index=index, id=id)
        return True
    except NotFoundError:
        return False

def get_num_documents(es, index_pre):
    """
    Get the number of documents in the specified index.
    """
    num_documents = es.count(index=index_pre)['count']
    log.info(f"num_documents: {num_documents}")
    return num_documents

def calculate_num_batches(num_documents, batch_size):
    """
    Calculate the number of batches based on the total number of documents and batch size.
    """
    num_batches = (num_documents + batch_size - 1) // batch_size
    log.info(f"num_batches: {num_batches}")
    return num_batches

def get_last_timestamp(timestamp):
    """
    Get the last timestamp to track the progress of document retrieval.
    """
    if timestamp:
        last_timestamp = [int(timestamp)]
    else:
        last_timestamp = 0
    return last_timestamp

def contains_keyword(keywords, text):
    """
    Check if the text contains any of the specified keywords.
    """
    for keyword in keywords:
        pattern = r"\b" + re.escape(keyword) + r"\w*\b"
        if re.search(pattern, text, flags=re.IGNORECASE):
            return True
    return False
