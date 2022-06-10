from model.validation.section_model import BasicSectionInput
from model.enums import Direction
from src.concrete.concrete import Concrete
from src.steel.steel import Steel
from src.sections.section import Section

class BasicSection(Section):

    def __init__(self, section_data: BasicSectionInput, concrete: Concrete, steel: Steel)-> None:
        """Defines an object that contains section data"""
        self.__section_data = section_data
        self.__concrete = concrete
        self.__steel = steel

    def moment_curvature(self, direction: Direction, axial: float):
        print('not coded yet')
    
    def shear_capacity(self):
        print('not coded yet')
    
    def domain_MN(self, axial: float) -> float:
        print('not coded yet')
    
    def get_height(self) -> float:
        """Returns the section height."""
        return self.__section_data.h
    
    def get_section_data(self) -> None:
        """Returns the validated input data."""
        return self.__section_data

    def get_concrete(self) -> Concrete:
        """Returns the concrete material."""
        return self.__concrete
    
    def get_steel(self) -> Steel:
        """Returns the steel material."""
        return self.__steel

    def __str__(self) -> str:
        return f"""
        BasicSection Object
        section id      : {self.__section_data.id}
        h               : {self.__section_data.h}
        b               : {self.__section_data.b}
        cover           : {self.__section_data.cover} 
        As              : {self.__section_data.As} 
        As1             : {self.__section_data.As1}
        eq_bar_diameter : {self.__section_data.eq_bar_diameter}
        s               : {self.__section_data.s}
        """
