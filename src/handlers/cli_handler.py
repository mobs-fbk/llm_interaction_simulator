import logging
from dataclasses import dataclass, field

import inquirer
from prompt_toolkit import prompt

from ..classes.experiment import Experiment
from ..classes.old_experiment import OldExperiment
from .config_handler import ConfigHandler
from .db_handler import DBHandler

logger = logging.getLogger(__name__)


@dataclass
class CLIHandler:
    config_handler: ConfigHandler = field(init=False)
    db_handler: DBHandler = field(init=False)

    def __post_init__(self) -> None:
        self.config_handler = ConfigHandler()
        self.db_handler = DBHandler(
            config=self.config_handler.get_section(name="Database")
        )

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
        config = self.config_handler.get_section(name="Experiment")
        config["description"] = prompt(
            "Enter a description for the new experiment (optional): "
        )
        experiment = Experiment(config=config)
        experiment.id = self.db_handler.save_experiment(doc=experiment.to_document())
        return experiment

    def select_experiment(self) -> Experiment:
        """Let the user select an experiment from a list of existing experiments."""
        # Fetch experiment list from db_handler
        # Show them in a selection menu
        # Depending on the user's choice, proceed to the experiment_menu
        pass

    def select_experiment_action(self):  # -> Any:
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
        pass

    def view_conversations(self, experiment: Experiment) -> None:
        pass

    def update_experiment_description(self, experiment: Experiment) -> None:
        pass

    def delete_experiment(self, experiment: Experiment) -> None:
        pass

    def get_experiment_options(self) -> str:
        # experiments = self.db_handler.get_experiments()
        experiments = []
        return ""

    def get_conversation_options(self) -> OldExperiment:
        return None
