from abc import ABC, abstractmethod

from model.enums import Direction
from src.sections import Section

class Element(ABC):
    """
    Abstract class for element
    """

    @abstractmethod
    def __init__(self, section: Section, L: float) -> None:
        pass

    @abstractmethod
    def moment_rotation(self, direction: Direction, axial: float=0., consider_shear_iteraction: bool=True) -> dict:
        pass

    @abstractmethod
    def match(self, section: Section, L: float) -> bool:
        pass

    @abstractmethod
    def get_element_lenght(self) -> float:
        pass

    @abstractmethod
    def get_section(self) -> Section:
        pass
