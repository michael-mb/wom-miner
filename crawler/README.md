# Crawler

This project contains the crawler to crawl homepages of universities.

## Requirements & Setup

- Python 3.11
- [Scrapy 2.8.0](https://docs.scrapy.org/en/2.8/)
- [Python Elasticsearch Client 8.7.0](https://elasticsearch-py.readthedocs.io/en/v8.7.0/)

### Conda

Import environment:
```
conda env create -f environment.yml
conda activate pgwom-crawler
```

Export environment:
```
conda env export --from-history > environment.yml
```

You may also setup the project using Conda manually:

```
conda create --name pgwom-crawler python=3.11 scrapy=2.8.0 elasticsearch=8.7.0
conda activate pgwom-crawler
```

### Pipenv

Create environment:
```
pipenv install
pipenv shell
```

## How to use

Run `scrapy crawl filesystem -a university=u` where `u` refers to a valid TOML file in the `config` folder. Example:

```
scrapy crawl filesystem -a university=ude
scrapy crawl filesystem -a university=ude -L INFO                               # with logging level
scrapy crawl filesystem -a university=ude -L INFO --logfile logs/current.txt    # with log file
```

### Config

You can create many config files in the `../config/*.toml` directory. See the [TOML Specification](https://toml.io/en/v1.0.0) and the `ude.toml` example file. Supported keys:

- `entrypoint`: Where crawling starts
- `domains`: Which domains are visited
- `deny-urls` or `allow-urls`: A blocklist (or allowlist) with regexes that are tested on the visited URLs.

### State management

Refer to the official [Scrapy Guide](https://docs.scrapy.org/en/latest/topics/jobs.html) for pausing and resuming crawls. Examples:

```
scrapy crawl filesystem -a university=ude -L INFO --logfile logs/current-ude-filesystem.txt -s JOBDIR=crawled_content/_ude-local
scrapy crawl filesystem -a university=rub -L INFO --logfile logs/current-rub-filesystem.txt -s JOBDIR=crawled_content/_rub-local
```

### Elasticsearch

The crawler `elastic` expects a parameter that points to a `../config/elastic.<name>.toml` file. Examples for running the crawler and saving in Elastic:

```
scrapy crawl elastic -a university=ude -a elastic=local -L INFO --logfile logs/current-ude-elastic.txt -s JOBDIR=crawled_content/_ude-elastic
scrapy crawl elastic -a university=rub -a elastic=local -L INFO --logfile logs/current-rub-elastic.txt -s JOBDIR=crawled_content/_rub-elastic
```

### Change config files

You can edit the config files during a crawl. A use case is adding URL exclusions after the fact. Changes in `deny-urls` or `allow-urls` will be respected when launching the spider again.  However, a pause and resume (see above) is required. A change is _not_ detected if you just change the config and don't pause/resume the crawler.

### Scrapy config (maximum depth etc)

The following settings were set:

- Depth limit: 1000 - This stops the crawler at a maximum depth. The reason are dynamically generated URLs, with which the crawler would get stuck.
- Depth priority: 2 - Instead of a default depth search, a width search is performed.
- User Agent
- Obey robots.txt
- Download delay: 5 seconds - This limit has worked well at RUB and UDE. Smaller values have led to the rejection of requests.
- Randomize download delay: False - We don't have to hide the fact that we are a bot.
- Cookies enabled: False - We don't need any authentication or something else

Refer to [settings.py](crawler/settings.py) for further information how to manage the settings.
