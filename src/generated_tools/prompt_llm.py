from toolbox.base_tool import Tool
from utils.ollama_utils import ollama_call

class PromptLLM(Tool):
    @property
    def tool_desc(self) -> str:
        return "Sends a prompt to a specified LLM model and retrieves the response."

    @property
    def param_desc(self) -> str:
        return "system_prompt: str, user_prompt: str"

    @staticmethod
    def run(system_prompt, user_prompt):
        """
        Calls Ollama LLM with the given messages and model.
        messages should be a list of dicts like:
        [
           {"role": "system", "content": "..."},
           {"role": "user", "content": "..."}
        ]
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        try:
            response = ollama_call(messages)
            return response
        except Exception as e:
            return f"Error while calling the LLM: {str(e)}"