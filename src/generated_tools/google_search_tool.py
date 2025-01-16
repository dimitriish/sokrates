from toolbox.base_tool import Tool
import requests

class GoogleSearchTool(Tool):
    @property
    def tool_desc(self) -> str:
        return "Performs a Google search using the Google Search API and retrieves the results in format [{{title: link}}...]."

    @property
    def param_desc(self) -> str:
        return "query: The search term to use in Google."

    @staticmethod
    def run(query):
        """
        Performs a Google search using the Google Search API for the provided query.
        """
        try:
            api_key = "AIzaSyCsN66S0xHOhNxuDg1EWDQTakpbrbREndc"
            cx = "50b4305750e9341c1"
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "q": query,
                "key": api_key,
                "cx": cx
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            results = response.json()

            if "items" in results:
                return [
                    {"title": item["title"], "link": item["link"]} for item in results["items"]
                ]
            else:
                return "No results found."
        except Exception as e:
            return f"Error while performing Google search: {str(e)}"