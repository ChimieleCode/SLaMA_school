from model.enums import Direction
from src.frame.regular_frame import RegularFrame
from src.subassembly import SubassemblyFactory

def column_sidesway(
    sub_factory: SubassemblyFactory, 
    frame: RegularFrame, 
    direction: Direction=Direction.Positive) -> dict:
    """
    Computes the column sidesway of a frame
    
    :params sub_factory: Subasssembly factory of a given frame

    :params frame: the frame data

    :params direction: positive is considered left to right
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
    return {
        'base_shear' : overturning_moment / H_eff,
        'yielding' : yielding_rotation * sub_factory.get_subassembly(0).above_column.get_element_lenght(),
        'ultimate' : ultimate_rotation * sub_factory.get_subassembly(0).above_column.get_element_lenght()
    }



