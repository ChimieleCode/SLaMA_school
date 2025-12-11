from functools import cache

from src.elements import Element
from src.sections import Section


class ElementCollection:

    def __init__(self) -> None:
        self._column_elements : list[Element] = list()
        self._beam_elements : list[Element] = list()

    @cache
    def add_column(self, section: Section, L: float, _elementClass: type[Element]) -> Element:
        """Adds an element to the column element collection starting from a Section

        If an istance with same data is already contained in the collection,
        it will return the existing instance inside the collection.

        :param section: section object

        :param float L: length of the element

        :param _elementClass: element class that is going to be added
        """
        for column in self._column_elements:
            # Checks if there is already a element with same proprieties
            if column.match(section, L):
                return column
        # If no such element is defined, creates one
        new_column = _elementClass(section, round(L, ndigits=2))
        self._column_elements.append(new_column)
        return new_column

    @cache
    def add_beam(self, section: Section, L: float, _elementClass: type[Element]) -> Element:
        """Adds an element to the beam element collection starting from a Section

        If an istance with same data is already contained in the collection,
        it will return the existing instance inside the collection.

        :param section: section object

        :param float L: length of the element

        :param _elementClass: element class that is going to be added
        """
        for beam in self._beam_elements:
            # Checks if there is already a element with same proprieties
            if beam.match(section, L):
                return beam
        # If no such element is defined, creates one
        new_beam = _elementClass(section, round(L, ndigits=2))
        self._beam_elements.append(new_beam)
        return new_beam

    def get_beams(self) -> list[Element]:
        """
        Returns the list of beam elements in the SectionCollection
        """
        return self._beam_elements

    def get_columns(self) -> list[Element]:
        """
        Returns the list of column elements in the SectionCollection
        """
        return self._column_elements

    def reset(self, beams: bool=True, columns: bool=True) -> None:
        """
        Resets the element collection
        """
        if beams:
            self._beam_elements = list()
        if columns:
            self._column_elements = list()

    def __str__(self) -> str:
        print_ = ''
        for element in self._column_elements:
            print_ += str(element)
        for element in self._beam_elements:
            print_ += str(element)
        return print_
