from dataclasses import field, dataclass
from functools import cache
import math
from typing import List, Optional

from model.enums import Direction, ElementType, NodeType
from model.global_constants import EXTERNAL_NODE_ROTATION_CAPACITIES, INTERNAL_NODE_ROTATION_CAPACITIES, NODES_KJ_VALUES
from src.elements import Element
from src.frame import RegularFrame
from src.utils import analytical_intersection

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
        self.node_type = self.__find_nodetype()
        self.kj = NODES_KJ_VALUES[self.node_type.value]

        if self.delta_axial == 0:
            self.downwind = False
            self.upwind = False
        else:
            self.upwind = self.delta_axial > 0
            self.downwind = self.delta_axial < 0
        if self.node_type in (NodeType.Internal, NodeType.TopInternal):
            if self.right_beam.get_section().get_depth() != self.right_beam.get_section().get_depth():
                raise AssertionError('All the beams of a floor must have the same height in order to work with this node formulaton')            

    # Private methods
    def __find_nodetype(self) -> NodeType:
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
    def __shear_moment_conversion_factor(self) -> float:
        """
        Returns the conversion factor for the beam-column joint in order to b   
        express the capacity of given joint in equivalent column moment
        """
        beam_height = max(
            self.right_beam.get_section().get_height() if self.right_beam is not None else 0,
            self.left_beam.get_section().get_height() if self.left_beam is not None else 0
        )
        beam_depth = (
            self.right_beam.get_section().get_depth() 
            if self.right_beam is not None 
            else self.left_beam.get_section().get_depth()
        )
        if self.node_type in (NodeType.TopInternal, NodeType.Internal):
            beam_factor = self.beam_length - self.below_column.get_section().get_height()
        else:
            beam_factor = self.beam_length - 0.5 * self.below_column.get_section().get_height()
        if self.node_type in (NodeType.TopInternal, NodeType.TopExternal):
            column_factor = self.column_length - 0.5 * beam_height
        else:
            column_factor = 0.5 * (self.column_length - beam_height)
        
        return (
            (0.9 * column_factor * self.beam_length * beam_depth) 
            / (self.column_length * beam_factor - 0.9 * self.beam_length * beam_depth)
        )

    # Public methods
    def domain_MN(self, axial: List[float]) -> List[float]:
        """
        Get MN domain of the joint
        """
        if self.node_type is NodeType.Base:
            return self.above_column.get_section().domain_MN(axial=axial)
    
        node_area = (
            self.below_column.get_section().get_effective_width() 
            * self.below_column.get_section().get_height()
        )
        tensile_strength_MPa = self.kj * math.sqrt(self.below_column.get_section().get_concrete().fc * 10**-3)

        def __probable_shear_capacity(axial: float) -> float:
            """
            Computes the probable capacity of the node in column equivalent moment
            """
            try:
                return (
                    0.85 * node_area 
                    * tensile_strength_MPa * 10**3
                    * math.sqrt(1 + axial * 10**-3 / (node_area * tensile_strength_MPa)) 
                    * self.__shear_moment_conversion_factor()
                )
            except ValueError:
                return 0
        
        return [__probable_shear_capacity(axial_load) for axial_load in axial]

    def delta_axial_moment(self, axials: List[float], direction: Direction = Direction.Positive) -> List[float]: 
        """
        Returns the moment that produces the given axial load
        """
        delta_N = self.delta_axial if direction is Direction.Positive else -self.delta_axial
        if delta_N == 0:
            delta_N = 10**-6
        return [1/-delta_N * (axial - self.axial) for axial in axials]

    @cache
    def get_hierarchy(self, direction: Direction = Direction.Positive) -> dict:
        """
        Returns the hierarchy of subassembly
        """
        if self.node_type is NodeType.Base:
            print('not coded yet')
            return 0
        
        counter_direction = Direction.Negative if direction == Direction.Positive else Direction.Positive
        
        columns_number = (self.above_column is not None) + 1
        beam_number = (self.left_beam is not None) + (self.right_beam is not None)
        conversion_factor = beam_number / columns_number

        beam_capacity_curve = lambda axial: conversion_factor/beam_number * sum(
            [
                self.left_beam.moment_rotation(counter_direction)['moment'][-1] if self.left_beam is not None else 0,
                self.right_beam.moment_rotation(direction)['moment'][-1] if self.right_beam is not None else 0
            ]
        )

        column_capacity_curve = lambda axial: 1/columns_number * sum(
            [
                self.above_column.get_section().domain_MN([axial])[0] if self.above_column is not None else 0,
                self.below_column.get_section().domain_MN([axial])[0]
            ]
        )

        joint_capacity_curve = lambda axial: self.domain_MN([axial])[0]

        delta_axial_curve = lambda axial: self.delta_axial_moment([axial], direction)[0]

        joint_capacity_axial = analytical_intersection(self.axial, joint_capacity_curve, delta_axial_curve)
        column_capacity_axial = analytical_intersection(self.axial, column_capacity_curve, delta_axial_curve)
        beam_capacity_axial = analytical_intersection(self.axial, beam_capacity_curve, delta_axial_curve)

        capacities = {
            ElementType.Joint : delta_axial_curve(joint_capacity_axial),
            ElementType.Column : delta_axial_curve(column_capacity_axial),
            ElementType.Beam : delta_axial_curve(beam_capacity_axial)
        }

        weakest = ''
        for key in capacities.keys():
            if weakest != '' and capacities[key] < capacities[weakest]:
                weakest = key
            elif weakest == '':
                weakest = key
        
        # find rotations of weakest element
        if weakest == ElementType.Joint:
            if self.node_type in (NodeType.External, NodeType.TopExternal):
                rotation_capacities = EXTERNAL_NODE_ROTATION_CAPACITIES
            else:
                rotation_capacities = INTERNAL_NODE_ROTATION_CAPACITIES
        elif weakest == ElementType.Beam:
            rotation_capacities = (
                min(
                    self.left_beam.moment_rotation(counter_direction)['rotation'][0] if self.left_beam is not None else 1,
                    self.right_beam.moment_rotation(direction)['rotation'][0] if self.right_beam is not None else 1
                ),
                min(
                    self.left_beam.moment_rotation(counter_direction)['rotation'][-1] if self.left_beam is not None else 1,
                    self.right_beam.moment_rotation(direction)['rotation'][-1] if self.right_beam is not None else 1
                ),
            )
        elif weakest == ElementType.Column:
            rotation_capacities = (
                min(
                    self.above_column.moment_rotation(counter_direction,axial=column_capacity_axial)['rotation'][0] if self.above_column is not None else 1,
                    self.below_column.moment_rotation(direction,axial=column_capacity_axial)['rotation'][0]
                ),
                min(
                    self.above_column.moment_rotation(counter_direction,axial=column_capacity_axial)['rotation'][-1] if self.above_column is not None else 1,
                    self.below_column.moment_rotation(direction,axial=column_capacity_axial)['rotation'][-1]
                ),
            )
        else:
            raise AssertionError('We have no idea why it failed, but the subassembly could not find the weakest element')
        
        return{
            'beam_equivalent' : 1/conversion_factor * capacities[weakest],
            'rotation_yielding' : rotation_capacities[0],
            'rotation_ultimate' : rotation_capacities[-1]
        }
    
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








    


