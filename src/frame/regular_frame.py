from functools import cache
from typing import List, Tuple
from typing_extensions import Self
import numpy as np

from math import floor

from model.validation import Regular2DFrameInput
from src.frame.graph import Graph, NodeNotFoundError
from src.collections import SectionCollection, ElementCollection
from src.elements import Element


class RegularFrame(Graph):

    def __init__(self, node_count: int,
                 lengths: List[float],
                 heights: List[float],
                 masses: List[float],
                 loads: List[float]):
        """
        Defines a frame data structure as a graph

        :param int node_count: number of nodes of frame

        :param lengths: x coordinates of columns starting from 0

        :param heights: z coordinates of floors excluding ground floor

        :param masses: mass of each floor

        :param loadas: vertical load on each node (from tributary areas)
        """
        super().__init__(node_count)
        self._lengths = lengths
        self._heights = heights
        self._masses = masses
        self._loads = loads

    @property
    @cache
    def spans(self) -> int:
        return len(self._lengths) - 1

    @property
    @cache
    def verticals(self) -> int:
        return len(self._lengths)

    @property
    @cache
    def floors(self) -> int:
        return len(self._heights)

    @property
    @cache
    def floor_forces_distribution(self) -> List[float]:
        """
        Returns the force distribution according to NTC 2018
        """
        # See §7.3.3.2 of NTC2018
        force_height = sum(mass * height for mass, height in zip(self._masses, self._heights))
        return list((mass * height) / force_height for mass, height in zip(self._masses, self._heights))

    @property
    @cache
    def forces_effective_height(self):
        """
        Returns the Heff of the force distribution
        """
        return sum(
            force * height
            for force, height in zip(self.floor_forces_distribution, self._heights)
            )

    @property
    @cache
    def _delta_axial_ratios(self) -> dict:
        """
        Computes the delta axial ratios for all the external nodes old approch
        """
        floor_shear = np.cumsum(
            np.flip(self.floor_forces_distribution)
        )

        # Zero is used to preserve the length after applying np.diff
        heights = [0.] + self._heights
        interstorey_heights = np.flip(np.diff(heights))

        # Compute total floor OTM due to column
        columns_floor_otm = [
            0.5 * inter_height * force
            for inter_height, force in zip(interstorey_heights, floor_shear)
        ]

        # Compute forces otm
        overturning_moment = np.flip(
            [
                np.dot(
                    np.array(heights[floor:]) - heights[floor],
                    [0.,] + self.floor_forces_distribution[floor:]
                )
                for floor, _  in enumerate(heights)
            ]
        )

        # Find delta axials as a difference of OTM forces and one resisted by columns
        delta_axials = [
            (otm - columns_otm)/self._lengths[-1]
            for otm, columns_otm in zip(overturning_moment[1:], columns_floor_otm)
        ]

        # Save span lengths used to pass from shear to moment
        first_span_lenght = self._lengths[1]
        last_span_lenght = self._lengths[-1] - self._lengths[-2]

        # Computes equivalent moments for delta axials
        beam_shears = np.diff(delta_axials, prepend=[0.])
        moment_beams_upwind = 0.5 * beam_shears * first_span_lenght
        moment_beams_downwind = 0.5 * beam_shears * last_span_lenght

        moment_column_upwind = [moment_beams_upwind[0]]
        moment_column_downwind = [moment_beams_downwind[0]]
        for floor in range(1, self.floors):
            moment_column_upwind.append(moment_beams_upwind[floor] - moment_column_upwind[floor - 1])
            moment_column_downwind.append(moment_beams_upwind[floor] - moment_column_upwind[floor - 1])

        return {
            'upwind' : np.flip(
                [
                    delta/moment
                    for delta, moment in zip(delta_axials, moment_column_upwind)
                ]
            ),
            'downwind' : np.flip(
                [
                    -delta/moment
                    for delta, moment in zip(delta_axials, moment_column_downwind)
                ],
            ),
        }

    def get_node_id(self, floor: int, vertical: int) -> int:
        """
        Returns the node id given floor and vertical
        """
        if floor > self.floors or floor < 0:
            raise NodeNotFoundError('Specified span does not exist')
        if vertical > self.spans or vertical < 0:
            raise NodeNotFoundError('Specified span does not exist')
        return (floor * self.verticals) + vertical

    def get_node_floor(self, node: int) -> int:
        """
        Returns the node floor location given the node id
        """
        if not(self.does_node_exist(node)):
            raise NodeNotFoundError('Given node does not exist')
        return floor(node / self.verticals)

    def get_node_vertical(self, node: int) -> int:
        """
        Returns the node vertical location given the node id
        """
        if not(self.does_node_exist(node)):
            raise NodeNotFoundError('Given node does not exist')
        return node % self.verticals

    def get_node_position(self, node: int) -> Tuple[int, int]:
        """
        Returns the node location [vertical, floor] given the id
        """
        if not(self.does_node_exist(node)):
            raise NodeNotFoundError('Given node does not exist')
        return self.get_node_vertical(node), self.get_node_floor(node)

    def get_node_coordinates(self, node: int) -> Tuple[float, float]:
        """
        Returns the node coordinates X, Y given the id
        """
        if not(self.does_node_exist(node)):
            raise NodeNotFoundError('Given node does not exist')
        vertical, floor = self.get_node_position(node)
        floor_heights = [0.] + self._heights
        return self._lengths[vertical], floor_heights[floor]

    def get_interstorey_height(self, floor: int) -> float:
        """
        Returns the interstorey height of given storey
        """
        if floor > self.floors or floor < 0:
            raise NodeNotFoundError('Specified span does not exist')
        if floor == 0:
            return self._heights[0]
        else:
            return self._heights[floor] - self._heights[floor - 1]

    def get_span_length(self, span: int) -> float:
        """
        Returns the span length given the span number starting from 0
        """
        if span >= self.spans or span < 0:
            raise NodeNotFoundError('Specified span does not exist')
        else:
            return self._lengths[span + 1] - self._lengths[span]

    @cache
    def get_delta_axial(self, node: int) -> float:
        """
        Returns the deltaN value normalized for a column moment of 1 kNm given the id of node Gnetile PhD thesis
        """
        if self.get_node_vertical(node) == 0:
            # return self._delta_axial_ratios['upwind'][self.get_node_floor(node) - 1]
            direction_multiplier = 1

        elif self.get_node_vertical(node) == self.verticals - 1:
            # return self._delta_axial_ratios['downwind'][self.get_node_floor(node) - 1]
            direction_multiplier = -1

        else:
            return 0
            # internal node, no delta

        floors = self.floors

        # A.19 PhD Roberto Gentile
        shear_demand_ratio = (3 * self.verticals - 2) / 2

        floor = self.get_node_floor(node)
        # A.20 PhD Roberto Gentile
        lambda_1 = 2/((floors + 1) * floors) * (floors * (floors + 1) - floor * (floor - 1))/2
        lambda_2 = 1/((floors + 1) * floors) * (
            (floors * (floors + 1) * (2 * floors +1) - floor * (floor - 1) * (2 * floor - 1))/6
            - (floor - 1) * (floors * (floors + 1) - floor * (floor - 1))/2
        )
        # A.22 assuming l'c = H/2
        return direction_multiplier * 4 / self._lengths[-1] * lambda_2 / lambda_1 * shear_demand_ratio


    def get_axial(self, node: int) -> float:
          """
          Get the total axial force acting on given node
          """
          return round(sum(self._loads[node::self.verticals]), ndigits=2)

    def get_floor_height(self, floor: int) -> float:
        """
        Returns the absolute height of a given floor
        """
        if floor <= 0 or floor > self.floors:
            raise NodeNotFoundError('Specified span does not exist')
        return self._heights[floor - 1]

    def get_heights(self) -> List[float]:
        """
        Returns the heights of every floor
        """
        return self._heights

    def get_lengths(self) -> List[float]:
        """
        Returns the heights of every floor
        """
        return self._lengths

    def get_effective_mass(self) -> float:
        disp = np.arange(0, self.floors) + 1
        mass_disp = np.dot(np.array(self._masses), disp)
        mass_disp_sq = np.dot(np.array(self._masses), disp**2)
        return mass_disp**2 / mass_disp_sq
        # return 0.8 * sum(self.__masses)

    def __str__(self) -> str:
        return f"""
        Regular2DFrame Object
        verticals   : {self.verticals}
        floors      : {self.floors}
        L           : {self._lengths}
        H           : {self._heights}
        m           : {self._masses}
        loads       : {self._loads}
        sections    : .elements
        graph       : use repr()
        """


