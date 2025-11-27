from pydantic import BaseModel

from model.validation.frame_input import Regular2DFrameInput
from model.validation.material_validation import SimpleMaterialInput
from model.validation.section_model import BasicSectionCollectionInput


class FrameGrid(BaseModel):
    """
    Validator data model for frame grid
    """
    main_frames: list[tuple[Regular2DFrameInput, int]]
    cross_frames: list[tuple[Regular2DFrameInput, int]]


class MultiFrameInput(BaseModel):
    """
    Validator data model for multi-frame input
    """
    tag: int
    materials: SimpleMaterialInput
    sections: BasicSectionCollectionInput
    frames: FrameGrid
    masses: list[float]


    class Config:
        frozen = True
