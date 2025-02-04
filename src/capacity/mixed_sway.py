from model.enums import Direction
from src.frame.regular_frame import RegularFrame
from src.subassembly import SubassemblyFactory
from model.data_models import FrameCapacity

from itertools import product
import numpy as np

# Usefull constants
G = 9.81

def mixed_sidesway(
    sub_factory: SubassemblyFactory,
    frame: RegularFrame,
    direction: Direction=Direction.Positive) -> FrameCapacity:
    """
    Computes the mixed sidesway of a frame

    Args:
        sub_factory (SubassemblyFactory): object that handles the subassembly creation
        frame (RegularFrame): Frame data
        direction (Direction, optional): Direction of push. Defaults to Direction.Positive.

    Returns:
        Capacity: capacity curve of the building
    """
    sub_capacities = [{}] * frame.get_node_count()
    for vertical in range(frame.verticals):
        subassembly_id = frame.get_node_id(
                floor=0,
                vertical=vertical
            )
        subassembly = sub_factory.get_subassembly(
            subassembly_id
        )
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
            ).rot_c
        }

    # Subassemblies
    for sub_id in range(frame.verticals, frame.get_node_count()):
        subassembly = sub_factory.get_subassembly(
            sub_id
        )

        sub_capacities[sub_id] = {
            'moment' : subassembly.get_hierarchy(direction=direction).beam_eq,
            'yielding' : subassembly.get_hierarchy(direction=direction).rot_y,
            'ultimate' : subassembly.get_hierarchy(direction=direction).rot_c
        }

    delta_axials = np.zeros(frame.get_node_count())

    for sub_id, capacity in enumerate(sub_capacities):

        if sub_id < frame.verticals:
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

    }
    return FrameCapacity(
        name='Mixed Sidesway',
        mass=frame.get_effective_mass(),
        base_shear=[overturning_moment / frame.forces_effective_height] * 2,
        disp=[
            yielding_frame_rotation * frame.forces_effective_height,
            ultimate_frame_rotation * frame.forces_effective_height
        ]
    )

