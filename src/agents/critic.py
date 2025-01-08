import json
import os
from utils.ollama_utils import ollama_call
import ast

def is_executable_script(tool_code):
    try:
        ast.parse(tool_code)
        return True
    except SyntaxError as e:
        print(f"Syntax Error: {e}")
        return False
    except Exception as e:
        print(f"Other Error: {e}")
        return False

class Critic:
    def __init__(self, tool_manager, model: str = "gemma2:2b"):
        self.tool_manager = tool_manager
        self.model = model

    def evaluate(self, subtask: dict, actor_output: dict) -> dict:
        """
        Evaluate the actor’s output to decide if the chosen tool and approach are correct.
        
        Parameters:
        - subtask: dict like {"subtask": "...", "description": "...", "success_criteria": "..."}
        - actor_output: dict like:
          {
            'completed': bool,
            'output': ...,
            'errors': ...,
            'chosen_tool': 'ToolName',
            'created_tool': bool
          }

        The Critic will:
        1. Fetch the tool code of the chosen tool (if any).
        2. Use an LLM (Ollama) to determine if this approach is correct and meets the subtask criteria.
        
        The LLM should return JSON such as:
        {
          "is_correct": true/false,
          "report": "Explanation of why it is correct or not.",
        }

        Returns:
        A dict with keys "is_correct", "report".
        """
        chosen_tool = actor_output.get("chosen_tool")
        tool_code = "No tool chosen."
        if chosen_tool:
            # Get the tool code from the ToolManager
            tool_path = self.tool_manager._tool_filename(chosen_tool)
            if os.path.exists(tool_path):
                with open(tool_path, 'r') as f:
                    tool_code = f.read()
            else:
                # If tool code is not found, return a fallback response
                return {
                    "is_correct": False,
                    "report": f"Tool {chosen_tool} code not found.",
                }
                

        # Prepare the prompt for the LLM
        # The system message instructs the LLM about its role
        # The user message provides the subtask, actor_output, and tool code,
        # and requests a JSON response.
        messages = [
            {
                "role": "system",
                "content": "You are a critic evaluating if the chosen tool and approach are correct for the given subtask."
            },
            {
                "role": "user",
                "content": (
                    f"Subtask: {json.dumps(subtask, indent=2)}\n"
                    f"Actor output: {json.dumps(actor_output, indent=2)}\n\n"
                    f"Tool Code:\n```python\n{tool_code}\n```\n\n"
                    "Decide if this approach solves the subtask correctly. It shouldn't be perfect, it should at least work"
                    "Describe what was done and what was good and bad. "
                    "Return a JSON response with keys: 'report' (string), 'is_correct' (bool)"
                )
            }
        ]
        for attempt in range(3):
            try:
                response = ollama_call(messages, model=self.model)
                parsed = json.loads(self._extract_json(response))
                # Ensure the required fields are present; if not, fallback
                if "is_correct" not in parsed or "report" not in parsed:
                    if actor_output.get("created_tool", False):
                        self.tool_manager.delete_tool(chosen_tool)
                    return {
                        "is_correct": actor_output.get("is_correct", False),
                        "report": "LLM did not provide required fields. Using fallback.",
                    }
                if actor_output.get("created_tool", False) and (not is_executable_script(tool_code) or not parsed['is_correct']):
                    self.tool_manager.delete_tool(chosen_tool)
                return parsed
            except json.JSONDecodeError:
                if actor_output.get("created_tool", False):
                    self.tool_manager.delete_tool(chosen_tool)
                print(f'Json parsing failed on attempt {attempt}')

        return {
            "is_correct": False,
            "report": "Unable to parse LLM's response; fallback used.",
        }
        

    def _extract_json(self, response: str) -> str:
        """
        Extract the JSON content from the LLM response, handling code fences if present.
        """
        if '```json' in response:
            response = response.split('```json', 1)[-1]
        if '```' in response:
            response = response.split('```', 1)[0]
        return response.strip()