import math
from typing import List
from src.hazard.hazard_spectra import SeismicHazard
from model.enums import SoilCategory, TopographicCategory
from model.validation import NTC2018HazardInput
from model.global_constants import G, PI
from functools import cache

class NTC2018SeismicHazard(SeismicHazard):
    """
    SeismicHazard class
    """
    def __init__(self, haz_input: NTC2018HazardInput):
        self.__hazard_input = haz_input
    
    @property
    @cache
    def Cc(self) -> float:
        """
        Returns the Cc NT2018 constant for class soil category
        """
        if self.__hazard_input.soil_category == SoilCategory.SoilA:
            return 1.
    
        if self.__hazard_input.soil_category == SoilCategory.SoilB:
            return 1.1 * self.__hazard_input.Tc_star**-0.2

        if self.__hazard_input.soil_category == SoilCategory.SoilC:
            return 1.05 * self.__hazard_input.Tc_star**-0.33

        if self.__hazard_input.soil_category == SoilCategory.SoilD:
            return 1.25 * self.__hazard_input.Tc_star**-0.5
            
        if self.__hazard_input.soil_category == SoilCategory.SoilE:
            return 1.15 * self.__hazard_input.Tc_star**-0.4
        
    @property
    @cache
    def Tc(self) -> float:
        """
        Returns the period corresponding to the end of the plateau
        """
        return self.Cc * self.__hazard_input.Tc_star
    
    @property
    @cache
    def Tb(self) -> float:
        """
        Returns the period corrisponding to the start of the plateau
        """
        return self.Tc/3

    @property
    @cache
    def Td(self) -> float:
        """
        Returns the period corrisponding to the start of the constant displacements
        """
        return 4. * self.__hazard_input.ag + 1.6

    @property
    @cache
    def Ss(self) -> float:
        """
        Returns the soil coefficient
        """
        if self.__hazard_input.soil_category == SoilCategory.SoilA:
            return 1.
    
        if self.__hazard_input.soil_category == SoilCategory.SoilB:
            return min(
                1.2,
                max(
                    1.,
                    1.4 - 0.4 * self.__hazard_input.F0 * self.__hazard_input.ag
                )
            )

        if self.__hazard_input.soil_category == SoilCategory.SoilC:
            return min(
                1.5,
                max(
                    1.,
                    1.7 - 0.6 * self.__hazard_input.F0 * self.__hazard_input.ag
                )
            )

        if self.__hazard_input.soil_category == SoilCategory.SoilD:
            return min(
                1.8,
                max(
                    0.9,
                    2.4 - 1.5 * self.__hazard_input.F0 * self.__hazard_input.ag
                )
            )
            
        if self.__hazard_input.soil_category == SoilCategory.SoilE:
            return min(
                1.6,
                max(
                    1.,
                    2. - 1.1 * self.__hazard_input.F0 * self.__hazard_input.ag
                )
            )
    
    @property
    @cache
    def St(self) -> float:
        """
        Returns the topographic coefficient
        """
        if self.__hazard_input.topographic_category == TopographicCategory.CatT1:
            return 1.
        
        if self.__hazard_input.topographic_category == TopographicCategory.CatT2:
            return 1.2
        
        if self.__hazard_input.topographic_category == TopographicCategory.CatT3:
            return 1.2
        
        if self.__hazard_input.topographic_category == TopographicCategory.CatT4:
            return 1.4
    
    @cache
    def get_spectral_acceleration(self, period: float, damping: float = .05, scale_factor: float = 1.) -> float:
        """
        Computes the spectral acceleration
        
        :params period: the period at which the spectral acceleration is evaluated
        
        :params damping: the equivalent viscous damping
        
        :params scale_factor: the scale factor for the spectra
        """
        eta = scale_factor * max(
            0.55,
            math.sqrt(10/(5 + damping * 100))
        )
        if 0 <= period and period < self.Tb:
            return (
                self.__hazard_input.ag * self.Ss * self.St * eta * self.__hazard_input.F0 
                * (period/self.Tb + 1/(eta * self.__hazard_input.F0) * (1 - period/self.Tb))
            )
        if self.Tb <= period and period < self.Tc:
            return self.__hazard_input.ag * self.Ss * self.St * eta * self.__hazard_input.F0
        
        if self.Tc <= period and period < self.Td:
            return self.__hazard_input.ag * self.Ss * self.St * eta * self.__hazard_input.F0 * self.Tc/period
        
        if self.Td <= period:
            return self.__hazard_input.ag * self.Ss * self.St * eta * self.__hazard_input.F0 * self.Tc * self.Td/period**2
    
    @cache
    def get_spectral_displacement(self, period: float, damping: float = .05, scale_factor: float = 1.) -> float:
        """
        Computes the spectral displacement
        
        :params period: the period at which the spectral acceleration is evaluated
        
        :params damping: the equivalent viscous damping
        
        :params scale_factor: the scale factor for the spectra
        """
        return G * period**2 / (4 * PI**2) * self.get_spectral_acceleration(period, damping, scale_factor)

    @cache
    def periods_array(self, max_period: float = 4., npoints: int = 20) -> List[float]:
        """
        Computes a list of periods at which the spectra is going to be evaluated

        :params max_period: max period of the list

        :params npoints: number of periods in list excluding 0, Tb, Tc, Td
        """
        periods = {max_period/npoints * (i + 1) for i in range(npoints)}
        periods.add(0.)
        periods.add(self.Tb)
        periods.add(self.Tc)
        periods.add(self.Td)
        return sorted(list(periods))


    




    