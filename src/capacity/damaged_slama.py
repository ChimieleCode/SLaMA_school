import numpy as np
import model.config as config

from model.enums import Direction, ElementType
from src.utils import import_configuration
from src.frame.regular_frame import RegularFrame
from src.subassembly import SubassemblyFactory
from model.data_models import FrameCapacity

import numpy as np

# Usefull constants
G = 9.81

# Import config data
cfg : config.MNINTConfig
cfg = import_configuration(config.CONFIG_PATH, object_hook=config.MNINTConfig)

# Modification factors formulas
def joint_mod_factors(ductility: float) -> dict:
    """
    Computes the reduction factors K, Q, res. drift given the ductility for a joint element

    Args:
        ductility (float): ductility value

    Returns:
        dict: correction factors for damaged element
    """
    # Stiffness only is modified
    return {
        'K' : ductility**-1 if ductility > 1 else 1,
        'Q' : 1,
        'res' : 0
    }

def element_mod_factors(ductility: float) -> dict:
    """
    Computes the reduction factors K, Q, res. drift given the ductility for a column or beam element

    Args:
        ductility (float): ductility value

    Returns:
        dict: correction factors for damaged element
    """
    # Di Ludovico et al. 2013
    # K   eq 13-14
    # Q   eq 22-23
    # res eq 29-30
    return {
        'K' : 1 - (1.07 - 0.98 * ductility**-0.8) if ductility > 0.9 else 1,
        'Q' : 1 - 0.03 * (ductility - 4) if ductility > 4 else 1,
        'res' : np.polyval([0.007, 0.3, 0], (ductility - 2)) if ductility > 2 else 0
    }

MOD_FACTORS_PLAIN_BARS = {
    ElementType.Joint : joint_mod_factors,
    ElementType.Beam : element_mod_factors,
    ElementType.LeftBeam : element_mod_factors,
    ElementType.RightBeam : element_mod_factors,
    ElementType.Column : element_mod_factors,
    ElementType.AboveColumn : element_mod_factors,
    ElementType.BelowColumn : element_mod_factors,
}


