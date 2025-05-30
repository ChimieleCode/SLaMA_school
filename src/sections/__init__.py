from abc import ABC, abstractmethod
from typing import List
from dataclasses import dataclass

from model.enums import Direction, SectionType
from src.steel.steel import Steel
from src.concrete.concrete import Concrete


@dataclass
class MomentCurvature:
    mom_y: float    # yielding moment
    mom_c: float    # capacity moment
    phi_y: float    # yielding curvature
    phi_c: float    # capacity curvature


@dataclass
class ShearEnvelope:
    cap_undamaged: float    # capacity undamaged
    cap_residual: float     # capacity residual
    duc_undamaged: float    # ductility undamaged
    duc_residual: float     # ductility residual


@dataclass
class MNDomain:
    moment: List[float]
    axial: List[float]


class Section(ABC):
    """
    Abstract class for section
    """
    @abstractmethod
    def moment_curvature(self, direction: Direction, axial: float=0.) -> MomentCurvature:
        pass

    @abstractmethod
    def domain_MN(self, axial: float) -> float:
        pass

    @abstractmethod
    def shear_capacity(self, L: float, axial: float = 0.) -> ShearEnvelope:
        pass

    @abstractmethod
    def plastic_hinge_length(self, L: float) -> float:
        pass

    @abstractmethod
    def get_height(self) -> float:
        pass

    @abstractmethod
    def get_effective_width(self) -> float:
        pass

    @abstractmethod
    def get_section_data(self) -> object:
        pass

    @abstractmethod
    def get_concrete(self) -> Concrete:
        pass

    @abstractmethod
    def get_steel(self) -> Steel:
        pass

    @abstractmethod
    def get_section_type(self) -> SectionType:
        pass

    @abstractmethod
    def get_depth(self) -> float:
        pass
