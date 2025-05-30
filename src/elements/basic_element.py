from functools import cache, wraps
from model.enums import Direction, FailureType

from src.elements import Element, MomentRotation

from src.sections import Section
from src.utils import intersection


class BasicElement(Element):
    """
    An element object containing data of the given structural member
    """

    def __init__(self, section: Section, L: float) -> None:
        """
        Defines an object containing the section data and element net lenght
        """
        self._section = section
        self._L = round(L, ndigits=2)

    def match(self, section: Section, L: float) -> bool:
        """
        Check if an instance match given data
        """
        return (self._section.get_section_data() == section.get_section_data()) and (self._L == round(L, ndigits=2))

    @cache
    def moment_rotation(self,   # pyright: ignore[reportIncompatibleMethodOverride]
                        direction: Direction=Direction.Positive,
                        consider_shear_iteraction: bool = True,
                        axial: float = 0.) -> MomentRotation:
        """
        Computes the moment rotation of the element

        :params direction: direction of bending (positive mean lower reinforcement is in tension)
        :params consider_shear_interaction: consider the limiting capability of shear capacity
        :params axial: axial stress on the section
        """
        moment_curvature = self._section.moment_curvature(
            direction=direction,
            axial=axial
        )
        plastic_hinge = self._section.plastic_hinge_length(self._L)

        yielding_rotation = moment_curvature.phi_y * self._L/6
        plastic_rotation = plastic_hinge * (moment_curvature.phi_c - moment_curvature.phi_y)

        capping_rotation = yielding_rotation + plastic_rotation

        # Ignore shear interaction, no action needed
        if not consider_shear_iteraction:
            return MomentRotation(
                mom_y=moment_curvature.mom_y,
                mom_c=moment_curvature.mom_c,
                rot_y=yielding_rotation,
                rot_c=capping_rotation,
                failure=FailureType.Moment
            )

        # Get the shear capacity
        shear_capacity = self._section.shear_capacity(
            L=self._L,
            axial=axial
        )

        # Compute the evelope in terms of moment-rotation
        shear_moment_cap_undamaged = shear_capacity.cap_undamaged * self._L/2
        shear_moment_cap_residual = shear_capacity.cap_residual * self._L/2

        shear_rotation_undamaged = yielding_rotation + (shear_capacity.duc_undamaged - 1) * plastic_hinge * moment_curvature.phi_y
        shear_rotation_residual = yielding_rotation + (shear_capacity.duc_residual - 1) * plastic_hinge * moment_curvature.phi_y

        # Residual capacity shear is higher than maximum capacity of section, no shear interaction
        if shear_moment_cap_residual >= moment_curvature.mom_c:
            return MomentRotation(
                mom_y=moment_curvature.mom_y,
                mom_c=moment_curvature.mom_c,
                rot_y=yielding_rotation,
                rot_c=capping_rotation,
                failure= FailureType.Moment
            )

        # The elastic strenght of section is higher than the elastic capaity in shear
        # Shear interaction in elastic loading
        if shear_moment_cap_undamaged <= moment_curvature.mom_y:
            failure_rotation = shear_moment_cap_undamaged * yielding_rotation / moment_curvature.mom_y
            return MomentRotation(
                mom_y=shear_moment_cap_undamaged,
                mom_c=shear_moment_cap_undamaged,
                rot_y=failure_rotation,
                rot_c=failure_rotation,
                failure= FailureType.ShearFragile
            )

        # The section reaches his ductility in moment before the shear degradation and cannot reach the shear capacity
        # No shear interaction is possible
        if (shear_rotation_undamaged >= capping_rotation)\
            and (shear_moment_cap_undamaged >= moment_curvature.mom_c):

            return MomentRotation(
                mom_y=moment_curvature.mom_y,
                mom_c=moment_curvature.mom_c,
                rot_y=yielding_rotation,
                rot_c=capping_rotation,
                failure= FailureType.Moment
            )

        shear_interaction_slope = (shear_moment_cap_residual - shear_moment_cap_undamaged)\
                                   / (shear_rotation_residual - shear_rotation_undamaged)
        moment_interaction_slope = (moment_curvature.mom_c - shear_moment_cap_undamaged)\
                                    / (capping_rotation - shear_rotation_undamaged)

        # No intersection in the degrading part
        # No shear interaction
        if shear_interaction_slope >= moment_interaction_slope:
            return MomentRotation(
                mom_y=moment_curvature.mom_y,
                mom_c=moment_curvature.mom_c,
                rot_y=yielding_rotation,
                rot_c=capping_rotation,
                failure= FailureType.Moment
            )

        shear_envelope_moment = (shear_moment_cap_undamaged, shear_moment_cap_undamaged, shear_moment_cap_residual)
        shear_envelope_rotation = (0, shear_rotation_undamaged, shear_rotation_residual)

        beam_curve_moment = (0, moment_curvature.mom_y, moment_curvature.mom_c)
        beam_curve_rotation = (0, yielding_rotation, capping_rotation)

        # Beam ductility overshoots the shear envelope I adjust the shear envelope
        if shear_rotation_residual <= capping_rotation:
            # extension of shear interaction definition
            shear_envelope_rotation += (capping_rotation,)
            shear_envelope_moment += (shear_moment_cap_residual,)

        shear_interaction = intersection(
            beam_curve_rotation,
            beam_curve_moment,
            shear_envelope_rotation,
            shear_envelope_moment
        )

        if shear_interaction is None:
            return MomentRotation(
                mom_y=moment_curvature.mom_y,
                mom_c=moment_curvature.mom_c,
                rot_y=yielding_rotation,
                rot_c=capping_rotation,
                failure= FailureType.Moment
            )

        rot_c, mom_c = shear_interaction
        return MomentRotation(
            mom_y=moment_curvature.mom_y,
            mom_c=mom_c,
            rot_y=yielding_rotation,
            rot_c=rot_c,
            failure= FailureType.ShearDuctile
        )

    def get_plastic_hinge_lenght(self) -> float:
        """
        Get plastic hinge length for an element
        """
        return self._section.plastic_hinge_length(self._L)

    def get_element_lenght(self):
        """
        Get element net length
        """
        return self._L

    def get_section(self) -> Section:
        """
        Get section object of the element
        """
        return self._section

    def __str__(self) -> str:
        return self._section.__str__() + f"L               : {self._L}\n"


