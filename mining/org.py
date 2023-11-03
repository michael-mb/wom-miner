from org.org_miner import org_miner
import argparse
from womutils.elastic import configure_elastic_from_config, es_client

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('universities', help='The universities e.g. "rub" (comma-separated). Used to identify the indices.')
    parser.add_argument('elastic', help='The elastic instance configuration e.g. "local".')
    args = parser.parse_args()

    configure_elastic_from_config(args.elastic)
    es = es_client()

    for university in args.universities.split(','):
        print(f"Starting {university}.")
        uni_index_name = "crawl-rawdata-" + university
        org_miner(rawdata_index_name=uni_index_name, es=es)