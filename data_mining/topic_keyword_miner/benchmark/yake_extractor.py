import string
from nltk.corpus import stopwords
import yake

def preprocess_text(text):
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = ' '.join(text.split())
    return text

def extract(text, lang='en', max_ngram_size=3, deduplication_threshold=0.9, numOfKeywords=20):
    preprocessed_text = preprocess_text(text)
    stopwords_list = set(stopwords.words('english'))
    custom_kw_extractor = yake.KeywordExtractor(lan=lang, n=max_ngram_size, dedupLim=deduplication_threshold, top=numOfKeywords, features=None)
    if stopwords_list is not None:
        custom_kw_extractor.stopword_set = stopwords_list
    keywords = custom_kw_extractor.extract_keywords(preprocessed_text)
    keyword_list = [kw[0] for kw in keywords if kw[0].strip() and kw[0] not in stopwords_list]
    return keyword_list


if __name__ == "__main__":
    text = """
    Python is a high-level, interpreted and general-purpose dynamic programming language 
    that focuses on code readability. The syntax in Python helps the programmers to do 
    coding in fewer steps as compared to Java or C++.
    Universities often teach Python in their computer science courses.

    TextRank is a graph-based ranking algorithm that was initially developed for automatic text summarization. 
    However, it has been adapted for keyword extraction by representing a document as a graph of words or phrases, 
    where nodes represent words or phrases, and edges represent the co-occurrence or semantic similarity between them.
    """
    keywords = extract(text)
    print(keywords)
