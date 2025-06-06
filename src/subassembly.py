import model.config as config
import math

from dataclasses import field, dataclass
from functools import cache, partial
from typing import Optional, Dict, Tuple, Any

from model.enums import Direction, ElementType, NodeType
from src.elements import Element
from src.frame import RegularFrame
from src.utils import analytical_intersection, import_configuration

# Import config data
cfg : config.MNINTConfig
cfg = import_configuration(config.CONFIG_PATH, object_hook=config.MNINTConfig)

# Usefull constants
BEAM_ELEMENTS = (
    ElementType.Beam,
    ElementType.LeftBeam,
    ElementType.RightBeam
)
COLUMN_ELEMENTS = (
    ElementType.Column,
    ElementType.AboveColumn,
    ElementType.BelowColumn
)
INTERNAL_NODES = (
    NodeType.Internal,
    NodeType.TopInternal
)
TOP_NODES = (
    NodeType.TopExternal,
    NodeType.TopInternal
)


@dataclass
class SubHierarchy:
    beam_eq: float
    rot_y: float
    rot_c: float
    weakest: ElementType


@dataclass
class Subassembly:
    node            : int
    delta_axial     : float
    axial           : float
    beam_length     : float
    column_length   : float
    left_beam       : Optional[Element] = field(default=None)
    right_beam      : Optional[Element] = field(default=None)
    below_column    : Optional[Element] = field(default=None)
    above_column    : Optional[Element] = field(default=None)
    node_type       : NodeType = field(init=False)
    downwind        : bool = field(init=False)
    upwind          : bool = field(init=False)
    kj              : float = field(init=False)

    def __post_init__(self) -> None:
        self.node_type = self._find_nodetype()
        self.kj = cfg.nodes.tension_kj_values.__dict__[self.node_type.value]

        if self.delta_axial == 0:
            self.downwind = False
            self.upwind = False
        else:
            self.upwind = self.delta_axial > 0
            self.downwind = self.delta_axial < 0
        if self.node_type in INTERNAL_NODES:

            assert self.right_beam is not None
            assert self.left_beam is not None

            if self.right_beam.get_section().get_depth() != self.right_beam.get_section().get_depth():
                raise AssertionError(
                    """All the beams of a floor must have the same height in order to
                    work with this node formulaton"""
                )

    # Propriesties

    @property
    def beam_count(self):
        return (self.right_beam is not None) + (self.left_beam is not None)

    @property
    def column_count(self):
        return (self.above_column is not None) + (self.below_column is not None)

    @property
    def _element_map(self) -> Dict[ElementType, Element | None]:
        return {
            ElementType.AboveColumn: self.above_column,
            ElementType.BelowColumn: self.below_column,
            ElementType.RightBeam: self.right_beam,
            ElementType.LeftBeam: self.left_beam
        }

    # Private methods
    def _find_nodetype(self) -> NodeType:
        """
        Finds the node type using a logic Tree
        """
        if self.below_column is None:
            return NodeType.Base
        elif self.above_column is None:
            if (self.left_beam is None) or (self.right_beam is None):
                return NodeType.TopExternal
            else:
                return NodeType.TopInternal
        elif (self.left_beam is None) or (self.right_beam is None):
            return NodeType.External
        else:
            return NodeType.Internal

    @cache
    def _shear_moment_conversion_factor(self) -> float:
        """
        Returns the conversion factor for the beam-column joint in order to b
        express the capacity of given joint in equivalent column moment
        """
        beam_height = max(
            self.right_beam.get_section().get_height()
                if self.right_beam is not None else 0,
            self.left_beam.get_section().get_height()
                if self.left_beam is not None else 0
        )
        beam_depth = min(
            self.right_beam.get_section().get_depth()
                if self.right_beam is not None else 1e3,
           self.left_beam.get_section().get_depth()
                if self.left_beam is not None else 1e3
        )

        assert self.below_column is not None
        if self.node_type in INTERNAL_NODES:
            beam_factor = (
                self.beam_length
                - self.below_column.get_section().get_height()
            )
        else:
            beam_factor = (
                self.beam_length
                - 0.5 * self.below_column.get_section().get_height()
            )
        if self.node_type in TOP_NODES:
            column_factor = self.column_length - 0.5 * beam_height
        else:
            column_factor = 0.5 * (self.column_length - beam_height)

        return (
            (0.9 * column_factor * self.beam_length * beam_depth)
            / (self.column_length * beam_factor - 0.9 * self.beam_length * beam_depth)
        )

    # Public methods
    def get_element(self, element_type: ElementType) -> Element | None:
        element = self._element_map.get(element_type)
        return element

    def domain_MN(self, axial: float) -> float:
        """
        Get MN domain of the joint
        """
        if self.node_type is NodeType.Base:
            assert self.above_column is not None
            return self.above_column.get_section().domain_MN(axial=axial)

        assert self.below_column is not None
        node_area = (
            self.below_column.get_section().get_effective_width()
            * self.below_column.get_section().get_height()
        )
        tensile_strength_MPa = self.kj * math.sqrt(
            self.below_column.get_section().get_concrete().fc * 10**-3
        )

        try:
            tension_capacity = (
                0.85 * node_area
                * tensile_strength_MPa * 10**3
                * math.sqrt(1 + axial * 10**-3 / (node_area * tensile_strength_MPa))
                * self._shear_moment_conversion_factor()
            )
        except ValueError:
            return 0

        if self.node_type == NodeType.Internal:
            compression_strength_MPa = (
                cfg.nodes.compression_kj_value
                * self.below_column.get_section().get_concrete().fc
                * 10**-3
            )
            try:
                compression_capacity = (
                    0.85 * node_area
                    * compression_strength_MPa * 10**3
                    * math.sqrt(1 - axial * 10**-3 / (node_area * compression_strength_MPa))
                    * self._shear_moment_conversion_factor()
                )
                return min(compression_capacity, tension_capacity)
            except ValueError:
                return 0

        return tension_capacity


    def delta_axial_moment(self,
                           axial: float,
                           direction: Direction = Direction.Positive) -> float:
        """
        Returns the moment that produces the given axial load
        """
        delta_N = (
            self.delta_axial
                if direction is Direction.Positive
                else -self.delta_axial
        )
        # No division by 0 please
        if delta_N == 0:
            delta_N = 10**-6
        return 1/-delta_N * (axial - self.axial)

    def get_hierarchy(self, direction: Direction = Direction.Positive) -> SubHierarchy:
        """
        Computes the hierarchy of subassembly.
            The algorithm can be chosen in config file -> sub_hierarchy
            'avg' : the hierarchy considers the average capacity for columns and beams
            'low' : the hierarchy considers every element on its own

        Args:
            direction (Direction, optional): Direction of push.
                Defaults to Direction.Positive.

        Returns:
            dict: hierarchy data
        """
        algs = {
            config.SubHyerarchyAlg.Total: total_hierarchy,
            config.SubHyerarchyAlg.Average: average_hierarchy,
            config.SubHyerarchyAlg.Lowest: single_hierarchy
        }
        return algs[cfg.subassembly_settings.sub_hierarchy](
            subassembly=self,
            direction=direction
        )

    def get_stiffness(self,  direction: Direction = Direction.Positive) -> float:
        """
        Retuns the equivalent stiffness of the subassembly.
            The algorithm can be chosen in config file -> sub_stiffness
            'avg' : weakest element works in parallel with undamaged one
            'low' : weakest element stiffness is considered for columns and beams

        Args:
            direction (Direction, optional): Direction of push.
                Defaults to Direction.Positive.

        Returns:
            float: equivalent sub stiffness
        """
        algs = {
            config.SubStiffnessAlg.Average : get_total_stiffness,
            config.SubStiffnessAlg.Lowest : get_low_stiffness
        }
        return algs[cfg.subassembly_settings.sub_stiffness](
            subassembly=self,
            direction=direction
        )

    def __hash__(self):
        return hash(
            (
                self.node,
                self.above_column,
                self.below_column,
                self.left_beam,
                self.right_beam
            )
        )

