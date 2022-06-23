from model.enums import Direction, SectionType
from src.utils import import_from_json, intersection

from model.validation import Regular2DFrameInput, BasicSectionCollectionInput, SimpleMaterialInput
from src.steel.steel import Steel   # does not see the package
from src.concrete import Concrete
from src.collections import SectionCollection
from src.sections import BasicSection
from src.frame import RegularFrameBuilder
from src.elements import BasicElement
from src.subassembly import SubassemblyFactory
from src.analysis import column_sidesway, beam_sidesway, mixed_sidesway

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
    sections = SectionCollection()
    sections.reset()

    for validated_section in validated_sections.beams:
        section = BasicSection(
            section_data=validated_section, 
            concrete=concrete, 
            steel=steel,
            section_type=SectionType.Beam
        )
        sections.add_beam_section(section)

    for validated_section in validated_sections.columns:
        section = BasicSection(
            section_data=validated_section, 
            concrete=concrete, 
            steel=steel,
            section_type=SectionType.Column
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

    print(
        beam_sidesway(
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




def gerarchia(subassembly):
    axials = [
        -500,
        -300,
        -100,
        100,
        300,
        500,
        700
    ]
    if subassembly.left_beam is not None:
        print('Left beam capacity:', subassembly.left_beam.moment_rotation(direction=Direction.Negative))

    if subassembly.right_beam is not None:
        print('Right beam capacity:', subassembly.right_beam.moment_rotation()) 

    if subassembly.above_column is not None:
        domain_upper = {
            'axials' : axials,
            'moments' : subassembly.above_column.get_section().domain_MN(axials)
        }
        print('Above column domain:', domain_upper)
    
    domain_lower = {
        'axials' : axials,
        'moments' : subassembly.below_column.get_section().domain_MN(axials)
    }
    print('Below column domain:', domain_lower)

    domain_joint = {
        'axials' : axials,
        'moments' : subassembly.domain_MN(axials)
    }
    print('joint domain:', domain_joint)
 
    print('Axial:', subassembly.axial)
    print('delta:', subassembly.delta_axial)


    
    # import numpy as np 
    # from itertools import product
    # node_super = np.zeros((frame.verticals, frame.floors))
    # for vertical, floor in product(range(frame.verticals),range(frame.floors)):
    #     node_super[vertical][floor] = subassemly_factory.get_subassembly(
    #         frame.get_node_id(
    #             floor=floor + 1,
    #             vertical=vertical
    #         )
    #     ).get_hierarchy()['rotations'][0]

    # print(node_super)