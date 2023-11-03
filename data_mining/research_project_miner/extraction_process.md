# Research Project Miner 

This document defines the process of extracting data from one or more html documents. 

TODO: Define what we should extract from the pages (text, title, list etc) ... anything that might be important for mining. This will be used to define exactly what we need for the preprocessing stage 

Goal: 
- Our task is to find out the name of the research project. For example: "Language Engineering for Multilevel Modelling" 
- Then link this with the persons and institutes such as: "Prof. Dr. Ulrich Frank" and "Chair of Information Systems and Enterprise Modelling".
- In addition, we would then have to do Text Summarization or Key Word Extraction, if possible, to determine the goal of the research project.

## I - What do we need and what do we need to do 

1. Exclude pages that are not about research and projects: 
SOLUTION: Keyword matching: Create a list of keywords to search in each document according to the language

What we need: 
- Page language
- Extracted TEXT from HTML 
- URL Analysis (naming conventions ?
  - https://sse.uni-due.de/research-funding
  - https://sse.uni-due.de/forschung/projekte/dynabic
  - https://sse.uni-due.de/forschung/projekte/ml4sas
- Natural Language Processing (NLP)

TODO:
- id ok
- last_update (time) ok
- url(Original-Webseite als klickbare Link wird angezeigt) ok
- summarization ok
- personnen ok

- Type (universität, Fakultäten, Institute, Lehrstühle, Personen, Forschungsprojekte) -- Dennis

place (Ort als Physischer Standort der Entität wird angezeigt) -- ignore first
higher_level_units(Direkt übergeordnete Einheiten werden als klickbare Links angezeigt) -- ignore first
subordinate units(Direkt nachgeordnete Einheiten werden als klickbare Links angezeigt) -- ignore first


english_keywords = [
    "project",
    "research",
    "area",
    "interest",
    "initiative",
    "activities",
    "Academic",
    "collaboration",
    "publication",
    "institute",
    "lab",
    "investigator",
    "supervisor",
    "methodology",
    "outcomes",
    "finding",
    "objective",
    "goal",
    "report",
    "seminar",
    "presentation",
    "methodolog",
    "experiment",
    "analysis",
    "results",
    "publication",
    "journal",
    "conference",
    "symposiums",
    "workshops",
    "presentations",
    "posters",
    "abstract",
    "committee",
    "dissemination",
    "evaluation",
    "innovation",
    "breakthrough",
    "challenge"
]

german_keywords = [
    "projekt",
    "forschung"
    "gebiete",
    "interessen",
    "initiativen",
    "schwerpunkt",
    "aktivitäten",
    "wissenschaft",
    "kooperationen",
    "teams",
    "publikationen",
    "förderung",
    "institute",
    "leiter",
    "dozenten",
    "ergebnisse",
    "ziele",
    "impact",
    "bewertung",
    "exzellenz",
    "bericht",
    "konferenz",
    "symposien",
    "vorträge",
    "methoden",
    "resultat",
    "fragen",
    "experiment",
    "analyse",
    "förderungsmöglichkeit",
    "zeitschrift",
    "werkstätten",
    "evaluation",
    "innovation",
    "herausforderung"
]

Notes: 
- We could create a score system that determines if the site actually talks about the theme and based on that we can choose to extract or not the data from this page in question
- Save the result of this process as a metadata of the page in elastic (to avoid repeating it every time)

2. Name of Research Projects & Professors & Institute:

What we need:
- Extracted TEXT from HTML 

Notes:
- Use natural language processing (NLP) techniques to identify the project names from the collected information.
- Apply methods like named entity recognition (NER) or pattern matching to extract the project names accurately.
- Extract the names of people and institutes associated with each research project.
- Use NLP techniques to link the extracted names with their respective projects.
- This can be achieved through entity linking or by establishing relationships based on the context of the project descriptions.

3. Text Summary & Keyword Extraction:

What we need:
- Extracted TEXT from HTML
Apply text summarization techniques to generate a brief summary of the research project.


4. At The End: 

```
{
  "research_projects": [
    {
      "name": "Language Engineering for Multilevel Modelling",
      "language": "de",
      "id": "0001",
      "related_projects": [ ],
      "related_nodes": [ ],
      "people": [
        {
          "name": "Ulrich Frank" // Entity ID ? 
        },
        {
          "name": "Dr. Franz Wagner" // Entity ID ? 
        }
      ],
      "institutes": [
        {
          "name": "Chair of Information Systems and Business Modeling"
        }
      ],
      "summary": "A research project focused on language engineering techniques for multilevel modeling.",
      "keywords": ["language engineering", "multilevel modeling", "research"],
      "origin": "https://www.wi-inf.uni-duisburg-essen.de/LE4MM/", 
      "links": ["https://www.wi-inf.uni-duisburg-essen.de/LE4MM/",
              "https://www.wi-inf.uni-duisburg-essen.de/LE4MM/prospects"],
    }
  ]
}
```


## Merkmale einer Projektseite 

## II- Preprocessing 

After crawling the HTML code, the preprocessing stage involves extracting relevant information from the crawled data. Here are some steps you can take:

1. HTML Parsing
- Parse the HTML code to extract the relevant elements such as project names, descriptions, people, institutes, and other related information. (with keywords first)
- libraries like BeautifulSoup for efficient HTML parsing.

2. Text Extraction and Cleaning
- Extract the textual content from the parsed HTML, excluding any irrelevant elements like scripts, stylesheets, or navigation menus.
- Clean the extracted text by removing HTML tags, special characters, and unnecessary whitespace.

Beforehand, it's beneficial to ensure that you have or perform the following NLP tasks:

Tokenization: Break down the extracted text into individual tokens (words, punctuation, etc.) for further processing.
Stopword Removal: Eliminate common words (e.g., "a," "the," "is") that don't contribute much to the meaning of the text.
Lemmatization or Stemming: Reduce words to their base or root form to handle variations (e.g., "running" to "run," "institutes" to "institute").
These NLP preprocessing steps help in cleaning and structuring the text data, enabling effective entity recognition, summarization, and keyword extraction.

(Summarization Paper)

3. Named Entity Recognition (NER)
- Apply NER techniques to identify and extract named entities such as person names, institute names, and project names from the cleaned text.
- Pretrained NER models from libraries like spaCy or GPT can help with entity recognition.

4. Entity Linking
??? - how can we do this 

5. Text Summarization 

6. Keyword Extraction