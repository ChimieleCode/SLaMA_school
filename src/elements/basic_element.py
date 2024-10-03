from functools import cache
from model.enums import Direction, FailureType
from src.elements.element import Element, MomentRotation
from src.sections.section import Section
from src.utils import intersection

class BasicElement(Element):
    """
    An element object containing data of the given structural member
    """

    def __init__(self, section: Section, L: float) -> None:
        """
        Defines an object containing the section data and element net lenght
        """
        self.__section = section
        self.__L = round(L, ndigits=2)

    def match(self, section: Section, L: float) -> bool:
        """
        Check if an instance match given data
        """
        return (self.__section.get_section_data() == section.get_section_data()) and (self.__L == round(L, ndigits=2))

    @cache
    def moment_rotation(self,
                        direction: Direction=Direction.Positive,
                        consider_shear_iteraction: bool=True,
                        axial: float=0.) -> dict:
        """
        Computes the moment rotation of the element

        :params direction: direction of bending (positive mean lower reinforcement is in tension)
        :params consider_shear_interaction: consider the limiting capability of shear capacity
        :params axial: axial stress on the section
        """
        moment_curvature = self.__section.moment_curvature(
            direction=direction,
            axial=axial
        )
        plastic_hinge = self.__section.plastic_hinge_length(self.__L)

        yielding_rotation = moment_curvature.phi_y * self.__L/6
        plastic_rotation = plastic_hinge * (moment_curvature.phi_c - moment_curvature.phi_y)

        moment_rotation = {
            'moment' : (moment_curvature.mom_y, moment_curvature.mom_c),
            'rotation' : (yielding_rotation, yielding_rotation + plastic_rotation)
        }

        if not consider_shear_iteraction:
            moment_rotation['failure'] = FailureType.Moment
            return moment_rotation

        shear_capacity = self.__section.shear_capacity(
            L=self.__L,
            axial=axial
        )

        shear_capacity_envelope = {
            'moment' : tuple(
                shear * self.__L/2 for shear in (shear_capacity.cap_undamaged, shear_capacity.cap_residual)
            ),
            'rotation' : tuple(
                yielding_rotation + (ductility - 1) * plastic_hinge * moment_curvature.phi_y
                for ductility in (shear_capacity.duc_undamaged, shear_capacity.duc_residual)
            ),
        }

        if shear_capacity_envelope['moment'][1] >= moment_rotation['moment'][1]:
            # shear failure not possible
            moment_rotation['failure'] = FailureType.Moment
            return moment_rotation


        if shear_capacity_envelope['moment'][0] <= moment_rotation['moment'][0]:
            # shear failure in elastic loading
            return {
                'moment' : (shear_capacity_envelope['moment'][0],) * 2,
                'rotation' : (
                    shear_capacity_envelope['moment'][0] * moment_rotation['rotation'][0] / moment_rotation['moment'][0],
                ) * 2,
                'failure' : FailureType.ShearFragile
            }

        if shear_capacity_envelope['rotation'][0] >= moment_rotation['rotation'][1]:

            if shear_capacity_envelope['moment'][0] >= moment_rotation['moment'][1]:
                # shear failure not possible
                moment_rotation['failure'] = FailureType.Moment
                return moment_rotation

        else:
            shear_interaction_slope = (
                (shear_capacity_envelope['moment'][1] - shear_capacity_envelope['moment'][0])
                / (shear_capacity_envelope['rotation'][1] - shear_capacity_envelope['rotation'][0])
            )
            moment_interaction_slope = (
                (moment_rotation['moment'][1] - shear_capacity_envelope['moment'][0])
                / (moment_rotation['rotation'][1] - shear_capacity_envelope['rotation'][0])
            )

            if shear_interaction_slope >= moment_interaction_slope:
                # shear failure not possible
                moment_rotation['failure'] = FailureType.Moment
                return moment_rotation

        if shear_capacity_envelope['rotation'][-1] <= moment_rotation['rotation'][-1]:
            # extension of shear interaction definition
            shear_capacity_envelope['rotation'] += (moment_rotation['rotation'][-1],)
            shear_capacity_envelope['moment'] += (shear_capacity_envelope['moment'][-1],)

        shear_interaction = intersection(
            (0,) + moment_rotation['rotation'],
            (0,) + moment_rotation['moment'],
            (0,) + shear_capacity_envelope['rotation'],
            (shear_capacity_envelope['moment'][0],) + shear_capacity_envelope['moment']
        )

        if shear_interaction is None:
            # shear failure not found
            moment_rotation['failure'] = FailureType.Moment
            return moment_rotation

        return {
            'moment' : (moment_rotation['moment'][0], shear_interaction['y']),
            'rotation' : (moment_rotation['rotation'][0], shear_interaction['x']),
            'failure' : FailureType.ShearDuctile
        }

    def get_plastic_hinge_lenght(self) -> float:
        """
        Get plastic hinge length for an element
        """
        return self.__section.plastic_hinge_length(self.__L)

    def get_element_lenght(self):
        """
        Get element net length
        """
        return self.__L

    def get_section(self) -> Section:
        """
        Get section object of the element
        """
        return self.__section

    def __str__(self) -> str:
        return self.__section.__str__() + f"L               : {self.__L}\n"


