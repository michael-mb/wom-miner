# WOM Operations Guide

## Required Software

- [Elasticsearch](https://www.elastic.co/en/downloads/elasticsearch)
- [Kibana](https://www.elastic.co/de/downloads/kibana) (optional for managing the Elastic Stack)
- For running the Crawler, Preprocessing and Data Mining Modules:
    - [Python](https://www.python.org/downloads/) (developed with 3.11, but newer versions should be fine)
    - [Pipenv](https://pipenv.pypa.io/en/latest/)
- For the Frontend:
    - [Node.js](https://nodejs.org/download) for build (not required on a server, can also be built locally)
    - A webserver

## Install services

See [INSTALL.md](INSTALL.md) for installing the required Elasticsearch (mandatory) and Kibana (optional) services via systemd on a Linux machine.

Depending on the Elasticsearch configuration, add a new file `config/elastic.production.toml` with the following content (replace the values):

```
instance = "https://localhost:9200"
username = "ElasticsearchUsername"
password = "PasswordOfTheElasticSearchUser"
disable_security = true
```

# Run Python Scripts

```
sudo chmod +x ./master-script.sh
./master-script.sh ude production
./master-script.sh rub production
```

# Build frontend

Depending on the Elasticsearch instance location, you have to change the URLs in `vite.config.js` (only for Development) and `src/config/config.js`. Depending on the Webserver location, you have to adjust the `base` path in `vite.config.js`.

```
cd ../frontend/wom-miner-frontend
npm install
npm run build
```

The resulting `dist` folder can then be deployed on a webserver.
