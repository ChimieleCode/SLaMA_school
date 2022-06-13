import numpy as np

from model.validation.section_model import BasicSectionInput
from src.concrete.concrete import Concrete
from src.steel.steel import Steel
from model.enums import Direction

def analytic_coment_curvature(section_data: BasicSectionInput, 
                              concrete: Concrete, 
                              steel: Steel,
                              direction: Direction = Direction.Positive,
                              axial: float = 0) -> dict:
    """
    Computes the moment curvature of a BasicSection using analytical formulation
    """
    # if direction is negative, swaps the top and bottom reinfocement
    if direction == Direction.Positive:
        # reinforcement_area (As_top, As_bot)
        reinforcement_area = (section_data.As, section_data.As1)
    else:
        # reinforcement_area (As_top, As_bot)
        reinforcement_area = (section_data.As1, section_data.As)
    
    moment_curvature = dict()
    
    reinforcement_depth = (section_data.cover, section_data.h - section_data.cover)

    # yielding point, top epsilon is positive
    epsilon_c_top = max(np.roots([
        0.5 * concrete.E * section_data.b * reinforcement_depth[1]+ steel.E * reinforcement_area[0] * (1 - reinforcement_depth[0]/reinforcement_depth[1]),
        steel.E * reinforcement_area[0] * -steel.epsilon_y * (2 * reinforcement_depth[0]/reinforcement_depth[1]- 1) - reinforcement_area[1] * steel.fy - axial,
        -steel.epsilon_y * (axial + reinforcement_area[1] * steel.fy + steel.E * reinforcement_area[0] * steel.epsilon_y * reinforcement_depth[0]/reinforcement_depth[1])
        ]))

    curvature = (epsilon_c_top + steel.epsilon_y) / reinforcement_depth[1]
    neutral_axis_depth = reinforcement_depth[1] * epsilon_c_top / (epsilon_c_top + steel.epsilon_y)

    epsilon_steel_top = curvature * (neutral_axis_depth - section_data.cover)
    steel_tension = (epsilon_steel_top * steel.E, -steel.fy)
    steel_force = tuple(tension * area for tension, area in zip(steel_tension, reinforcement_area))
    steel_moment = tuple(force * (section_data.h/2 - depth) for force, depth in zip(steel_force, reinforcement_depth))

    concrete_moment = 0.5 * concrete.E * epsilon_c_top * section_data.b * neutral_axis_depth * (section_data.h/2 - neutral_axis_depth/3)

    moment_curvature['yield'] = {
        'moment' : sum(steel_moment) + concrete_moment,
        'curvature' : curvature 
    }
    
    # ultimate point, bottom epsilon is negative
    epsilon_steel_bot = min(np.roots([
        -steel.E * reinforcement_area[0] * reinforcement_depth[0]/reinforcement_depth[1],
        axial + steel.fy * reinforcement_area[1] + steel.E * reinforcement_area[0] * concrete.epsilon_u * (2 * reinforcement_depth[0]/reinforcement_depth[1] - 1),
        (0.8 * concrete.fc * section_data.b * reinforcement_depth[1] + steel.E * reinforcement_area[0] * concrete.epsilon_u * (1 - reinforcement_depth[0]/reinforcement_depth[1]) - steel.fy * reinforcement_area[1] - axial) * concrete.epsilon_u
    ]))

    curvature = (concrete.epsilon_u - epsilon_steel_bot) / reinforcement_depth[1]
    neutral_axis_depth = reinforcement_depth[1] * concrete.epsilon_u / (concrete.epsilon_u - epsilon_steel_bot)
    epsilon_steel_top = curvature * (neutral_axis_depth - section_data.cover)
    # if top steel yields
    if epsilon_steel_top > steel.epsilon_y:
        epsilon_steel_bot = concrete.epsilon_u * (0.8 * concrete.fc * section_data.b * reinforcement_depth[1] + steel.fy * (reinforcement_area[0] - reinforcement_area[1]) - axial) / (steel.fy * (reinforcement_area[0] - reinforcement_area[1]) - axial)
        print(epsilon_steel_bot)
        curvature = (concrete.epsilon_u - epsilon_steel_bot) / reinforcement_depth[1]
        neutral_axis_depth = reinforcement_depth[1] * concrete.epsilon_u / (concrete.epsilon_u - epsilon_steel_bot)
        steel_tension = (steel.fy, -steel.fy)
    else: 
        steel_tension = (epsilon_steel_top * steel.E, -steel.fy)

    steel_force = tuple(tension * area for tension, area in zip(steel_tension, reinforcement_area))
    steel_moment = tuple(force * (section_data.h/2 - depth) for force, depth in zip(steel_force, reinforcement_depth))

    concrete_moment = 0.8 * concrete.fc * section_data.b * neutral_axis_depth * (section_data.h/2 - 0.4 * neutral_axis_depth)
    
    moment_curvature['ultimate'] = {
        'moment' : sum(steel_moment) + concrete_moment,
        'curvature' : curvature 
    }

    return moment_curvature


    

