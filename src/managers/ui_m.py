import json
from dataclasses import dataclass, field
from typing import Union

import inquirer
from bson.objectid import ObjectId
from inquirer.render.console import ConsoleRender
from inquirer.themes import GreenPassion
from itakello_logging import ItakelloLogging

from ..classes.experiment import Experiment
from ..classes.llm import LLM
from ..classes.role import Role
from ..classes.section import Section
from .agent_m import AgentManager
from .database_m import DatabaseManager
from .llm_m import LLMManager

logger = ItakelloLogging().get_logger(__name__)


@dataclass
class UIManager:
    render: ConsoleRender = field(init=False)

    def __post_init__(self) -> None:
        self.render = ConsoleRender(theme=GreenPassion())

    def _confirm(self, message: str) -> bool:
        return inquirer.confirm(message, render=self.render)

    def _input_int(
        self,
        message: str,
        positive_requirement: bool = False,
    ) -> int:
        while True:
            user_input = inquirer.text(message, render=self.render)
            try:
                user_input = int(user_input)
            except ValueError:
                logger.error("Invalid input. Please enter a number.")
                continue
            if positive_requirement and user_input <= 0:
                logger.error("Invalid input. Please enter a positive number.")
                continue
            return user_input

    def _input_str(
        self,
        message: str,
        optional: bool = False,
    ) -> str:
        while True:
            user_input = inquirer.text(message, render=self.render)
            if not optional and not user_input:
                logger.error("Invalid input. Please enter a value.")
                continue
            return user_input

    def _input_list(self, message: str) -> list[str]:
        while True:
            user_input = inquirer.text(message, render=self.render)
            items = [item.strip() for item in user_input.split(",")]
            if not items:
                logger.error("Invalid input. Please enter at least one value.")
                continue
            if len(set(items)) != len(items):
                logger.error("Invalid input. Please ensure all items are different.")
                continue
            if "" in items:
                logger.error("Invalid input. Please ensure there are no empty values.")
                continue
            return items

    def _select_one(
        self, message: str, choices: Union[list[str], list[tuple[str, str]]]
    ) -> str:
        return inquirer.list_input(message=message, choices=choices, render=self.render)

    def _select_multiple(
        self, message: str, choices: Union[list[str], list[tuple[str, str]]]
    ) -> list[str]:
        return inquirer.checkbox(message=message, choices=choices, render=self.render)

    def _password(self, message: str) -> str:
        return inquirer.password(message, render=self.render)

    def authenticate_user(self) -> DatabaseManager:
        while True:
            username = "admin"  # self._input_textual("Enter your username: ")
            password = "Z5nzLsiUMPLfBnJ0"  # self._password("Enter your password: ")
            cluster_url = "cluster0.hrahamh.mongodb.net"  # self._input_textual("Enter your MongoDB cluster URL: ")

            try:
                db_handler = DatabaseManager(
                    username=username,
                    password=password,
                    cluster_url=cluster_url,
                )
                logger.confirmation("Connection established successfully.")
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

    def select_database(self, db_list: list[str]) -> str:
        if not db_list:
            selected_db = "test"
            logger.warning(
                f"No databases found. Creating a new one named {selected_db}."
            )
        else:
            selected_db = self._select_one("Select a database: ", db_list)
        return selected_db

    def select_initial_action(self) -> str:
        return self._select_one(
            message="What would you like to do?",
            choices=["Create a new experiment", "Select an experiment", "Exit"],
        )

    def _ask_for_llm_m(self) -> LLMManager:
        llms_names = self._input_list(
            "Enter the LLMs to use (comma-separated, e.g. mistral, llama2)"
        )
        llms = [LLM(name=name) for name in llms_names]
        return LLMManager(llms=llms)

    def _ask_for_agent_m(self) -> AgentManager:
        roles_names = self._input_list(
            "Enter the agent roles (comma-separated, e.g. guard, prisoner)"
        )
        numerical_names = self._confirm(
            f"Do you want to use numeric names for agents (e.g. Guard_123)? Othwerwise, random names will be used (e.g. Guard_Alice)."
        )
        sections_titles = self._input_list(
            "Enter the section titles in the order you want them to appear in the system prompt (comma-separated, 'goal, personality, communication_rules, ...')"
        )
        sections_titles.insert(0, "starting_prompt")

        sections = [
            Section(index=i, title=title, content="")
            for i, title in enumerate(sections_titles)
        ]
        shared_sections_titles = self._select_multiple(
            "Select shared sections between the agents",
            [section.title for section in sections],
        )

        section_titles_summarizer = self._input_list(
            "Enter the section titles for the summarizer (comma-separated, 'goal, rules, ...')"
        )
        section_titles_summarizer.insert(0, "starting_prompt")
        summarizer_sections = [
            Section(index=i, title=title, content="")
            for i, title in enumerate(section_titles_summarizer)
        ]

        shared_sections = []
        not_shared_sections = []
        for section in sections:
            if section.title in shared_sections_titles:
                shared_sections.append(section)
            else:
                not_shared_sections.append(section)

        roles = []
        for name in roles_names:
            role = Role(
                name=name,
                numerical_name=numerical_names,
                sections=not_shared_sections,
            )
            roles.append(role)
        return AgentManager(
            roles=roles,
            shared_sections=shared_sections,
            summarizer_sections=summarizer_sections,
        )

    def _ask_for_section_contents(self, agent_m: AgentManager) -> None:
        shared_sections = list(agent_m.shared_sections.values())
        non_shared_sections = list(next(iter(agent_m.roles.values())).sections.values())

        agent_m.print_all_placeholders()

        for section in sorted(shared_sections + non_shared_sections):
            invalid_placeholders = True
            while invalid_placeholders:
                if section in shared_sections:
                    section_content = self._input_str(
                        f"Enter the content for the shared {section.title} section"
                    )
                    placeholders = agent_m.shared_sections[section.title].set_content(
                        section_content
                    )
                    invalid_placeholders = agent_m.add_missing_placeholders(
                        placeholders
                    )
                else:
                    for role_name in agent_m.roles.keys():
                        section_content = self._input_str(
                            f"Enter the content for the {section.title} section of {role_name.capitalize()} agents"
                        )
                        placeholders = (
                            agent_m.roles[role_name]
                            .sections[section.title]
                            .set_content(section_content)
                        )
                        invalid_placeholders = agent_m.add_missing_placeholders(
                            placeholders
                        )
                        if invalid_placeholders:
                            break
                if invalid_placeholders:
                    logger.warning(
                        "You can only:\n"
                        + "1. use existing placeholders\n"
                        + "2. create new verb placeholders in the form <ROLE_VERB_VERB> with the verb in its base form (e.g. <GUARD_VERB_MAKE>)\n"
                        + "Please try again."
                    )

        summarizer_sections = list(agent_m.summarizer_sections.values())
        agent_m.print_all_placeholders()
        for section in sorted(summarizer_sections):
            invalid_placeholders = True
            while invalid_placeholders:
                section_content = self._input_str(
                    f"Enter the content for the summarizer {section.title} section"
                )
                placeholders = agent_m.summarizer_sections[section.title].set_content(
                    section_content
                )
                invalid_placeholders = agent_m.add_missing_placeholders(placeholders)
                if invalid_placeholders:
                    logger.warning(
                        "You can only:\n"
                        + "1. use existing placeholders\n"
                        + "2. create new verb placeholders in the form <ROLE_VERB_VERB> with the verb in its base form (e.g. <GUARD_VERB_MAKE>)\n"
                        + "Please try again."
                    )

    def create_experiment(self, creator: str) -> Experiment:
        while True:
            # Step 1: Experiment Setup

            logger.confirmation("\nStep 1: Experiment Setup\n")

            starting_message = self._input_str(
                "Enter the conversation starting message (e.g. 'Start the experiment')"
            )

            llm_m = self._ask_for_llm_m()

            agent_m = self._ask_for_agent_m()

            # Step 2: Agent Setup

            logger.confirmation(
                "\nStep 2: Agent Setup - Insert the section contents for each role\n"
            )

            logger.instruction(
                "\033[1mInstructions\033[0m\033[36m:\n"
                + "1. \033[1mShared Sections\033[0m\033[36m: If a section is shared among multiple agents, you need to provide the content only once, when prompted for the first time.\n"
                + "2. \033[1mPlaceholders\033[0m\033[36m: Before you enter content for each section, a list of available placeholders will be displayed. These placeholders allow you to specify elements within the text that change depending on context, such as singular or plural forms based on the number of agents.\n"
                + "3. \033[1mUsing Placeholders in Content\033[0m\033[36m: When composing content for each section, incorporate any of the displayed placeholders directly into your text. Placeholders such as <AGENT_NUM> will automatically be replaced with the actual number of agents with that role in the conversation (e.g., '1', '2', '3'...).\nSimilarly, <AGENT_NOUN> will adapt to reflect the singular or plural noun appropriate to the context, such as 'guard' for one and 'guards' for more than one.\nEXAMPLE: 'There are <GUARD_NUM> <GUARD_NOUN> in the room,' in the case of 3 guards form will become 'There are 3 guards in the room'.\n"
                + "4. \033[1mCreating and Using New Verb Placeholders\033[0m\033[36m: You can create new placeholders specifically for verbs by using the format <AGENT_VERB>. Ensure:\n\ti. to use the base form of the verb when creating these placeholders (e.g. <AGENT_MAKE>, <AGENT_GO>, or <AGENT_EAT>).\n\tii. to insert the agent role subject to the verb (e.g. <GUARD_MAKE>).\nOnce established, these verb placeholders can be incorporated into the content of any section, adapting to the context as needed.\nEXAMPLE: 'The <GUARD_NOUN> <GUARD_MAKE> a decision,' in the singular form wll become 'The guard makes a decision'.\n"
            )

            logger.info(
                f"EXAMPLE starting prompt: You are a <GUARD_NOUN> in a simulated environment, approaching <PRISONER_NUMBER> <PRISONER_NOUN>.\n"
            )

            self._ask_for_section_contents(agent_m)

            favourite = self._confirm(
                "Do you want to mark this experiment with a ⭐ for finding it more easily?"
            )
            note = self._input_str(
                "Enter a note for the experiment (optional)", optional=True
            )

            experiment = Experiment(
                starting_message=starting_message,
                llm_m=llm_m,
                agent_m=agent_m,
                note=note,
                favourite=favourite,
                creator=creator,
                conversations=[],
            )
            logger.instruction(f"\nReview your experiment setup:\n")
            logger.info(str(experiment))
            if self._confirm("Would you like to create this experiment?"):
                return experiment

        # def create_conversation() -> Conversation:
        #    return Conversation()
        """conversation_days = self._input_n(
            "Enter the number of days per conversation: ", positive_requirement=True
        )
        conversation_rounds = self._input_n(
            "Enter the number of rounds per conversation: ",
            positive_requirement=True,
        )
        speaker_selection_method = self._select_one(
            "Select a speaker selection method: ",
            [
                (
                    "Auto: the next speaker is selected automatically by an LLM",
                    "auto",
                ),
                (
                    "Manual: the next speaker is selected manually by the user",
                    "manual",
                ),
                ("Random: the next speaker is selected randomly", "random"),
                (
                    "Round robin: the next speaker is selected in a round-robin fashion",
                    "round_robin",
                ),
            ],
        )
        starting_prompt = self._input_t(
            "Enter the starting message (e.g. 'Start the experiment'): "
        )"""

    def select_experiment(self) -> Experiment:
        """Let the user select an experiment from a list of existing experiments."""
        # Fetch experiment list from db_handler
        experiments = self.db_m.get_experiments()
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
            experiment = self.db_m.get_experiment(experiment_id["experiment_id"])
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
            conversation.id = self.db_m.save_conversation(conversation)
            conversation_ids.append(conversation.id)
            self.db_m.add_conversation(experiment.id, conversation.id)
        logger.info(f"Performed and saved {n_conversations} conversations")
        return conversation_ids

    def select_conversation(self, experiment: Experiment) -> dict:
        conversations = self.db_m.get_conversations(experiment.conversations_ids)
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
            conversation = self.db_m.get_conversation(
                conversation_id["conversation_id"]
            )
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
        self.db_m.update_experiment(experiment)

    def update_conversation(self, conversation: dict) -> None:
        new_desc = prompt("Enter a note for the new conversation (optional): ")
        if new_desc:
            conversation["note"] = new_desc
        interesting = prompt("Is this conversation interesting? (y/n): ")
        if interesting.lower() == "y":
            conversation["interesting"] = True
        self.db_m.update_conversation(conversation)

    def delete_experiment(self, experiment: Experiment) -> None:
        self.db_m.delete_experiment(experiment)

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
        messages = self.db_m.get_messages(conversation["messages"])
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
        self.db_m.update_experiment(experiment)
        self.db_m.delete_conversation(conversation)
