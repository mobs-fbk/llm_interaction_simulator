import logging
from dataclasses import dataclass, field
from datetime import datetime

import inquirer
from prompt_toolkit import prompt

from ..classes.conversation import Conversation
from ..classes.experiment import Experiment
from .config_handler import config_handler
from .db_handler import DBHandler

logger = logging.getLogger(__name__)


@dataclass
class CLIHandler:
    db: DBHandler = field(init=False)

    def __post_init__(self) -> None:
        self.db = DBHandler()

    def select_main_action(self) -> str:
        """Let the user choose to create a new experiment or select an existing one."""
        questions = [
            inquirer.List(
                "action",
                message="What would you like to do?",
                choices=["Create a new experiment", "Select an experiment", "Exit"],
            )
        ]
        action = inquirer.prompt(questions)
        if action is not None:
            return action["action"]
        else:
            return "Exit"

    def create_experiment(self) -> Experiment:
        """Handle the creation of a new experiment."""
        config = config_handler.get_section(name="Experiment")
        config["description"] = prompt(
            "Enter a description for the new experiment (optional): "
        )
        config["creation_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        config["creator"] = self.db.config["user"]
        config["conversations"] = []
        config["interesting"] = False
        experiment = Experiment(config=config)
        experiment.id = self.db.save_experiment(doc=experiment.to_document())
        return experiment

    def select_experiment(self) -> Experiment:
        """Let the user select an experiment from a list of existing experiments."""
        # Fetch experiment list from db_handler
        # Show them in a selection menu
        # Depending on the user's choice, proceed to the experiment_menu
        return Experiment(config={})

    def select_experiment_action(self) -> str:
        """Let the user choose what to do with the selected experiment."""
        questions = [
            inquirer.List(
                "action",
                message="Select action:",
                choices=[
                    "Perform new conversations",
                    "View old conversations",
                    "Update experiment description",
                    "Delete experiment",
                    "Go back",
                ],
            )
        ]
        action = inquirer.prompt(questions)
        if action is not None:
            return action["action"]
        else:
            return "Exit"

    # Placeholder methods for each action
    def perform_conversations(self, experiment: Experiment) -> None:
        # Perform new conversation and save it to db_handler
        # Take as input the number of conversations to perform
        pass

    def select_conversation(self, experiment: Experiment) -> Conversation:
        # Fetch conversation list from db_handler
        return Conversation()

    def update_experiment_description(self, experiment: Experiment) -> None:
        # Update experiment description and save it to db_handler
        # NOTE: Also a toggle to set the experiment as interesting or not
        pass

    def delete_experiment(self, experiment: Experiment) -> None:
        pass

    def select_conversation_action(self) -> str:
        """Let the user choose what to do with the selected conversation."""
        questions = [
            inquirer.List(
                "action",
                message="Select action:",
                choices=[
                    "View conversation",
                    "Update conversation",
                    "Delete conversation",
                    "Go back",
                ],
            )
        ]
        action = inquirer.prompt(questions)
        if action is not None:
            return action["action"]
        else:
            return "Exit"

    def view_conversation(self, conversation: Conversation) -> None:
        pass

    def update_conversation(self, conversation: Conversation) -> None:
        pass

    def delete_conversation(self, conversation: Conversation) -> None:
        pass
