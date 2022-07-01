from model.enums import Direction
from src.plotting import plot_PAM, plot_base_shear, plot_ADRS
from src.performance import compute_ISV, compute_PAM, get_risk_class
from src.scripts import convert_to_section_collection
from src.utils import export_to_json, import_from_json
from src.hazard import NTC2018SeismicHazard
from model.validation import Regular2DFrameInput, BasicSectionCollectionInput, SimpleMaterialInput, NTC2018HazardInput
from src.steel.steel import Steel   # does not see the package
from src.concrete import Concrete
from src.sections import BasicSection
from src.frame import RegularFrameBuilder
from src.elements import BasicElement
from src.subassembly import SubassemblyFactory
from src.capacity import column_sidesway, beam_sidesway, mixed_sidesway, mixed_sidesway_low_yielding

def main():
    """
    Main process
    """
    # Import frame data
    frame_dct = import_from_json('.\Inputs\Frame.json')
    # Validate frame data
    validated_frame = Regular2DFrameInput(
        **frame_dct
    )

    # Import section data
    sections_dct = import_from_json('.\Inputs\Sections.json')
    # validate section data
    validated_sections = BasicSectionCollectionInput(
        **sections_dct
    )

    # Import material data
    materials_dct = import_from_json('.\Inputs\Materials.json')
    # Validate material data
    validated_materials = SimpleMaterialInput(
        **materials_dct
    )

    # Instansiate material objects
    steel = Steel(**validated_materials.steel.__dict__)
    concrete = Concrete(**validated_materials.concrete.__dict__)

    # Instanciate Section Data and visitors
    sections = convert_to_section_collection(
        validated_sections,
        concrete,
        steel,
        section_type=BasicSection
    )

    # Build frame model
    frame_builder = RegularFrameBuilder(
        frame_data=validated_frame,
        sections=sections,
        element_object=BasicElement
    )
    frame_builder.build_frame()
    frame = frame_builder.get_frame()

    # Get subassemblies
    subassemly_factory = SubassemblyFactory(frame=frame)

    # Compute capacity
    # beam_sway_capacity = beam_sidesway(
    #     sub_factory=subassemly_factory,
    #     frame=frame
    # )
    # column_sway_capacity = column_sidesway(
    #     sub_factory=subassemly_factory,
    #     frame=frame
    # )
    mixed_sway_capacity = mixed_sidesway(
        sub_factory=subassemly_factory,
        frame=frame
    )
    # mixed_sway_capacity_low = mixed_sidesway_low_yielding(
    #     sub_factory=subassemly_factory,
    #     frame=frame
    # )

    # # Export results
    # export_to_json(
    #     filepath='.\Outputs\\beam_sway.json',
    #     data=beam_sway_capacity.__dict__
    # )
    # export_to_json(
    #     filepath='.\Outputs\\column_sway.json',
    #     data=column_sway_capacity.__dict__
    # )
    # export_to_json(
    #     filepath='.\Outputs\\mixed_sway.json',
    #     data=mixed_sway_capacity.__dict__
    # )
    # export_to_json(
    #     filepath='.\Outputs\\mixed_sway_low.json',
    #     data=mixed_sway_capacity_low
    # )

    # # Performance
    # hazard_dct_SLV = import_from_json('.\Inputs\Hazard_SLV.json')
    # validated_hazard_input_SLV = NTC2018HazardInput(
    #     **hazard_dct_SLV
    # )
    # hazard_spectra_SLV = NTC2018SeismicHazard(validated_hazard_input_SLV)
    
    # hazard_dct_SLD = import_from_json('.\Inputs\Hazard_SLD.json')
    # validated_hazard_input_SLD = NTC2018HazardInput(
    #     **hazard_dct_SLD
    # )
    # hazard_spectra_SLD = NTC2018SeismicHazard(validated_hazard_input_SLD)

    # new_building_standard = compute_ISV(
    #     capacity=mixed_sway_capacity,
    #     hazard=hazard_spectra_SLV
    # )
    # expected_annual_loss = compute_PAM(
    #     capacity=mixed_sway_capacity,
    #     hazard=[hazard_spectra_SLD, hazard_spectra_SLV]
    # )
    # plot_PAM(
    #     expected_annual_loss,
    #     'r',
    #     '.\Graphs\PAM.png'
    # )
    # plot_ADRS(
    #     mixed_sway_capacity,
    #     hazard_spectra_SLV,
    #     new_building_standard,
    #     save_path='.\Graphs\ADRS.png'
    # )



# Profile Mode
if __name__ == '__main__':
    import cProfile
    import pstats

    with cProfile.Profile() as pr:
        main()

    stats = pstats.Stats(pr)
    stats.sort_stats(pstats.SortKey.TIME)
    stats.print_stats()
    # can be optimized the solution for intersection (ditch scipy and lambdas)

