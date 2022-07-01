from abc import ABC, abstractmethod
from typing import List

class SeismicHazard(ABC):

    @abstractmethod
    def get_spectral_acceleration(self, period: float, damping: float = .05, scale_factor: float = 1.) -> float:
        pass

    @abstractmethod
    def get_spectral_displacement(self, period: float, damping: float = .05, scale_factor: float = 1.) -> float:
        pass

    @abstractmethod
    def periods_array(self, max_period: float = 4., npoints: int = 20) -> List[float]:
        pass