# -------------------------------------------------------------------------------------------------
# Subassembly factory
# -------------------------------------------------------------------------------------------------

class SubassemblyFactory:

    def __init__(self, frame: RegularFrame) -> None:
        """
        Subassembly Factory starting from frame data
        """
        self.__frame = frame

    @cache
    def get_subassembly(self, node: int) -> Subassembly:
        """
        Returns the the subasssembly data as Subassembly object

        Args:
            node (int): node id

        Returns:
            Subassembly: subassembly object
        """
        subassembly: Dict[str, Any] = {
            'node' : node,
            'beam_length' : 0,
            'column_length' : 0
        }
        # Gets subassembly elements data
        subassembly_elements = self.__frame.get_node_elements(node)
        for element in subassembly_elements:
            if element[1] == element[0] + self.__frame.verticals:
                subassembly['above_column'] = element[2]
                subassembly['column_length'] += 0.5 * self.__frame.get_interstorey_height(
                    self.__frame.get_node_floor(node)
                )
                continue
            if element[1] == element[0] - self.__frame.verticals:
                subassembly['below_column'] = element[2]
                subassembly['column_length'] += 0.5 * self.__frame.get_interstorey_height(
                    self.__frame.get_node_floor(node) - 1
                )
                continue
            if element[1] == element[0] - 1:
                subassembly['left_beam'] = element[2]
                subassembly['beam_length'] += 0.5 * self.__frame.get_span_length(
                    self.__frame.get_node_vertical(node) - 1
                )
                continue
            if element[1] == element[0] + 1:
                subassembly['right_beam'] = element[2]
                subassembly['beam_length'] += 0.5 * self.__frame.get_span_length(
                    self.__frame.get_node_vertical(node)
                )
                continue

        subassembly['column_length'] = subassembly['column_length'].__round__(2)
        subassembly['beam_length'] = subassembly['beam_length'].__round__(2)
        # Gets the axial stress acting on the node
        subassembly['axial'] = self.__frame.get_axial(node)
        # Computes delta axial
        subassembly['delta_axial'] = self.__frame.get_delta_axial(node)
        return Subassembly(**subassembly)

