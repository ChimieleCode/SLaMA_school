from model.enums import Direction, SectionType
from src.scripts import convert_to_section_collection
from src.utils import import_from_json, intersection

from model.validation import Regular2DFrameInput, BasicSectionCollectionInput, SimpleMaterialInput
from src.steel.steel import Steel   # does not see the package
from src.concrete import Concrete
from src.collections import SectionCollection
from src.sections import BasicSection
from src.frame import RegularFrameBuilder
from src.elements import BasicElement
from src.subassembly import SubassemblyFactory
from src.capacity import column_sidesway, beam_sidesway, mixed_sidesway

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

    # Instanciate Section Data and visitors
    sections = convert_to_section_collection(
        validated_sections,
        concrete,
        steel,
        section_type=BasicSection
    )

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

    print(
        beam_sidesway(
            sub_factory=subassemly_factory,
            frame=frame
        )
    )
    print(
        mixed_sidesway(
            sub_factory=subassemly_factory,
            frame=frame
        )
    )
    print(
        column_sidesway(
            sub_factory=subassemly_factory,
            frame=frame
        )
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
    # can be optimized the solution for intersection (ditch scipy and lambdas)

