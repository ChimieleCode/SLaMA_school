from dataclasses import dataclass
import numpy as np


@dataclass
class FrameCapacity:
    name: str
    mass: float
    disp: list[float]
    base_shear: list[float]

    def __mul__(self, other: float) -> 'FrameCapacity':
        """
        Multiplies the capacity by a scalar value.
        
        Args:
            other (float): The scalar value to multiply with.
        
        Returns:
            FrameCapacity: A new FrameCapacity instance with scaled values.
        """
        return FrameCapacity(
            name=self.name,
            mass=self.mass * other,
            disp=self.disp,
            base_shear=[bs * other for bs in self.base_shear]
        )
    
    def __add__(self, other: 'FrameCapacity') -> 'FrameCapacity':
        """
        Adds another FrameCapacity instance to this one.
        Args:
            other (FrameCapacity): The FrameCapacity instance to add.
        Returns:
            FrameCapacity: A new FrameCapacity instance with combined values.
        """
        # Get all the unique disps
        disps = sorted(
            set(d for d in (self.disp + other.disp))
            )
        
        self_bs = [np.interp(d, self.disp, self.base_shear, right=0.) for d in disps]
        other_bs = [np.interp(d, other.disp, other.base_shear, right=0.) for d in disps]

        return FrameCapacity(
            name=f"{self.name} + {other.name}",
            mass=self.mass + other.mass,
            disp=disps,
            base_shear=[s + o for s, o in zip(self_bs, other_bs)]
        )
