import json
from utils.ollama_utils import ollama_call
import re
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app.log',
    filemode='a'
)
logger = logging.getLogger(__name__)

class Actor:
    def __init__(self, tool_manager, model: str = "gemma2:2b"):
        self.tool_manager = tool_manager
        self.model = model

    def perform_subtask(self, subtask: dict, artifacts=None, critic_comment=None) -> dict:
        """
        Attempt to solve the subtask using available tools.
        If a needed tool doesn't exist, create it by generating the full Python file via Ollama.

        Returns a dict:
        {
            "completed": bool,
            "output": "...",
            "errors": "..." or None,
            "chosen_tool": "...",
            "created_tool": "...",
            "tool_args": {...}
        }
        """
        result = {"completed": False, "output": None, "errors": None, "chosen_tool": None, "created_tool": None, "tool_args": {}}
        tools = self.tool_manager.list_tools()
        decision = self._get_tool_decision(
            subtask_prompt=f"Subtask: {subtask['subtask']}\nExisting Tools:\n{tools}.\nPrevious steps artifacts:{artifacts}\nFeedback from critic after previous try{critic_comment}"
        )
        if not decision:
            result["errors"] = "Failed to parse Ollama response."
            return result
        result['tool_args'] = decision.get("tool_args", {})
        if decision.get("action") == "create_tool":
            new_tool_name = self.design_tool(subtask, artifacts, critic_comment)
            if not new_tool_name:
                result["errors"] = "Failed to create new tool."
                return result
            result['created_tool'] = new_tool_name
            tools = self.tool_manager.list_tools()
            decision = self._get_tool_decision(
                subtask_prompt=f"Subtask: {subtask['subtask']}\nExisting Tools:\n{tools}.\nPrevious steps artifacts:{artifacts}\nFeedback from critic after previous try{critic_comment}"
            )
            result['tool_args'] = decision.get("tool_args", {})
            if not decision:
                result["errors"] ="Failed to parse Ollama response after tool creation."
                return result

        # Attempt to use the chosen tool
        chosen_tool = decision.get("tool_name")
        if chosen_tool:
            tool_obj = self.tool_manager.get_tool(chosen_tool.lower())
            if tool_obj:
                try:
                    output = tool_obj.run(**decision.get("tool_args", {}))
                    result['completed'] = True
                    result['output'] = output
                    result['chosen_tool'] = chosen_tool
                    return result
                except Exception as e:
                    result['errors'] = str(e)
                    result['chosen_tool'] = chosen_tool
                    return result
            else:
                result['errors'] = f"Tool '{chosen_tool}' not found."
                return result
        else:
            result['errors'] = "No tool chosen."
            return result

    def design_tool(self, subtask: dict, artifacts=None, critic_comment=None) -> bool:
        """
        Design a new tool based on the subtask by interacting with Ollama.
        Generates the tool specifications and code, then saves it using ToolManager.
        """
        design_tool = self._get_tool_design(
            description=subtask.get('description', 'No description provided.'),
            artifacts=artifacts,
            critic_comment=critic_comment
        )
        if not design_tool:
            print("Failed to obtain tool creation data from Ollama.")
            return None

        required_fields = ["tool_name", "tool_description", "args_description"]
        if not all(field in design_tool for field in required_fields):
            print(f"Design tool data missing required fields: {design_tool}")
            return None

        tool_code = self._generate_tool_code(
            tool_name=design_tool["tool_name"],
            tool_description=design_tool["tool_description"],
            args_description=design_tool["args_description"]
        )

        if not tool_code:
            print("Failed to generate tool code.")
            return None

        save_success = self.tool_manager.add_tool(design_tool["tool_name"], tool_code)
        if not save_success:
            print(f"Failed to save the new tool '{design_tool['tool_name']}'.")
            return None

        logger.info(f"Successfully created and saved tool '{design_tool['tool_name']}'.")
        return design_tool["tool_name"]

    def _generate_tool_code(self, tool_name: str, tool_description: str, args_description: str) -> str:
        """
        Generate the full Python code for a new tool using Ollama.
        """
        example_tool = """
from toolbox.base_tool import Tool

class ExampleTool(Tool):
    @property
    def tool_desc(self) -> str:
        return "An example tool that does something useful. Returns result"

    @property
    def param_desc(self) -> str:
        return "param1: description of param1, param2: description of param2"

    @staticmethod
    def run(**kwargs):
        param1 = kwargs.get('param1')
        param2 = kwargs.get('param2')
        Here you need to implement full logic
        result = f"Processed {param1} and {param2}"
        return result
"""

        messages = [
            {"role": "system", "content": """You are a tool creator that generates Python classes for new tools based on the base_tool interface. 
Provide the full Python code for the tool, including necessary imports and class definitions. Ensure the tool is well-structured and follows best practices."""},
            {"role": "user", "content": f"""Generate a Python class for a new tool with the following specifications:

Tool Name: {tool_name}
Tool Description: {tool_description}
Parameters Description: {args_description}

Here is an example of a tool implementation:

{example_tool}

Implement executable new tool based on description. Answer only python code. Do not add explanation or comments
You are autonomous agent: avoid any user input calls, always use arguments instead."""},
        ]

        # Attempt to get the tool code from Ollama
        for attempt in range(3):
            try:
                response = ollama_call(messages, model=self.model)
                logger.debug(f"Ollama Tool Code Response: {response}")

                tool_code = self._extract_code(response, language="python")
                if tool_code:
                    return tool_code
                else:
                    print("No Python code found in the response.")
            except Exception as e:
                print(f"Attempt {attempt + 1}: Failed to generate tool code. Error: {e}")

        return ""

    def _get_tool_decision(self, subtask_prompt: str) -> dict:
        """
        Helper method to get a tool decision from Ollama.
        Otherwise, comments are removed.
        """

        system_content = """You are an actor that decides which tool from custom toolbox to use or to create a new tool to accomplish the subtask. 
use_tool option for calling existing tool, create_tool - for implementing new tools. Maintain parameterizability to ensure the tool's broad applicability.
Choose only existing tools to use
Return json only without comments
Output sample:
{
    "action": "use_tool" or "create_tool",
    "tool_name": "...",
    "tool_args": {...}
}
"""

        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": subtask_prompt}
        ]

        for attempt in range(3):
            try:
                response = ollama_call(messages, model=self.model)
                logger.debug(f"Ollama Decision Response: {response}")
                response_json = self._extract_json(response)
                decision = json.loads(response_json)
                return decision
            except json.JSONDecodeError:
                print(f'Incorrect JSON format, trying again. Attempt {attempt + 1}')
            except Exception as e:
                print(f'Unexpected error: {e}, trying again. Attempt {attempt + 1}')

        return None

    def _get_tool_design(self, description: str, artifacts, critic_comment) -> dict:
        """
        Helper method to obtain tool design JSON from Ollama.
        """
        tool_creation_messages = [
            {
                "role": "system", 
                "content": """You are a tool creator. 
User wants a new tool to accomplish the specified subtask.
Write tool description in details
Return a JSON with the following keys:
"tool_name": string, in snake case 
"tool_description": string, 
"args_description": string, 
Format the entire response as JSON only without comments."""
            },
            {
                "role": "user",
                "content": f"Subtask description: {description}\nDesign a tool for general case, not this particular usage if possible.\nPrevious steps artifacts:{artifacts}\nFeedback from critic after previous try{critic_comment}"
            }
        ]

        for attempt in range(3):
            try:
                tool_creation_response = ollama_call(tool_creation_messages, model=self.model)
                logger.debug(f"Ollama Tool Creation Response: {tool_creation_response}")

                tool_creation_response = self._extract_json(tool_creation_response)
                design_tool = json.loads(tool_creation_response)
                return design_tool
            except json.JSONDecodeError:
                print(f"Failed to parse tool creation JSON from Ollama, trying again. Attempt {attempt + 1}")
            except Exception as e:
                print(f"Unexpected error during tool creation: {e}, trying again. Attempt {attempt + 1}")

        return {}

    def _extract_json(self, response: str) -> str:
        """
        Extract JSON content from the response, handling possible code fences.
        """
        json_fence = '```json'
        if json_fence in response:
            response = response.split(json_fence)[-1]
        if '```' in response:
            response = response.split('```')[0]
        return response.strip()

    def _extract_code(self, response: str, language: str = "python") -> str:
        """
        Extract code block from the response based on the specified language.
        """
        code_fence = f"```{language}"
        if code_fence in response:
            parts = response.split(code_fence)
            if len(parts) > 1:
                code_part = parts[-1].split("```")[0]
                return code_part.strip()
        return ""