from collections import Counter
from extractors.rake_extractor import extract as rake_extract
from extractors.textrank_extractor import extract as textrank_extract
from extractors.tfidf_extractor import extract as tfidf_extract
from extractors.keybert_extractor import extract as keybert_extract
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import re
from unidecode import unidecode
from index_word_count import common_string
from functools import partial
from keywords_common import clean_text



@lru_cache(maxsize=None)
def cached_extract(func, text, lang=None):
    if func.__name__ == 'keybert_extract':
        func = partial(func, lang=lang)
    return func(text)

from collections import Counter

def normalize_scores(keyword_tupel_list):
    '''Normalizes the scores of a list of keywords to a value between 0 and 1.'''
    if not keyword_tupel_list:
        return []

    max_weight = max([weight for keyword, weight in keyword_tupel_list], default=0)
    normalized_keywords = [(keyword, weight / max_weight) for keyword, weight in keyword_tupel_list]
    return normalized_keywords

def get_unique_keywords(doc_tupel_lists):
    '''Takes a list of lists of keyword tupels and returns a list of lists of unique keywords with aggregated weights.'''
    result = []
    for tupel_list in doc_tupel_lists:
        unique_keywords = {}
        for keyword, weight in tupel_list:
            if keyword in unique_keywords:
                unique_keywords[keyword] += float(weight)
            else:
                unique_keywords[keyword] = float(weight)
        unique_keywords = [(kw, round(wt, 3)) for kw, wt in unique_keywords.items()]
        unique_keywords.sort(key=lambda x: x[1], reverse=True)
        result.append(unique_keywords)
    return result


def get_unfiltered_keywords(raw_docs_list, lang=None):
    '''Extracts keywords from a text using RAKE, TextRank, and TF-IDF and returns the top percentile.'''
    raw_docs_tuple = tuple(raw_docs_list)
    lang_tuple = tuple(lang) 

    with ThreadPoolExecutor(max_workers=4) as executor:
        future_rake = executor.submit(rake_extract, raw_docs_tuple, lang_tuple)
        future_textrank = executor.submit(textrank_extract, raw_docs_tuple, lang_tuple)
        future_tfidf = executor.submit(tfidf_extract, raw_docs_tuple, lang_tuple)
        future_keybert = executor.submit(keybert_extract, raw_docs_tuple, lang_tuple)
        
        try:
            rake_keywords = future_rake.result()
        except Exception as e:
            print(f"An error occurred in rake_extract: {str(e)}, text: {raw_docs_tuple}")
            rake_keywords = []
            
        try:
            textrank_keywords = future_textrank.result()
        except Exception as e:
            print(f"An error occurred in textrank_extract: {str(e)}, text: {raw_docs_tuple}")
            textrank_keywords = []
            
        try:
            tfidf_keywords = future_tfidf.result()
        except Exception as e:
            print(f"An error occurred in tfidf_extract: {str(e)}, text: {raw_docs_tuple}")
            tfidf_keywords = []
            
        try:
            keybert_keywords = future_keybert.result()
        except Exception as e:
            print(f"An error occurred in keybert_extract: {str(e)}, text: {raw_docs_tuple}")
            keybert_keywords = []

    all_docs_keywords = []
    for i in range(len(raw_docs_list)):
        all_docs_keywords.append(rake_keywords[i] + textrank_keywords[i] + tfidf_keywords[i] + keybert_keywords[i])
    all_docs_keywords = get_unique_keywords(all_docs_keywords)
    len_keyword_lists = [min(len(keyword_tupel_list), 30) for keyword_tupel_list in all_docs_keywords]
    all_docs_normalized_scores = []
    for idx, keyword_tupel_list in enumerate(all_docs_keywords):
        all_docs_normalized_scores.append(normalize_scores(keyword_tupel_list[:len_keyword_lists[idx]]))
    final_keyword_list = []

    for keyword_list in all_docs_normalized_scores:
        filtered_keywords = [(kw, round(score, 3)) for kw, score in keyword_list if score > 0]
        final_keyword_list.append(filtered_keywords)

    return final_keyword_list




def keyword_batch_extractor(plain_text_list, lang_list=None, index="preprocessing-ude", connection=None):
    '''Extracts keywords from a list of plain texts and returns a list of lists of keywords.'''
    plain_text_list = [clean_text(plain_text) for plain_text in plain_text_list]
    raw_keywords_list = get_unfiltered_keywords(plain_text_list, lang_list)

    keywords_list = []
    for sublist in raw_keywords_list:
        filtered_sublist = [(keyword, score) for keyword, score in sublist 
                            if not common_string(index=index, search_string=keyword, connection=connection)]
        keywords_list.append(filtered_sublist)
    
    return keywords_list




if __name__ == "__main__":
    text = """
    Meldungen aus der UDE Best Retail Paper Award der AMA Oliver Büttner ausgezeichnet -//
    von Ulrike Eichweber - 22.03.2023 Für den Artikel "Exploratory Shopping: Attention//
    Affects Instore Exploration and Unplanned Purchasing“ erhielt UDE-Prof. //
    Oliver Büttner jetzt den Best Retail Paper Award der American Marketing //
    Association (AMA). Der Aufsatz erschien 2020 im renommierten Journal of //
    Consumer Research. Der Wirtschaftspsychologe wurde gemeinsam mit seinen//
    Co-Autoren Mathias Streicher (Universität Innsbruck) und Zachary Estes//
    (City University of London) ausgezeichnet. In ihrem Artikel fassen //
    die drei Wissenschaftler die Ergebnisse zu ihrem Forschungsprojekt //
    über den Einfluss von visuellen Reizen auf das Einkaufverhalten //
    zusammen. In mehreren Experimenten im Labor und in Geschäften //
    konnen sie zeigen, dass digitale Displays, auf denen Waren angepriesen //
    werden, die Aufmerksamkeitsbreite beim Shoppen verändern können: Die Menschen //
    gehen auf Erkundungstour im Laden, die in vielen Fällen dann bei eigentlich//
    nicht geplanten Käufen endete. "Die Befunde zeigen die Bedeutung unbewusster //
    Aufmerksamkeitssteuerung bei der Entstehung ungeplanter Kaufentscheidungen", //
    resümiert Büttner. Den Award vergibt die AMA für Arbeiten, die einen bedeutenden //
    Beitrag zur Handelsforschung leisten. Dabei konnten Beiträge aus sämtlichen //
    englischsprachigen Marketing-Journals nominiert werden. Die Preisverleihung //
    fand bei der diesjährigen AMA Winter Academic Conference in Nashville (USA) statt. //
    Weitere Informationen: https://amarapsig.org/?page_id=445 Post-Views: 419"""
    keywords = get_unfiltered_keywords([text,text], ["de","en"])
    for i in keywords:
        print(i)