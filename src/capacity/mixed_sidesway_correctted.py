from model.enums import Direction
from model.global_constants import G
from src.frame.regular_frame import RegularFrame
from src.subassembly import SubassemblyFactory

import numpy as np

def mixed_sidesway_low_yielding(
    sub_factory: SubassemblyFactory, 
    frame: RegularFrame, 
    direction: Direction=Direction.Positive) -> dict:
    """
    Computes the mixed sidesway of a frame considering a lower yielding 

    Args:
        sub_factory (SubassemblyFactory): object that handles the subassembly creation 
        frame (RegularFrame): Frame data
        direction (Direction, optional): Direction of push. Defaults to Direction.Positive.

    Returns:
        dict: capacity curve of the building
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
    
    # finds the rotations
    yielding_frame_rotation = min([sub_data['yielding'] for sub_data in sub_capacities])

    # scale the capacity of each 
    for sub_data in sub_capacities:
        sub_data['updated_moment'] = yielding_frame_rotation / sub_data['yielding'] * sub_data['moment']
        
    # Ultimate
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
        
    
    base_delta_axials_ultimate = [sum(delta_axials[i::frame.verticals]) for i in range(frame.verticals)]

    overturning_moment_ultimate = direction * sum(
            delta_axial * length 
            for delta_axial, length in zip(base_delta_axials_ultimate, frame.get_lengths())
        ) + sum(sub_capacities[sub_id]['moment'] for sub_id in range(frame.verticals))
    
    # Yielding
    delta_axials = np.zeros(frame.get_node_count())

    for sub_id, capacity in enumerate(sub_capacities):

        if sub_id <= frame.verticals:
            continue
        
        subassembly = sub_factory.get_subassembly(sub_id)
        if subassembly.left_beam is not None:
            delta_axials[sub_id] += (
                direction * (sub_capacities[sub_id - 1]['updated_moment'] + capacity['updated_moment'])
                / subassembly.left_beam.get_element_lenght()
            )

        if subassembly.right_beam is not None:
            delta_axials[sub_id] -= (
                direction * (sub_capacities[sub_id + 1]['updated_moment'] + capacity['updated_moment'])
                / subassembly.right_beam.get_element_lenght()
            )
        
    
    base_delta_axials_yielding = [sum(delta_axials[i::frame.verticals]) for i in range(frame.verticals)]

    overturning_moment_yielding = direction * sum(
            delta_axial * length 
            for delta_axial, length in zip(base_delta_axials_yielding, frame.get_lengths())
        ) + sum(sub_capacities[sub_id]['updated_moment'] for sub_id in range(frame.verticals))
    
    # Ultimate rotation
    ultimate_frame_rotation = min([sub_data['ultimate'] for sub_data in sub_capacities])
    
    capacity = {
        'name' : 'Mixed Sidesway Low Yielding',
        'base_shear' : overturning_moment_ultimate / frame.forces_effective_height,
        'yielding_base_shear' : overturning_moment_yielding / frame.forces_effective_height,
        'acc_capacity' : overturning_moment_ultimate / frame.forces_effective_height / frame.get_effective_mass() / G,
        'yielding' : yielding_frame_rotation * frame.forces_effective_height,
        'ultimate' : ultimate_frame_rotation * frame.forces_effective_height
    }

    return capacity