# -------------------------------------------------------------------------------------------------
# Shared functions and constants
# -------------------------------------------------------------------------------------------------

def flip_direction(direction: Direction) -> Direction:
    """
    Returns the opposite direction to the given one
    """
    if direction == Direction.Positive:
        return Direction.Negative
    return Direction.Positive

def get_node_rotations(node_type: NodeType) -> Tuple[float, float]:
    """
    Returns the yielding and ultimate node rotations given node type
    """
    if node_type in INTERNAL_NODES:
        return tuple(cfg.nodes.internal_node_rotation.__dict__.values())
    return tuple(cfg.nodes.external_node_rotation.__dict__.values())

def find_weakest(capacities: Dict[ElementType, float]) -> ElementType | None:
    # Find the weakest
    weakest = None
    for key in capacities.keys():
        if weakest is None or capacities[key] < capacities[weakest]:
            weakest = key

    return weakest



# -------------------------------------------------------------------------------------------------
# Hierarchy functions
# -------------------------------------------------------------------------------------------------
@cache
def total_hierarchy(subassembly: Subassembly,
                      direction: Direction = Direction.Positive) -> SubHierarchy:
    """
    Hyerarchy of strenght using the average capacity of columns and beams and considering lowest rotation

    Args:
        subassembly (Subassembly): Subassembly object
        direction (Direction, optional): direction fo push.
            Defaults to Direction.Positive.

    Raises:
        NotImplementedError: base node does noth have a hierarchy
            implementation yet (column - foundation)
        AssertionError: if weak element is neither columns, beam or joint

    Returns:
        dict: hierarchy data
    """
    if subassembly.node_type is NodeType.Base:
        raise NotImplementedError()

    counter_direction = flip_direction(direction)

    columns_number = (subassembly.above_column is not None) + 1
    beam_number = (subassembly.left_beam is not None) + (subassembly.right_beam is not None)
    conversion_factor = beam_number / columns_number

    # In total we use the sum of the elements
    def _beam_capacity(_: float) -> float:
        return 1/columns_number * sum(
            [
                subassembly.left_beam.moment_rotation(counter_direction).mom_c
                    if subassembly.left_beam is not None else 0,
                subassembly.right_beam.moment_rotation(direction).mom_c
                    if subassembly.right_beam is not None else 0
            ]
        )

    def _column_capacity(axial: float) -> float:
        return 1/columns_number * sum(
            [
                subassembly.above_column.get_section().domain_MN(axial)
                    if subassembly.above_column is not None else 0,
                subassembly.below_column.get_section().domain_MN(axial)
                    if subassembly.below_column is not None else 0,
            ]
        )

    _delta_axial_curve = partial(subassembly.delta_axial_moment, direction=direction)

    joint_capacity_axial = analytical_intersection(
        subassembly.axial,
        function_1=subassembly.domain_MN,
        function_2=_delta_axial_curve
    )
    column_capacity_axial = analytical_intersection(
        subassembly.axial,
        function_1=_column_capacity,
        function_2=_delta_axial_curve
    )
    beam_capacity_axial = analytical_intersection(
        subassembly.axial,
        function_1=_beam_capacity,
        function_2=_delta_axial_curve
    )

    capacities = {
        ElementType.Joint: _delta_axial_curve(joint_capacity_axial),
        ElementType.Column: _delta_axial_curve(column_capacity_axial),
        ElementType.Beam: _delta_axial_curve(beam_capacity_axial)
    }

    # Find the weakest
    weakest = find_weakest(capacities)

    # find rotations of weakest element
    if weakest == ElementType.Joint:
        rot_y, rot_c = get_node_rotations(subassembly.node_type)
    elif weakest == ElementType.Beam:
        rot_y = min(
            subassembly.left_beam.moment_rotation(counter_direction).rot_y
                if subassembly.left_beam is not None else 1,
            subassembly.right_beam.moment_rotation(direction).rot_y
                if subassembly.right_beam is not None else 1
        )
        rot_c = min(
            subassembly.left_beam.moment_rotation(counter_direction).rot_c
                if subassembly.left_beam is not None else 1,
            subassembly.right_beam.moment_rotation(direction).rot_c
                if subassembly.right_beam is not None else 1
        )
    elif weakest == ElementType.Column:
        rot_y = min(
            subassembly.above_column.moment_rotation(
                counter_direction,axial=column_capacity_axial
                ).rot_y if subassembly.above_column is not None else 1,
            subassembly.below_column.moment_rotation(
                direction,axial=column_capacity_axial
                ).rot_y if subassembly.below_column is not None else 1
        )
        rot_c = min(
            subassembly.above_column.moment_rotation(
                counter_direction,axial=column_capacity_axial
                ).rot_c if subassembly.above_column is not None else 1,
            subassembly.below_column.moment_rotation(
                direction,axial=column_capacity_axial
                ).rot_c  if subassembly.below_column is not None else 1
        )
    else:
        raise AssertionError(
            'The subassembly could not find the weakest element'
        )

    return SubHierarchy(
        beam_eq=1/conversion_factor * capacities[weakest],
        rot_y=rot_y,
        rot_c=rot_c,
        weakest=weakest
    )


