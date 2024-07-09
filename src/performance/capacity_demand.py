import math
from scipy.interpolate import interp1d

from src.hazard import SeismicHazard
from model.data_models import FrameCapacity

# Usefull constants
G = 9.81

def compute_ISV(capacity: FrameCapacity, hazard: SeismicHazard) -> float:
    """
    Compute the IS-V (analog of %NBS) for a given capacity curve and seismic demand
    """
    acc_capacity = capacity.base_shear[-1] / capacity.mass / G
    effective_period = math.sqrt(capacity.disp[-1] / acc_capacity * 4 * math.pi**2 / G) 
    damping = get_damping(capacity.disp[-1] / capacity.disp[0])
    return acc_capacity / hazard.get_spectral_acceleration(effective_period, damping)


def compute_ISD(capacity: FrameCapacity, hazard: SeismicHazard) -> float:
    """
    Compute the IS-D (analog of %NBS at damage state) for a given capacity curve and seismic demand
    """
    acc_capacity = capacity.base_shear[0] / capacity.mass / G
    effective_period = math.sqrt(capacity.disp[0] / acc_capacity * 4 * math.pi**2 / G) 
    return acc_capacity / hazard.get_spectral_acceleration(effective_period)


def get_damping(ductility: float) -> float:
    """
    Computes damping according to C2 NZSEE
    """
    base_damping = 0.05
    damping_values = (
        0,
        2,
        6,
        8,
        10
    )
    ductility_values = (
        1,
        1.25,
        2,
        3,
        6
    )
    if ductility <= 1:
        return base_damping

    if ductility >= 6:
        return base_damping + 0.01 * max(damping_values)

    interpolator = interp1d(
        ductility_values,
        damping_values,
        assume_sorted=True
    )
    return base_damping + 0.01 * interpolator._evaluate([ductility])[0]
