from signal import raise_signal
from model.frame_input import Regular2DFrameInput
from model.section_model import BasicSectionCollectionInput
from src.element import BasicElement, BasicElementCollection
from src.element import BasicSection

from model.global_constants import NODES_KJ_VALUES

class Regular2DFrame:
    """Regular2DFrame Class
    : frame_input from from frame data model :
    : sections from sections data model      :
    """
    elements = BasicElementCollection()

    def __init__(self, frame_input: Regular2DFrameInput, sections: BasicSectionCollectionInput):
        """ Defines an object containing the section data, the frame data 
        and the graph representation of the structural model """
        # Data model of frame
        self._data = frame_input

        # Data model of sections
        self._sections = sections
        self.beam_sections = [BasicSection(section) for section in sections.beams]
        self.column_sections = [BasicSection(section) for section in sections.columns]

        # Graph representation
        self._nodes_count = len(frame_input.loads)
        self._nodes = range(self._nodes_count)
        self._adj_list = {node: set() for node in self._nodes}
        self._popolate()

    @property
    def H(self):
        return self._data.H
    
    @property
    def L(self):
        return self._data.L
    
    @property
    def m(self):
        return self._data.m

    @property
    def loads(self):
        return self._data.loads
    
    @property
    def verticals(self):
        return len(self._data.L)

    @property
    def spans(self):
        return len(self._data.L) - 1
    
    @property
    def floors(self):
        return len(self._data.H)
    
    @property
    def storey_heights(self):
        return [current - previous for previous, current in zip([0] + self.H, self.H)]

    @property
    def span_lengths(self):
        return [current - previous for previous, current in zip(self.L, self.L[1:])]
    
    @property
    def frame_data(self):
        return self._data

    @property
    def floor_forces_distribution(self):
        # See §7.3.3.2 of NTC2018
        force_height = sum(mass * height for mass, height in zip(self.m, self.H))
        return tuple((mass * height) / force_height for mass, height in zip(self.m, self.H))


    # Methods
    def does_node_exist(self, node: int) -> bool:
        """Checks if the graph contains given node"""
        return node in self._nodes

    def get_node_elements(self, node: int) -> list:
        """Returns the elements connected to specified node [(node-i, node-j, element), ...] """
        if not(self.does_node_exist(node)):
            raise IndexError('Given node does not exist')
        elements = list()
        for neighbour in self._adj_list[node]:
            elements.append((node, *neighbour))
        return elements


    def get_node_id(self, floor: int, vertical: int) -> int:
        """ Returns the node id given floor and vertical """
        if floor > self.floors or floor < 0:
            raise IndexError('Specified span does not exist')
        if vertical > self.spans or vertical < 0:
            raise IndexError('Specified span does not exist')
        return (floor * self.verticals) + vertical


    def get_node_floor(self, node: int) -> int:
        """ Returns the node floor location given the node id """
        if not(self.does_node_exist):
            raise IndexError('Given node does not exist')
        return int(node / self.verticals)
    

    def get_node_vertical(self, node: int) -> int:
        """ Returns the node vertical location given the node id """
        if not(self.does_node_exist):
            raise IndexError('Given node does not exist')
        return node % self.verticals


    def get_node_position(self, node: int) -> dict:
        """ Returns the node location {'vertical' : ..., 'floor' : ...} given the id """
        if not(self.does_node_exist):
            raise IndexError('Given node does not exist')
        return {
            'vertical': self.get_node_vertical(node),
            'floor': self.get_node_floor(node)
        }


    def get_node_coordinates(self, node: int) -> dict:
        """ Returns the node coordinates {'X' : ..., 'Z' : ...} given the id """
        if not(self.does_node_exist):
            raise IndexError('Given node does not exist')
        position = self.get_node_position(node)
        return {
            'X': self.L[position['vertical']],
            'Z': self.H[position['floor']]
        }


    def get_node_load(self, node: int) -> float:
        """ Get the load on a given node """
        if not(self.does_node_exist):
            raise IndexError('Given node does not exist')
        return self.loads[node]
    

    def get_interstorey_height(self, floor: int) -> float:
        """ Returns the interstorey height of given storey """
        if floor > self.floors or floor < 0:
            raise IndexError('Specified span does not exist')
        if floor == 0:
            return self.H[0]
        else:
            return self.H[floor] - self.H[floor - 1]
    

    def get_span_length(self, span: int) -> float:
        """ Returns the span lenght given the span number starting from 0"""
        if span >= self.spans or span < 0:
            raise IndexError('Specified span does not exist')
        else:
            return self.L[span + 1] - self.L[span]


    def get_delta_axial(self, node: int) -> float:
        """ Returns the deltaN value normalized for a column moment of 1 kNm given the id of node"""
        # Determines the influence lenght and sign of Delta_N
        if self.get_node_vertical(node) == 0:
            influence_length = self.span_lengths[0] / 2
            delta_N = 1
        elif self.get_node_vertical(node) == self.spans:
            influence_length = self.span_lengths[-1] / 2
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
        delta_N = delta_N * (sum(force * height for force, height in zip(self.floor_forces_distribution[floor:], self.H[floor:])) - 0.5 * interstorey_height * floor_shear) / self.L[-1]
        M_col = 0.5 * floor_shear * interstorey_height * influence_length/self.L[-1]
        return delta_N / M_col


    def get_subassembly(self, node: int) -> dict:
        """ Returns the subassemply data as dict """
        floor = self.get_node_floor(node)
        vertical = self.get_node_vertical(node)
        subassembly = dict()

        # Identifies node type
        node_type = ''
        if floor == self.floors:
            node_type += 'top'
        elif floor == 0:
            node_type += 'base'

        if vertical == self.spans:
            node_type += 'right'
        elif vertical == 0:
            node_type += 'left'

        subassembly['type'] = node_type

        # Gets subassembly elements data
        subassembly_elements = self.get_node_elements(node)
        for element in subassembly_elements:
            if element[1] == element[0] + self.verticals:
                subassembly['upper'] = element[2]
                continue
            if element[1] == element[0] - self.verticals:
                subassembly['lower'] = element[2]
                continue
            if element[1] == element[0] - 1:
                subassembly['left'] = element[2]
                continue
            if element[1] == element[0] + 1:
                subassembly['right'] = element[2]
                continue

        # Gets the axial stress acting on the node
        subassembly['axial'] = sum(self.loads[node::self.verticals])

        # Computes delta axial
        subassembly['delta_axial'] = self.get_delta_axial(node)

        # Computes kj to be modified
        subassembly['kj'] = NODES_KJ_VALUES.get(node_type, 0)
        return subassembly


    # Private Methods
    def _column_lenght(self, floor: int, vertical: int) -> dict:
        """ Computes the shear lenghts of specified element"""
        if floor == 0:
            H_storey = self._data.H[0]
        else:
            H_storey = self._data.H[floor] - self._data.H[floor - 1]

        if vertical == 0:
            # Gets the tag of the first beam section connected on top
            beam_tag = self._data.beams[floor][0]
            return {
                'tag': self._data.columns[floor][0],
                'lenght': round((H_storey - self._sections.beams[beam_tag].h), ndigits=2)
            }
        
        elif vertical == self.spans:
            # Gets the tag of the last beam section connected on top
            beam_tag = self._data.beams[floor][-1]
            return {
                'tag': self._data.columns[floor][-1],
                'lenght': round((H_storey - self._sections.beams[beam_tag].h), ndigits=2)
            }
        else:
            beam_tag_1 = self._data.beams[floor][vertical]
            beam_tag_2 = self._data.beams[floor][vertical - 1]
            return {
                'tag': self._data.columns[floor][vertical],
                'lenght': round((H_storey - max(self._sections.beams[beam_tag_1].h, self._sections.beams[beam_tag_2].h)), ndigits=2)
            }


    def _beam_lenght(self, floor: int, span: int) -> dict:
        L_span = self._data.L[span + 1] - self._data.L[span]
        column_tag_1 = self._data.columns[floor][span]
        column_tag_2 = self._data.columns[floor][span + 1]
        return{
            'tag': self._data.beams[floor][span],
            'lenght': round((L_span - 0.5 * (self._sections.columns[column_tag_1].h + self._sections.columns[column_tag_2].h)), ndigits=2)
        }
    

    def _add_element(self, node1: int, node2: int, element: BasicElement) -> None:
        """ Adds a element column to frame. """
        self._adj_list[node1].add((node2, element))
        self._adj_list[node2].add((node1, element))


    def _popolate(self) -> None:
        """ Defines the graph structure starting from the frame data. """
        n_columns = len(self._data.L)

        def __add_storey_columns(floor: int) -> None:
            """ Adds all the columns of a given floor. """
            for vertical in range(n_columns):
                node = vertical + (floor * n_columns)
                column_data = self._column_lenght(floor, vertical)
                section = self.elements.add_column_section(self.column_sections[column_data['tag']], column_data['lenght'])
                self._add_element(node, node + n_columns, section)
        
        def __add_storey_beams(floor: int) -> None:
            """ Adds all the beams of a given floor. """
            for span in range(n_columns - 1):
                node = span + ((floor + 1) * n_columns)
                beam_data = self._beam_lenght(floor, span)
                section = self.elements.add_beam_section(self.beam_sections[beam_data['tag']], beam_data['lenght'])
                self._add_element(node, node + 1, section)
        
        for floor, _ in enumerate(self._data.H):
            __add_storey_beams(floor)
            __add_storey_columns(floor)


    def __repr__(self) -> str:
        print_ = ''
        for key, item in  self._adj_list.items():
            print_ += f'node {key} : {item} \n'
        return print_


    def __str__(self) -> str:
        return f"""
        Regular2DFrame Object
        verticals   : {self.verticals}
        floors      : {self.floors}
        L           : {self.L}
        H           : {self.H}
        m           : {self.m}
        loads       : {self.loads}
        sections    : .elements
        graph       : use repr()
        """