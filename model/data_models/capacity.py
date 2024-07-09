from dataclasses import dataclass

@dataclass
class FrameCapacity:
    name: str
    mass: int
    disp: list[float]
    base_shear: list[float]