@cache
def average_hierarchy(subassembly: Subassembly,
                      direction: Direction = Direction.Positive) -> SubHierarchy:
    """
    Hyerarchy of strenght using the average capacity of columns and beams considering average rotation for yielding

    Args:
        subassembly (Subassembly): Subassembly object
        direction (Direction, optional): direction fo push.
            Defaults to Direction.Positive.

    Raises:
        NotImplementedError: base node does noth have a hierarchy
            implementation yet (column - foundation)
        AssertionError: if weak element is neither columns, beam or joint

    Returns:
        dict: hierarchy data
    """
    if subassembly.node_type is NodeType.Base:
        raise NotImplementedError()

    counter_direction = flip_direction(direction)

    columns_number = (subassembly.above_column is not None) + 1
    beam_number = (subassembly.left_beam is not None) + (subassembly.right_beam is not None)
    conversion_factor = beam_number / columns_number

    # In total we use the sum of the elements
    def _beam_capacity(_: float) -> float:
        return 1/columns_number * sum(
            [
                subassembly.left_beam.moment_rotation(counter_direction).mom_c
                    if subassembly.left_beam is not None else 0,
                subassembly.right_beam.moment_rotation(direction).mom_c
                    if subassembly.right_beam is not None else 0
            ]
        )

    def _column_capacity(axial: float) -> float:
        return 1/columns_number * sum(
            [
                subassembly.above_column.get_section().domain_MN(axial)
                    if subassembly.above_column is not None else 0,
                subassembly.below_column.get_section().domain_MN(axial)
                    if subassembly.below_column is not None else 0,
            ]
        )

    _delta_axial_curve = partial(subassembly.delta_axial_moment, direction=direction)

    joint_capacity_axial = analytical_intersection(
        subassembly.axial,
        function_1=subassembly.domain_MN,
        function_2=_delta_axial_curve
    )
    column_capacity_axial = analytical_intersection(
        subassembly.axial,
        function_1=_column_capacity,
        function_2=_delta_axial_curve
    )
    beam_capacity_axial = analytical_intersection(
        subassembly.axial,
        function_1=_beam_capacity,
        function_2=_delta_axial_curve
    )

    capacities = {
        ElementType.Joint : _delta_axial_curve(joint_capacity_axial),
        ElementType.Column : _delta_axial_curve(column_capacity_axial),
        ElementType.Beam : _delta_axial_curve(beam_capacity_axial)
    }

    # Find the weakest
    weakest = find_weakest(capacities)

    # find rotations of weakest element
    if weakest == ElementType.Joint:
        rot_y, rot_c = get_node_rotations(subassembly.node_type)
    elif weakest == ElementType.Beam:
        rot_y = sum([
            subassembly.left_beam.moment_rotation(counter_direction).rot_y
                if subassembly.left_beam is not None else 0,
            subassembly.right_beam.moment_rotation(direction).rot_y
                if subassembly.right_beam is not None else 0
        ]) / beam_number
        rot_c = min(
            subassembly.left_beam.moment_rotation(counter_direction).rot_c
                if subassembly.left_beam is not None else 1,
            subassembly.right_beam.moment_rotation(direction).rot_c
                if subassembly.right_beam is not None else 1
        )
    elif weakest == ElementType.Column:
        rot_y = sum([
            subassembly.above_column.moment_rotation(
                counter_direction, axial=column_capacity_axial
                ).rot_y if subassembly.above_column is not None else 0,
            subassembly.below_column.moment_rotation(
                direction, axial=column_capacity_axial
                ).rot_y if subassembly.below_column is not None else 0
        ]) / columns_number
        rot_c = min(
            subassembly.above_column.moment_rotation(
                counter_direction, axial=column_capacity_axial
                ).rot_c if subassembly.above_column is not None else 1,
            subassembly.below_column.moment_rotation(
                direction, axial=column_capacity_axial
                ).rot_c  if subassembly.below_column is not None else 1
        )
    else:
        raise AssertionError(
            'The subassembly could not find the weakest element'
        )

    return SubHierarchy(
        beam_eq=1/conversion_factor * capacities[weakest],
        rot_y=rot_y,
        rot_c=rot_c,
        weakest=weakest
    )

