from pydantic import BaseModel

from model.validation.material_validation import SimpleMaterialInput
from model.validation.section_model import BasicSectionCollectionInput
from model.validation.frame_input import Regular2DFrameInput


class FrameGrid(BaseModel):
    """
    Validator data model for frame grid
    """
    main_frames: list[tuple[Regular2DFrameInput, int]]
    cross_frames: list[tuple[Regular2DFrameInput, int]]


class MultiFrameIput(BaseModel):
    """
    Validator data model for multi-frame input
    """
    tag: str
    materials: SimpleMaterialInput
    sections: BasicSectionCollectionInput
    frames: FrameGrid
    masses: list[float]


    class Config:
        frozen = True
