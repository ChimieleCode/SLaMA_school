from enum import Enum

class NodeType(str, Enum):
    Internal    = 'internal'
    External    = 'external'
    TopInternal = 'top_internal'
    TopExternal = 'top_external'
    Base        = 'base'