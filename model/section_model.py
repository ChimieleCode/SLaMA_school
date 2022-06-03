from typing import List
from pydantic import BaseModel, validator

class BasicSectionInput(BaseModel):
    """ Validator data model for structural frame

    eq_bar_diameter is used instead of single bar diameters
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

    @validator('columns')
    def columns_check_id_match(cls, value):
        column_id_set = set()
        for column in value:
            column_id_set.add(column.id) 
        if len(column_id_set) != len(value):
            raise ValueError('different column sections have the same id, the section id must be unique')
        return value

    @validator('beams')
    def beams_check_id_match(cls, value):
        beam_id_set = set()
        for beam in value:
            beam_id_set.add(beam.id) 
        if len(beam_id_set) != len(value):
            raise ValueError('different column sections have the same id, the section id must be unique')
        return value