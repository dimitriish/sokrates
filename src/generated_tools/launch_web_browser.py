from toolbox.base_tool import Tool

class LaunchWebBrowser(Tool):
    @property
    def tool_desc(self) -> str:
        return "A tool that instructs the LLM to launch a web browser by executing a command specific to the operating system."

    @property
    def param_desc(self) -> str:
        return ""

    @staticmethod
    def run(**kwargs):
        import os

        if os.name == 'nt':
            os.system('start chrome')
        elif os.name == 'posix':
            os.system('open -a "Google Chrome"')
        elif os.name == 'java':
            os.system('xdg-open http://www.google.com')

        result = "Web browser launched"
        return result