def damaged_sidesway_sub_stiff(
    sub_factory: SubassemblyFactory, 
    frame: RegularFrame, 
    drift: float,
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
            )['rotation'][-1],
            'element' : ElementType.Column
        }
    
    # Subassemblies
    for sub_id in range(frame.verticals, frame.get_node_count()):
        subassembly = sub_factory.get_subassembly(
            sub_id
        )

        sub_capacities[sub_id] = {
            'moment' : subassembly.get_hierarchy(direction=direction)['beam_equivalent'],
            'yielding' : subassembly.get_hierarchy(direction=direction)['rotation_yielding'],
            'ultimate' : subassembly.get_hierarchy(direction=direction)['rotation_ultimate'],
            'stiffness' : subassembly.get_stiffness(direction=direction),
            'element' : subassembly.get_hierarchy(direction=direction)['element'],
            'columns' : subassembly.column_count,
            'beams' : subassembly.beam_count
        }
    # Modify the subassembly capacities
    for id, subassembly in enumerate(sub_capacities):
        # Columns
        if id < frame.verticals:
            ductility = abs(drift) / subassembly['yielding']
            reduction_factors = MOD_FACTORS_PLAIN_BARS[subassembly['element']](ductility)

            # Damaged columns
            subassembly['moment'] = reduction_factors['Q'] * subassembly['moment']
            subassembly['yielding'] = subassembly['yielding'] * (reduction_factors['Q']/reduction_factors['K'])
            subassembly['ultimate'] = subassembly['ultimate'] - subassembly['yielding'] * reduction_factors['res']
        
        # Subs
        else:
            sub_equivalent_yielding = subassembly['moment'] / subassembly['stiffness']
            # print(sub_equivalent_yielding)
            if subassembly['element'] == ElementType.Joint:
                element_yielding = cfg.nodes.cracking_rotation
            else: 
                element_yielding = subassembly['yielding']

            # Considers the elastic deformation of other members in the subassembley
            ductility = (drift - sub_equivalent_yielding) / element_yielding + 1
            # print(drift, element_yielding)
            
            reduction_factors = MOD_FACTORS_PLAIN_BARS[subassembly['element']](ductility)
            # print(id, ductility, reduction_factors) 
            subassembly['ultimate'] = subassembly['ultimate'] - subassembly['yielding'] * reduction_factors['res']
            subassembly['moment'] = subassembly['moment'] * reduction_factors['Q']

            if subassembly['element'] == ElementType.Joint:
                sub_weak_element_stiffness = subassembly['columns'] * subassembly['moment'] / element_yielding
            else: 
                sub_weak_element_stiffness = subassembly['moment'] / element_yielding

            stiffness_coefficent = (1 - reduction_factors['K']) / reduction_factors['K']
            subassembly['stiffness'] = (1 / subassembly['stiffness'] 
                                        + subassembly['beams'] / sub_weak_element_stiffness * stiffness_coefficent)**-1

            # yielding_sub_rotation = subassembly['moment'] / subassembly['stiffness']
            # elastic_rotation = yielding_sub_rotation - subassembly['yielding']
            # element_drift = max(0, drift - elastic_rotation)
            # if subassembly['element'] == ElementType.Joint:
            #     ductility = abs(element_drift) / cfg.nodes.cracking_rotation
            # else:
            #     ductility = abs(element_drift) / subassembly['yielding']
            # reduction_factors = MOD_FACTORS_PLAIN_BARS[subassembly['element']](ductility)

            # sub_original_stiffness = subassembly['moment']/subassembly['yielding']
            # # Change moment
            # subassembly['moment'] = reduction_factors['Q'] * subassembly['moment']
            # # Use changed moment and original stiffness
            # subassembly['yielding'] = subassembly['moment'] / (sub_original_stiffness * reduction_factors['K'])
            # subassembly['ultimate'] = subassembly['ultimate'] - subassembly['yielding'] * reduction_factors['res']
            # # Updates subassembly stiffness
            # if subassembly['element'] == ElementType.Joint:
            #     sub_original_stiffness = subassembly['columns'] * sub_original_stiffness

            # subassembly['stiffness'] = (
            #     subassembly['beams']/(subassembly['moment']/subassembly['yielding'])
            #     - subassembly['beams']/sub_original_stiffness
            #     + 1/subassembly['stiffness']
            # )**-1

    # finds the rotations
    for sub_id, sub_capacity in enumerate(sub_capacities):
        if sub_id < frame.verticals:
            continue
        sub_capacity['new_yielding'] = sub_capacity['moment']/sub_capacity['stiffness']

    base_yielding = min(sub_capacities[sub_id]['yielding'] for sub_id in range(frame.verticals))

    top_yield = min(sub_capacities[sub_id]['new_yielding'] for sub_id in range(frame.verticals, frame.get_node_count()))

    new_yielding = min(base_yielding, top_yield)

    # scale the capacity of each 
    for sub_id, sub_data in enumerate(sub_capacities):
        if sub_id < frame.verticals:
            sub_data['updated_moment'] = new_yielding/sub_data['yielding'] * sub_data['moment']
            continue

        sub_data['updated_moment'] = new_yielding * sub_data['stiffness']
    
    # print(
    #     [sub_data['new_yielding'] 
    #     if sub_id >= frame.verticals else 0
    #     for sub_id, sub_data in enumerate(sub_capacities)]
    #     )

        
    # Ultimate
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




