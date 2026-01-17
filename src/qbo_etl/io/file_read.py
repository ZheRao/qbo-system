from importlib.resources import files
import json

def read_configs(config_type:str, name:str) -> dict:
    """
    Reads and return configurations stored in json_configs/config_type/name, e.g., json_configs/io/path.win.json
    """
    p = files("qbo_etl.json_configs").joinpath(f"{config_type}/{name}")
    return json.loads(p.read_text())