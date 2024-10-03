import math
import numpy as np
import model.config as config
from functools import cache
from typing import List

from model.validation.section_model import BasicSectionInput
from model.enums import Direction, SectionType
from src.concrete import Concrete
from src.steel.steel import Steel
from .section import MNDomain, Section, MomentCurvature, ShearEnvelope
from src.utils import import_configuration

# Import config data
cfg : config.MNINTConfig
cfg = import_configuration(config.CONFIG_PATH, object_hook=config.MNINTConfig)

class BasicSection(Section):

    def __init__(self,
                 section_data: BasicSectionInput,
                 concrete: Concrete,
                 steel: Steel,
                 section_type: SectionType) -> None:
        """
        Defines an object that contains section data
        """
        self.__section_data = section_data
        self.__concrete = concrete
        self.__steel = steel
        self.__section_type = section_type

    def moment_curvature(self, direction: Direction = Direction.Positive, axial: float = 0.) -> MomentCurvature:
        """
        Computes the yielding point and ultimate point of moment curvature
        """
        algs = {
            config.MomentCurvatureAlg.StressBlock : analytic_moment_curvature
        }
        return algs[cfg.element_settings.moment_curvature](
            section_data=self.__section_data,
            concrete=self.__concrete,
            steel=self.__steel,
            direction=direction,
            axial=round(axial, ndigits=2)
        )

    def domain_MN(self, axial: float, direction: Direction=Direction.Positive) -> float:
        """
        Computes the MN domain of the section
        """
        algs = {
            config.DomainMNAlg.FourPoints : four_points_MN_domain
        }
        domain = algs[cfg.element_settings.domain_mn](
            section_data=self.__section_data,
            concrete=self.__concrete,
            steel=self.__steel,
            direction=direction
        )

        return float(
            np.interp(
                x=axial,
                xp=domain.axial,
                fp=domain.moment,
                left=0,
                right=0
            )
        )

    def shear_capacity(self, L: float, axial: float = 0.) -> dict:
        """
        Computes the shear capacity of the section
        """
        algs = {
            config.ShearFormula.NTC2018 : NotImplemented,
            config.ShearFormula.NZSEE2017 : shear_NZSEE2017
        }
        return algs[cfg.element_settings.shear_formulation](
            section_data=self.__section_data,
            concrete=self.__concrete,
            steel=self.__steel,
            L=round(L, ndigits=2),
            axial=round(axial, ndigits=2)
        )

    @cache
    def plastic_hinge_length(self, L: float) -> float:
        """
        Formulation from C5 NZSEE2017
        """
        k_factor = min(
            0.08,
            0.2*(self.__steel.fu/self.__steel.fy - 1)
        )
        strain_penetration = 0.022 * self.__steel.fy * self.__section_data.eq_bar_diameter * 10**-6
        return (k_factor * L/2 + strain_penetration)

    def get_height(self) -> float:
        """
        Returns the section height
        """
        return self.__section_data.h

    def get_effective_width(self) -> float:
        """
        Returns the effective width of the section
        """
        return self.__section_data.b

    @cache
    def get_depth(self) -> float:
        return self.__section_data.h - self.__section_data.cover

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

    def get_section_type(self) -> SectionType:
        """
        Return section type
        """
        return self.__section_type

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
def analytic_moment_curvature(section_data: BasicSectionInput,
                              concrete: Concrete,
                              steel: Steel,
                              direction: Direction = Direction.Positive,
                              axial: float = 0) -> MomentCurvature:
    """
    Computes the moment curvature of a BasicSection using analytical formulation

    :params section_data: validated section data for a given section object

    :params concrete: concrete of the section

    :params steel: steel of the rebars

    :params direction: direction of bending (positive mean lower reinforcement is in tension)

    :params axial: axial stress acting on the section
    """
    # Unpack data for better clarity
    E_c = concrete.E
    ec_u = concrete.epsilon_u
    fc = concrete.fc

    b = section_data.b
    h = section_data.h
    cop = section_data.cover
    As_bot = section_data.As
    As_top = section_data.As1
    d_top = cop
    d_bot = h - cop

    E_s = steel.E
    ey_s = steel.epsilon_y
    fy_s = steel.fy

    # if direction is negative, swaps the top and bottom reinfocement
    if direction is Direction.Negative:
        As_top, As_bot = As_bot, As_top

    # Yelding point, top epsilon is positive
    ec_top = max(
        np.roots(
            [
                0.5 * E_c * b * d_bot + steel.E * As_top * (1 - d_top/d_bot),
                - ey_s * E_s * As_top * (2 * d_top/d_bot - 1) - As_bot * fy_s - axial,
                - ey_s * (axial + As_bot * fy_s + E_s * As_top * ey_s * d_top/d_top)
            ]
        )
    )

    curvature = (ec_top + ey_s) / d_bot
    n_axis_depth = d_bot * ec_top / (ec_top + ey_s)

    es_top = curvature * (n_axis_depth - cop)

    steel_stress_top = es_top * E_s
    steel_stress_bot = -fy_s

    steel_force_top = steel_stress_top * As_top
    steel_force_bot = steel_stress_bot * As_bot

    steel_moment = steel_force_top * (h/2 - d_top) + steel_force_bot * (h/2 - d_bot)
    concrete_moment = 0.5 * E_c * ec_top * b * n_axis_depth * (h/2 - n_axis_depth/3)

    moment_yielding = steel_moment + concrete_moment
    curvature_yielding = curvature

    # Capacity point, bottom epsilon is negative
    es_bot = min(
        np.roots(
            [
                -E_s * As_top * d_top/d_bot,
                axial + fy_s * As_bot + E_s * As_top * ec_u * (2 * d_top/d_bot - 1),
                (0.8 * fc * b * d_bot + E_s * As_top * ec_u * (1 - d_top/d_bot) - fy_s * As_bot - axial) * ec_u
            ]
        )
    )

    curvature = (ec_u - es_bot) / d_bot
    n_axis_depth = d_bot * ec_u / (ec_u - es_bot)
    es_top = curvature * (n_axis_depth - cop)

    # if top steel yields
    if es_top > ey_s:
        es_bot = ec_u * (0.8 * fc * b * d_bot + fy_s * (As_top - As_bot) - axial) / (fy_s * (As_top - As_bot) - axial)
        curvature = (ec_u - es_bot) / d_bot
        n_axis_depth = d_bot * ec_u / (ec_u - es_bot)
        steel_tension_top = fy_s
    else:
        steel_tension_top = es_top * E_s
    steel_tension_bot = -fy_s

    steel_force_top = steel_tension_top * As_top
    steel_force_bot = steel_tension_bot * As_bot

    steel_moment = steel_force_top * (h/2 - d_top) + steel_force_bot * (h/2 - d_bot)
    concrete_moment = 0.8 * fc * b * n_axis_depth * (h/2 - 0.4 * n_axis_depth)

    moment_capacity = steel_moment + concrete_moment
    curvature_capacity = curvature

    return MomentCurvature(
        mom_y=moment_yielding,
        mom_c=moment_capacity,
        phi_y=curvature_yielding,
        phi_c=curvature_capacity
    )

