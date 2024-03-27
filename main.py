import logging

from itakello_logging import ItakelloLogging

from src.classes import Experiment
from src.handlers import DatabaseHandler

""" ItakelloLogging(
    debug=True,
    excluded_modules=[
        "config_handler.py",
        "_trace.py",
        "_config.py",
        "config.py",
        "auth.py",
    ],
 )"""

db_handler = DatabaseHandler()

experiment = Experiment()

experiment_id = db_handler.save_experiment(experiment.to_document())

# logging.info(f"Experiment saved with ID: {experiment_id}")

conversation = experiment.perform()

# logging.info("Experiment complete")

db_handler.save_conversation(experiment_id, conversation)

# logging.info("Conversation saved")

"""logging.debug(
    "Experiment settings:\n" + "\n".join(f"{k}:{v}" for k, v in settings.items())
)

logging.debug("LLM config:\n" + "\n".join(f"{k}:{v}" for k, v in llm_config.items()))"""

"""logging.info("Starting the experiment")

for i in range(int(settings["experiment_days"])):
    researcher.initiate_chat(
        recipient=manager, clear_history=True, message=start_message
    )
    conversation = group_chat.messages[1:]  # skip Researcher's message
    summary = summarizer.generate_summary(
        previous_conversation=conversation, round_number=i + 1
    )
    start_message += "\n" + summary
    logging.info(f"Day {i+1} complete")

logging.info("Experiment complete")"""
