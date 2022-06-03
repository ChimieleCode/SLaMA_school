from model.section_model import BasicSectionInput

class BasicSection:
    """ A Section object contains data  on the section input model"""

    def __init__(self, section_data: BasicSectionInput):
        """ Defines an object that contains section data """
        self._section_data = section_data

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

