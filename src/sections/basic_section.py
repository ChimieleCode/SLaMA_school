from model.validation.section_model import BasicSectionInput
from model.enums import Direction
from src.concrete.concrete import Concrete
from src.steel.steel import Steel
from src.sections.section import Section

class BasicSection(Section):

    def __init__(self, section_data: BasicSectionInput, concrete: Concrete, steel: Steel):
        """Defines an object that contains section data"""
        self.__section_data = section_data
        self.__concrete = concrete
        self.__steel = steel

    def moment_curvature(self, direcion: Direction, axial: float):
        print('not implemented yet')
    
    def shear_capacity(self):
        print('not implemented yet')
    
    def domain_MN(self):
        print('not implemented yet')
    
    def get_height(self) -> float:
        return self.__section_data.h
    
    def get_section_data(self):
        return self.__section_data


