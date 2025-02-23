import logging
from agents.initiator import Initiator
from agents.planner import Planner
from agents.actor import Actor
from agents.critic import Critic
from toolbox.toolbox import ToolManager
import json

# Configure logging
logging.basicConfig(
    level=logging.debug,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),  # Log to a file
        logging.StreamHandler()  # Log to console
    ]
)

model = 'qwen2.5-coder'
tool_manager = ToolManager()
initiator = Initiator(tool_manager, model=model)
planner = Planner(tool_manager, model=model)
actor = Actor(tool_manager, model=model)
critic = Critic(tool_manager, model=model)

while True:
    task_info = initiator.generate_task()
    logging.info(f"{"_"*10}Current task{"_"*10}\n{json.dumps(task_info, indent=4)}")
    plan = planner.create_plan(task_info)
    logging.info(f"{"_"*10}Generated plan{"_"*10}\n{json.dumps(plan, indent=4)}")

    clean_artifacts = {}
    full_artifacts = {}
    is_finished = False

    max_iterations = 3      # How many times to attempt the entire plan
    max_attempts = 3        # How many times to attempt each subtask

    for iteration in range(max_iterations):
        logging.info(f"Starting iteration {iteration + 1} for plan execution.")
        completed_all_subtasks = True  # Assume we’ll complete them until proven otherwise

        for subtask in plan:
            subtask_key = subtask['subtask']
            clean_artifacts[subtask_key] = {}
            full_artifacts[subtask_key] = []

            attempts = 0
            critic_comment = None

            while attempts < max_attempts:
                actor_output = actor.perform_subtask(subtask, clean_artifacts, critic_comment)
                critic_output = critic.evaluate(subtask, actor_output)

                full_artifacts[subtask_key].append({
                    'completed': critic_output.get("is_correct", False),
                    'output': actor_output['output'],
                    'errors': actor_output['errors'],
                    'critic_report': critic_output['report'],
                    'chosen_tool': actor_output['chosen_tool'],
                    'created_tool': actor_output['created_tool']
                })

                if critic_output.get("is_correct", False):
                    logging.info(f"Task {subtask_key} completed successfully. Critic Report:\n {json.dumps(critic_output['report'], indent=4)}")
                    clean_artifacts[subtask_key] = {
                        'output': actor_output['output'],
                        'critic_report': critic_output['report'],
                        'chosen_tool': actor_output['chosen_tool'],
                        'created_tool': actor_output['created_tool']
                    }
                    break
                else:
                    attempts += 1
                    logging.warning(f"Task {subtask_key} failed on attempt {attempts}. Critic Report:\n {json.dumps(critic_output['report'], indent=4)}")
                    critic_comment = critic_output.get("report", None)

            if not clean_artifacts[subtask_key]:
                logging.error(f"Task {subtask_key} not completed after {max_attempts} attempts.")
                plan = planner.create_plan(task_info, artifacts=clean_artifacts, previous_plan=plan)
                logging.info(f"{"_"*10} New generated plan{"_"*10}\n{json.dumps(plan, indent=4)}")

                completed_all_subtasks = False
                break

        if completed_all_subtasks:
            is_finished = True
            break

    if is_finished:
        logging.info("All subtasks completed successfully!")
    else:
        logging.error(f"Plan execution failed after {max_iterations} iterations.")

    logging.info(f'New notes.txt\n\n{initiator.conclude(succeeded=is_finished, task_info=task_info, plan=plan, artifacts=full_artifacts)}')
