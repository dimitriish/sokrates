from abc import ABC, abstractmethod

class Tool(ABC):
    @property
    def tool_desc(self) -> str:
        """Detailed description of the tool."""
        pass

    @property
    def param_desc(self) -> str:
        """Description of the parameters required by the tool."""
        pass

    @staticmethod
    @abstractmethod
    def run(**kwargs):
        """Abstract static method to execute the tool."""
        pass