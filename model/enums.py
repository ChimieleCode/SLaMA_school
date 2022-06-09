from enum import Enum

class NodeType(str, Enum):
    Internal    = 'internal'
    External    = 'external'
    TopInternal = 'top_internal'
    TopExternal = 'top_external'
    Base        = 'base'

class Direction(int, Enum):
    Positive    = 1
    negative    = -1