# Sway function depricated
def damaged_mixed_sidesway(
    sub_factory: SubassemblyFactory, 
    frame: RegularFrame, 
    drift: float,
    direction: Direction=Direction.Positive) -> FrameCapacity:
    """
    Computes the mixed sidesway of a frame

    Args:
        sub_factory (SubassemblyFactory): object that handles the subassembly creation 
        frame (RegularFrame): Frame data
        drift (float): peak drift of damage state
        direction (Direction, optional): Direction of push. Defaults to Direction.Positive.

    Returns:
        Capacity: capacity curve of the building
    """
    sub_capacities = [0] * frame.get_node_count()
    # Base Columns
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
            )['rotation'][-1],
            'element' : ElementType.Column
        }
    
    # Subassemblies
    for sub_id in range(frame.verticals, frame.get_node_count()):
        subassembly = sub_factory.get_subassembly(
            sub_id
        )

        sub_capacities[sub_id] = {
            'moment' : subassembly.get_hierarchy(direction=direction)['beam_equivalent'],
            'yielding' : subassembly.get_hierarchy(direction=direction)['rotation_yielding'],
            'ultimate' : subassembly.get_hierarchy(direction=direction)['rotation_ultimate'], 
            'element' : subassembly.get_hierarchy(direction=direction)['element']
        }

    # Modify the subassembly capacities
    for subassembly in sub_capacities:
        ductility = abs(drift) / subassembly['yielding']
        reduction_factors = MOD_FACTORS_PLAIN_BARS[subassembly['element']](ductility)

        # Change Subassembly Params
        subassembly['moment'] = reduction_factors['Q'] * subassembly['moment']
        subassembly['ultimate'] = subassembly['ultimate'] - subassembly['yielding'] * reduction_factors['res']
        subassembly['yielding'] = subassembly['yielding'] * (reduction_factors['Q'] / reduction_factors['K'])
    

    # Compute delta axials
    delta_axials = np.zeros(frame.get_node_count())

    for sub_id, capacity in enumerate(sub_capacities):
        # Skip Base Nodes
        if sub_id < frame.verticals:
            continue
        
        # Needed from topological info
        subassembly = sub_factory.get_subassembly(sub_id)

        # Shear from left beam if present
        if subassembly.left_beam is not None:
            delta_axials[sub_id] += (
                direction * (sub_capacities[sub_id - 1]['moment'] + capacity['moment'])
                / subassembly.left_beam.get_element_lenght()
            )

        # Shear from right beam if present
        if subassembly.right_beam is not None:
            delta_axials[sub_id] -= (
                direction * (sub_capacities[sub_id + 1]['moment'] + capacity['moment'])
                / subassembly.right_beam.get_element_lenght()
            )
    
    # Compute total delta axials for OTM
    base_delta_axials = [sum(delta_axials[i::frame.verticals]) for i in range(frame.verticals)]

    # Compute OTM using delta Axials
    overturning_moment = direction * sum(
            delta_axial * length 
            for delta_axial, length in zip(base_delta_axials, frame.get_lengths())
        ) + sum(sub_capacities[sub_id]['moment'] for sub_id in range(frame.verticals))
    
    # Define ultimate rotation as the lowest ultimate rortation of subassemblies
    ultimate_frame_rotation = min([sub_data['ultimate'] for sub_data in sub_capacities])
    # Define ultimate rotation as the lowest ultimate rortation of subassemblies
    yielding_frame_rotation = min([sub_data['yielding'] for sub_data in sub_capacities])

    if yielding_frame_rotation > ultimate_frame_rotation:
        print(drift, yielding_frame_rotation, ultimate_frame_rotation)
        raise AssertionError('yielding disp cannot be larger than ultimate disp')
        
    capacity = {
        'name' : 'Damaged Mixed Sidesway',
        'mass' : frame.get_effective_mass(),
        'base_shear' : [overturning_moment / frame.forces_effective_height] * 2,
        'disp' : [
            yielding_frame_rotation * frame.forces_effective_height,
            ultimate_frame_rotation * frame.forces_effective_height
        ]
    }
    return FrameCapacity(**capacity)