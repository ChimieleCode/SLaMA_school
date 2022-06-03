from src.frame import Regular2DFrame
from src.utils import import_from_json
from model.frame_input import Regular2DFrameInput
from model.section_model import BasicSectionCollectionInput

def main():
    """ Main process. """

    #import frame data
    frame_dct = import_from_json('.\Inputs\Frame.json')

    #validate frame data
    frame = Regular2DFrameInput(
        **frame_dct
    )

    #import section data
    sections_dct = import_from_json('.\Inputs\Sections.json')

    #validate section data
    sections = BasicSectionCollectionInput(
        **sections_dct
    )

    #initiate the class
    structural_model = Regular2DFrame(frame, sections)

    # print(structural_model.elements.column_elements.__len__())

# Don t change
if __name__ == '__main__':
    main()
