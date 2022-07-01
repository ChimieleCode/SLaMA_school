from dataclasses import dataclass

@dataclass(frozen=True)
class Capacity:
    """
    Dataclass containing the capacity data
    """
    base_shear   : float
    acc_capacity : float
    yielding     : float
    ultimate     : float
    name         : str

    
