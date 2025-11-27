import argparse
import csv
from enum import Enum
from functools import partial
from pathlib import Path
from typing import Callable

from model.data_models import FrameCapacity
from model.enums import Direction, ElementType
from model.validation.frame_input import Regular2DFrameInput
from model.validation.input_validation import MultiFrameInput
from model.validation.material_validation import SimpleMaterialInput
from model.validation.section_model import BasicSectionCollectionInput
from src.capacity import beam_sidesway, column_sidesway, mixed_sidesway
from src.concrete import Concrete
from src.elements.basic_element import BasicElement
from src.frame import RegularFrameBuilder
from src.frame.regular_frame import RegularFrame
from src.scripts.popolate_section_collection import \
    BasicSectionCollectionBuilder
from src.sections.basic_section import BasicSection
from src.steel import Steel  # does not see the package
from src.subassembly import SubassemblyFactory
from src.utils import export_to_json, import_from_json


def main(
        input_path: Path,
        output_path: Path,
        export_subs_folder: Path | None = None,
        mechanism: Callable[..., FrameCapacity] = mixed_sidesway
    ):
    """
    Main process
    """
    # -o-o-o-o-o- IMPORT AND VALIDATION -o-o-o-o-o-

    # Import files
    input_file_dct = import_from_json(input_path)
    validated_input = MultiFrameInput(
        **input_file_dct
    )

    # Pass validated sections and materials
    validated_material = validated_input.materials
    validated_sections = validated_input.sections

    # Main
    main_capacity_curves: list[FrameCapacity] = []
    for i, (frame, count) in enumerate(validated_input.frames.main_frames):
        capacity_curve = compute_capacity_curve(
            validated_sections=validated_sections,
            validated_frame=frame,
            validated_materials=validated_material,
            mechanism=mechanism,
            sub_export_path=export_subs_folder / f'main_frame_{i}.csv' if export_subs_folder else None
        )
        # scale the capacity curve by the count
        capacity_curve *= count

        main_capacity_curves.append(capacity_curve)

    main_capacity = main_capacity_curves[0]
    for curve in main_capacity_curves[1:]:
        main_capacity += curve

    # Cross
    cross_capacity_curves: list[FrameCapacity] = []
    for i, (frame, count) in enumerate(validated_input.frames.cross_frames):
        capacity_curve = compute_capacity_curve(
            validated_sections=validated_sections,
            validated_frame=frame,
            validated_materials=validated_material,
            mechanism=mechanism,
            sub_export_path=export_subs_folder / f'cross_frame_{i}.csv' if export_subs_folder else None
        )
        # scale the capacity curve by the count
        capacity_curve *= count

        cross_capacity_curves.append(capacity_curve)

    cross_capacity = cross_capacity_curves[0]
    for curve in cross_capacity_curves[1:]:
        cross_capacity += curve

    return export_to_json(
        output_path,
        {
            'tag': validated_input.tag,
            'main_capacity': main_capacity.to_dict(),
            'cross_capacity': cross_capacity.to_dict(),
            'masses': validated_input.masses
        }
    )


def compute_capacity_curve(
        validated_sections: BasicSectionCollectionInput,
        validated_frame: Regular2DFrameInput,
        validated_materials: SimpleMaterialInput,
        mechanism: Callable[..., FrameCapacity],
        sub_export_path: Path | None = None
) -> FrameCapacity:

    # Instansiate material objects
    steel = Steel(**validated_materials.steel.__dict__)
    concrete = Concrete(**validated_materials.concrete.__dict__)

    # Instanciate Section Data and visitors
    section_collection_builder = BasicSectionCollectionBuilder(
        concrete=concrete,
        steel=steel,
        section_cls=BasicSection
    )
    sections = section_collection_builder.build(validated_sections)

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

    # Compute capacity
    capacity_curve = mechanism(
        sub_factory=subassemly_factory,
        frame=frame
    )

    if sub_export_path is not None:
        # Ths does not work now
        export_subassemblies_as_csv(
            sub_export_path,
            subassemly_factory,
            frame
        )

    return capacity_curve


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


def export_subassemblies_as_csv(path: Path,
                                subassemly_factory: SubassemblyFactory,
                                frame: RegularFrame):

    subs = get_mixed_sidesway_capacities(subassemly_factory, frame)
    header = ['sub', 'M', 'y', 'u', 'el']

    data = zip(
        range(frame.get_node_count()),
        [sub['moment'] for sub in subs],
        [sub['yielding'] for sub in subs],
        [sub['ultimate'] for sub in subs],
        [sub['element'] for sub in subs]
    )

    with open(path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        writer.writerow(header)
        writer.writerows(data)


def get_mixed_sidesway_capacities(sub_factory: SubassemblyFactory, frame: RegularFrame, direction: Direction = Direction.Positive):

    sub_capacities = [{}] * frame.get_node_count()
    for vertical in range(frame.verticals):
        subassembly_id = frame.get_node_id(
                floor=0,
                vertical=vertical
            )
        subassembly = sub_factory.get_subassembly(subassembly_id)
        assert subassembly.above_column is not None
        sub_capacities[subassembly_id] = {
            'moment' : subassembly.above_column.moment_rotation(
                direction=direction,
                axial=subassembly.axial
            ).mom_c,
            'yielding' : subassembly.above_column.moment_rotation(
                direction=direction,
                axial=subassembly.axial
            ).rot_y,
            'ultimate' : subassembly.above_column.moment_rotation(
                direction=direction,
                axial=subassembly.axial
            ).rot_c,
            'element' : ElementType.Column
        }

    # Subassemblies
    for sub_id in range(frame.verticals, frame.get_node_count()):
        subassembly = sub_factory.get_subassembly(
            sub_id
        )

        sub_capacities[sub_id] = {
            'moment' : subassembly.get_hierarchy(direction=direction).beam_eq,
            'yielding' : subassembly.get_hierarchy(direction=direction).rot_y,
            'ultimate' : subassembly.get_hierarchy(direction=direction).rot_c,
            'element' : subassembly.get_hierarchy(direction=direction).weakest
        }

    return sub_capacities


class MechanismType(Enum):
    MixedSidesway = 'mixed_sidesway'
    NoShearSway = 'no_shear_sidesway'
    ColumnSidesway = 'column_sidesway'
    BeamSidesway = 'beam_sidesway'

    def get_mechanism(self) -> Callable[..., FrameCapacity]:
        """
        Returns the mechanism function associated with the enum value.
        """
        MECHANISM_MAP = {
            MechanismType.MixedSidesway: partial(mixed_sidesway, consider_shear_interaction=True),
            MechanismType.NoShearSway: partial(mixed_sidesway, consider_shear_interaction=False),
            MechanismType.ColumnSidesway: column_sidesway,
            MechanismType.BeamSidesway: beam_sidesway
        }
        return MECHANISM_MAP[self]


# Profile Mode
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process frame analysis inputs and outputs.')
    parser.add_argument('--input', type=Path, required=True, help='Path to input JSON file')
    parser.add_argument('--output', type=Path, required=True, help='Path to output JSON file')
    parser.add_argument('--subs', type=Path, required=False, help='Optional path to export subassemblies as CSV')
    parser.add_argument('--mechanism', type=str, choices=[m.value for m in MechanismType], default='mixed_sidesway',
                        help='Mechanism to use for capacity calculation')

    args = parser.parse_args()

    main(
        input_path=Path(args.input),
        output_path=Path(args.output),
        mechanism=MechanismType(args.mechanism).get_mechanism()
    )
