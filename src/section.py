from model.section_model import BasicSectionInput

class BasicSection:

    def __init__(self, section_data: BasicSectionInput):
        """Defines an object that contains section data """
        self._section_data_input = section_data

    @property
    def h(self):
        return self._section_data_input.h
    
    @property
    def b(self):
        return self._section_data_input.b
    
    @property
    def As(self):
        return self._section_data_input.As
    
    @property
    def As1(self):
        return self._section_data_input.As1
    
    @property
    def cover(self):
        return self._section_data_input.cover

    @property
    def eq_bar_diameter(self):
        return self._section_data_input.eq_bar_diameter
    
    @property
    def Ast(self):
        return self._section_data_input.Ast
    
    @property
    def s(self):
        return self._section_data_input.s
    
    @property
    def id(self):
        return self._section_data_input.id
    
    @property
    def d(self):
        return self._section_data_input.h - self._section_data_input.cover
    
    @property
    def section_data(self):
        return self._section_data_input

