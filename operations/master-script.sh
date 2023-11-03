# The master script executes all miners in the intended order

# Run with the following arguments:
# $1 - The university, e.g. "ude", "rub" - corresponds to a valid config file, e.g. "rub.toml"
# $2 - The Elasticsearch configuration - corresponds to a valid config file, e.g. "elastic.local.toml"

if [[ $# -ne 2 ]] ; then
    echo 'Missing or too many arguments.'
    exit 0
fi

mkdir ~/logs
mkdir ~/data
mkdir ~/data/crawler-state-$1

##### Crawler #####

cd ../crawler
pipenv install
pipenv shell

scrapy crawl elastic -a university=$1 -a elastic=$2 -L INFO --logfile ~/logs/crawler-$1.log -s JOBDIR=~/data/crawler-state-$1

##### Miners #####

cd ../mining
pipenv install
pipenv shell

python nltk.py
python -m spacy download de_core_news_lg
python -m spacy download de_core_news_sm
python -m spacy download en_core_web_lg
python -m spacy download en_core_web_sm

##### Preprocessing #####
python preprocessing.py $1 $2 --logfile ~/logs/preprocessing-$1.log --state ~/data/preprocessing-$1.state.txt

##### Keyword Extraction on preprocessing docs #####
cd keywords
python preprocessing_keywords.py --env production --unis ude rub
cd ..

##### People Miner #####
python people.py $1 $2 --logfile ~/logs/people-$1.log

##### Organization Miner #####
python org.py $1 $2

##### Research Project Miner #####
python research.py $1 $2 --logfile ~/logs/research-$1.log
python research/svm_main.py $1 $2 --logfile ~logs/research-svm-$1.log --model ./research/page_classification_model.pkl

##### Keyword Aggregation on Entities #####
cd keywords
python entity_keywords.py --env production --unis ude rub