class RegularFrameBuilder:

    def __init__(self,
                 frame_data: Regular2DFrameInput,
                 sections: SectionCollection,
                 element_object: type[Element]) -> None:
        """
        This is class builds a frame given the sections and the validated frame input
        """
        self._frame_data = frame_data
        self._sections = sections
        self._element_object = element_object
        self._elements = ElementCollection()
        self._frame = RegularFrame(len(frame_data.loads),
                                    lengths=frame_data.L,
                                    heights=frame_data.H,
                                    masses=frame_data.m,
                                    loads=frame_data.loads)

    def get_frame(self) -> RegularFrame:
        """
        Returns the built frame
        """
        return self._frame

    def get_elements(self) -> ElementCollection:
        """
        Get element collection
        """
        return self._elements

    def build_frame(self) -> None:
        """
        Defines the graph structure starting from the frame data
        """
        def __add_storey_columns(floor: int) -> None:
            """
            Adds all the columns of a given floor
            """
            for vertical in range(self._frame.verticals):
                node = vertical + (floor * self._frame.verticals)
                column_data = self.__column_length(floor, vertical)
                element = self._elements.add_column_element(
                    section=self._sections.get_columns()[column_data['tag']],
                    L=round(column_data['length'], ndigits=2),
                    _elementClass=self._element_object
                )
                self.__add_element(node, node + self._frame.verticals, element)

        def __add_storey_beams(floor: int) -> None:
            """
            Adds all the beams of a given floor
            """
            for span in range(self._frame.spans):
                node = span + ((floor + 1) * self._frame.verticals)
                beam_data = self.__beam_length(floor, span)
                element = self._elements.add_beam_element(
                    section=self._sections.get_beams()[beam_data['tag']],
                    L=round(beam_data['length'], ndigits=2),
                    _elementClass=self._element_object
                )
                self.__add_element(node, node + 1, element)

        # Builds elements for each floor
        for floor, _ in enumerate(self._frame_data.H):
            __add_storey_beams(floor)
            __add_storey_columns(floor)


    def __column_length(self, floor: int, vertical: int) -> dict:
        """
        Computes the shear lengths of specified element
        """
        if floor == 0:
            H_storey = self._frame_data.H[0]
        else:
            H_storey = self._frame_data.H[floor] - self._frame_data.H[floor - 1]

        if vertical == 0:
            # Gets the tag of the first beam section connected on top
            beam_tag = self._frame_data.beams[floor][0]
            return {
                'tag': self._frame_data.columns[floor][0],
                'length': (H_storey - self._sections.get_beams()[beam_tag].get_height())
            }
        elif vertical == self._frame.spans:
            # Gets the tag of the last beam section connected on top
            beam_tag = self._frame_data.beams[floor][-1]
            return {
                'tag': self._frame_data.columns[floor][-1],
                'length': (H_storey - self._sections.get_beams()[beam_tag].get_height())
            }
        else:
            beam_tag_1 = self._frame_data.beams[floor][vertical]
            beam_tag_2 = self._frame_data.beams[floor][vertical - 1]
            return {
                'tag': self._frame_data.columns[floor][vertical],
                'length': (H_storey - max(self._sections.get_beams()[beam_tag_1].get_height(), self._sections.get_beams()[beam_tag_2].get_height()))
            }


    def __beam_length(self, floor: int, span: int) -> dict:
        """
        Computes the shear lengths of specified element
        """
        L_span = self._frame_data.L[span + 1] - self._frame_data.L[span]
        column_tag_1 = self._frame_data.columns[floor][span]
        column_tag_2 = self._frame_data.columns[floor][span + 1]
        return{
            'tag': self._frame_data.beams[floor][span],
            'length': (L_span - 0.5 * (self._sections.get_columns()[column_tag_1].get_height() + self._sections.get_columns()[column_tag_2].get_height()))
        }

    def __add_element(self, node1: int, node2: int, element: Element) -> None:
        """
        Adds a element column to frame
        """
        self._frame.add_arch(
            i_node=node1,
            j_node=node2,
            weight=element)
        # Non oriented graph
        self._frame.add_arch(
            i_node=node2,
            j_node=node1,
            weight=element)


