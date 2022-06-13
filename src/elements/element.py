from abc import ABC, abstractmethod

from model.enums import Direction
from src.sections.section import Section

class Element(ABC):
    """
    Abstract class for element
    """

    @abstractmethod
    def __init__(self, section: Section, L: float) -> None:
        pass

    # add return type
    @abstractmethod
    def moment_rotation(self, direction: Direction, axial: float=0.):
        pass

    # add return type
    @abstractmethod
    def shear_moment_interaction(self, axial: float=0.) -> None:
        pass

    @abstractmethod
    def match(self, section: Section, L: float) -> bool:
        pass
