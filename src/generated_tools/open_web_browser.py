from toolbox.base_tool import Tool

class open_web_browser(Tool):
    @property
    def tool_desc(self) -> str:
        return "Opens a web browser with the specified URL."

    @property
    def param_desc(self) -> str:
        return "url: The URL of the website you want to open."

    @staticmethod
    def run(**kwargs):
        import webbrowser
        url = kwargs.get('url')
        if url:
            webbrowser.open(url)
        else:
            raise ValueError("URL parameter is required")