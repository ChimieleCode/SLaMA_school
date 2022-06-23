from enum import Enum, auto

class NodeType(str, Enum):
    Internal    = 'internal'
    External    = 'external'
    TopInternal = 'top_internal'
    TopExternal = 'top_external'
    Base        = 'base'

class Direction(int, Enum):
    Positive    = 1
    Negative    = -1

class FailureType(Enum):
    ShearDuctile = auto()
    ShearFragile = auto()
    Moment       = auto()

class SectionType(Enum):
    Beam   = auto()
    Column = auto()

class ElementType(str, Enum):
    Joint   = 'joint'
    Beam    = 'beam'
    Column  = 'column'