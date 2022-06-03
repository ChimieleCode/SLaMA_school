from typing import List
from model.section_model import BasicSectionInput
from src.section import BasicSection

class BasicElement:
    """ An element object contains data on the section and the lenght of an element
    like column or beam.
    """

    # If 2 floats have a lower difference will be considered as equal 
    _TOLLERANCE = 0.001

    def __init__(self, section: BasicSection, L: float):
        """ Defines an object containing the section data and
        element net lenght.
        """
        self._section_data = section
        self._L = L
    
    @property
    def L(self):
        return self._L

    @property
    def h(self):
        return self._section_data.h
    
    @property
    def b(self):
        return self._section_data.b
    
    @property
    def As(self):
        return self._section_data.As
    
    @property
    def As1(self):
        return self._section_data.As1
    
    @property
    def cover(self):
        return self._section_data.cover

    @property
    def eq_bar_diameter(self):
        return self._section_data.eq_bar_diameter
    
    @property
    def Ast(self):
        return self._section_data.Ast
    
    @property
    def s(self):
        return self._section_data.s
    
    @property
    def id(self):
        return self._section_data.id
    
    @property
    def d(self):
        return self._section_data.h - self._section_data.cover
    
    @property
    def section_data(self):
        return self._section_data

    def match(self, section: BasicSection, L: float) -> bool:
        """ Check if an instance match given data. """
        return (self._section_data.section_data == section.section_data) and (self.L == L)
    
    def __str__(self) -> str:
        return f"""
        BasicSection Object
        section id      : {self.id}
        h               : {self.h}
        b               : {self.b}
        L               : {self.L}
        cover           : {self.cover} 
        As              : {self.As} 
        As1             : {self.As1}
        eq_bar_diameter : {self.eq_bar_diameter}
        s               : {self.s}
        """

class BasicElementCollection:
    """ No data shall be provided to initiate an istance of this class. """
    column_elements : List[BasicElement] = list()
    beam_elements : List[BasicElement] = list()

    def add_column_section(self, section: BasicSection, L: float) -> BasicElement:
        """ Adds a section to the column section collection and converts it 
        into a BasicSection Object
        
        If an istance with same data is already contained in the collection, 
        it will return the existing instance inside the collection. 
        """
        for column in self.column_elements:
            # Checks if there is already a section with same proprieties
            if column.match(section, L):
                return column
        # If no such section is defined, creates one
        new_column = BasicElement(section=section, L=L)
        self.column_elements.append(new_column)
        return new_column

    def add_beam_section(self, section: BasicSection, L: float) -> BasicElement:
        """ Adds a section to the beam section collection and converts it 
        into a BasicSection Object 
        
        If an istance with same data is already contained in the collection, 
        it will return the existing instance inside the collection. 
        """
        for beam in self.beam_elements:
            # Checks if there is already a section with same proprieties
            if beam.match(section, L):
                return beam
        # If no such section is defined, creates one
        new_beam = BasicElement(section=section, L=round(L, ndigits=2))
        self.beam_elements.append(new_beam)
        return new_beam

    def __str__(self):
        print_ = ''
        for section in self.column_elements:
            print_ += str(section)
        for section in self.beam_elements:
            print_ += str(section)
        return print_
        


