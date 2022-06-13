from typing import List
from src.sections.section import Section

class SectionCollection:
  
    __column_sections : List[Section] = list()
    __beam_sections : List[Section] = list()

    def add_column_section(self, new_column: Section) -> None:
        """
        Adds a Section to the column section collection
        """
        self.__column_sections.append(new_column)
        return new_column

    def add_beam_section(self, new_beam: Section) -> None:
        """
        Adds a Section to the beam section collection
        """
        self.__beam_sections.append(new_beam)
        return 
    
    def get_beams(self) -> List[Section]:
        """
        Returns the list of beam sections in the SectionCollection
        """
        return self.__beam_sections

    def get_columns(self) -> List[Section]:
        """
        Returns the list of column sections in the SectionCollection
        """
        return self.__column_sections

    def reset(self, beams: bool=True, columns: bool=True) -> None:
        """
        Resets the section collection
        """
        if beams:
            self.__beam_sections = list()
        if columns:
            self.__column_sections = list()

    def __str__(self) -> str:
        print_ = ''
        for section in self.__column_sections:
            print_ += str(section)
        for section in self.__beam_sections:
            print_ += str(section)
        return print_
        


