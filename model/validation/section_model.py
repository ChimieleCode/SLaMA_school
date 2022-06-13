from typing import List
from pydantic import BaseModel, validator

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
    id              : str

class BasicSectionCollectionInput(BaseModel):
    columns : List[BasicSectionInput]
    beams   : List[BasicSectionInput]

    @validator('columns', 'beams')
    def section_id_no_duplicates(cls, value):
        section_id_set = set()
        for section in value:
            section_id_set.add(section.id) 
        if len(section_id_set) != len(value):
            raise ValueError('different sections have the same id, the section id must be unique')
        return value
