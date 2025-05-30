from pydantic import BaseModel
from model.enums import ImportanceClass, SoilCategory, LifeTime, TopographicCategory

class NTC2018HazardInput(BaseModel):
    ag                    : float
    F0                    : float
    Tc_star               : float
    Cu                    : ImportanceClass
    Vn                    : LifeTime
    soil_category         : SoilCategory
    topographic_category  : TopographicCategory
 



    