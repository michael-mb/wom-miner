"""
Methods for working with configuration files
"""

from pathlib import Path
import tomllib

def read_config(name:str) -> dict[str, object]:
    """Returns the content of the config file with the given name (only the name without file extension)"""
    path = get_config_path(name)
    if not path.is_file():
        raise FileNotFoundError("No configuration file found: " + str(path))
    with open(path, mode="rb") as f:
        config = tomllib.load(f)
    return config

def config_exists(name:str) -> bool:
    """Returns wether the given config file exists"""
    return get_config_path(name).is_file()
    
def ensure_config_exists(name:str) -> None:
    """Raises a FileNotFoundError if the passed config name does not exist"""
    path = get_config_path(name)
    if not path.is_file():
        raise FileNotFoundError("No configuration file found: " + str(path))

def get_config_path(name:str = None) -> Path:
    """Returns the path to a specific config name (if a name was specified) or the path to the config folder"""
    this_path = Path(__file__).parent         # Path of "config.py" ("womutils" folder)
    config_path = this_path / '../../config'  # Path where the config files are
    if name:
        return (config_path / f"{name}.toml").resolve() # The '/' operator works as intended for pathlib.Path objects
    else:
        return config_path.resolve()