
import numpy as np

from model.data_models import FrameCapacity
from model.enums import Direction, ElementType
from src.frame.regular_frame import RegularFrame
from src.subassembly import SubassemblyFactory, SubHierarchy

# Usefull constants
G = 9.81

def mixed_sidesway_low_yielding(
    sub_factory: SubassemblyFactory,
    frame: RegularFrame,
    direction: Direction=Direction.Positive) -> FrameCapacity:
    """
    Computes the mixed sidesway of a frame considering a lower yielding

    Args:
        sub_factory (SubassemblyFactory): object that handles the subassembly creation
        frame (RegularFrame): Frame data
        direction (Direction, optional): Direction of push. Defaults to Direction.Positive.

    Returns:
        dict: capacity curve of the building
    """
    sub_capacities: dict[int, SubHierarchy] = {}

    # Base columns
    for vertical in range(frame.verticals):
        subassembly_id = frame.get_node_id(
                floor=0,
                vertical=vertical
            )
        subassembly = sub_factory.get_subassembly(
            subassembly_id
        )

        assert subassembly.above_column is not None
        # moment rotation
        column_mom_rot = subassembly.above_column.moment_rotation(
            direction=direction,
            axial=subassembly.axial
        )
        sub_capacities[subassembly_id] = SubHierarchy(
            beam_eq=column_mom_rot.mom_c,
            rot_y=column_mom_rot.rot_y,
            rot_c=column_mom_rot.rot_c,
            weakest=ElementType.Column
        )

    # Subassemblies
    for sub_id in range(frame.verticals, frame.get_node_count()):
        # get the subassembly
        subassembly = sub_factory.get_subassembly(
            sub_id
        )
        # get the hierarchy
        sub_capacities[sub_id] = subassembly.get_hierarchy(direction=direction)

    # finds the rotations
    yielding_frame_rotation = min([sub_data.rot_y for sub_data in sub_capacities.values()])

    # scale the capacity of each
    updated_moments = {}
    for sub_id, sub_data in sub_capacities.items():
        updated_moments[sub_id] = yielding_frame_rotation / sub_data.rot_y * sub_data.beam_eq

    # Ultimate
    delta_axials = np.zeros(frame.get_node_count())

    for sub_id, capacity in sub_capacities.items():

        if sub_id < frame.verticals:
            continue

        subassembly = sub_factory.get_subassembly(sub_id)
        if subassembly.left_beam is not None:
            delta_axials[sub_id] += (
                direction * (sub_capacities[sub_id - 1].beam_eq + capacity.beam_eq)
                / subassembly.left_beam.get_element_lenght()
            )

        if subassembly.right_beam is not None:
            delta_axials[sub_id] -= (
                direction * (sub_capacities[sub_id + 1].beam_eq + capacity.beam_eq)
                / subassembly.right_beam.get_element_lenght()
            )

    base_delta_axials_ultimate = [sum(delta_axials[i::frame.verticals]) for i in range(frame.verticals)]

    overturning_moment_ultimate = direction * sum(
            delta_axial * length
            for delta_axial, length in zip(base_delta_axials_ultimate, frame.get_lengths())
        ) + sum(sub_capacities[sub_id].beam_eq for sub_id in range(frame.verticals))

    # Yielding
    delta_axials = np.zeros(frame.get_node_count())

    for sub_id, capacity in sub_capacities.items():

        if sub_id <= frame.verticals:
            continue

        subassembly = sub_factory.get_subassembly(sub_id)
        if subassembly.left_beam is not None:
            delta_axials[sub_id] += (
                direction * (updated_moments[sub_id - 1] + updated_moments[sub_id])
                / subassembly.left_beam.get_element_lenght()
            )

        if subassembly.right_beam is not None:
            delta_axials[sub_id] -= (
                direction * (updated_moments[sub_id + 1] + updated_moments[sub_id])
                / subassembly.right_beam.get_element_lenght()
            )


    base_delta_axials_yielding = [sum(delta_axials[i::frame.verticals]) for i in range(frame.verticals)]

    overturning_moment_yielding = direction * sum(
            delta_axial * length
            for delta_axial, length in zip(base_delta_axials_yielding, frame.get_lengths())
        ) + sum(updated_moments[sub_id] for sub_id in range(frame.verticals))

    # Ultimate rotation
    ultimate_frame_rotation = min([sub_data.rot_c for sub_data in sub_capacities.values()])

    capacity = {
        'name' : 'Mixed Sidesway Yielding',
        'mass' : frame.get_effective_mass(),
        'base_shear' : [
            overturning_moment_yielding / frame.forces_effective_height,
            overturning_moment_ultimate / frame.forces_effective_height
        ],
        'disp' : [
            yielding_frame_rotation * frame.forces_effective_height,
            ultimate_frame_rotation * frame.forces_effective_height
        ]
    }
    return FrameCapacity(**capacity)


