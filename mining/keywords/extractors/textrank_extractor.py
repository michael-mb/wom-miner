import spacy
import pytextrank
import numpy as np

nlp_models = {
    'en': spacy.load("en_core_web_sm"),
    'de': spacy.load("de_core_news_sm"),
}

for nlp in nlp_models.values():
    nlp.add_pipe("textrank")

def extract(text_list, lang_list):        
    keywords_list = []
    for text, language in zip(text_list, lang_list):
        nlp = nlp_models.get(language)
        try:
            doc = nlp(text)
            phrases = doc._.phrases
            word_weights = {}
            for phrase in phrases:
                words = phrase.text.split()
                weight = phrase.rank / len(words)
                for word in words:
                    if word in word_weights:
                        word_weights[word] += weight
                    else:
                        word_weights[word] = weight
            keywords = list(word_weights.items())
        except Exception as e:
            print(f"An error occurred: {str(e)}, text: {text}")
            keywords = []
        keywords_list.append(keywords)
    return keywords_list