# -----------------------------------------------------
# Shear Capacity Alghoritms
# -----------------------------------------------------
@cache
def shear_NZSEE2017(section_data: BasicSectionInput,
                    concrete: Concrete,
                    steel: Steel,
                    L: float,
                    axial: float = 0.) -> ShearEnvelope:
    """
    Shear capacity model provided by NZSEE2017

    :params section_data: validated section data for a given section object

    :params concrete: concrete of the section

    :params steel: steel of the rebars

    :params L: length of the elemtn that contains the section

    :params axial: axial stress acting on the section
    """
    # Unpack data for better clarity
    fc = concrete.fc

    b = section_data.b
    h = section_data.h
    s = section_data.s          # stirups spacing
    cop = section_data.cover
    As_bot = section_data.As
    As_top = section_data.As1
    d_top = cop
    d_bot = h - cop

    fy_s = steel.fy

    section_depth = d_bot - d_top

    # concrete contribution
    alpha = min(
        1.5,
        max(
            1,
            3 - L/h
        )
    )
    beta = min(
        1,
        0.5 + 20 * (As_top + As_bot) / (b * h)
    )
    gamma = np.array([0.29, 0.05])

    shear_concrete = gamma * alpha * beta * 0.8 * section_depth * b * math.sqrt(fc * 10**-3) * 10**3

    # steel contribution
    shear_steel = section_data.Ast * fy_s * section_depth/s

    # axial contribution
    indicative_neutral_axis = 0.15 * h
    shear_axial = axial * (h - indicative_neutral_axis) / L

    # total shear capacity
    shear_capacity = (shear_concrete + shear_axial + shear_steel) * 0.85

    return ShearEnvelope(
        cap_undamaged=shear_capacity[0],
        cap_residual=shear_capacity[1],
        duc_undamaged=3,
        duc_residual=15
    )


