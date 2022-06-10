from model.enums import Direction
from src.elements.element import Element
from src.sections.section import Section


class BasicElement(Element):
    """An element object contains data on the section and the lenght of an element
    like column or beam.
    """

    def __init__(self, section: Section, L: float) -> None:
        """Defines an object containing the section data and
        element net lenght.
        """
        self.__section = section
        self.__L = round(L, ndigits=2)
    
    def match(self, section: Section, L: float) -> bool:
        """Check if an instance match given data."""
        return (self.__section.get_section_data() == section.get_section_data()) and (self.__L == round(L, ndigits=2))

    def moment_rotation(self, direction: Direction, axial: float=0.):
        print('not implemented yet')

    def shear_moment_interaction(self, axial: float=0.):
        print('not implemented yet')

    def __str__(self) -> str:
        return self.__section.__str__() + f"L               : {self.__L}\n"

