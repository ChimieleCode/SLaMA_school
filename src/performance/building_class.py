from model.enums import RiskClass

def get_ISV_risk_class(IS_V: float) -> RiskClass:
    """
    Returns the risk class given IS-V
    """
    if IS_V > 1:
        return RiskClass.Ap
    
    if IS_V > 0.8:
        return RiskClass.A
    
    if IS_V > 0.6:
        return RiskClass.B
    
    if IS_V > 0.45:
        return RiskClass.C
    
    if IS_V > 0.3:
        return RiskClass.D
        
    if IS_V > 0.15:
        return RiskClass.E
    
    return RiskClass.F

def get_PAM_risk_class(PAM: float) -> RiskClass:
    """
    Returns the risk class given PAM
    """
    if PAM <= 0.5 :
        return RiskClass.Ap
    
    if PAM <= 1.:
        return RiskClass.A
    
    if PAM <= 1.5:
        return RiskClass.B
    
    if PAM <= 2.5:
        return RiskClass.C
    
    if PAM <= 3.5:
        return RiskClass.D
        
    if PAM <= 4.5:
        return RiskClass.E
    
    if PAM <= 7.5:
        return RiskClass.F
    
    return RiskClass.G


# def get_PAM_risk_class(PAM: float) -> RiskClass:
#     """
#     Returns the risk class given IS-V
#     """
#     fields = (
#         0.5,
#         1.,
#         1.5,
#         2.5,
#         3.5,
#         4.5,
#         7.5
#     )
#     classe = (
#         RiskClass.Ap,
#         RiskClass.A,
#         RiskClass.B,
#         RiskClass.C,
#         RiskClass.D,
#         RiskClass.E,
#         RiskClass.F,
#         RiskClass.G
#     )

#     for i, value in enumerate(fields):
#         if PAM <= value:
#             return classe[i]
    
#     return classe[-1]


def get_risk_class(IS_V: float, PAM: float) -> RiskClass:
    """
    Returns the lowest risk class given IS-V and PAM
    """
    return max(
        get_ISV_risk_class(IS_V),
        get_PAM_risk_class(PAM)
    )
    