# Instructions: Activate conda environment and call "python elastic-connection-test.py"

from elasticsearch import Elasticsearch
from pathlib import Path
import tomllib

if __name__ == "__main__":
    with open(Path(f"../config/elastic.local.toml"), "rb") as f:
        config = tomllib.load(f)

    disable_security = config.get('disable_security', False)
    client = Elasticsearch(
        config['instance'],
        basic_auth=(config['username'], config['password']),
        verify_certs=not disable_security,
        ssl_show_warn=not disable_security
    )

    if not client:
        raise RuntimeError("Could not configure Elasticsearch instance")
    if not client.ping():
        raise RuntimeError("Elasticsearch instance not available")
    print(client.info())