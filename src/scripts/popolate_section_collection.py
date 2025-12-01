from model.enums import SectionType
from model.validation.section_model import BasicSectionCollectionInput
from src.collections.section_collection import SectionCollection
from src.concrete.concrete import Concrete
from src.sections import Section
from src.sections.basic_section import BasicSection, BasicSectionData
from src.steel.steel import Steel


class BasicSectionCollectionBuilder:
    """
    Builds a SectionCollection from validated input using provided concrete, steel and section class.
    """

    def __init__(self, concrete: Concrete, steel: Steel, section_cls: type[Section] | None = None) -> None:
        self.concrete = concrete
        self.steel = steel
        self.section_cls = section_cls or BasicSection

    def build(self, validated_sections: BasicSectionCollectionInput) -> SectionCollection:
        sections = SectionCollection()
        sections.reset()

        for validated_section in validated_sections.beams:
            sections.add_beam(
                self.section_cls(
                    section_data=BasicSectionData.from_validated_input(validated_section),
                    concrete=self.concrete,
                    steel=self.steel,
                    section_type=SectionType.Beam
                )
            )

        for validated_section in validated_sections.columns:
            sections.add_column(
                self.section_cls(
                    section_data=BasicSectionData.from_validated_input(validated_section),
                    concrete=self.concrete,
                    steel=self.steel,
                    section_type=SectionType.Column
                )
            )

        return sections
