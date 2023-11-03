class IgnoreThisPageException(Exception):
    """Raised when the current page should be ignored"""
    pass
class TooLongForSpacy(Exception):
    """Raised when a text is too long for NLP with Spacy"""
    pass