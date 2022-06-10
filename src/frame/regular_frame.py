from functools import cache
from typing import List, Tuple
from model.validation.frame_input import Regular2DFrameInput
from src.frame.graph import Graph, NodeNotFoundError

class RegularFrame(Graph):
    
    def __init__(self, node_count: int, lengths: List[float], heights: List[float],
                 masses: List[float], loads: List[float]):
        """Defines a frame data structure as a graph."""
        super().__init__(node_count)
        self.__lenghts = lengths
        self.__heights = heights
        self.__masses = masses
        self.__loads = loads
    
    @property
    @cache
    def spans(self) -> int:
        return len(self.__lenghts) - 1

    @property
    @cache
    def verticals(self) -> int:
        return len(self.__lenghts)
    
    @property
    @cache
    def floors(self) -> int:
        return len(self.__heights)

    @property
    @cache
    def floor_forces_distribution(self) -> Tuple[float]:
        # See §7.3.3.2 of NTC2018
        force_height = sum(mass * height for mass, height in zip(self.__masses, self.__heights))
        return tuple((mass * height) / force_height for mass, height in zip(self.__masses, self.__heights))

    
    def get_node_id(self, floor: int, vertical: int) -> int:
        """Returns the node id given floor and vertical."""
        if floor > self.floors or floor < 0:
            raise NodeNotFoundError('Specified span does not exist')
        if vertical > self.spans or vertical < 0:
            raise NodeNotFoundError('Specified span does not exist')
        return (floor * self.verticals) + vertical
    
    def get_node_floor(self, node: int) -> int:
        """Returns the node floor location given the node id."""
        if not(self.does_node_exist(node)):
            raise NodeNotFoundError('Given node does not exist')
        return int(node / self.verticals)
    
    def get_node_vertical(self, node: int) -> int:
        """Returns the node vertical location given the node id."""
        if not(self.does_node_exist(node)):
            raise NodeNotFoundError('Given node does not exist')
        return node % self.verticals

    def get_node_position(self, node: int) -> dict:
        """Returns the node location {'vertical' : ..., 'floor' : ...} given the id."""
        if not(self.does_node_exist(node)):
            raise NodeNotFoundError('Given node does not exist')
        return {
            'vertical': self.get_node_vertical(node),
            'floor': self.get_node_floor(node)
        }
    
    def get_node_coordinates(self, node: int) -> dict:
        """Returns the node coordinates {'X' : ..., 'Z' : ...} given the id."""
        if not(self.does_node_exist(node)):
            raise NodeNotFoundError('Given node does not exist')
        position = self.get_node_position(node)
        return {
            'X': self.L[position['vertical']],
            'Z': self.__heights[position['floor']]
        }

    def get_interstorey_height(self, floor: int) -> float:
        """Returns the interstorey height of given storey."""
        if floor > self.floors or floor < 0:
            raise NodeNotFoundError('Specified span does not exist')
        if floor == 0:
            return self.__heights[0]
        else:
            return self.__heights[floor] - self.__heights[floor - 1]
    
    def get_span_length(self, span: int) -> float:
        """Returns the span lenght given the span number starting from 0."""
        if span >= self.spans or span < 0:
            raise NodeNotFoundError('Specified span does not exist')
        else:
            return self.__lenghts[span + 1] - self.__lenghts[span]

    def get_delta_axial(self, node: int) -> float:
        """Returns the deltaN value normalized for a column moment of 1 kNm given the id of node."""
        # Determines the influence lenght and sign of Delta_N
        if self.get_node_vertical(node) == 0:
            influence_length = self.get_span_length(1) / 2
            delta_N = 1
        elif self.get_node_vertical(node) == self.spans:
            influence_length = self.get_span_length(self.spans - 1) / 2
            delta_N = -1
        else:
            # If node is internal, no delta is present
            return 0
        # Get floor level below
        floor = self.get_node_floor(node) - 1
        # Base nodes does not have a floor below
        if floor < 0:
            floor = 0
        floor_shear = sum(self.floor_forces_distribution[floor:])
        interstorey_height = self.get_interstorey_height(floor)
        # Delta N normalization
        delta_N = delta_N * (sum(force * height for force, height in zip(self.floor_forces_distribution[floor:], self.__heights[floor:])) - 0.5 * interstorey_height * floor_shear) / self.__lenghts[-1]
        M_col = 0.5 * floor_shear * interstorey_height * influence_length/self.__lenghts[-1]
        return delta_N / M_col  

    def get_axial(self, node: int) -> float:
          """Get the total axial force acting on given node."""
          return round(sum(self.__loads[node::self.verticals]), ndigits=2)

    def __str__(self) -> str:
        return f"""
        Regular2DFrame Object
        verticals   : {self.verticals}
        floors      : {self.floors}
        L           : {self.__lenghts}
        H           : {self.__heights}
        m           : {self.__masses}
        loads       : {self.__loads}
        sections    : .elements
        graph       : use repr()
        """





    
