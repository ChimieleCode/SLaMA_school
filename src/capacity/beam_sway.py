from model.data_models import FrameCapacity
from model.enums import Direction
from src.frame.regular_frame import RegularFrame
from src.subassembly import SubassemblyFactory

from itertools import product
import numpy as np

# constants
G = 9.81

def beam_sidesway(
    sub_factory: SubassemblyFactory,
    frame: RegularFrame,
    direction: Direction=Direction.Positive) -> FrameCapacity:
    """
    Computes the beam sidesway of a frame

    Args:
        sub_factory (SubassemblyFactory): Subassemblly factory of the given frame
        frame (RegularFrame): frame shared by subassembly_factory
        direction (Direction, optional): Direction of push. Defaults to Direction.Positive.

    Returns:
        FrameCapacity: capacity of the frame
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

        assert subassembly.above_column is not None
        column_moment_capacity.append(
            subassembly.above_column.moment_rotation(
                direction=direction,
                axial=subassembly.axial
            ).mom_c
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
                moment_rotation.mom_c for moment_rotation in moment_rotations.values()
                )/subassembly.left_beam.get_element_lenght()

            for moment_rotation in moment_rotations.values():
                yielding_rotations.append(moment_rotation.rot_y)
                ultimate_rotations.append(moment_rotation.rot_c)

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
                moment_rotation.mom_c for moment_rotation in moment_rotations.values()
                )/subassembly.right_beam.get_element_lenght()

            for moment_rotation in moment_rotations.values():
                yielding_rotations.append(moment_rotation.rot_y)
                ultimate_rotations.append(moment_rotation.rot_c)

    base_delta_axials = [sum(delta_axial_vertical) for delta_axial_vertical in delta_axials]
    overturning_moment = direction * sum(
            delta_axial * length
            for delta_axial, length in zip(base_delta_axials, frame.get_lengths())
        ) + sum(column_moment_capacity)

    return FrameCapacity(
        name='Beam Sidesway',
        mass=frame.get_effective_mass(),
        base_shear=[overturning_moment / frame.forces_effective_height] * 2,
        disp=[
            min(yielding_rotations) * frame.forces_effective_height,
            min(ultimate_rotations) * frame.forces_effective_height
        ]
    )


