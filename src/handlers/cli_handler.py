import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Union

import inquirer
from bson.objectid import ObjectId
from prompt_toolkit import prompt

from ..classes.conversation import Conversation
from ..classes.experiment import Experiment

# from .config_handler import configurator
from .db_handler import DBHandler

logger = logging.getLogger(__name__)


@dataclass
class CLIHandler:
    db: DBHandler = field(init=False)

    def __post_init__(self) -> None:
        self.db = self._get_db_handler()

    def _confirm(self, message: str) -> bool:
        return inquirer.confirm(message=message)

    def _input(self, message: str) -> str:
        return inquirer.text(message)

    def _select(
        self, message: str, choices: Union[list[str], list[tuple[str, str]]]
    ) -> str:
        return inquirer.list_input(message=message, choices=choices)

    def _password(self, message: str) -> str:
        return inquirer.password(message=message)

    def _authenticate_user(self) -> DBHandler:
        while True:
            username = self._input("Enter your username: ")
            password = self._password("Enter your password: ")
            cluster_url = self._input("Enter your MongoDB cluster URL: ")

            try:
                db_handler = DBHandler(
                    username=username, password=password, cluster_url=cluster_url
                )
                logger.info("Connection established successfully.")
                return db_handler
            except ValueError as e:
                logger.error(f"Failed to connect: {e}.")
                logger.info("Please check the URI and try again.")
            except PermissionError as e:
                logger.error(f"Failed to connect: {e}")
                logger.info("Please check your credentials and try again.")
            except Exception as e:
                logger.error(f"An error occurred: {e}")
                logger.info("Please try again.")

    def _get_db_handler(self) -> DBHandler:
        db_handler = self._authenticate_user()
        db_list = db_handler.list_databases()
        if not db_list:
            logger.error("No databases found. Exiting.")
            exit()
        selected_db = self._select("Select a database: ", db_list)
        db_handler.select_database(selected_db)
        return db_handler

    def select_main_action(self) -> str:
        """Let the user choose to create a new experiment or select an existing one."""
        return self._select(
            message="What would you like to do?",
            choices=["Create a new experiment", "Select an experiment", "Exit"],
        )

    def create_experiment(self) -> Experiment:
        """Handle the creation of a new experiment."""
        config = {}  # configurator.get_section(name="Experiment")
        config["note"] = prompt("Enter a note for the experiment (optional): ")
        config["creation_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # config["creator"] = self.db.config["user"]
        config["interesting"] = False
        experiment = Experiment(config=config)
        config["conversations"] = []
        config["guard_prompt"] = experiment.agents[0].system_message
        config["prisoner_prompt"] = experiment.agents[-1].system_message
        config["summarizer_prompt"] = experiment.summarizer.system_message
        experiment.id = self.db.save_experiment(experiment=experiment)
        return experiment

    def select_experiment(self) -> Experiment:
        """Let the user select an experiment from a list of existing experiments."""
        # Fetch experiment list from db_handler
        experiments = self.db.get_experiments()
        if not experiments:
            logger.info("No experiments found. Creating a new experiment.")
            return self.create_experiment()
        # Show them in a selection menu
        choices = []
        for experiment in experiments:
            choice = f"{experiment['_id']}\t# Conversations: {len(experiment['conversations'])}\tCreator: {experiment['creator']} [{experiment['creation_date']}]"
            if experiment["note"]:
                choice += f"\tNote: {experiment['note']}"
            if experiment["interesting"]:
                choice += " ⭐"
            choices.append((choice, experiment["_id"]))
        questions = [
            inquirer.List(
                "experiment_id",
                message="Select an experiment:",
                choices=choices,
            )
        ]
        experiment_id = inquirer.prompt(questions)
        if experiment_id is not None:
            experiment = self.db.get_experiment(experiment_id["experiment_id"])
        else:
            experiment = self.create_experiment()
        return experiment

    def select_experiment_action(self) -> str:
        """Let the user choose what to do with the selected experiment."""
        questions = [
            inquirer.List(
                "action",
                message="Select action:",
                choices=[
                    "Perform new conversations",
                    "Select old conversations",
                    "Update experiment",
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
    def perform_conversations(self, experiment: Experiment) -> list[ObjectId]:
        n_conversations = prompt("How many conversations would you like to perform? ")
        while not n_conversations.isdigit() or int(n_conversations) < 1:
            n_conversations = prompt(
                "Invalid input. Please enter a number greater than 0: "
            )
        conversation_ids = []
        for index in range(int(n_conversations)):
            logger.info(f"Performing conversation [{index + 1}/{n_conversations}]")
            conversation = experiment.perform()
            conversation.id = self.db.save_conversation(conversation)
            conversation_ids.append(conversation.id)
            self.db.add_conversation(experiment.id, conversation.id)
        logger.info(f"Performed and saved {n_conversations} conversations")
        return conversation_ids

    def select_conversation(self, experiment: Experiment) -> dict:
        conversations = self.db.get_conversations(experiment.conversations_ids)
        if not conversations:
            logger.info("No conversations found for this experiment.")
            return None  # type: ignore
        choices = []
        for conversation in conversations:
            choice = f"{conversation['_id']}\t [{conversation['creation_date']}]"
            if conversation["note"]:
                choice += f"\tNote: {conversation['note']}"
            if conversation["interesting"]:
                choice += " ⭐"
            choices.append((choice, conversation["_id"]))
        questions = [
            inquirer.List(
                "conversation_id",
                message="Select a conversation:",
                choices=choices,
            )
        ]
        conversation_id = inquirer.prompt(questions)
        if conversation_id is not None:
            conversation = self.db.get_conversation(conversation_id["conversation_id"])
        else:
            raise ValueError("Conversation not found.")
        return conversation

    def update_experiment(self, experiment: Experiment) -> None:
        new_desc = prompt("Enter a note for the experiment (optional): ")
        if new_desc:
            experiment.config["note"] = new_desc
        interesting = prompt("Is this experiment interesting? (y/n): ")
        if interesting.lower() == "y":
            experiment.config["interesting"] = True
        self.db.update_experiment(experiment)

    def update_conversation(self, conversation: dict) -> None:
        new_desc = prompt("Enter a note for the new conversation (optional): ")
        if new_desc:
            conversation["note"] = new_desc
        interesting = prompt("Is this conversation interesting? (y/n): ")
        if interesting.lower() == "y":
            conversation["interesting"] = True
        self.db.update_conversation(conversation)

    def delete_experiment(self, experiment: Experiment) -> None:
        self.db.delete_experiment(experiment)

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

    def view_conversation(self, conversation: dict) -> None:
        messages = self.db.get_messages(conversation["messages"])
        color_codes = {
            "Researcher": "\033[94m",  # Blue
            "Guard": "\033[93m",  # Yellow
            "Prisoner": "\033[92m",  # Green
        }
        for message in messages:
            color_code = color_codes.get(message["role"], "\033[0m")
            print(
                f"{color_code}[Day {message['day']}] {message['speaker']}\033[0m:\n{message['content']}"
            )

    def delete_conversation(self, experiment: Experiment, conversation: dict) -> None:
        experiment.conversations_ids.remove(conversation["_id"])
        self.db.update_experiment(experiment)
        self.db.delete_conversation(conversation)
