from operator import ne
from model.enums import Direction
from src.sections.moment_curvature.analitic_moment_curvature import analytic_coment_curvature
from src.utils import import_from_json

from model.validation import Regular2DFrameInput, BasicSectionCollectionInput, SimpleMaterialInput
from src.steel.steel import Steel   # does not see the package
from src.concrete import Concrete
from src.collections import SectionCollection, SubassemblyCollection
from src.sections import BasicSection
from src.frame import RegularFrameBuilder
from src.elements import BasicElement
from src.subassembly import SubassemblyFactory


def main():
    """
    Main process
    """
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

    print(analytic_coment_curvature(validated_sections.beams[0], concrete, steel, Direction.Positive, axial=200))

    

    
# Profile Mode
if __name__ == '__main__':
    import cProfile
    import pstats

    with cProfile.Profile() as pr:
        main()

    stats = pstats.Stats(pr)
    stats.sort_stats(pstats.SortKey.TIME)
    # stats.print_stats()



def build_model():
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