def mixed_sidesway_sub_stiff(
    sub_factory: SubassemblyFactory,
    frame: RegularFrame,
    direction: Direction=Direction.Positive) -> FrameCapacity:
    """
    Computes the mixed sidesway considering subassembley stiffness

    Args:
        sub_factory (SubassemblyFactory): object that handles the subassembly creation
        frame (RegularFrame): Frame data
        direction (Direction, optional): Direction of push. Defaults to Direction.Positive.

    Returns:
        dict: capacity curve of the building
    """
    sub_capacities: dict[int, SubHierarchy] = {}
    sub_stiffnesses: dict[int, float] = {}
    # Columns
    for vertical in range(frame.verticals):
        subassembly_id = frame.get_node_id(
                floor=0,
                vertical=vertical
            )
        subassembly = sub_factory.get_subassembly(
            subassembly_id
        )

        assert subassembly.above_column is not None
        # moment rotation
        column_mom_rot = subassembly.above_column.moment_rotation(
            direction=direction,
            axial=subassembly.axial
        )
        sub_capacities[subassembly_id] = SubHierarchy(
            beam_eq=column_mom_rot.mom_c,
            rot_y=column_mom_rot.rot_y,
            rot_c=column_mom_rot.rot_c,
            weakest=ElementType.Column
        )
        sub_stiffnesses[subassembly_id] = column_mom_rot.mom_y / column_mom_rot.rot_y

    # Subassemblies
    for sub_id in range(frame.verticals, frame.get_node_count()):
        subassembly = sub_factory.get_subassembly(
            sub_id
        )

        sub_capacities[sub_id] = subassembly.get_hierarchy(direction=direction)
        sub_stiffnesses[sub_id] = subassembly.get_stiffness(direction=direction)

    # finds the rotations
    updated_yielding: dict[int, float] = {}
    for sub_id, sub_capacity in sub_capacities.items():
        # Skip base columns
        if sub_id < frame.verticals:
            continue
        # Calculate new yielding
        updated_yielding[sub_id] = sub_capacity.beam_eq/ sub_stiffnesses[sub_id]

    # Yielding of base columns
    base_yielding = min(sub_capacities[sub_id].rot_y for sub_id in range(frame.verticals))
    # Yielding of subs
    top_yield = min(updated_yielding[sub_id] for sub_id in range(frame.verticals, frame.get_node_count()))

    new_yielding = min(base_yielding, top_yield)

    # Updates Moments
    updated_moments = {}
    for sub_id, sub_data in sub_capacities.items():
        if sub_id < frame.verticals:
            updated_moments[sub_id] = new_yielding / sub_data.rot_y * sub_data.beam_eq
            continue

        updated_moments[sub_id] = new_yielding * sub_stiffnesses[sub_id]

    # print(
    #     [sub_data['new_yielding']
    #     if sub_id >= frame.verticals else 0
    #     for sub_id, sub_data in enumerate(sub_capacities)]
    #     )

    # Ultimate
    delta_axials = np.zeros(frame.get_node_count())

    for sub_id, capacity in sub_capacities.items():

        if sub_id < frame.verticals:
            continue

        subassembly = sub_factory.get_subassembly(sub_id)
        if subassembly.left_beam is not None:
            delta_axials[sub_id] += (
                direction * (sub_capacities[sub_id - 1].beam_eq + capacity.beam_eq)
                / subassembly.left_beam.get_element_lenght()
            )

        if subassembly.right_beam is not None:
            delta_axials[sub_id] -= (
                direction * (sub_capacities[sub_id + 1].beam_eq + capacity.beam_eq)
                / subassembly.right_beam.get_element_lenght()
            )

    base_delta_axials_ultimate = [sum(delta_axials[i::frame.verticals]) for i in range(frame.verticals)]

    overturning_moment_ultimate = direction * sum(
            delta_axial * length
            for delta_axial, length in zip(base_delta_axials_ultimate, frame.get_lengths())
        ) + sum(sub_capacities[sub_id].beam_eq for sub_id in range(frame.verticals))

    # Yielding
    delta_axials = np.zeros(frame.get_node_count())

    for sub_id, capacity in enumerate(sub_capacities):

        if sub_id <= frame.verticals:
            continue

        subassembly = sub_factory.get_subassembly(sub_id)
        if subassembly.left_beam is not None:
            delta_axials[sub_id] += (
                direction * (updated_moments[sub_id - 1] + updated_moments[sub_id])
                / subassembly.left_beam.get_element_lenght()
            )

        if subassembly.right_beam is not None:
            delta_axials[sub_id] -= (
                direction * (updated_moments[sub_id + 1] + updated_moments[sub_id])
                / subassembly.right_beam.get_element_lenght()
            )


    base_delta_axials_yielding = [sum(delta_axials[i::frame.verticals]) for i in range(frame.verticals)]

    overturning_moment_yielding = direction * sum(
            delta_axial * length
            for delta_axial, length in zip(base_delta_axials_yielding, frame.get_lengths())
        ) + sum(updated_moments[sub_id] for sub_id in range(frame.verticals))

    # Ultimate rotation
    ultimate_frame_rotation = min([sub_data.rot_c for sub_data in sub_capacities.values()])

    capacity = {
        'name' : 'Mixed Sidesway Yielding',
        'mass' : frame.get_effective_mass(),
        'base_shear' : [
            0,
            overturning_moment_yielding / frame.forces_effective_height,
            overturning_moment_ultimate / frame.forces_effective_height
        ],
        'disp' : [
            0,
            new_yielding * frame.forces_effective_height,
            ultimate_frame_rotation * frame.forces_effective_height
        ]
    }
    return FrameCapacity(**capacity)
