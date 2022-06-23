from model.enums import Direction
from src.frame.regular_frame import RegularFrame
from src.subassembly import SubassemblyFactory

from itertools import product
import numpy as np

def mixed_sidesway(
    sub_factory: SubassemblyFactory, 
    frame: RegularFrame, 
    direction: Direction=Direction.Positive) -> dict:
    """
    Computes the mixed sidesway of a frame

    :params sub_factory: Subasssembly factory of a given frame

    :params frame: the frame data

    :params direction: positive is considered left to right
    """
    yielding_rotations = list()
    ultimate_rotations = list()
    # Columns
    column_moment_capacity = list()
    for vertical in range(frame.verticals):

        subassembly = sub_factory.get_subassembly(
            frame.get_node_id(
                floor=0,
                vertical=vertical
            )
        )
        
        column_moment_capacity.append(
            subassembly.above_column.moment_rotation(
                direction=direction,
                axial=subassembly.axial
            )['moment'][-1]
        )
        yielding_rotations.append(
            subassembly.above_column.moment_rotation(
                direction=direction,
                axial=subassembly.axial
            )['rotation'][0] 
        )
        ultimate_rotations.append(
            subassembly.above_column.moment_rotation(
                direction=direction,
                axial=subassembly.axial
            )['rotation'][-1] 
        )
    
    # Subassemblies
    delta_axials = np.zeros((frame.verticals, frame.floors))

    for vertical, floor in product(range(frame.verticals),range(frame.floors)):
        subassembly = sub_factory.get_subassembly(
            frame.get_node_id(
                floor=floor + 1,
                vertical=vertical
            )
        )
        yielding_rotations.append(
            subassembly.get_hierarchy(direction=direction)['rotation_yielding']
        )
        ultimate_rotations.append(
            subassembly.get_hierarchy(direction=direction)['rotation_ultimate']
        )

        if subassembly.left_beam is not None:
            left_sub_moment = sub_factory.get_subassembly(
                frame.get_node_id(
                    floor=floor + 1,
                    vertical=vertical - 1
                )
            ).get_hierarchy(direction=direction)['beam_equivalent']

            delta_axials[vertical][floor] += (
                direction 
                * (left_sub_moment + subassembly.get_hierarchy(direction=direction)['beam_equivalent'])
                / subassembly.left_beam.get_element_lenght())

        if subassembly.right_beam is not None:
            right_sub_moment = sub_factory.get_subassembly(
                frame.get_node_id(
                    floor=floor + 1,
                    vertical=vertical + 1
                )
            ).get_hierarchy(direction=direction)['beam_equivalent']

            delta_axials[vertical][floor] -= (
                direction 
                * (right_sub_moment + subassembly.get_hierarchy(direction=direction)['beam_equivalent'])
                / subassembly.right_beam.get_element_lenght())

    H_eff = 2/3 * frame.get_heights()[-1]
    base_delta_axials = [sum(delta_axial_vertical) for delta_axial_vertical in delta_axials]
    overturning_moment = direction * sum(
            delta_axial * length 
            for delta_axial, length in zip(base_delta_axials, frame.get_lengths())
        ) + sum(column_moment_capacity)
    
    return {
        'base_shear' : overturning_moment / H_eff,
        'yielding' : min(yielding_rotations) * H_eff,
        'ultimate' : min(ultimate_rotations) * H_eff
    }


