from dataclasses import field, dataclass
from typing import Optional
from model.enums import NodeType
from model.global_constants import NODES_KJ_VALUES
from src.elements.element import Element

@dataclass
class Subassembly:

    node            : int
    delta_axial     : float
    axial           : float
    left_beam       : Optional[Element] = field(default=None)
    right_beam      : Optional[Element] = field(default=None)
    below_column    : Optional[Element] = field(default=None)
    above_column    : Optional[Element] = field(default=None)
    node_type       : NodeType = field(init=False)
    downwind        : bool = field(init=False)
    upwind          : bool = field(init=False)
    kj              : float = field(init=False)

    def __post_init__(self):
        self.node_type = self.__find_nodetype()
        self.kj = NODES_KJ_VALUES[self.node_type.value]
        if self.delta_axial == 0:
            self.downwind = False
            self.upwind = False
        else:
            self.upwind = self.delta_axial > 0
            self.downwind = self.delta_axial < 0

    # Private methods
    def __find_nodetype(self):
        """Finds the node type using a logic Tree."""
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
    

from src.frame.regular_frame import RegularFrame


class SubassemblyFactory:

    def __init__(self, frame: RegularFrame) -> None:
        """Subassembly Factory starting from frame data."""
        self.__frame = frame

    def get_subassembly(self, node: int) -> Subassembly:
        """Get the subassembly data given the node from the frame data."""
        subassembly = {
            'node' : node
        }
        # Gets subassembly elements data
        subassembly_elements = self.__frame.get_node_elements(node)
        for element in subassembly_elements:
            if element[1] == element[0] + self.__frame.verticals:
                subassembly['above_column'] = element[2]
                continue
            if element[1] == element[0] - self.__frame.verticals:
                subassembly['below_column'] = element[2]
                continue
            if element[1] == element[0] - 1:
                subassembly['left_beam'] = element[2]
                continue
            if element[1] == element[0] + 1:
                subassembly['right_beam'] = element[2]
                continue

        # Gets the axial stress acting on the node
        subassembly['axial'] = self.__frame.get_axial(node)
        # Computes delta axial
        subassembly['delta_axial'] = self.__frame.get_delta_axial(node)
        return Subassembly(**subassembly)

        


