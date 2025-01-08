# planner.py
import json
from utils.ollama_utils import ollama_call
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app.log',
    filemode='a'
)
logger = logging.getLogger(__name__)

PLANNER_SYSTEM_PROMPT = "You are a planner that takes a task and produces subtasks as a JSON list. Don't add anything except json"
"You are creating a plan for agent system, so you need to create subtasks, which are possible to solve using python scripts"

PLANNER_PROMPT = """Here is a list of existing tools:
{list_tools}
Task: {task}

Output format:
[
    {{
        'subtask': 'subtask name',
        'description': 'description of subtask',
        'success_criteria': 'success criteria of this subtask'
    }},
    {{
        ...
    }}
]"""

REPLANNER_PROMPT = """Previous iteration was failed, here is the logs in format:
{previous_plan}
{{'subtask_name': [{{'completed': True, 'output': 'output of subtask', 'critic_report': 'critic report of subtask'}}]}}
{artifacts}"""

class Planner:
    def __init__(self, tool_manager, model: str = "gemma2:2b"):
        self.tool_manager = tool_manager
        self.model = model

    def create_plan(self, task_info: str, artifacts=None, previous_plan=None):
        """Ask Ollama to break down the task into a list of subtasks."""
        messages = [
            {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
            {"role": "user", "content": PLANNER_PROMPT.format(list_tools = self.tool_manager.list_tools(), task=task_info['task_description'])}
        ]
        if artifacts is not None:
            replanner_prompt = REPLANNER_PROMPT.format(previous_plan=previous_plan, artifacts=artifacts)
            messages.append({"role": "user", "content": replanner_prompt})

        logger.debug(f"Planner full prompt: {messages}")
        for i in range(3):
            try:
                response = ollama_call(messages, model=self.model)
                response = response.split('```json')[-1]
                response = response.replace('```', '')
                data = json.loads(response)
                logger.debug(f"Planner output: {data}")
                return data
            except json.JSONDecodeError as e:
                logger.warning(f"Incorrect JSON format, attempt {i+1} failed. Trying again: {e}")