# -----------------------------------------------------
# MN Domains Algorithms
# -----------------------------------------------------
@cache
def four_points_MN_domain(section_data: BasicSectionInput,
                          concrete: Concrete,
                          steel: Steel,
                          direction: Direction = Direction.Positive) -> MNDomain:
    """
    Computes the four points of the domain

    :params section_data: validated section data for a given section object

    :params concrete: concrete of the section

    :params steel: steel of the rebars

    :params direction: direction of bending (positive mean lower reinforcement is in tension)
    """
    # Unpack data for better clarity
    E_c = concrete.E
    ec_u = concrete.epsilon_u
    fc = concrete.fc

    b = section_data.b
    h = section_data.h
    cop = section_data.cover
    As_bot = section_data.As
    As_top = section_data.As1
    d_top = cop
    d_bot = h - cop

    E_s = steel.E
    ey_s = steel.epsilon_y
    fy_s = steel.fy

    # if direction is negative, swaps the top and bottom reinfocement
    if direction is Direction.Negative:
        As_top, As_bot = As_bot, As_top

    # Point A
    axial_A = - fy_s * (As_top + As_bot)
    moment_A = fy_s * (As_bot - As_top) * (h / 2 - cop)

    # Point B
    neutral_axis = (h - cop) * ec_u / (ec_u + 10**-2)
    es_top = ec_u/neutral_axis * (neutral_axis - cop)

    axial_B = (
        neutral_axis * 0.8 * b * fc
        + As_top * min(E_s * es_top, fy_s)
        - As_bot * fy_s
        )
    moment_B = (
        neutral_axis * 0.8 * b * fc * (h/2 - 0.4 * neutral_axis)
        + As_top * min(E_s * es_top, fy_s) * (h/2 - cop)
        + As_bot * fy_s * (h/2 - cop)
    )

    # Point C
    neutral_axis = (h - cop) * ec_u / (ec_u + ey_s)
    es_top = ec_u/neutral_axis * (neutral_axis - cop)

    axial_C = (
        neutral_axis * 0.8 * b * fc
        + As_top * min(E_s * es_top, fy_s)
        - As_bot * fy_s
        )
    moment_C = (
        neutral_axis * 0.8 * b * fc * (h/2 - 0.4 * neutral_axis)
        + As_top * min(E_s * es_top, fy_s) * (h/2 - cop)
        + As_bot * fy_s * (h/2 - cop)
    )

    # Point D
    axial_D = b * h * fc - axial_A
    moment_D = - moment_A

    return MNDomain(
        moment= [
            moment_A,
            moment_B,
            moment_C,
            moment_D
        ],
        axial = [
            axial_A,
            axial_B,
            axial_C,
            axial_D
        ]
    )
