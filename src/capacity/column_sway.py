from model.enums import Direction
from src.frame.regular_frame import RegularFrame
from src.subassembly import SubassemblyFactory
from model.data_models import FrameCapacity

# Usefull constants
G = 9.81

def column_sidesway(
    sub_factory: SubassemblyFactory, 
    frame: RegularFrame, 
    direction: Direction=Direction.Positive) -> FrameCapacity:
    """
    Computes the column sidesway of a frame
    
    Args:
        sub_factory (SubassemblyFactory): Subassemblly factory of the given frame
        frame (RegularFrame): frame shared by subassembly_factory
        direction (Direction, optional): Direction of push. Defaults to Direction.Positive.

    Returns:
        FrameCapacity: capacity of the frame
    """
    column_moment_rotations = list()
    for i in range(frame.verticals):
        subassembly = sub_factory.get_subassembly(
            frame.get_node_id(
                floor=0,
                vertical=i
            )
        )
        column_moment_rotations.append(
            subassembly.above_column.moment_rotation(
                direction=direction,
                axial=subassembly.axial
            )
        )
    
    overturning_moment = sum(
        column_moment_rotation['moment'][-1] 
        for column_moment_rotation in column_moment_rotations
    )

    yielding_rotation = min(
        column_moment_rotation['rotation'][0] 
        for column_moment_rotation in column_moment_rotations
    )
    ultimate_rotation = min(
        column_moment_rotation['rotation'][-1] 
        for column_moment_rotation in column_moment_rotations
    )
    H_eff = 0.5 * frame.get_heights()[-1]
    
    capacity = {
        'name' : 'Column Sidesway',
        'mass' : frame.get_effective_mass(),
        'base_shear' : [overturning_moment / H_eff] * 2,
        'disp' : [
            yielding_rotation * sub_factory.get_subassembly(0).above_column.get_element_lenght(),
            ultimate_rotation * sub_factory.get_subassembly(0).above_column.get_element_lenght()
        ]
    }
    return FrameCapacity(**capacity)



