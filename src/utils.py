import json
from pyparsing import Any
import yaml
from pathlib import Path
from typing import Callable, List, Sequence, Tuple
import numpy as np
from scipy.interpolate import interp1d
from scipy.optimize import fsolve


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

def import_configuration(config_path: Path, object_hook = None) -> Any:
    """
    Imports the config file and returns a dictionary if object_hook is not specified

    Args:
        config_path (Path): config.yaml Path
        object_hook (object, optional): Dataclass structure for config information. Defaults to None.

    Returns:
        Any: config dictionary. If object hook is defined, will return an object_hook.__class__ instance
    """
    with open(config_path) as yamlfile:
        config_dct = yaml.safe_load(yamlfile)

    if object_hook is not None:
        return object_hook(
            **config_dct
        )
    return config_dct

def analytical_intersection(
    initial_guess: float,
    function_1: Callable[[float], float],
    function_2: Callable[[float], float]) -> float:
    """
    Finds the closest intersection between two curves
    """
    difference_function = lambda x: function_1(x) - function_2(x)
    return fsolve(difference_function, initial_guess)[0]

def intersection(x1: Sequence[float], y1: Sequence[float], x2: Sequence[float], y2: Sequence[float]) -> Tuple[float, float] | None:
    """
    Finds the intersections of two discretized curves
    """
    function_1 = interp1d(x1, y1, kind='linear')
    function_2 = interp1d(x2, y2, kind='linear')

    x_domain = np.linspace(max(x1[0], x2[0]), min(x1[-1], x2[-1]))

    y1_interpolation = function_1(x_domain)
    y2_interpolation = function_2(x_domain)

    indexes = np.argwhere(np.diff(np.sign(y1_interpolation - y2_interpolation))).flatten()

    if indexes.size == 0:
        return None

    index = indexes[0]

    inv_linear_matrix = np.linalg.inv(
        [
            [1, x_domain[index]],
            [1, x_domain[index + 1]]
        ]
    )
    func_1_line = np.matmul(
        inv_linear_matrix,
        [y1_interpolation[index], y1_interpolation[index + 1]]
    )
    func_2_line = np.matmul(
        inv_linear_matrix,
        [y2_interpolation[index], y2_interpolation[index + 1]]
    )
    intersection_coordinates = np.matmul(
        np.linalg.inv(
            [
                [func_1_line[1], -1],
                [func_2_line[1], -1]
            ]
        ),
        [-func_1_line[0], -func_2_line[0]]
    )

    return intersection_coordinates[0], intersection_coordinates[1]
