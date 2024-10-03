from abc import ABC, abstractmethod
from dataclasses import dataclass

from model.enums import Direction, FailureType
from src.sections import Section


@dataclass
class MomentRotation:
    mom_y: float    # yielding moment
    mom_c: float    # capacity moment
    rot_y: float    # yielding rotation
    rot_c: float    # capacity rotation
    failure: FailureType


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
