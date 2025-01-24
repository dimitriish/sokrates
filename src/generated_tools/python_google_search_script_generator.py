from toolbox.base_tool import Tool

class PythonGoogleSearchScriptGenerator(Tool):
    @property
    def tool_desc(self) -> str:
        return "Generates a basic Python script structure that utilizes the Google Search API."

    @property
    def param_desc(self) -> str:
        return ""

    @staticmethod
    def run(**kwargs):
        script_template = """\
import os
from googleapiclient.discovery import build

def search_google(query, api_key, cse_id):
    service = build("customsearch", "v1", developerKey=api_key)
    res = service.cse().list(q=query, cx=cse_id).execute()
    return res.get("items", [])

if __name__ == "__main__":
    API_KEY = 'YOUR_API_KEY'
    CSE_ID = 'YOUR_CSE_ID'
    query = input("Enter your search query: ")
    results = search_google(query, API_KEY, CSE_ID)
    for result in results:
        print(result['link'])
"""
        return script_template