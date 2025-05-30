from pydantic import BaseModel
from typing import Any
from enum import Enum
from pathlib import Path

CONFIG_PATH = Path('./src/conf/config.yaml')

# -------------------------------------------------------------------------------------------------
# Validation Enums
# -------------------------------------------------------------------------------------------------
class MomentCurvatureAlg(str, Enum):
    StressBlock = 'stress_block'

class ShearFormula(str, Enum):
    NTC2018 = 'NTC2018'
    NZSEE2017 = 'NZSEE2017'

class DomainMNAlg(str, Enum):
    FourPoints = 'four_points'

class SubHyerarchyAlg(str, Enum):
    Total = 'tot'
    Average = 'avg'
    Lowest = 'low'

class SubStiffnessAlg(str, Enum):
    Average = 'avg'
    Lowest = 'low'

# -------------------------------------------------------------------------------------------------
# Config data model
# -------------------------------------------------------------------------------------------------

class NodeTensionValues(BaseModel):
    internal : float
    external : float
    top_internal : float
    top_external : float
    base : Any

class NodeRotations(BaseModel):
    yielding : float
    ultimate : float

class NodesConfig(BaseModel):
    tension_kj_values : NodeTensionValues
    compression_kj_value : float
    external_node_rotation : NodeRotations
    internal_node_rotation : NodeRotations
    cracking_rotation : float

class ElementConfig(BaseModel):
    moment_curvature : MomentCurvatureAlg
    moment_shear_interaction : bool
    shear_formulation : ShearFormula
    domain_mn : DomainMNAlg

class SubassemblyConfig(BaseModel):
    sub_hierarchy : SubHyerarchyAlg
    sub_stiffness : SubStiffnessAlg

class MNINTConfig(BaseModel):
    nodes: NodesConfig
    element_settings: ElementConfig
    subassembly_settings: SubassemblyConfig

