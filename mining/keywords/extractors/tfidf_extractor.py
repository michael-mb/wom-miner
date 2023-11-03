import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.corpus import stopwords
from extractors.helper import normalize_scores

stop_words = {
    'en': set(stopwords.words('english')),
    'de': set(stopwords.words('german')),
}

vectorizer = TfidfVectorizer()

def extract(text_list, lang_list):
    text_list = list(text_list)
    keywords_list = []
    for text, language in zip(text_list, lang_list):
        try:
            tfidf_matrix = vectorizer.fit_transform([text])
            feature_names = vectorizer.get_feature_names_out()
            tfidf_scores = tfidf_matrix.toarray()[0]
            normalized_scores = normalize_scores(tfidf_scores)
            word_weights = {}
            for idx, score in enumerate(normalized_scores):
                word = feature_names[idx]
                if word not in stop_words[language]:
                    if word in word_weights:
                        word_weights[word] += tfidf_scores
                    else:
                        word_weights[word] = score 
            keywords = list(word_weights.items())
        except Exception as e:
            print(f"An error occurred: {str(e)}, text: {text}")
            keywords = []
        keywords_list.append(keywords)
    return keywords_list
