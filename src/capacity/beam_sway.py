from model.global_constants import G
from src.capacity.capacity import Capacity
from model.enums import Direction
from src.frame.regular_frame import RegularFrame
from src.subassembly import SubassemblyFactory

from itertools import product
import numpy as np

def beam_sidesway(
    sub_factory: SubassemblyFactory, 
    frame: RegularFrame, 
    direction: Direction=Direction.Positive) -> Capacity:
    """
    Computes the beam sidesway of a frame

    :params sub_factory: Subasssembly factory of a given frame

    :params frame: the frame data

    :params direction: positive is considered left to right
    """
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
    
    # Beams
    delta_axials = np.zeros((frame.verticals, frame.floors))
    yielding_rotations = list()
    ultimate_rotations = list()
    for vertical, floor in product(range(frame.verticals),range(frame.floors)):
        subassembly = sub_factory.get_subassembly(
            frame.get_node_id(
                floor=floor + 1,
                vertical=vertical
            )
        )

        if subassembly.left_beam is not None:
            moment_rotations = {
                'positive' : subassembly.left_beam.moment_rotation(
                    direction=Direction.Positive,
                    consider_shear_iteraction=False
                ),
                'negative' : subassembly.left_beam.moment_rotation(
                    direction=Direction.Negative,
                    consider_shear_iteraction=False
                )
            }
            delta_axials[vertical][floor] += direction * sum(
                moment_rotation['moment'][-1] for moment_rotation in moment_rotations.values()
                )/subassembly.left_beam.get_element_lenght()

            for moment_rotation in moment_rotations.values():
                yielding_rotations.append(moment_rotation['rotation'][0])
                ultimate_rotations.append(moment_rotation['rotation'][-1])

        if subassembly.right_beam is not None:
            moment_rotations = {
                'positive' : subassembly.right_beam.moment_rotation(
                    direction=Direction.Positive,
                    consider_shear_iteraction=False
                ),
                'negative' : subassembly.right_beam.moment_rotation(
                    direction=Direction.Negative,
                    consider_shear_iteraction=False
                )
            }
            delta_axials[vertical][floor] -= direction * sum(
                moment_rotation['moment'][-1] for moment_rotation in moment_rotations.values()
                )/subassembly.right_beam.get_element_lenght()
            
            for moment_rotation in moment_rotations.values():
                yielding_rotations.append(moment_rotation['rotation'][0])
                ultimate_rotations.append(moment_rotation['rotation'][-1])

    base_delta_axials = [sum(delta_axial_vertical) for delta_axial_vertical in delta_axials]
    overturning_moment = direction * sum(
            delta_axial * length 
            for delta_axial, length in zip(base_delta_axials, frame.get_lengths())
        ) + sum(column_moment_capacity)
    
    capacity = {
        'name' : 'Beam Sidesway',
        'base_shear' : overturning_moment / frame.forces_effective_height,
        'acc_capacity' : overturning_moment / frame.forces_effective_height / frame.get_effective_mass() / G,
        'yielding' : min(yielding_rotations) * frame.forces_effective_height,
        'ultimate' : min(ultimate_rotations) * frame.forces_effective_height
    }
    return Capacity(**capacity)


