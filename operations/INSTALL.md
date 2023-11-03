# Install services

## Elasticsearch

1. Download Elasticsearch from https://www.elastic.co/de/downloads/elasticsearch and unzip it
1. Open `elasticsearch/config/elasticsearch.yml`
   - You may add a path to store all data, e.g.:
     ```
     path.data: /mnt/data/pg-wom/elastic-data
     ```
   - You may add a snapshot directory, e.g.:
     ```
     path.repo:
       - /mnt/data/pg-wom/elastic-snapshot
     ```
   - You may add a logfile path, e.g.:
     ```
     path.logs: /mnt/data/pg-wom/logs
     ```
   - You may add additional security configuration, etc.
1. Copy `elastic-pgwom.service` to `/etc/systemd/system/wom-elastic.service`
1. You may have to update the `ExecStart` command, depending on the path where Elasticsearch was unzipped.
1. The Elasticsearch service can now be managed by systemd, e.g.:
   - `systemctl start wom-elastic`
   - `systemctl stop wom-elastic`
   - `systemctl status wom-elastic`

## Kibana

1. Download Kibana from https://www.elastic.co/de/downloads/kibana and unzip it
1. Open `kibana/config/kibana.yml`
   - You may add a path to store all data, e.g.:
     ```
     path.data: /mnt/data/pg-wom/kibana-data
     ```
   - You may add information where the server is publicly available, e.g.:
     ```
     server.basePath: "/kibana"
     server.publicBaseUrl: "https://wom.handte.org/kibana"
     ```
   - You may add a logfile configuration and a path, e.g.:
     ```
     logging:
       root:
         level: info
         appenders: [rolling-file]
       appenders:
         rolling-file:
         type: rolling-file
         fileName: /mnt/data/pg-wom/logs/kibana.log
         policy:
           type: size-limit
           size: 50mb
         strategy:
           type: numeric
           pattern: '-%i'
           max: 10
         layout:
           type: pattern
     ```
   - You may disable telemetry, e.g.:
     ```
     telemetry.allowChangingOptInStatus: false
     telemetry.optIn: false
     ```
   - You may add additional security or SSL configuration, e.g.:
     ```
     server.ssl.enabled: true
     server.ssl.keystore.path: /home/pg-wom/kibana-8.8.1/config/kibana-cert.p12
     ```
1. Copy `kibana-pgwom.service` to `/etc/systemd/system/wom-kibana.service`
1. You may have to update the `ExecStart` command, depending on the path where Elasticsearch was unzipped.
1. As written above, Kibana can also be managed via systemd

## Systemd

Tell systemd to automatically start the services on boot:

```
systemctl enable wom-elastic
systemctl enable wom-kibana
```

Disable this behavior:

```
# Disable:
systemctl disable wom-elastic
systemctl disable wom-kibana
```