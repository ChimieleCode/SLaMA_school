from model.enums import Direction
from src.elements.element import Element
from src.sections.section import Section


class BasicElement(Element):
    """An element object contains data on the section and the lenght of an element
    like column or beam.
    """

    def __init__(self, section: Section, L: float):
        """Defines an object containing the section data and
        element net lenght.
        """
        self.__section = section
        self.__L = L

    def match(self, section: Section, L: float) -> bool:
        """Check if an instance match given data."""
        return (self.__section.get_section_data() == section.get_section_data()) and (self.__L == L)

    def moment_rotation(self, direction: Direction, axial: float=0.):
        print('not implemented yet')

    def shear_moment_interaction(self, axial: float=0.):
        print('not implemented yet')
