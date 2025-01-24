from toolbox.base_tool import Tool

class GoogleSearch(Tool):
    @property
    def tool_desc(self) -> str:
        return "This tool opens a web browser with Google's search results for a specified query."

    @property
    def param_desc(self) -> str:
        return "query: The search query to be entered into Google's search bar."

    @staticmethod
    def run(**kwargs):
        query = kwargs.get('query')
        import webbrowser
        url = f"https://www.google.com/search?q={query}"
        webbrowser.open(url)
        return f"Opening Google search for '{query}'"