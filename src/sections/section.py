from abc import ABC, abstractmethod

from model.enums import Direction

class Section(ABC):
    """Abstract method for section"""
    # add return type
    @abstractmethod
    def moment_curvature(self, direcion: Direction, axial: float=0.):
        pass

    # add return type
    @abstractmethod
    def domain_MN(self):
        pass

    # add return type
    @abstractmethod
    def shear_capacity(self):
        pass
    
    @abstractmethod
    def get_height(self) -> float:
        pass

    @abstractmethod
    def get_section_data(self):
        pass
