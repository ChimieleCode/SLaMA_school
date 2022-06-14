import json
from pathlib import Path
from typing import List, Tuple
import numpy as np
from scipy.interpolate import interp1d

def import_from_json(filepath: Path) -> dict:
    """
    Imports a .json file and converts it into a dictionary
    """
    with open(filepath, 'r') as jsonfile:
        return json.loads(jsonfile.read())

def export_to_json(filepath: Path, data: dict) -> None:
    """
    Exports a given dict into a json file
    """
    with open(filepath, 'w') as jsonfile:
        json.dump(data, jsonfile, ensure_ascii=False, indent=4)
    

def intersection (x1: List[float], y1: List[float], x2: List[float], y2: List[float]) -> Tuple[float]:
    """
    Finds the intersections of two discretized curves
    """

    function_1 = interp1d(x1, y1, kind='linear')
    function_2 = interp1d(x2, y2, kind='linear')

    x_domain = np.linspace(max(x1[0], x2[0]), min(x1[-1], x2[-1]))

    y1_interpolation = function_1(x_domain)
    y2_interpolation = function_2(x_domain)

    indexes = np.argwhere(np.diff(np.sign(y1_interpolation - y2_interpolation))).flatten()

    intersections = {
        'x' : tuple(x_domain[indexes]), 
        'y' : tuple(y1_interpolation[indexes])
    }

    return intersections