from src.collections.element_collection import ElementCollection
from src.collections.section_collection import SectionCollection
from src.elements.element import Element
    
class RegularFrameBuilder:

    def __init__(self, frame_data: Regular2DFrameInput, sections: SectionCollection, element_object: type[Element]) -> None:
        """This is class builds a frame given the sections and the validated frame input."""
        self.__frame_data = frame_data
        self.__sections = sections
        self.__element_object = element_object
        self.__elements = ElementCollection()
        self.__frame = RegularFrame(len(frame_data.loads), lengths=frame_data.L,
                                    heights=frame_data.H, masses=frame_data.m, 
                                    loads=frame_data.loads)

    def get_frame(self) -> RegularFrame:
        """Returns the built frame."""
        return self.__frame

    def get_elements(self) -> ElementCollection:
        """Get element collection."""
        return self.__elements

    def build_frame(self) -> None:
        """Defines the graph structure starting from the frame data."""
        def __add_storey_columns(floor: int) -> None:
            """Adds all the columns of a given floor."""
            for vertical in range(self.__frame.verticals):
                node = vertical + (floor * self.__frame.verticals)
                column_data = self.__column_lenght(floor, vertical)
                element = self.__elements.add_column_element(
                    section=self.__sections.get_columns()[column_data['tag']], 
                    L=round(column_data['lenght'], ndigits=2),
                    _elementClass=self.__element_object      
                )
                self.__add_element(node, node + self.__frame.verticals, element)

        def __add_storey_beams(floor: int) -> None:
            """Adds all the beams of a given floor."""
            for span in range(self.__frame.spans):
                node = span + ((floor + 1) * self.__frame.verticals)
                beam_data = self.__beam_lenght(floor, span)
                element = self.__elements.add_beam_element(
                    section=self.__sections.get_beams()[beam_data['tag']], 
                    L=round(beam_data['lenght'], ndigits=2),
                    _elementClass=self.__element_object
                )
                self.__add_element(node, node + 1, element)

        # Builds elements for each floor
        for floor, _ in enumerate(self.__frame_data.H):
            __add_storey_beams(floor)
            __add_storey_columns(floor)


    def __column_lenght(self, floor: int, vertical: int) -> dict:
        """Computes the shear lenghts of specified element."""
        if floor == 0:
            H_storey = self.__frame_data.H[0]
        else:
            H_storey = self.__frame_data.H[floor] - self.__frame_data.H[floor - 1]

        if vertical == 0:
            # Gets the tag of the first beam section connected on top
            beam_tag = self.__frame_data.beams[floor][0]
            return {
                'tag': self.__frame_data.columns[floor][0],
                'lenght': (H_storey - self.__sections.get_beams()[beam_tag].get_height())
            }
        elif vertical == self.__frame.spans:
            # Gets the tag of the last beam section connected on top
            beam_tag = self.__frame_data.beams[floor][-1]
            return {
                'tag': self.__frame_data.columns[floor][-1],
                'lenght': (H_storey - self.__sections.get_beams()[beam_tag].get_height())
            }
        else:
            beam_tag_1 = self.__frame_data.beams[floor][vertical]
            beam_tag_2 = self.__frame_data.beams[floor][vertical - 1]
            return {
                'tag': self.__frame_data.columns[floor][vertical],
                'lenght': (H_storey - max(self.__sections.get_beams()[beam_tag_1].get_height(), self.__sections.get_beams()[beam_tag_2].get_height()))
            }

        
    def __beam_lenght(self, floor: int, span: int) -> dict:
        L_span = self.__frame_data.L[span + 1] - self.__frame_data.L[span]
        column_tag_1 = self.__frame_data.columns[floor][span]
        column_tag_2 = self.__frame_data.columns[floor][span + 1]
        return{
            'tag': self.__frame_data.beams[floor][span],
            'lenght': (L_span - 0.5 * (self.__sections.get_columns()[column_tag_1].get_height() + self.__sections.get_columns()[column_tag_2].get_height()))
        }
    
    def __add_element(self, node1: int, node2: int, element: Element) -> None:
        """Adds a element column to frame."""
        self.__frame.add_arch(
            i_node=node1,
            j_node=node2,
            weight=element)
        # Non oriented graph
        self.__frame.add_arch(
            i_node=node2,
            j_node=node1,
            weight=element)
    

    


    
