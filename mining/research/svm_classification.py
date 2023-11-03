import numpy as np
import pysbd
import logging
import joblib
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

log = logging.getLogger(__name__)

def filter_data(data, segments, min_sentence, min_words, max_words, max_sentence):
    if len(segments) < min_sentence:                                                                        # check min sentence
        log.debug(f"The document with url {data.get('url')} doesn't meet the minimum sentence requirement.")
        return []                                                                                            # Skip the document if it doesn't meet the minimum sentence requirement

    filtered_segments = []                                                                                   # ["This is a sentence.", "This is a other sentence.", ... ]
    for counter, seg in enumerate(segments):                                                                 # remove to short or to long sentences
        word_numbers = len(seg.split())
        if word_numbers >= min_words and word_numbers <= max_words:
            filtered_segments.append(seg)

        if counter >= max_sentence-1:
            break

    if len(filtered_segments) < min_sentence:                                                                   # check min sentence again
        log.debug(f"The document with url {data.get('url')} doesn't meet the minimum sentence requirement.")
        return [] # Skip the document if it doesn't meet the minimum sentence requirement
    
    return filtered_segments

def process_embeddings(embeddings, pca_model, max_sentence):
    transformed_embeddings  = pca_model.transform(embeddings)         # reduce dimension - emb is an np.array like: [0.040342, 0.038845, ...]  with less data
    
    result_data = []
    for t_emb in transformed_embeddings :
        result_data.extend(t_emb)

    padding_length = pca_model.n_components * max_sentence - len(result_data)
    if padding_length > 0:
        return np.pad(result_data, (0, padding_length), mode='constant')
    elif padding_length == 0:
        return np.array(result_data)
    else:
        log.error(f'Error while process embeddings. padding_length can not be less then 0, but padding_length is {padding_length}')

class SVM_Page_classifier:

    def __init__(self, model_path):
        """
        Initialize the SVM_Page_classifier.

        Args:
            model_path (str): Path to the saved model file.
        """
        loaded_svm_model, loaded_pca_model, metadata = joblib.load(model_path)

        self.svm_model = loaded_svm_model
        self.pca_model = loaded_pca_model
        
        self.min_sentence = metadata['min_sentence']
        self.min_words = metadata['min_words']
        self.max_words = metadata['max_words']
        self.max_sentence = metadata['max_sentence']

        self.sentence_model = SentenceTransformer('sentence-transformers/distiluse-base-multilingual-cased-v1')    

    def _preprocessing_data(self, data: dict):
        """
        Preprocess the data for prediction.

        Args:
            data (dict): Input data dictionary with '_source' and 'content_txt' keys.

        Returns:
            bool: Flag indicating the success of data preprocessing.
            numpy.ndarray: Processed document features.
        """
        lang = None
        
        if data.get('lang', None):
            lang = data.get('lang', None)
        else:
            lang = data.get('language', None)
        segmenter = pysbd.Segmenter(language=lang, clean=False)                                   # Segment the document into sentences
        
        context = data.get('content_txt')
        if not context:
            context = data.get('content')
        segments = segmenter.segment(context)                                                      # ["This is a sentence.", "This is a other sentence.", ... ]
        
        filtered_segments = filter_data(data=data, segments=segments, max_sentence=self.max_sentence, max_words=self.max_words, min_sentence=self.min_sentence, min_words=self.min_words)
        if not filtered_segments:
            return False, []
        embeddings = [self.sentence_model.encode(seg, show_progress_bar=False) for seg in filtered_segments] # compute sentence embeddigns - emb is an np.array like: [0.00034, -1.034003, 0.0300334, ...] 
        result_data = process_embeddings(pca_model=self.pca_model, embeddings=embeddings, max_sentence=self.max_sentence)
        return True, result_data


    def predict(self, page):
        """
        Perform prediction on the input page.

        Args:
            page (dict): Input page data.

        Returns:
            int: Predicted label.
        """
        try:
            source = page.get('_source')            
            if source:
                page = source
            (success, doc_features) = self._preprocessing_data(data=page)
            if not success:
                log.debug('Document cannot be classified.')
                return -1  # Other label
            else:
                return self.svm_model.predict(np.array(doc_features).reshape(1, -1))
        except Exception as e:
            log.error('Document cannot be classified.', exc_info=True)



