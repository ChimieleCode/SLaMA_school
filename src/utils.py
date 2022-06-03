import json
from pathlib import Path

def import_from_json(filepath: Path | str) -> dict:
    """Imports a .json file and converts it into a dictionary"""
    with open(filepath, 'r') as jsonfile:
        return json.loads(jsonfile.read())

def export_to_json(filepath: Path | str, data: dict) -> None:
    """Exports a given dict into a json file"""
    with open(filepath, 'w') as jsonfile:
        json.dump(data, jsonfile, ensure_ascii=False, indent=4)
    
