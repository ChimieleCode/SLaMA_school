from enum import Enum, auto
from turtle import right

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
    Joint       = 'joint'
    Beam        = 'beam'
    Column      = 'column'
    AboveColumn = 'abovecolumn'
    BelowColumn = 'belowcolumn'
    LeftBeam    = 'leftbeam'
    RightBeam   = 'rightbeam'


class ImportanceClass(float, Enum):
    CuI     = 0.7
    CuII    = 1.
    CuIII   = 1.5
    CuIV    = 2


class SoilCategory(str, Enum):
    SoilA = "A"
    SoilB = "B"
    SoilC = "C"
    SoilD = "D"
    SoilE = "E"


class TopographicCategory(str, Enum):
    CatT1 = "T1"
    CatT2 = "T1"
    CatT3 = "T1"
    CatT4 = "T1"


class LifeTime(int, Enum):
    value1 = 10
    value2 = 50
    value3 = 100


# the space in front of the A+ is needed to have a sorted scale
class RiskClass(str, Enum):
    Ap = ' A+'
    A  = 'A'
    B  = 'B'
    C  = 'C'
    D  = 'D'
    E  = 'E'
    F  = 'F'
    G  = 'G'