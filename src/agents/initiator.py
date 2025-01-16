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
Generate a new task. The task should be clear, specific, not abstract and achievable as a user request.
Each iteration you need to do something new, don't repeat the same tasks."""


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
                
    def conclude(self, succeeded, task_info: dict, plan, artifacts):
        """
        Conclude the task and update the memory.
        This method:
            - Reads the current memory.
            - Describes all arguments (succeeded, task_info, plan, artifacts) to the model,
            along with the previous notes.
            - Asks the model to generate new notes that incorporate previous notes.
            - Ensures some text from the old memory is kept.
            - Writes the updated memory back to the memory file.
        """
        previous_memory = self.read_long_term_memory()

        # Build a prompt to incorporate old memory with new details.
        # You can adjust the wording/structure below according to your usage.
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a memory aggregator. You will receive:\n"
                    "1) The previous memory (a text).\n"
                    "2) A boolean indicating if the task succeeded.\n"
                    "3) A dictionary describing the task.\n"
                    "4) A plan.\n"
                    "5) Artifacts produced from the task.\n\n"
                    "Your goal is to produce updated notes by merging all of this information. "
                    "Write what to do next, what pay attention to, and your long-term goals. "
                    "Sometimes you need to retain some of the exact text from the previous memory. "
                    "Output the final updated memory in plain text. No JSON formatting."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Previous Memory:\n{previous_memory}\n\n"
                    f"Task Succeeded: {succeeded}\n"
                    f"Task Info: {task_info}\n"
                    f"Plan: {plan}\n"
                    f"Artifacts: {artifacts}\n\n"
                    "Please return the updated memory, ensuring you keep important info from previous memory\n"
                )
            }
        ]

        logger.debug(f"Conclude prompt: {messages}")

        try:
            new_memory = ollama_call(messages, model=self.model).strip()
            logger.debug(f"New memory response: {new_memory}")
            
            # Update the file with the newly generated memory
            self.update_memory(new_memory)
            logger.info("Memory has been updated successfully in 'conclude'.")
        except Exception as e:
            logger.error(f"Error during concluding step: {e}")
        return new_memory