@cache
def single_hierarchy(subassembly: Subassembly,
                     direction: Direction = Direction.Positive) -> SubHierarchy:
    """
    Returns the hierarchy of subassembly considering the capacity of the single elements

    Args:
        subassembly (Subassembly): subassembly object
        direction (Direction, optional): direction of push. D
            Defaults to Direction.Positive.

    Raises:
        NotImplementedError: base node does noth have a hierarchy
            implementation yet (column - foundation)
        AssertionError: if weak element is neither columns, beam or joint

    Returns:
        dict: hierarchy data
    """
    if subassembly.node_type is NodeType.Base:
            raise NotImplementedError

    counter_direction = flip_direction(direction)

    columns_number = (subassembly.above_column is not None) + 1
    beam_number = (subassembly.left_beam is not None) + (subassembly.right_beam is not None)
    conversion_factor = beam_number / columns_number

    capacities = dict()

    delta_axial_curve = lambda axial: subassembly.delta_axial_moment(axial, direction)

    # Left Beam
    if subassembly.left_beam is not None:
        left_beam_capacity_curve = lambda _: (
            conversion_factor * subassembly.left_beam.moment_rotation(  # pyright: ignore[reportOptionalMemberAccess]
                counter_direction
                ).mom_c
        )
        left_beam_capacity_axial = analytical_intersection(
            subassembly.axial,
            left_beam_capacity_curve,
            delta_axial_curve
        )
        capacities[ElementType.LeftBeam] = delta_axial_curve(left_beam_capacity_axial)

    # Right Beam
    if subassembly.right_beam is not None:
        right_beam_capacity_curve = lambda _: (
            conversion_factor * subassembly.right_beam.moment_rotation( # pyright: ignore[reportOptionalMemberAccess]
                direction
                ).mom_c
        )
        right_beam_capacity_axial = analytical_intersection(
            subassembly.axial,
            right_beam_capacity_curve,
            delta_axial_curve
        )
        capacities[ElementType.RightBeam] = delta_axial_curve(right_beam_capacity_axial)

    # Above Column
    if subassembly.above_column is not None:
        above_column_capacity_curve = lambda axial: (
            subassembly.above_column.get_section().domain_MN(axial) # pyright: ignore[reportOptionalMemberAccess]
        )
        above_column_capacity_axial = analytical_intersection(
            subassembly.axial,
            above_column_capacity_curve,
            delta_axial_curve
        )
        capacities[ElementType.AboveColumn] = delta_axial_curve(above_column_capacity_axial)

    # Below Column
    assert subassembly.below_column is not None
    below_column_capacity_curve = lambda axial: (
        subassembly.below_column.get_section().domain_MN(axial)     # pyright: ignore[reportOptionalMemberAccess]
    )
    below_column_capacity_axial = analytical_intersection(
        subassembly.axial,
        below_column_capacity_curve,
        delta_axial_curve
    )
    capacities[ElementType.BelowColumn] = delta_axial_curve(below_column_capacity_axial)

    # Joint
    joint_capacity_axial = analytical_intersection(
        subassembly.axial,
        subassembly.domain_MN,
        delta_axial_curve
    )
    capacities[ElementType.Joint] = delta_axial_curve(joint_capacity_axial)

    # Find weakest
    weakest = find_weakest(capacities)

    # find rotations of weakest element
    if weakest == ElementType.Joint:
        rot_y, rot_c = get_node_rotations(subassembly.node_type)
    elif weakest == ElementType.LeftBeam:
        assert subassembly.left_beam is not None
        rot_y = subassembly.left_beam.moment_rotation(counter_direction).rot_y
        rot_c = subassembly.left_beam.moment_rotation(counter_direction).rot_c

    elif weakest == ElementType.RightBeam:
        assert subassembly.right_beam is not None
        rot_y = subassembly.right_beam.moment_rotation(direction).rot_y
        rot_c = subassembly.right_beam.moment_rotation(direction).rot_c

    elif weakest == ElementType.AboveColumn:
        assert subassembly.above_column is not None
        rot_y = subassembly.above_column.moment_rotation(
                counter_direction, axial=above_column_capacity_axial    # pyright: ignore[reportPossiblyUnboundVariable]
            ).rot_y
        rot_c = subassembly.above_column.moment_rotation(
                counter_direction, axial=above_column_capacity_axial    # pyright: ignore[reportPossiblyUnboundVariable]
            ).rot_c

    elif weakest == ElementType.BelowColumn:
        rot_y = subassembly.below_column.moment_rotation(
                direction, axial=below_column_capacity_axial
            ).rot_y
        rot_c = subassembly.below_column.moment_rotation(
                direction, axial=below_column_capacity_axial
            ).rot_c

    else:
        raise AssertionError(
            'The subassembly could not find the weakest element'
        )
    return SubHierarchy(
        beam_eq=1/conversion_factor * capacities[weakest],
        rot_y=rot_y,
        rot_c=rot_c,
        weakest=weakest
    )

