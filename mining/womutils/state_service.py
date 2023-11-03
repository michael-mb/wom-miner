"""
Can be used to track the current state while processing many Elasticsearch documents, e.g. a timestamp.
"""

import os
from pathlib import Path
import logging

log = logging.getLogger(__name__)
file:Path

def configure(state_file:str):
    """Configures the State Service to write to a file. It is safe to pass 'None'"""
    global file
    if state_file:
        file = Path(state_file)
        log.info("State configured with file: " + str(file.resolve()))
    else:
        log.info("No state configured.")
        file = None

def write(state):
    """Writes the passed state to the file."""
    if not file:
        return None
    
    try:
        with open(file, 'w') as f:
            f.write(str(state))
    except Exception as e:
        log.exception(f"Could not write back state '" + str(state) + "' to file: " + str(file.resolve()))

def clear():
    """Deletes the state file, if exists"""
    if os.path.exists(file):
        log.info("State deleted.")
        os.remove(file)

def read():
    """Reads the state from the pre-configured file. Returns None if the file is not present or the state is not configured."""
    if not file:
        return None

    if os.path.exists(file):
        # Read state from existing file
        with open(file, 'r') as f:
            state = f.read().strip()
        log.info("State read: " + state)
        return state
    else:
        # If the file is not present, it is created, but otherwise left empty
        with open(file, 'w') as f:
            pass
        log.info("No state avialable.")
        return None 