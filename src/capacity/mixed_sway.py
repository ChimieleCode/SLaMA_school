from model.enums import Direction
from model.global_constants import G
from src.frame.regular_frame import RegularFrame
from src.subassembly import SubassemblyFactory
from src.capacity.capacity import Capacity

from itertools import product
import numpy as np

def mixed_sidesway(
    sub_factory: SubassemblyFactory, 
    frame: RegularFrame, 
    direction: Direction=Direction.Positive) -> Capacity:
    """
    Computes the mixed sidesway of a frame

    Args:
        sub_factory (SubassemblyFactory): object that handles the subassembly creation 
        frame (RegularFrame): Frame data
        direction (Direction, optional): Direction of push. Defaults to Direction.Positive.

    Returns:
        Capacity: capacity curve of the building
    """
    sub_capacities = [0] * frame.get_node_count()
    for vertical in range(frame.verticals):
        subassembly_id = frame.get_node_id(
                floor=0,
                vertical=vertical
            )
        subassembly = sub_factory.get_subassembly(
            subassembly_id
        )
        
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
            )['rotation'][-1] 
        }
    
    # Subassemblies
    for sub_id in range(frame.verticals, frame.get_node_count()):
        subassembly = sub_factory.get_subassembly(
            sub_id
        )

        sub_capacities[sub_id] = {
            'moment' : subassembly.get_hierarchy(direction=direction)['beam_equivalent'],
            'yielding' : subassembly.get_hierarchy(direction=direction)['rotation_yielding'],
            'ultimate' : subassembly.get_hierarchy(direction=direction)['rotation_ultimate'] 
        }

    delta_axials = np.zeros(frame.get_node_count())

    for sub_id, capacity in enumerate(sub_capacities):

        if sub_id <= frame.verticals:
            continue
        
        subassembly = sub_factory.get_subassembly(sub_id)
        if subassembly.left_beam is not None:
            delta_axials[sub_id] += (
                direction * (sub_capacities[sub_id - 1]['moment'] + capacity['moment'])
                / subassembly.left_beam.get_element_lenght()
            )

        if subassembly.right_beam is not None:
            delta_axials[sub_id] -= (
                direction * (sub_capacities[sub_id + 1]['moment'] + capacity['moment'])
                / subassembly.right_beam.get_element_lenght()
            )
        
    
    base_delta_axials = [sum(delta_axials[i::frame.verticals]) for i in range(frame.verticals)]

    overturning_moment = direction * sum(
            delta_axial * length 
            for delta_axial, length in zip(base_delta_axials, frame.get_lengths())
        ) + sum(sub_capacities[sub_id]['moment'] for sub_id in range(frame.verticals))
    
    ultimate_frame_rotation = min([sub_data['ultimate'] for sub_data in sub_capacities])
    yielding_frame_rotation = min([sub_data['yielding'] for sub_data in sub_capacities])
    
    capacity = {
        'name' : 'Mixed Sidesway',
        'base_shear' : overturning_moment / frame.forces_effective_height,
        'acc_capacity' : overturning_moment / frame.forces_effective_height / frame.get_effective_mass() / G,
        'yielding' : yielding_frame_rotation * frame.forces_effective_height,
        'ultimate' : ultimate_frame_rotation * frame.forces_effective_height
    }

    return Capacity(**capacity)




# Depricated
def depricated_mixed_sidesway(
    sub_factory: SubassemblyFactory, 
    frame: RegularFrame, 
    direction: Direction=Direction.Positive) -> Capacity:
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

    base_delta_axials = [sum(delta_axial_vertical) for delta_axial_vertical in delta_axials]
    overturning_moment = direction * sum(
            delta_axial * length 
            for delta_axial, length in zip(base_delta_axials, frame.get_lengths())
        ) + sum(column_moment_capacity)
    
    capacity = {
        'name' : 'Mixed Sidesway',
        'base_shear' : overturning_moment / frame.forces_effective_height,
        'acc_capacity' : overturning_moment / frame.forces_effective_height / frame.get_effective_mass() / G,
        'yielding' : min(yielding_rotations) * frame.forces_effective_height,
        'ultimate' : min(ultimate_rotations) * frame.forces_effective_height
    }

    return Capacity(**capacity)
