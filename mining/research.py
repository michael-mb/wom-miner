import argparse
from research.main import start
from womutils.log import configure_logging
from womutils.config import ensure_config_exists, read_config
from womutils.elastic import configure_elastic_from_config

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('university', help='The university e.g. "rub". Used to identify the indices.')
    parser.add_argument('elastic', help='The elastic instance configuration e.g. "local".')
    parser.add_argument('--logfile', help='Path to a logfile (optional)')
    parser.add_argument('--timestamp', help='last timestamp to continue the execution (optional)')
    args = parser.parse_args()

    # Configure logging, university and elastic
    configure_logging(args.logfile)
    ensure_config_exists(args.university) # If university config does not exist, there is no chance that this will work
    configure_elastic_from_config(args.elastic)

    # Using preprocessing config for reading batch_size
    cfg = read_config("preprocessing")

    # Start work
    start(cfg['batch_size'], args.university, args.timestamp)
