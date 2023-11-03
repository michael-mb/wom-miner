import hashlib

def sha256(text: str):
    """Returns the sha256 hash of the passed string"""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()