import math
import numpy as np
from functools import cache
from typing import List

from model.validation.section_model import BasicSectionInput
from model.enums import Direction
from src.concrete import Concrete
from src.steel.steel import Steel  
from src.sections.section import Section

class BasicSection(Section):

    def __init__(self, 
                 section_data: BasicSectionInput, 
                 concrete: Concrete, 
                 steel: Steel)-> None:
        """
        Defines an object that contains section data
        """
        self.__section_data = section_data
        self.__concrete = concrete
        self.__steel = steel

    def moment_curvature(self, direction: Direction, axial: float):
        """
        Computes the yielding point and ultimate point of moment curvature
        """
        return analytic_coment_curvature(
            section_data=self.__section_data,
            concrete=self.__concrete,
            steel=self.__steel,
            direction=direction,
            axial=round(axial, ndigits=2)
            )
    
    # def domain_MN(self, axial: float) -> float:
    #     print('not coded yet')
    def domain_MN(self, axial: List[float], direction: Direction = Direction.Positive) -> List[float]:
        """
        Computes the MN domain of the section
        """
        return four_points_MN_domain(
            section_data=self.__section_data,
            concrete=self.__concrete,
            steel=self.__steel,
            axial=axial,
            direction=direction
        )

    def shear_capacity(self, L: float, axial: float = 0.) -> dict:
        """
        Computes the shear capacity of the section
        """
        return shear_NZSEE2017(
            section_data=self.__section_data,
            concrete=self.__concrete,
            steel=self.__steel,
            L=round(L, ndigits=2),
            axial=round(axial, ndigits=2)
            )
    
    @cache
    def plastic_hinge_length(self, L: float) -> float:
        k_factor = min(
            0.08,
            0.2*(self.__steel.fu/self.__steel.fy - 1)
        )
        strain_penetration = 0.022 * self.__steel.fy * 10**-3 * self.__section_data.eq_bar_diameter
        return (k_factor * L/2 + strain_penetration)
    
    def get_height(self) -> float:
        """
        Returns the section height
        """
        return self.__section_data.h
    
    def get_section_data(self) -> BasicSectionInput:
        """
        Returns the validated input data
        """
        return self.__section_data

    def get_concrete(self) -> Concrete:
        """
        Returns the concrete material
        """
        return self.__concrete
    
    def get_steel(self) -> Steel:
        """
        Returns the steel material
        """
        return self.__steel

    def __str__(self) -> str:
        return f"""
        BasicSection Object
        section id      : {self.__section_data.id}
        h               : {self.__section_data.h}
        b               : {self.__section_data.b}
        cover           : {self.__section_data.cover} 
        As              : {self.__section_data.As} 
        As1             : {self.__section_data.As1}
        eq_bar_diameter : {self.__section_data.eq_bar_diameter}
        s               : {self.__section_data.s}
        """

# -----------------------------------------------------
# Moment Curvatue algotirhms
# -----------------------------------------------------

