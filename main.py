from src.utils import import_from_json

from model.validation.frame_input import Regular2DFrameInput
from model.validation.section_model import BasicSectionCollectionInput
from model.validation.material_validation import SimpleMaterialInput
from src.steel.steel import Steel
from src.concrete.concrete import Concrete
from src.collections.section_collection import SectionCollection
from src.sections.basic_section import BasicSection
from src.frame.regular_frame import RegularFrameBuilder
from src.elements.basic_element import BasicElement
from src.subassembly import SubassemblyFactory
from src.collections.subassembly_collection import SubassemblyCollection

def main():
    """Main process."""
    # Import frame data
    frame_dct = import_from_json('.\Inputs\Frame.json')
    # Validate frame data
    validated_frame = Regular2DFrameInput(
        **frame_dct
    )

    # Import section data
    sections_dct = import_from_json('.\Inputs\Sections.json')
    # validate section data
    validated_sections = BasicSectionCollectionInput(
        **sections_dct
    )

    # Import material data
    materials_dct = import_from_json('.\Inputs\Materials.json')
    # Validate material data
    validated_materials = SimpleMaterialInput(
        **materials_dct
    )

    # Instansiate material objects
    steel = Steel(**validated_materials.steel.__dict__)
    concrete = Concrete(**validated_materials.concrete.__dict__)

    # Instanciate Section Data and visitors
    sections = SectionCollection()
    sections.reset()

    for validated_section in validated_sections.beams:
        section = BasicSection(
            section_data=validated_section, 
            concrete=concrete, 
            steel=steel
        )
        sections.add_beam_section(section)

    for validated_section in validated_sections.columns:
        section = BasicSection(
            section_data=validated_section, 
            concrete=concrete, 
            steel=steel
        )
        sections.add_column_section(section)
    
    # Build frame model
    frame_builder = RegularFrameBuilder(
        frame_data=validated_frame,
        sections=sections,
        element_object=BasicElement
    )
    frame_builder.build_frame()
    frame = frame_builder.get_frame()

    # Get subassemblies
    subassemly_factory = SubassemblyFactory(frame=frame)
    subassemblies = SubassemblyCollection()

    for node in frame.get_nodes():
        subassemblies.add_subassembly(
            subassemly_factory.get_subassembly(node)
        )

    

    
# Profile Mode
if __name__ == '__main__':
    import cProfile
    import pstats

    with cProfile.Profile() as pr:
        main()

    stats = pstats.Stats(pr)
    stats.sort_stats(pstats.SortKey.TIME)
    # stats.print_stats()
