from src.sections import Section


class SectionCollection:

    def __init__(self) -> None:
        self._column_sections : list[Section] = list()
        self._beam_sections : list[Section] = list()

    def add_column(self, section: Section) -> None:
        """
        Adds a Section to the column section collection
        """
        self._column_sections.append(section)

    def add_beam(self, section: Section) -> None:
        """
        Adds a Section to the beam section collection
        """
        self._beam_sections.append(section)

    def get_beams(self) -> list[Section]:
        """
        Returns the list of beam sections in the SectionCollection
        """
        return self._beam_sections

    def get_columns(self) -> list[Section]:
        """
        Returns the list of column sections in the SectionCollection
        """
        return self._column_sections

    def reset(self, beams: bool = True, columns: bool = True) -> None:
        """
        Resets the section collection
        """
        if beams:
            self._beam_sections = list()
        if columns:
            self._column_sections = list()

    def __str__(self) -> str:
        print_ = ''
        for section in self._column_sections:
            print_ += str(section)
        for section in self._beam_sections:
            print_ += str(section)
        return print_
