import argparse
import csv
from pathlib import Path

import pandas as pd

from model.enums import Direction, ElementType
from model.validation import (BasicSectionCollectionInput, Regular2DFrameInput,
                              SimpleMaterialInput)
from src.capacity import mixed_sidesway, mixed_sidesway_sub_stiff
from src.capacity.fema_306_sway import (damaged_sidesway,
                                        damaged_sidesway_sub_stiff)
from src.concrete import Concrete
from src.elements.basic_element import BasicElement
from src.frame import RegularFrameBuilder
from src.frame.regular_frame import RegularFrame
from src.reduction_values import (DamageState, ElementFailureFEMA306,
                                  FEMA306LambdaValues)
from src.scripts import convert_to_section_collection
from src.sections.basic_section import BasicSection
from src.steel import Steel  # does not see the package
from src.subassembly import SubassemblyFactory
from src.utils import export_to_json, import_from_json


def main(input_dct_path: Path,
         damaged_csv_path: Path,
         output_curve_path: Path,
         sub_output_path: Path | None = None) -> None:
    """
    Main process
    """
    # -o-o-o-o-o- IMPORT AND VALIDATION -o-o-o-o-o-
    # Import files
    input_file_dct = import_from_json(input_dct_path)
    damage_states_df = pd.read_csv(damaged_csv_path, index_col=0)

    # Import frame data
    frame_dct = input_file_dct['frame']
    # print(frame_dct)
    # Validate frame data
    validated_frame = Regular2DFrameInput(
        **frame_dct
    )

    # Import section data
    sections_dct = input_file_dct['sections']
    # validate section data
    validated_sections = BasicSectionCollectionInput(
        **sections_dct
    )

    # Import material data
    materials_dct = input_file_dct['materials']
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

    # Compute capacity
    classic_SLaMA = mixed_sidesway(
        sub_factory=subassemly_factory,
        frame=frame
    )
    stiffness_SLaMA = mixed_sidesway_sub_stiff(
        sub_factory=subassemly_factory,
        frame=frame
    )

    COMPONENT_MAP = {
        ElementType.Column: ElementFailureFEMA306.ColumnRCLapSlice,
        ElementType.Beam: ElementFailureFEMA306.ColumnRCLapSlice,
        ElementType.Joint: ElementFailureFEMA306.JointRC,
        ElementType.AboveColumn: ElementFailureFEMA306.ColumnRCLapSlice,
        ElementType.BelowColumn: ElementFailureFEMA306.ColumnRCLapSlice,
        ElementType.LeftBeam: ElementFailureFEMA306.ColumnRCLapSlice,
        ElementType.RightBeam: ElementFailureFEMA306.ColumnRCLapSlice,
    }

    damaged_curves_classic = {}
    damaged_curves_sub_stiff = {}
    damaged_curves_modified = {}
    for idx, row in damage_states_df.iterrows():
        print(f'Processing scenario {idx}')
        # Create damage state map
        damage_state_map = {
            int(kk): FEMA306LambdaValues.get_lambda_values( # type: ignore[reportArgumentType]
                damage_state=DamageState(vv),
                component=COMPONENT_MAP[
                    subassemly_factory.get_subassembly(int(kk)).get_hierarchy().weakest # type: ignore[reportArgumentType]
                ]
            ) for kk, vv in row.items()
        }
        damaged_curves_classic[idx] = damaged_sidesway(
            sub_factory=subassemly_factory,
            frame=frame,
            lambda_values=damage_state_map,
            direction=Direction.Positive,
        )
        damaged_curves_sub_stiff[idx] = damaged_sidesway_sub_stiff(
            sub_factory=subassemly_factory,
            frame=frame,
            lambda_values=damage_state_map,
            direction=Direction.Positive,
            limit_yielding=False
        )
        damaged_curves_modified[idx] = damaged_sidesway_sub_stiff(
            sub_factory=subassemly_factory,
            frame=frame,
            lambda_values=damage_state_map,
            direction=Direction.Positive,
            limit_yielding=True
        )

    # -o-o-o-o-o- EXPORT RESULTS -o-o-o-o-o-
    results_dct = {
        'classic_SLaMA': classic_SLaMA.to_dict(),
        'stiffness_SLaMA': stiffness_SLaMA.to_dict(),
        'damaged_curves_classic': [d.to_dict() for d in damaged_curves_classic.values()],
        'damaged_curves_sub_stiff': [d.to_dict() for d in damaged_curves_sub_stiff.values()],
        'damaged_curves_modified': [d.to_dict() for d in damaged_curves_modified.values()]
    }
    export_to_json(
        filepath=output_curve_path,
        data=results_dct
    )

    if sub_output_path is not None:
        export_subassemblies_as_csv(
            sub_output_path,
            subassemly_factory,
            frame
        )


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

# Profile Mode
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process frame analysis inputs.')
    parser.add_argument('-i', '--input', required=True, help='Path to input JSON file')
    parser.add_argument('-o', '--output', required=True, help='Output path for JSON results')
    parser.add_argument('-d', '--damaged', required=True, help='Folder for damaged CSV outputs')
    args = parser.parse_args()

    main(
        input_dct_path=Path(args.input),
        damaged_csv_path=Path(args.damaged),
        output_curve_path=Path(args.output)
    )
