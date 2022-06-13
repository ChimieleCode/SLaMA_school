from pydantic import BaseModel, validator
from typing import List

class Regular2DFrameInput(BaseModel):
    """
    Validator data model for structural frame

    Input is validated to make sure that the defined
    frame is consistent
    """
    H       : List[float]
    L       : List[float]
    m       : List[float]
    loads   : List[float]
    columns : List[List[int]]
    beams   : List[List[int]]

    @validator('H')
    def H_comulative_no_ground_floor(cls, value):
        if abs(value[0]) <= 0.001:
            value = value[1:]
            print('H should not contain groung floor data, the script provided')
        if value != sorted(value):
            raise ValueError('must contain comulated height')
        return value
        # Verifica che 2 non siano uguali da implementare

    @validator('L')
    def L_comulative(cls, value):
        if abs(value[0]) >= 0.001:
            value = [0.0] + value
            print('first lenght in L should be 0, the script provided')
        if value != sorted(value):
            raise ValueError('must contain comulated lenghts')
        return value
    
    @validator('m')
    def m_lenght_equal_to_H(cls, value, values):
        if len(value) != len(values['H']):
            raise ValueError('m and H must be the same lenght')
        return value

    @validator('loads')
    def loads_must_match_nodes(cls, value, values):
        nodes = (len(values['H']) + 1) * len(values['L'])
        if len(value) != nodes:
            raise ValueError('loads values must match number of nodes')
        return value
        # ignorare il piano terra e aggiungere 0 al pian terreno [0.] * len(values['L'])

    @validator('columns')
    def columns_number_check(cls, value, values):
        column_count = len(values['L']) * len(values['H'])
        if sum(len(floor) for floor in value) != column_count:
            raise ValueError('number of column tags does not match element count')
        return value
    
    @validator('beams')
    def beams_number_check(cls, value, values):
        beam_count = (len(values['L']) - 1) * len(values['H'])
        if sum(len(floor) for floor in value) != beam_count:
            raise ValueError('number of beam tags does not match element count')
        return value