from dataclasses import dataclass

@dataclass
class FrameCapacity:
    name: str
    mass: float
    disp: list[float]
    base_shear: list[float]
