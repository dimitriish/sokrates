from toolbox.base_tool import Tool
import subprocess

class InstallGoogleSearchApiClientLibrary(Tool):
    @property
    def tool_desc(self) -> str:
        return "This tool ensures that the Google Search API client library is installed in your Python environment. It checks if the library is already installed and installs it if necessary using pip."

    @property
    def param_desc(self) -> str:
        return ""

    @staticmethod
    def run(**kwargs):
        try:
            import googleapiclient.discovery  # noqa: F401
            result = "Google Search API client library is already installed."
        except ImportError:
            subprocess.run(["pip", "install", "google-api-python-client"], check=True)
            result = "Google Search API client library has been installed."

        return result