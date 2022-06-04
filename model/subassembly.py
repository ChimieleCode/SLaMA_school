from dataclasses import field, dataclass
from re import A
from typing import Optional
from model.enums import NodeType
from model.global_constants import NODES_KJ_VALUES
from src.element import BasicElement

@dataclass
class Subassembly:

    node            : int
    delta_axial     : float
    axial           : float
    left_beam       : Optional[BasicElement] = field(default=None)
    right_beam      : Optional[BasicElement] = field(default=None)
    below_column    : Optional[BasicElement] = field(default=None)
    above_column    : Optional[BasicElement] = field(default=None)
    node_type       : NodeType = field(init=False)
    downwind        : bool = field(init=False)
    upwind          : bool = field(init=False)
    kj              : float = field(init=False)

    def __post_init__(self):
        self.node_type = self._find_nodetype()
        self.kj = NODES_KJ_VALUES[self.node_type.value]
        if self.delta_axial == 0:
            self.downwind = False
            self.upwind = False
        else:
            self.upwind = self.delta_axial > 0
            self.downwind = self.delta_axial < 0

    # Private methods

    def _find_nodetype(self):
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
    


        


