import os
import gensim
from gensim import corpora
from gensim.models import LdaModel

class TopicModel:
    def __init__(self, num_topics=10, passes=10):
        self.num_topics = num_topics
        self.passes = passes
        self.dictionary = None
        self.model = None

    def train(self, documents):
        self.dictionary = corpora.Dictionary(documents)
        corpus = [self.dictionary.doc2bow(doc) for doc in documents]
        self.model = LdaModel(corpus, num_topics=self.num_topics, passes=self.passes, id2word=self.dictionary)

    def predict(self, document):
        if self.model is None or self.dictionary is None:
            raise ValueError("Model has not been trained or loaded. Please train or load the model first.")
        bow = self.dictionary.doc2bow(document)
        topics = self.model.get_document_topics(bow)
        topics = sorted(topics, key=lambda x: x[1], reverse=True)
        top_topic = topics[0][0]
        top_words = self.model.show_topic(top_topic)
        words = [word for word, _ in top_words]
        return top_topic, words

    def save_model(self, filename):
        model_path = os.path.join("data-mining", "topic_keyword_miner", "topic_models", filename)
        self.model.save(model_path)

    def load_model(self, filename):
        model_path = os.path.join("data-mining", "topic_keyword_miner", "topic_models", filename)
        self.model = LdaModel.load(model_path)
        self.dictionary = self.model.id2word

documents = [
    ['biology', 'dna', 'genes', 'organisms', 'evolution', 'cell', 'protein', 'species', 'ecology', 'microbiology', 'genetics', 'bioinformatics', 'anatomy', 'biotechnology', 'immunology'],
    ['computer', 'programming', 'code', 'software', 'algorithm', 'data', 'machine_learning', 'artificial_intelligence', 'networks', 'database', 'cybersecurity', 'cloud_computing', 'data_structures', 'operating_systems', 'robotics'],
    ['physics', 'particles', 'energy', 'quantum', 'relativity', 'forces', 'fields', 'atoms', 'nuclear', 'thermodynamics', 'astronomy', 'cosmology', 'electromagnetism', 'optics', 'plasma'],
    ['psychology', 'behavior', 'cognition', 'emotions', 'neuroscience', 'mental_health', 'personality', 'development', 'social', 'psychotherapy', 'child_psychology', 'cognitive_science', 'clinical_psychology', 'psychometrics', 'biopsychology'],
    ['history', 'culture', 'society', 'politics', 'revolution', 'ancient', 'war', 'civilization', 'empire', 'historiography', 'renaissance', 'medieval', 'diplomacy', 'colonialism', 'archaeology'],
    ['chemistry', 'organic', 'inorganic', 'physical', 'biochemistry', 'chemical_bonds', 'reactions', 'analytical', 'molecules', 'compounds', 'spectroscopy', 'chemical_kinetics', 'thermochemistry', 'quantum_chemistry', 'polymer'],
    ['mathematics', 'algebra', 'geometry', 'calculus', 'statistics', 'probability', 'differential_equations', 'linear_algebra', 'combinatorics', 'number_theory', 'topology', 'discrete_mathematics', 'numerical_analysis', 'mathematical_logic', 'complex_analysis'],
    ['arts', 'painting', 'sculpture', 'theatre', 'music', 'dance', 'literature', 'architecture', 'cinema', 'photography', 'printmaking', 'design', 'digital_art', 'performance_art', 'art_history'],
    ['engineering', 'mechanical', 'civil', 'electrical', 'materials', 'chemical', 'biomedical', 'aerospace', 'computer_engineering', 'structural', 'software_engineering', 'nanotechnology', 'energy_engineering', 'environmental_engineering', 'industrial_engineering'],
    ['economics', 'microeconomics', 'macroeconomics', 'economic_policy', 'finance', 'game_theory', 'international_economics', 'labor_economics', 'economic_history', 'behavioral_economics', 'development_economics', 'health_economics', 'monetary_economics', 'econometrics', 'public_economics'],
    ['philosophy', 'ethics', 'epistemology', 'metaphysics', 'logic', 'philosophy_of_science', 'political_philosophy', 'philosophy_of_mind', 'aesthetics', 'existentialism', 'continental_philosophy', 'ancient_philosophy', 'philosophy_of_language', 'philosophy_of_law', 'philosophy_of_religion'],
    ['linguistics', 'syntax', 'semantics', 'phonetics', 'phonology', 'sociolinguistics', 'psycholinguistics', 'pragmatics', 'linguistic_anthropology', 'neurolinguistics', 'morphology', 'computational_linguistics', 'historical_linguistics', 'discourse_analysis', 'syntax'],
    ['environmental_science', 'ecology', 'climate_change', 'conservation', 'sustainability', 'pollution', 'biodiversity', 'natural_resources', 'environmental_policy', 'earth_science', 'geography', 'marine_science', 'environmental_health', 'waste_management', 'forest_ecology']
]

if __name__ == '__main__':  
    model = TopicModel(num_topics=5, passes=10)
    model.train(documents)
    model.save_model('topic_model.lda')
    loaded_model = TopicModel()
    loaded_model.load_model('topic_model.lda')
    new_document = ['programming', 'computer', 'algorithm', 'data']
    topic, words = loaded_model.predict(new_document)
    print(f"The new document belongs to topic {topic}")
    print(f"Related words in the topic: {', '.join(words)}")
