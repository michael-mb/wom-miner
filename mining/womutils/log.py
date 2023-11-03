"""
Logging utils, based on the python 'logging' module
"""

import logging
from logging.handlers import TimedRotatingFileHandler
import sys

def configure_logging(logfile:str, rootLevel = logging.INFO):
    """Configures Logging in the console with a unified formatter. If 'logfile' is specified, it prepares an additional rotating logfile at the passed path."""
    formatter = logging.Formatter(fmt="%(asctime)s [%(levelname)-8s] %(name)-40s : %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    # Setup root logger
    root = logging.getLogger()
    root.setLevel(rootLevel)

    # Setup console logging
    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setFormatter(formatter)
    root.addHandler(consoleHandler)

    # Setup additional rotating logfile if specified
    if logfile:
        fileHandler = TimedRotatingFileHandler(logfile, when="midnight", encoding="utf-8")
        fileHandler.setFormatter(formatter)
        root.addHandler(fileHandler)

    # Set different levels for some loggers
    logging.getLogger('elastic_transport.transport').setLevel(logging.WARNING)
    logging.getLogger('trafilatura').setLevel(logging.INFO)
