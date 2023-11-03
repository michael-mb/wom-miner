---
gitea: none
include_toc: true
---

# Mining

**Setup**

1. Install requirements:  
   ```
   pipenv install        # For development (e.g. Jupyter Notebooks and Evaluation): "pipenv install -d"
   pipenv run cmd        # Alternative: "pipenv shell"
   ```
2. Download additional NLTK data (see [Installing NLTK Data](https://www.nltk.org/data.html) and [API docs of nltk.downloader](https://www.nltk.org/api/nltk.downloader.html#downloading-packages)):
   ```
   python
   import nltk
   nltk.download('stopwords')
   nltk.download('punkt')
   ```
3. Import Spacy models (see [Trained Models & Pipelines](https://spacy.io/models)):
   ```
   python -m spacy download de_core_news_lg
   python -m spacy download de_core_news_sm
   python -m spacy download en_core_web_lg
   python -m spacy download en_core_web_sm
   ```
   In case of problems:
   ```
   python -m spacy validate
   ```

## Preprocessing

Creates index with prefix `preprocessing-` with the following information:

- id: ID of the original document
- url: URL of the page (from crawler data)
- title: Title of the page (from crawler data)
- timestamp: When the document was pre-processed
- content_html: Cleaned HTML content without head, header, footer etc. (Beautifulsoup)
- content_xml: Cleaned HTML content in simplified XML form (Trafilatura)
- content_txt: Content of the page in plaintext (Trafilatura)
- content_txt_without_stopwords: Content of the page in plaintext without stopwords
- lang: Language of the document
- person_names: Which people names were recognized by NER

Prepares the following fields:

- keywords: Will be filled by the Keyword Extraction with keywords that describe the document

**Usage**

```
python preprocessing.py -h
```

**Examples**

```
python preprocessing.py rub local --logfile logs/preprocessing-rub.log --state logs/preprocessing-rub.state.txt
python preprocessing.py ude local --logfile logs/preprocessing-ude.log --state logs/preprocessing-ude.state.txt
```

Run with `--update` to _only_ update fields instead of indexing the whole document. This won't override existing keywords and other information.

## People Miner

**Usage**

```
python people.py -h
```

**Usage Examples**

```
python people.py rub local --logfile logs/people-rub.log
python people.py ude local --logfile logs/people-ude.log
python people.py ude,rub local --logfile logs/people-ude.log
python people.py ude,rub local --single https://s3.paluno.uni-due.de/team
python people.py ude,rub production --csv
python people.py ude,rub production --csv --logfile logs/people.log
python people.py ude,rub production --interactive
python people.py ude production --logfile logs/people-ude.log
python people.py rub production --logfile logs/people-rub.log
```

## Organization Miner

**Usage**

```
python org.py -h
```

**Usage Examples**

```
python org.py rub local
python org.py ude local
python org.py ude,rub local
python org.py ude production
python org.py rub production
python org.py ude,rub production
```

## Research Miner

```
python research.py -h
```

**Usage Examples**

```
python research.py rub remote --logfile logs/research-rub.log
python research.py ude remote --logfile logs/research-ude.log
```

**With Timestamp**

```
python research.py rub remote --logfile logs/research-rub.log --timestamp 123456
python research.py ude remote --logfile logs/research-ude.log --timestamp 123456
```

**SVM Usage**
```
python ./research/svm_main.py rub remote --logfile logs/research-svm-rub.log --timestamp 123456 --model ./research/page_classification_model.pkl
```