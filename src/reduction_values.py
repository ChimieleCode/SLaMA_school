from __future__ import \
    annotations  # Enables postponed evaluation of type annotations (Python 3.7+)

from dataclasses import dataclass
from enum import Enum

# Default lambda values for the undamaged state (K, Q, D)
UNDAMAGED_LAMBDA = (1.0, 1.0, 1.0)


class DamageState(int, Enum):
    undamaged = 0
    slight = 1
    moderate = 2
    severe = 3


@dataclass(frozen=True)
class LambdaValues:
    """
    Data class to store lambda reduction factors for a component.
    - K: Stiffness reduction factor
    - Q: Strength reduction factor
    - D: Deformation reduction factor
    The class is immutable (frozen=True).
    """
    K: float
    Q: float
    D: float


class ElementFailureFEMA306(str, Enum):
    """
    Enum representing different types of element failure modes as per FEMA 306.
    The string values are used as keys or for display.
    """
    ColumnRCLapSlice = 'ColumnRCLapSlice'  # RC column lap splice failure
    ColumnRCShear = 'ColumnRCShear'        # RC column shear failure
    JointRC = 'JointRC'                    # RC joint failure


class FEMA306LambdaValues:
    """
    Class to encapsulate the mapping of element failure types and their corresponding lambda values for each damage state.
    """

    # Mapping of element failure types and their corresponding lambda values for each damage state.
    # The structure is:
    #   { ElementFailureFEMA306: { DamageState: LambdaValues } }
    _VALUES = {
        ElementFailureFEMA306.ColumnRCLapSlice: {
            DamageState.undamaged: LambdaValues(*UNDAMAGED_LAMBDA),  # No reduction
            DamageState.slight: LambdaValues(K=0.9, Q=1.0, D=1.0),   # Slight reduction in stiffness
            DamageState.moderate: LambdaValues(K=0.8, Q=0.5, D=1.0), # Moderate reduction in stiffness and strength
            DamageState.severe: LambdaValues(K=0.5, Q=0.5, D=1.0),   # Severe reduction in stiffness and strength
        },
        ElementFailureFEMA306.ColumnRCShear: {
            DamageState.undamaged: LambdaValues(*UNDAMAGED_LAMBDA),
            DamageState.slight: LambdaValues(K=0.9, Q=0.9, D=1.0),   # Slight reduction in both stiffness and strength
            DamageState.moderate: LambdaValues(K=0.7, Q=0.7, D=0.4), # Moderate reduction, including deformation
            DamageState.severe: LambdaValues(K=0.4, Q=0.2, D=0.4),   # Severe reduction in all factors
        },
        ElementFailureFEMA306.JointRC: {
            DamageState.undamaged: LambdaValues(*UNDAMAGED_LAMBDA),
            DamageState.slight: LambdaValues(K=0.9, Q=1.0, D=1.0),
            DamageState.moderate: LambdaValues(K=0.8, Q=0.5, D=0.9), # Moderate reduction, less in deformation
            DamageState.severe: LambdaValues(K=0.5, Q=0.5, D=1.0),
        }
    }

    @classmethod
    def get_lambda_values(cls, component: ElementFailureFEMA306, damage_state: DamageState) -> LambdaValues:
        """
        Retrieve the lambda reduction factors for a given component and damage state.

        Args:
            component (ElementFailureFEMA306): The type of structural component failure.
            damage_state (DamageState): The current damage state of the component.

        Returns:
            LambdaValues: The reduction factors (K, Q, D) for the specified component and damage state.

        Raises:
            KeyError: If the component or damage state is not defined in the mapping.
        """
        return cls._VALUES[component][damage_state]
