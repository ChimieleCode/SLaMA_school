from src.concrete.concrete import Concrete
from model.validation.section_model import BasicSectionCollectionInput
from model.enums import SectionType
from src.collections.section_collection import SectionCollection
from src.sections import Section
from src.steel.steel import Steel


def convert_to_section_collection(validated_sections: BasicSectionCollectionInput,
                                  concrete: Concrete,
                                  steel: Steel,
                                  section_type: type[Section]) -> SectionCollection:
    """
    This script turns a validated section collection input into a section collection
    """
    sections = SectionCollection()
    sections.reset()

    for validated_section in validated_sections.beams:
        sections.add_beam_section(
            section_type(
                section_data=validated_section,
                concrete=concrete,
                steel=steel,
                section_type=SectionType.Beam
            )
        )

    for validated_section in validated_sections.columns:
        sections.add_column_section(
            section_type(
                section_data=validated_section,
                concrete=concrete,
                steel=steel,
                section_type=SectionType.Column
            )
        )

    return sections