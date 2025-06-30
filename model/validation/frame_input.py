from pydantic import BaseModel, field_validator


class Regular2DFrameInput(BaseModel):
    """
    Validator data model for structural frame

    Input is validated to make sure that the defined
    frame is consistent
    """
    L       : list[float]
    H       : list[float]
    m       : list[float]
    loads   : list[float]
    columns : list[list[int]]
    beams   : list[list[int]]

    class Config:
        frozen = True

    @field_validator('H')
    def H_comulative_no_ground_floor(cls, value):
        if abs(value[0]) <= 0.001:
            value = value[1:]
            print('H should not contain groung floor data, the script provided')
        if value != sorted(value):
            raise ValueError('must contain comulated height')
        return value
        # Verifica che 2 non siano uguali da implementare

    @field_validator('L')
    def L_comulative(cls, value):
        if abs(value[0]) >= 0.001:
            value = [0.0] + value
            print('first lenght in L should be 0, the script provided')
        if value != sorted(value):
            raise ValueError('must contain comulated lenghts')
        return value

    @field_validator('m')
    def m_lenght_equal_to_H(cls, value, info):
        if len(value) != len(info.data.get('H')):
            raise ValueError('m and H must be the same lenght')
        return value

    @field_validator('loads')
    def loads_must_match_nodes(cls, value, info):
        nodes = (len(info.data.get('H')) + 1) * len(info.data.get('L'))
        if len(value) != nodes:
            raise ValueError(f'loads values must match number of nodes \nexpected: {nodes}, got: {len(value)}')
        return value
        # ignorare il piano terra e aggiungere 0 al pian terreno [0.] * len(values['L'])

    @field_validator('columns')
    def columns_number_check(cls, value, info):
        column_count = len(info.data.get('L')) * len(info.data.get('H'))
        if sum(len(floor) for floor in value) != column_count:
            raise ValueError('number of column tags does not match element count')
        return value

    @field_validator('beams')
    def beams_number_check(cls, value, info):
        beam_count = (len(info.data.get('L')) - 1) * len(info.data.get('H'))
        if sum(len(floor) for floor in value) != beam_count:
            raise ValueError('number of beam tags does not match element count')
        return value