# -------------------------------------------------------------------------------------------------
# Stiffness functions
# -------------------------------------------------------------------------------------------------
@cache
def get_total_stiffness(subassembly: Subassembly,
                        direction: Direction = Direction.Positive) -> float:
    """
    Retuns the equivalent stiffness of the subassembly

    Args:
        direction (Direction, optional): Direction of push. Defaults to Direction.Positive. Defaults to Direction.Positive.
    """
    counter_direction = flip_direction(direction)

    joint_rotation = cfg.nodes.cracking_rotation

    # Initialize the stifness data including joint value and lower column
    stiffnesses = {
        'beam' : 0,
        'column' : (
            subassembly.below_column.moment_rotation(
                counter_direction,
                axial=subassembly.axial
                ).mom_y
            / subassembly.below_column.moment_rotation(
                counter_direction,
                axial=subassembly.axial
            ).rot_y
        ),
        'joint' : subassembly.domain_MN(subassembly.axial)/joint_rotation
    }
    # This will be needed to convert moments from column equivalent to beam equivalent
    n_columns = 1
    n_beams = 0

    # Updates beams' stiffness factor with left beam stiffness (if present)
    if subassembly.left_beam is not None:
        stiffnesses['beam'] += (
            subassembly.left_beam.moment_rotation(counter_direction).mom_y
            / subassembly.left_beam.moment_rotation(counter_direction).rot_y
        )
        n_beams += 1
    # Updates beams' stiffness factor with right beam stiffness (if present)
    if subassembly.right_beam is not None:
        stiffnesses['beam'] += (
            subassembly.right_beam.moment_rotation(direction).mom_y
            / subassembly.right_beam.moment_rotation(direction).rot_y
        )
        n_beams += 1

    # Updates columns' stiffness factor with top column stiffness (if present)
    if subassembly.above_column is not None:
        stiffnesses['column'] += (
            subassembly.above_column.moment_rotation(
                direction,
                axial=subassembly.axial
                ).mom_y
            / subassembly.above_column.moment_rotation(
                direction,
                axial=subassembly.axial
                ).rot_y
        )
        n_columns += 1

    # Corrects the joint stifness accounting for the number of columns
    stiffnesses['joint'] = stiffnesses['joint'] * n_columns

    return (sum(stiff**-1 for stiff in stiffnesses.values()))**-1 * 1/n_beams



