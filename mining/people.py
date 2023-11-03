import argparse
from people.main import start, start_single
from womutils.log import configure_logging
from womutils.config import ensure_config_exists, read_config
from womutils.elastic import configure_elastic_from_config
import logging
import sys

log = logging.getLogger(__name__)

def goto_interactive_mode(universities):
    """Starts an interactive shell where to place the URL and get the output immediately"""
    url = ""
    while url != "exit":
        print("Enter a URL or type 'exit' . . .")
        url = input().strip()
        if url and (url.startswith("http://") or url.startswith("https://")):
            for university in universities.split(','):
                try:
                    start_single(url, university)
                except BaseException:
                    log.exception("Error.")
        print("--------------------------------------------------------------------------------------------------------------------")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # Note that we cannot use argparse's 'nargs' feature because 'universities' is a positional argument
    parser.add_argument('universities', help='The universities e.g. "rub" (comma-separated). Used to identify the indices.')
    parser.add_argument('elastic', help='The elastic instance configuration e.g. "local".')
    parser.add_argument('--logfile', help='Path to a logfile (optional)')
    parser.add_argument('--single', help='Process a single URL')
    parser.add_argument('--interactive', help='Start an interactive shell', action='store_true')
    parser.add_argument('--csv', help='Only save the people in a CSV file instead of an Elasticsearch index', action='store_true')
    args = parser.parse_args()

    # Configure logging, universities and elastic
    if args.single or args.interactive:
        configure_logging(args.logfile, rootLevel=logging.DEBUG)
    else:
        configure_logging(args.logfile)

    for university in args.universities.split(','):
        ensure_config_exists(university) # If university config does not exist, there is no chance that this will work
    configure_elastic_from_config(args.elastic)

    # Using preprocessing config for reading batch_size
    cfg = read_config("preprocessing")

    if args.interactive:
        goto_interactive_mode(args.universities)
        print("Finished.")
        sys.exit(0)

    # Start work
    for university in args.universities.split(','):
        if args.single:
            start_single(args.single, university)
        else:
            start(cfg['batch_size'], university, args.csv)
