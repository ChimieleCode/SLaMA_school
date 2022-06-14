from model.enums import Direction
from src.elements.element import Element
from src.sections.section import Section


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

    def moment_rotation(self, direction: Direction = Direction.Positive, axial: float=0.) -> dict:
        """
        Computes the moment rotation of the element
        """
        moment_curvature = self.__section.moment_curvature(
            direction=direction,
            axial=axial
        )
        plastic_hinge = self.__section.plastic_hinge_length(self.__L)

        yielding_rotation = moment_curvature['yielding']['curvature'] * self.__L/6
        plastic_rotation = plastic_hinge * (moment_curvature['ultimate']['curvature'] 
                                            - moment_curvature['yielding']['curvature'])

        moment_rotation =  {
            'yielding' : {
                'moment' : moment_curvature['yielding']['moment'],
                'rotaton' : yielding_rotation
            },
            'ultimate' : {
                'moment' : moment_curvature['ultimate']['moment'],
                'rotaton' : yielding_rotation + plastic_rotation
            }
        }

        shear_capacity = self.__section.shear_capacity(
            L=self.__L,
            axial=axial
        )

        shear_capacity_envelope = {
            'moment' : tuple(
                shear * self.__L/2 for shear in shear_capacity['shear_capacity']
            ),
            'rotation' : tuple(
                yielding_rotation + (ductility - 1) * plastic_hinge * moment_curvature['yielding']['curvature'] 
                for ductility in shear_capacity['curvature_ductility']
            ),
        }

        # Code intersection
       
        return moment_rotation



    def shear_moment_interaction(self, axial: float=0.):
        """
        Computes the interaction between shear capacity and moment-rotation
        """

        # Might not be needed

    def get_element_lenght(self):
        return self.__L

    def get_section(self) -> Section:
        return self.__section
        
    def __str__(self) -> str:
        return self.__section.__str__() + f"L               : {self.__L}\n"