@cache
def delta_axial_ratios(self: RegularFrame) -> dict:
    """
    Computes the delta axial ratios for all the external nodes
    """
    heights = [0.] + self._heights
    floor_shear = np.cumsum(
        np.flip(self.floor_forces_distribution)
    )
    interstorey_heights = np.flip(np.diff(heights))
    columns_floor_otm = [
        0.5 * inter_height * force
        for inter_height, force in zip(interstorey_heights, floor_shear)
    ]
    overturning_moment = np.flip(
        [
            np.dot(
                np.array(heights[floor:]) - heights[floor],
                [0.,] + self.floor_forces_distribution[floor:]
            )
            for floor, _  in enumerate(heights)
        ]
    )
    delta_axials = [
        (otm - columns_otm)/self._lengths[-1]
        for otm, columns_otm in zip(overturning_moment[1:], columns_floor_otm)
    ]

    first_span_lenght = self._lengths[1]
    last_span_lenght = self._lengths[-1] - self._lengths[-2]

    # Computes equivalent moments for delta axials
    beam_shears = np.diff(delta_axials, prepend=[0.])
    moment_beams_upwind = 0.5 * beam_shears * first_span_lenght
    moment_beams_downwind = 0.5 * beam_shears * last_span_lenght

    moment_column_upwind = [moment_beams_upwind[0]]
    moment_column_downwind = [moment_beams_downwind[0]]
    for floor in range(1, self.floors):
        moment_column_upwind.append(moment_beams_upwind[floor] - moment_column_upwind[floor - 1])
        moment_column_downwind.append(moment_beams_upwind[floor] - moment_column_upwind[floor - 1])
    print(len(moment_beams_upwind))
    return {
        'upwind' : np.flip(
            [
                delta/moment
                for delta, moment in zip(delta_axials, moment_column_upwind)
            ]
        ),
        'downwind' : np.flip(
            [
                -delta/moment
                for delta, moment in zip(delta_axials, moment_column_downwind)
            ],
        ),
    }

