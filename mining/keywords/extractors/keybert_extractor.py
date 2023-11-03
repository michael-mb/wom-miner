from keybert import KeyBERT
from sklearn.feature_extraction.text import CountVectorizer

models = {
    'de': KeyBERT(model="distiluse-base-multilingual-cased"),
    'en': KeyBERT(model="distilbert-base-nli-mean-tokens"),
}

vectorizer = CountVectorizer()

def extract(text_list, lang_list):        
    text_list = list(text_list)
    keywords_list = []

    for text, lang in zip(text_list, lang_list):
        if lang not in models:
            lang = 'de'
        kw_model = models[lang]
        try:
            document_matrix = vectorizer.fit_transform([text])
            feature_names = vectorizer.get_feature_names_out()
            keywords = kw_model.extract_keywords(docs=[text], vectorizer=vectorizer, top_n=10)
        except Exception as e:
            print(f"An error occurred: {str(e)}, text: {text}")
            keywords = []
        keywords_list.append(keywords)
    return keywords_list
