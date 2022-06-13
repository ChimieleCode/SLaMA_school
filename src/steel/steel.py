# from abc import ABC, abstractmethod

# class Steel(ABC):
#     """Abstract steel class"""

from dataclasses import dataclass
from functools import cache

@dataclass(frozen=True)
class Steel:
    id          : str
    fy          : float
    fu          : float
    E           : float
    epsilon_u   : float

    @property
    @cache
    def epsilon_y(self) -> float:
        return self.fy / self.E

