import os
import numpy as np
import requests
import re
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
import joblib
from nltk.corpus import gutenberg
import nltk
nltk.download('gutenberg')
training_data = []
training_labels = []
for file_id in gutenberg.fileids():
    text = ' '.join(gutenberg.words(file_id))
    training_data.append(text)
    training_labels.append(file_id)

test_data = [
    "The field of machine learning is growing rapidly",
    "Deep learning is a subset of artificial intelligence",
    "Python libraries like scikit-learn and TensorFlow are used for machine learning",
    "Statistical analysis is an important part of data science",
    "Universities play a crucial role in advancing research",
    "Computer science programs at universities provide a strong foundation",
]
test_labels = ["Unknown"] * len(test_data)


path = "mining/preprocessing/keywords/bayes_models/"
model_path = os.path.join(path, "trained_model.pkl")
vectorizer_path = os.path.join(path, "vectorizer.pkl")

if not os.path.exists(model_path):
    vectorizer = CountVectorizer()
    X_train = vectorizer.fit_transform(training_data)
    X_test = vectorizer.transform(test_data)
    clf = MultinomialNB()
    clf.fit(X_train, training_labels)
    joblib.dump(clf, model_path)
    joblib.dump(vectorizer, vectorizer_path)
else:
    clf = joblib.load(model_path)
    vectorizer = joblib.load(vectorizer_path)


def classify(text):
    '''Classify text using Naive Bayes.'''
    test_data = [text]
    X_test = vectorizer.transform(test_data)
    predicted_labels = clf.predict(X_test)
    return predicted_labels[0]

def extract(text):
    '''Extract keywords from text using the classify function.'''
    keywords = [word for word in text.split(" ") if classify(word) != "Unknown" and len(word) > 0]
    return keywords

if __name__ == "__main__":
    input_text = """
        Python is a high-level, interpreted and general-purpose dynamic programming language 
        that focuses on code readability. The syntax in Python helps the programmers to do 
        coding in fewer steps as compared to Java or C++.
        Universities often teach Python in their computer science courses.
    """
    training_labels.append("Web Corpus")
    keywords = extract(input_text)
    print(keywords)
