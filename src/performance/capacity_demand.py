import math
from model.global_constants import PI, G
from src.hazard import SeismicHazard
from src.capacity import Capacity

def compute_ISV(capacity: Capacity, hazard: SeismicHazard) -> float:
    """
    Compute the IS-V (analog of %NBS) for a given capacity curve and seismic demand
    """
    effective_period = math.sqrt(capacity.ultimate / capacity.acc_capacity * 4 * PI**2/G) 
    damping = 0.1 # to be changed with ductile relationship
    return capacity.acc_capacity/hazard.get_spectral_acceleration(effective_period, damping)

def compute_ISD(capacity: Capacity, hazard: SeismicHazard) -> float:
    """
    Compute the IS-D (analog of %NBS at damage state) for a given capacity curve and seismic demand
    """
    effective_period = math.sqrt(capacity.yielding / capacity.acc_capacity * 4 * PI**2/G) 
    return capacity.acc_capacity/hazard.get_spectral_acceleration(effective_period)
