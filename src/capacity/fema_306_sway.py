import numpy as np

import model.config as config
from model.data_models import FrameCapacity
from model.enums import Direction, ElementType
from src.frame.regular_frame import RegularFrame
from src.reduction_values import LambdaValues
from src.subassembly import SubassemblyFactory, SubHierarchy
from src.utils import import_configuration

# Import config data
cfg : config.MNINTConfig
cfg = import_configuration(config.CONFIG_PATH, object_hook=config.MNINTConfig)


def damaged_sidesway_sub_stiff(
    sub_factory: SubassemblyFactory,
    frame: RegularFrame,
    lambda_values: dict[int, LambdaValues],
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
    # Get original values
    for vertical in range(frame.verticals):
        subassembly_id = frame.get_node_id(
                floor=0,
                vertical=vertical
            )
        subassembly = sub_factory.get_subassembly(
            subassembly_id
        )

        assert subassembly.above_column is not None
        # Moment rotation
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
    sub_stiffnesses: dict[int, float] = {}
    for sub_id in range(frame.verticals, frame.get_node_count()):
        subassembly = sub_factory.get_subassembly(
            sub_id
        )
        sub_stiffnesses[sub_id] = subassembly.get_stiffness(direction=direction)
        sub_capacities[sub_id] = subassembly.get_hierarchy(direction=direction)

    # Modify the subassembly capacities
    sub_stiffnesses_damaged: dict[int, float] = {}
    sub_capacities_damaged: dict[int, SubHierarchy] = {}
    for sub_id, sub_cap in sub_capacities.items():
        reduction_factors = lambda_values[sub_id]
        # Columns
        if sub_id < frame.verticals:
            # Damaged columns
            sub_capacities_damaged[sub_id] = SubHierarchy(
                beam_eq=sub_cap.beam_eq * reduction_factors.Q,
                rot_y=sub_cap.rot_y * (reduction_factors.Q/reduction_factors.K),
                rot_c=sub_cap.rot_c * reduction_factors.D,
                weakest=ElementType.Column
            )

        # Subs
        else:
            subassembly = sub_factory.get_subassembly(sub_id)
            # print(sub_equivalent_yielding)
            if sub_cap.weakest is ElementType.Joint:
                element_yielding = cfg.nodes.cracking_rotation
            else:
                element_yielding = sub_cap.rot_y

            # print(id, ductility, reduction_factors)
            sub_capacities_damaged[sub_id] = SubHierarchy(
                beam_eq=sub_cap.beam_eq * reduction_factors.Q,
                rot_y=sub_cap.rot_y * (reduction_factors.Q/reduction_factors.K),        # Check this
                rot_c=sub_cap.rot_c * reduction_factors.D,
                weakest=sub_cap.weakest
            )

            if sub_cap.weakest is ElementType.Joint:
                sub_weak_element_stiffness = subassembly.column_count * sub_cap.beam_eq / element_yielding
            else:
                sub_weak_element_stiffness = sub_cap.beam_eq / element_yielding

            stiffness_coefficent = (1 - reduction_factors.K) / reduction_factors.K
            sub_stiffnesses_damaged[sub_id] = (
                1 / sub_stiffnesses[sub_id] + subassembly.beam_count / sub_weak_element_stiffness * stiffness_coefficent
            )**-1


    # finds the rotations
    updated_yielding: dict[int, float] = {}
    for sub_id, sub_capacity in sub_capacities_damaged.items():
        if sub_id < frame.verticals:
            continue
        updated_yielding[sub_id] = sub_capacity.beam_eq / sub_stiffnesses_damaged[sub_id]

    base_yielding = min(sub_capacities_damaged[sub_id].rot_y for sub_id in range(frame.verticals))

    top_yield = min(updated_yielding[sub_id] for sub_id in range(frame.verticals, frame.get_node_count()))

    new_yielding = min(base_yielding, top_yield)

    # scale the capacity of each
    updated_moments: dict[int, float] = {}
    for sub_id, sub_data in sub_capacities_damaged.items():
        if sub_id < frame.verticals:
            updated_moments[sub_id] = new_yielding / sub_data.rot_y * sub_data.beam_eq
            continue

        updated_moments[sub_id] = new_yielding * sub_stiffnesses_damaged[sub_id]

    # Ultimate
    delta_axials = np.zeros(frame.get_node_count())

    for sub_id, capacity in sub_capacities_damaged.items():

        if sub_id < frame.verticals:
            continue

        subassembly = sub_factory.get_subassembly(sub_id)
        if subassembly.left_beam is not None:
            delta_axials[sub_id] += (
                direction * (sub_capacities_damaged[sub_id - 1].beam_eq + capacity.beam_eq)
                / subassembly.left_beam.get_element_lenght()
            )

        if subassembly.right_beam is not None:
            delta_axials[sub_id] -= (
                direction * (sub_capacities_damaged[sub_id + 1].beam_eq + capacity.beam_eq)
                / subassembly.right_beam.get_element_lenght()
            )


    base_delta_axials_ultimate = [sum(delta_axials[i::frame.verticals]) for i in range(frame.verticals)]

    overturning_moment_ultimate = direction * sum(
            delta_axial * length
            for delta_axial, length in zip(base_delta_axials_ultimate, frame.get_lengths())
        ) + sum(sub_capacities_damaged[sub_id].beam_eq for sub_id in range(frame.verticals))

    # Yielding
    delta_axials = np.zeros(frame.get_node_count())

    for sub_id, capacity in sub_capacities_damaged.items():

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
    ultimate_frame_rotation = min([sub_data.rot_c for sub_data in sub_capacities_damaged.values()])

    capacity = {
        'name' : 'Damaged Mixed Sidesway',
        'mass' : frame.get_effective_mass(),
        'base_shear' : [
            overturning_moment_yielding / frame.forces_effective_height,
            overturning_moment_ultimate / frame.forces_effective_height
        ],
        'disp' : [
            new_yielding * frame.forces_effective_height,
            ultimate_frame_rotation * frame.forces_effective_height
        ]
    }
    return FrameCapacity(**capacity)
