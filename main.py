from pathlib import Path

from model.enums import Direction, ElementType
from model.validation import (Regular2DFrameInput, BasicSectionCollectionInput,
                              SimpleMaterialInput, NTC2018HazardInput)
from src.steel import Steel   # does not see the package
from src.concrete import Concrete
from src.sections import BasicSection
from src.frame import RegularFrameBuilder
from src.elements import BasicElement
from src.subassembly import SubassemblyFactory
from src.hazard import NTC2018SeismicHazard
from src.frame.regular_frame import RegularFrame

from src.scripts import convert_to_section_collection
from src.utils import export_to_json, import_from_json
from src.performance import compute_ISV, compute_ISD
from src.capacity import (column_sidesway, beam_sidesway, mixed_sidesway,
                          mixed_sidesway_sub_stiff, damaged_sidesway_sub_stiff, damaged_mixed_sidesway)


def main():
    """
    Main process
    """
    # -o-o-o-o-o- IMPORT AND VALIDATION -o-o-o-o-o-

    # Import frame data
    frame_dct = import_from_json(Path('./Inputs/Frame.json'))
    # print(frame_dct)
    # Validate frame data
    validated_frame = Regular2DFrameInput(
        **frame_dct
    )

    # Import section data
    sections_dct = import_from_json(Path('./Inputs/Sections.json'))
    # validate section data
    validated_sections = BasicSectionCollectionInput(
        **sections_dct
    )

    # Import material data
    materials_dct = import_from_json(Path('./Inputs/Materials.json'))
    # Validate material data
    validated_materials = SimpleMaterialInput(
        **materials_dct
    )

    # -o-o-o-o-o- MODEL BUILDING -o-o-o-o-o-

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

    # -o-o-o-o-o- COMPUTE CAPACIIES -o-o-o-o-o-

    # print(frame.get_effective_mass())
    
    # Compute capacity
    beam_SLaMA = beam_sidesway(
        sub_factory=subassemly_factory,
        frame=frame
    )
    # print(beam_SLaMA)
    column_SLaMA = column_sidesway(
        sub_factory=subassemly_factory,
        frame=frame
    )
    # print(column_SLaMA)
    classic_SLaMA = mixed_sidesway(
        sub_factory=subassemly_factory,
        frame=frame
    )
    print('Classic:', classic_SLaMA, '\n')
    print('Beam:', beam_SLaMA, '\n')
    print('Column:', column_SLaMA, '\n')
    print(frame.forces_effective_height)



def get_subassemby_hierarchy(sub_factory: SubassemblyFactory, frame: RegularFrame) -> dict[int, ElementType]:
    """
    Gets the subassembly mechcanism data

    Args:
        sub_factory (SubassemblyFactory): subassembly factory
        frame (RegularFrame): frame object

    Returns:
        dict[int: ElementType]: list of sub critical elements
    """
    mechanisms = {}

    for sub_id in range(frame.verticals, frame.get_node_count()):
        subassembley = sub_factory.get_subassembly(sub_id)
        mechanisms[sub_id] = subassembley.get_hierarchy()

    return mechanisms


def export_subassemblies_as_csv(subassemly_factory, frame):
    import csv

    subs = get_mixed_sidesway_capacities(subassemly_factory, frame)
    header = ['sub', 'M', 'y', 'u', 'el']

    data = zip(
        range(frame.get_node_count()),
        [sub['moment'] for sub in subs],
        [sub['yielding'] for sub in subs],
        [sub['ultimate'] for sub in subs],
        [sub['element'] for sub in subs]
    )

    with open(Path('Outputs/subs.csv'), 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        writer.writerow(header)
        writer.writerows(data)


def get_mixed_sidesway_capacities(sub_factory: SubassemblyFactory, frame: RegularFrame, direction: Direction = Direction.Positive):

    sub_capacities = [0] * frame.get_node_count()
    for vertical in range(frame.verticals):
        subassembly_id = frame.get_node_id(
                floor=0,
                vertical=vertical
            )
        subassembly = sub_factory.get_subassembly(subassembly_id)

        sub_capacities[subassembly_id] = {
            'moment' : subassembly.above_column.moment_rotation(
                direction=direction,
                axial=subassembly.axial
            )['moment'][-1],
            'yielding' : subassembly.above_column.moment_rotation(
                direction=direction,
                axial=subassembly.axial
            )['rotation'][0],
            'ultimate' : subassembly.above_column.moment_rotation(
                direction=direction,
                axial=subassembly.axial
            )['rotation'][-1],
            'element' : ElementType.Column
        }

    # Subassemblies
    for sub_id in range(frame.verticals, frame.get_node_count()):
        subassembly = sub_factory.get_subassembly(
            sub_id
        )

        sub_capacities[sub_id] = {
            'moment' : subassembly.get_hierarchy(direction=direction)['beam_equivalent'],
            'yielding' : subassembly.get_hierarchy(direction=direction)['rotation_yielding'],
            'ultimate' : subassembly.get_hierarchy(direction=direction)['rotation_ultimate'],
            'element' : subassembly.get_hierarchy(direction=direction)['element']
        }

    return sub_capacities

# Profile Mode
if __name__ == '__main__':
    import cProfile
    import pstats

    with cProfile.Profile() as pr:
        for _ in range(1):
            main()

    stats = pstats.Stats(pr)
    # stats.sort_stats(pstats.SortKey.TIME).print_stats()


