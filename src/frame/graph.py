
from typing import List, Set, Tuple
from src.elements.element import Element

class NodeNotFoundError(Exception):
    """
    Raised when node is not found
    """
    message = 'given node was not found'

    def __str__(self) -> str:
        return self.message



class Graph:

    def __init__(self, node_count: int) -> None:
        """
        Graph data structure
        """
        self.__node_count = node_count
        self.__nodes = range(node_count)
        self.__adj_list = {node: set() for node in self.__nodes}
    
    def get_nodes(self):
        return self.__nodes

    def add_node(self) -> int:
        """
        Adds a node to the graph and returns new node id
        """
        self.__node_count += 1
        self.__nodes = range(self.__node_count)
        self.__adj_list[self.__node_count] = set()

    def add_arch(self, i_node: int, j_node: int, weight: Element) -> None:
        """
        Adds a oriented arch to the graph that points to node i starting from j
        """
        self.__adj_list[i_node].add((j_node, weight))

    def does_node_exist(self, node: int) -> bool:
        """
        Checks if a given node is defined in the graph
        """
        return node in self.__nodes

    def get_node_elements(self, node: int) -> List[Tuple[int, int, Element]]:
        """
        Returns the elements connected to specified node [(node-i, node-j, element), ...]
        """
        if node not in self.__nodes:
            raise NodeNotFoundError
        elements = list()
        for neighbour in self.__adj_list[node]:
            elements.append((node, *neighbour))
        return elements

    def __repr__(self) -> str:
        print_ = ''
        for key, item in  self.__adj_list.items():
            print_ += f'node {key} : {item} \n'
        return print_



    


    
