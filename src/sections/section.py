from abc import ABC, abstractmethod
from typing import List

from model.enums import Direction

class Section(ABC):
    """
    Abstract class for section
    """
    @abstractmethod
    def moment_curvature(self, direction: Direction, axial: float=0.) -> dict:
        pass

    @abstractmethod
    def domain_MN(self, axial: List[float]) -> List[float]:
        pass

    @abstractmethod
    def shear_capacity(self, L: float, axial: float = 0.) -> dict:
        pass

    @abstractmethod
    def plastic_hinge_length(self, L: float) -> float:
        pass
    
    @abstractmethod
    def get_height(self) -> float:
        pass

    @abstractmethod
    def get_section_data(self):
        pass

    @abstractmethod
    def get_concrete(self):
        pass

    @abstractmethod
    def get_steel(self):
        pass
