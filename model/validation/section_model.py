from typing import List

from pydantic import BaseModel, field_validator


class BasicSectionInput(BaseModel):
    """
    Validator data model for structural frame
    """
    h               : float
    b               : float
    As              : float
    As1             : float
    cover           : float
    eq_bar_diameter : float
    Ast             : float
    s               : float
    name            : str

    class Config:
        frozen = True


class BasicSectionCollectionInput(BaseModel):
    columns : List[BasicSectionInput]
    beams   : List[BasicSectionInput]

    @field_validator('columns', 'beams')
    def section_name_no_duplicates(cls, value):
        section_name_set = set()
        for section in value:
            section_name_set.add(section.name)
        if len(section_name_set) != len(value):
            raise ValueError('different sections have the same name, the section name must be unique')
        return value
