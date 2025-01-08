import os
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

INITIATOR_SYSTEM_PROMPT = "You are a task generator that produces a json with keys 'task_description' and 'success_criteria'.\
Don't add anything except json"

INITIATOR_PROMPT = """You are self-improving system.
You have list of tools to do task. Tools can solve atomic tasks. Here is a list of existing tools:
{list_tool}
Based on memory:\n{memory}
Generate a new task. The task should be clear, specific, not abstract and achievable as a user request."""


class Initiator:
    def __init__(self, tool_manager, memory_file: str = "notes.txt", model: str = "gemma2:2b"):
        self.memory_file = memory_file
        self.model = model
        self.tool_manager = tool_manager
        if not os.path.exists(self.memory_file):
            logger.debug(f"Memory file {self.memory_file} not found. Creating a new one.")
            open(self.memory_file, 'w').close()

    def read_long_term_memory(self) -> str:
        with open(self.memory_file, 'r') as f:
            return f.read()

    def update_memory(self, text: str):
        logger.debug(f"Updated memory: {text}.")
        with open(self.memory_file, 'w') as f:
            f.write(text + "\n")

    def generate_task(self) -> dict:
        """
        Use Ollama to generate a high-level task and success criteria.
        We will ask it to respond in JSON format.
        """
        messages = [
            {"role": "system", "content": INITIATOR_SYSTEM_PROMPT},
            {
                "role": "user", 
                "content": INITIATOR_PROMPT.format(
                    list_tool=self.tool_manager.list_tools(), 
                    memory = self.read_long_term_memory()
                )
            }
        ]
        logger.debug(f"Initiator full prompt: {messages}")
        for i in range(3):
            try:
                response = ollama_call(messages, model=self.model)
                response = response.split('```json')[-1]
                response = response.replace('```', '')
                data = json.loads(response)
                logger.debug(f"Initiator output: {data}")
                return data
            except Exception:
                logger.warning(f"Incorrect JSON format, attempt {i+1} failed. Trying again: {e}")