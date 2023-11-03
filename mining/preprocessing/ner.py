"""Performs Named Entity Recognition for Preprocessing"""

from womutils.log import configure_logging
from womutils.config import ensure_config_exists, read_config
from womutils.elastic import configure_elastic_from_config, retrieve_all_documents, es_client
from womutils.exceptions import IgnoreThisPageException, TooLongForSpacy
from people.name_analysis import is_normalized_name
import logging
from typing import List
import spacy
from spacy.language import Language
from spacy.tokens import Doc, Span

log = logging.getLogger(__name__)
_nlp_en: Language = None
_nlp_de: Language = None

# Only enable "ner" and "tagger" module (the latter requires "tok2vec")
# see https://spacy.io/models#design-cnn
# Since we don't use tagger at the moment (see last comment in this file), we also can disable it
# _disabled_spacy_pipelines = ["parser", "attribute_ruler", "lemmatizer"]
# NOTE: The models are also used in the People Miner
#       Keep this in mind when you edit this code
_disabled_spacy_pipelines = ["tok2vec", "tagger", "parser", "attribute_ruler", "lemmatizer"]

def get_english_model() -> Language:
    """Returns the used English language model"""
    global _nlp_en
    if not _nlp_en:
        _nlp_en = spacy.load("en_core_web_lg", disable=_disabled_spacy_pipelines)
    return _nlp_en

def get_german_model() -> Language:
    """Returns the used German language model"""
    global _nlp_de
    if not _nlp_de:
        # Only enable "ner" and "tagger" module (the latter requires "tok2vec")
        _nlp_de = spacy.load("de_core_news_lg", disable=_disabled_spacy_pipelines)
    return _nlp_de

def recognize_names(txt:str, lang:str) -> List[str]:
    """Returns a list of all recognized person names in the passed plaintext string"""
    global nlp_en, nlp_de

    if len(txt) >= 1000000:
        # SpaCy can only handle 1GB text per default, we keep this limit
        raise TooLongForSpacy()

    # Load models
    if lang == "de":
        nlp = get_german_model()
    elif lang == "en":
        nlp = get_english_model()
    else:
        raise IgnoreThisPageException("Wrong language")
    
    # Split table separators from Trafilatura
    txt = txt.replace("|", "\n")

    # Replace "Dr." and "Prof.". Otherwise SpaCy's DE model won't recognize these names
    if lang == 'de':
        txt = txt.replace("Dr.", "")
        txt = txt.replace("Prof.", "")

    doc = nlp(txt)
    names = doc.ents

    # Filter person names
    # PER is for the German model, PERSON for the English model
    names = filter(lambda ne: (ne.label_ == 'PER' or ne.label_ == 'PERSON'), names)

    result = []
    for name in names:

        # For Documentation see
        # - https://spacy.io/api/span#attributes
        # - https://spacy.io/api/doc#attributes
        # - https://spacy.io/api/token#attributes

        # Ignore names not matching a specific pattern for firstname, lastname and middle name
        if not is_normalized_name(name.text):
            continue

        # Ignore names starting/ending with a non-proper noun
        # see Part of Speech tagging: https://spacy.io/usage/linguistic-features#pos-tagging
        # Note that we cannot use "range(name.start, name.end)" because maybe in the middle of the name are non-proper nouns

        # TODO Dies erzeugt zu viele False Negatives, da Namen nicht Eigennamen sein müssen ("Hagen", "Müller", "Glaser").
        #      Deshalb erstmal deaktiviert.
        # if not doc[name.start].pos_ == 'PROPN':
        #     continue
        # if not doc[name.end-1].pos_ == 'PROPN':
        #     continue

        result.append(name.text)
    return result