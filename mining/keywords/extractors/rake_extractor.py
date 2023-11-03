'''Rate based keyword extractor'''
from rake_nltk import Rake
from extractors.helper import normalize_scores

r = Rake()
    
def extract(text_list, lang_list):
    text_list = list(text_list)
    keywords_list = []
    for text in text_list:
        try:
            r.extract_keywords_from_text(text)
            ranked_phrases_with_scores = r.get_ranked_phrases_with_scores()
            scores = [score for score, _ in ranked_phrases_with_scores]
            normalized_scores = normalize_scores(scores)
            word_weights = {}
            for (score, phrase), norm_score in zip(ranked_phrases_with_scores, normalized_scores):
                words = phrase.split()
                weight = norm_score / len(words)
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

