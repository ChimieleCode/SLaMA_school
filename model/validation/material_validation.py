from pydantic import BaseModel

class SimpleConcreteInput(BaseModel):
    """
    Data validator model of concrete with minimal parameters
    """
    id          : str
    fc          : float
    E           : float
    epsilon_0   : float
    epsilon_u   : float

    class Config:
        frozen = True


class SimpleSteelInput(BaseModel):
    """
    Data validator model of steel with minimal parameters
    """
    id          : str
    fy          : float
    fu          : float
    E           : float
    epsilon_u   : float

    class Config:
        frozen = True


class SimpleMaterialInput(BaseModel):
    """
    Input data validation for materials
    """
    concrete    : SimpleConcreteInput
    steel       : SimpleSteelInput
