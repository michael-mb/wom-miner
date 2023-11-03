from transformers import AutoTokenizer, AutoModelForTokenClassification
from transformers import pipeline

def extract(text):
    model = AutoModelForTokenClassification.from_pretrained("dslim/bert-base-NER")
    tokenizer = AutoTokenizer.from_pretrained("dslim/bert-base-NER")
    nlp = pipeline("ner", model=model, tokenizer=tokenizer)
    result = nlp(text)
    keywords = [word['word'] for word in result if word['entity'] != 'O']  # Exclude non-entity words
    return keywords


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
    print(extract(text))