@cache
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
        0.5 * concrete.E * section_data.b * reinforcement_depth[1] + steel.E * reinforcement_area[0] * (1 - reinforcement_depth[0]/reinforcement_depth[1]),
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

    moment_curvature['yielding'] = {
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
    
# -----------------------------------------------------
# Shear Capacity Alghoritms
# -----------------------------------------------------

@cache
def shear_NZSEE2017(section_data: BasicSectionInput, concrete: Concrete, steel: Steel, L: float, axial: float = 0.):
    """
    Shear capacity model provided by NZSEE2017
    """
    section_depth = section_data.h - section_data.cover

    # concrete contribution
    alpha = min(
        1.5,
        max(
            1,
            3 - L/section_data.h
        )
    )

    beta = min(
        1,
        0.5 + 20 * (section_data.As + section_data.As1) / (section_data.b * section_data.h)
    )

    gamma = np.array([0.29, 0.05])

    #dubbi sull'ordine di grandezza
    shear_concrete = gamma * alpha * beta * 0.8 * section_depth * section_data.b * math.sqrt(concrete.fc * 10**-3) * 10**3

    # steel contribution
    shear_steel = section_data.Ast * steel.fy * section_depth / section_data.s

    # axial contribution
    indicative_neutral_axis = 0.15 * section_data.h       # momentary
    shear_axial = axial * (section_data.h - indicative_neutral_axis) / L

    # total shear capacity
    shear_capacity = (shear_concrete + shear_axial + shear_steel) * 0.85

    return {
        'curvature_ductility' : (3, 15),
        'shear_capacity' : tuple(shear_capacity)
    }

# -----------------------------------------------------
# MN Domains Algorithms
# -----------------------------------------------------

def four_points_MN_domain(section_data: BasicSectionInput, concrete: Concrete, steel: Steel, axial: List[float], direction: Direction = Direction.Positive) -> List[float]:

    @cache
    def __compute_domain(section_data: BasicSectionInput, concrete: Concrete, steel: Steel, direction: Direction = Direction.Positive) -> dict:
        """
        Computes the four points of the domain
        """
        if direction == Direction.Positive:
            reinforcement_area = (section_data.As, section_data.As1)
        else:
            reinforcement_area = (section_data.As1, section_data.As)

        # Point A
        axial_A = -steel.fy * sum(reinforcement_area)
        moment_A = steel.fy * (reinforcement_area[1] - reinforcement_area[0]) * (section_data.h / 2 - section_data.cover)

        # Point B
        neutral_axis = (section_data.h - section_data.cover) * concrete.epsilon_u / (concrete.epsilon_u + 10**-2)
        epsilon_steel_top = concrete.epsilon_u/neutral_axis * (neutral_axis - section_data.cover)

        axial_B = (
            neutral_axis * 0.8 * section_data.b * concrete.fc 
            + reinforcement_area[0] * min(steel.E * epsilon_steel_top, steel.fy) 
            - reinforcement_area[1] * steel.fy
            )
        moment_B = (
            neutral_axis * 0.8 * section_data.b * concrete.fc * (section_data.h/2 - 0.4 * neutral_axis) 
            + reinforcement_area[0] * min(steel.E * epsilon_steel_top, steel.fy) * (section_data.h/2 - section_data.cover)
            + reinforcement_area[1] * steel.fy * (section_data.h/2 - section_data.cover)
        )

        # Point C
        neutral_axis = (section_data.h - section_data.cover) * concrete.epsilon_u / (concrete.epsilon_u + steel.epsilon_y)
        epsilon_steel_top = concrete.epsilon_u/neutral_axis * (neutral_axis - section_data.cover)

        axial_C = (
            neutral_axis * 0.8 * section_data.b * concrete.fc 
            + reinforcement_area[0] * min(steel.E * epsilon_steel_top, steel.fy) 
            - reinforcement_area[1] * steel.fy
            )
        moment_C = (
            neutral_axis * 0.8 * section_data.b * concrete.fc * (section_data.h/2 - 0.4 * neutral_axis) 
            + reinforcement_area[0] * min(steel.E * epsilon_steel_top, steel.fy) * (section_data.h/2 - section_data.cover)
            + reinforcement_area[1] * steel.fy * (section_data.h/2 - section_data.cover)
        )

        # Point D
        axial_D = section_data.b * section_data.h * concrete.fc - axial_A
        moment_D = -moment_A 

        return {
            'moment' : (
                moment_A,
                moment_B,
                moment_C,
                moment_D
            ),
            'axial' : (
                axial_A,
                axial_B,
                axial_C,
                axial_D
            )
        }

    domain = __compute_domain(
        section_data=section_data,
        concrete=concrete,
        steel=steel
    )

    return list(
        np.interp(
            x=axial, 
            xp=domain['axial'],
            fp=domain['moment'],
            left=0,
            right=0
            )
        )