@cache
def get_low_stiffness(subassembly: Subassembly,
                      direction: Direction = Direction.Positive) -> float:
    """
    Retuns the equivalent stiffness of the subassembly

    Args:
        direction (Direction, optional): Direction of push. Defaults to Direction.Positive. Defaults to Direction.Positive.
    """
    counter_direction = flip_direction(direction)

    joint_rotation = cfg.nodes.cracking_rotation

    stiffnesses = {
        'beam' : 0,
        'column' : 0,
        'joint' : subassembly.domain_MN(subassembly.axial)/joint_rotation
    }
    n_beams = 1
    if subassembly.node_type in INTERNAL_NODES:
        n_beams += 1

    n_columns = 1
    if subassembly.above_column is not None:
        n_columns += 1

    if subassembly.get_hierarchy()['element'] in BEAM_ELEMENTS:
        stiffnesses['beam'] = (
            n_beams
            * subassembly.get_hierarchy()['beam_equivalent']
            / subassembly.get_hierarchy()['rotation_yielding']
        )
    else:
        if subassembly.left_beam is not None:
            stiffnesses['beam'] += (
                subassembly.left_beam.moment_rotation(counter_direction).mom_y
                / subassembly.left_beam.moment_rotation(counter_direction).rot_y
            )

        if subassembly.right_beam is not None:
            stiffnesses['beam'] += (
                subassembly.right_beam.moment_rotation(direction).mom_y
                / subassembly.right_beam.moment_rotation(direction).rot_y
            )

    if subassembly.get_hierarchy()['element'] in COLUMN_ELEMENTS:
        stiffnesses['column'] = (
            n_columns
            * subassembly.get_hierarchy()['beam_equivalent']
            / subassembly.get_hierarchy()['rotation_yielding']
        )
    else:
        stiffnesses['column'] += (
            subassembly.below_column.moment_rotation(
                counter_direction,
                axial=subassembly.axial
            ).mom_y
            / subassembly.below_column.moment_rotation(
                counter_direction,
                axial=subassembly.axial
            ).rot_y
        )

        if subassembly.above_column is not None:
            stiffnesses['column'] += (
                subassembly.above_column.moment_rotation(
                    direction,
                    axial=subassembly.axial
                ).mom_y
                / subassembly.above_column.moment_rotation(
                    direction,
                    axial=subassembly.axial
                ).rot_y
            )

    stiffnesses['joint'] = stiffnesses['joint'] * n_columns

    return (n_beams * sum(stiff**-1 for stiff in stiffnesses.values()))**-1