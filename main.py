import logging

from itakello_logging import ItakelloLogging

from src.classes import Experiment
from src.handlers import DatabaseHandler

ItakelloLogging(
    debug=True,
    excluded_modules=["docker.utils.config", "docker.auth", "httpx"],
)

db_handler = DatabaseHandler()

experiment = Experiment()

experiment_id = db_handler.save_experiment(experiment.to_document())

conversation = experiment.perform()

db_handler.save_conversation(experiment_id, conversation)
