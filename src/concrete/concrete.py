# from abc import ABC, abstractmethod

# class Concrete(ABC):
#     """Abstract concrete class"""

from dataclasses import dataclass

@dataclass
class Concrete:
    id          : str
    fc          : float
    E           : float
    epsilon_0   : float
    epsilon_u   : float



        