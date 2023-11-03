import os
import time
import logging
from transformers import BartTokenizer, BartForConditionalGeneration

log = logging.getLogger(__name__)

# Set up BART summarization model and tokenizer
model_name = 'facebook/bart-large-cnn'
svm_model = './page_classification_model.pkl'
tokenizer = BartTokenizer.from_pretrained(model_name)
model = BartForConditionalGeneration.from_pretrained(model_name)
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

def generate_summary(inputs):
    """
    Generate a summary using the BART model.
    """
    summary_ids = model.generate(
        inputs['input_ids'],
        attention_mask=inputs['attention_mask'],
        num_beams=4,
        length_penalty=2.0,
        max_length=1024,
        min_length=200,
        no_repeat_ngram_size=3
    )
    return tokenizer.decode(summary_ids[0], skip_special_tokens=True)

def preprocess_text(text):
    """
    Preprocess the input text by tokenizing it with the BART tokenizer.
    """
    return tokenizer.batch_encode_plus(
        [text],
        max_length=1024,
        truncation=True,
        return_tensors='pt'
    )

def summarize(input_text):
    """
    Summarize the input text using the BART model.
    """
    if not input_text or len(input_text) < 10:
        return ""

    start_time = time.time()

    inputs = preprocess_text(input_text)
    summary = generate_summary(inputs)

    end_time = time.time()
    log.info("Summary time elapsed: " + str(end_time - start_time))

    return summary
