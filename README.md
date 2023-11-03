# Web Organization Mining

## Directories

- [**Config**](config): Config files that can be used across all modules.
- [**Data Mining**](data_mining): Concepts and Code for Data Mining
- [**Sandbox**](sandbox): Playground for experiments
- [**Operations**](operations): Scripts and instruction for running the system

## Modules

- [**Crawler**](crawler) - Crawls homepages of universities and saves them to an Elasticsearch index.
- [**Mining**](mining) - NLP processing
  - [**Keyword Extraction**](mining/keywords) - Keywords
  - [**Org Miner**](mining/org) - Organization structure, faculties, institutes and chairs
  - [**People Miner**](mining/people) - Information about people
  - [**Preprocessing**](mining/preprocessing) - Preprocessing of crawled documents
  - [**Research Project Miner**](mining/research) - Research projects
  - [**Topic Miner**](mining/topics) - Research topics
- [**Frontend**](frontend/wom-miner-frontend) - Vue.js Frontend