from src.subassembly import Subassembly

class SubassemblyCollection:

    __subassemblies = dict()

    def add_subassembly(self, subassembly: Subassembly) -> None:
        """Adds a subassembly to the colleciton, existing subassembly with matching node numer are overwritten."""
        self.__subassemblies[subassembly.node] = subassembly
    
    def reset(self) -> None:
        """Clears the subassembly collection."""
        self.__subassemblies = dict()