class SubassemblyFactory:

    def __init__(self, frame: RegularFrame) -> None:
        """
        Subassembly Factory starting from frame data
        """
        self.__frame = frame

    @cache
    def get_subassembly(self, node: int) -> Subassembly:
        """
        Get the subassembly data given the node from the frame data
        """
        subassembly = {
            'node' : node,
            'beam_length' : 0,
            'column_length' : 0
        }
        # Gets subassembly elements data
        subassembly_elements = self.__frame.get_node_elements(node)
        for element in subassembly_elements:
            if element[1] == element[0] + self.__frame.verticals:
                subassembly['above_column'] = element[2]
                subassembly['column_length'] += 0.5 * self.__frame.get_interstorey_height(self.__frame.get_node_floor(node))
                continue
            if element[1] == element[0] - self.__frame.verticals:
                subassembly['below_column'] = element[2]
                subassembly['column_length'] += 0.5 * self.__frame.get_interstorey_height(self.__frame.get_node_floor(node) - 1)
                continue
            if element[1] == element[0] - 1:
                subassembly['left_beam'] = element[2]
                subassembly['beam_length'] += 0.5 * self.__frame.get_span_length(self.__frame.get_node_vertical(node) - 1)
                continue
            if element[1] == element[0] + 1:
                subassembly['right_beam'] = element[2]
                subassembly['beam_length'] += 0.5 * self.__frame.get_span_length(self.__frame.get_node_vertical(node))
                continue
        
        subassembly['column_length'] = subassembly['column_length'].__round__(2)
        subassembly['beam_length'] = subassembly['beam_length'].__round__(2)
        # Gets the axial stress acting on the node
        subassembly['axial'] = self.__frame.get_axial(node)
        # Computes delta axial
        subassembly['delta_axial'] = self.__frame.get_delta_axial(node)
        return Subassembly(**subassembly)

        


