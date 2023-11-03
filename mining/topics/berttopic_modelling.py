from elasticsearch import Elasticsearch
from bertopic import BERTopic
import pandas as pd


es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
index_name = 'research_prject-ude'
query = {
    'query': {
        'match_all': {}
    }
}
res = es.search(index=index_name, body=query, size=10000)
docs = pd.DataFrame([doc['_source'] for doc in res['hits']['hits']])
documents = docs['content'].tolist() 
topic_model = BERTopic(language="english")
topics, _ = topic_model.fit_transform(documents)
print(topics)
