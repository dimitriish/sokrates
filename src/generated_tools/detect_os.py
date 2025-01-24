from toolbox.base_tool import Tool

class DetectOSTool(Tool):
    @property
    def tool_desc(self) -> str:
        return "Determines the operating system of the current machine to ensure compatibility when launching applications or services."

    @property
    def param_desc(self) -> str:
        return ""

    @staticmethod
    def run(**kwargs):
        import platform
        os_name = platform.system()
        return f"The detected operating system is: {os_name}"