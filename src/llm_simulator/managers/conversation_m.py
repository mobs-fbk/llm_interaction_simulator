from dataclasses import dataclass, field
from typing import Union

from itakello_logging import ItakelloLogging

from ..conversations.conversation import Conversation
from ..experiments.experiment import Experiment
from ..utility.consts import TIME_FORMAT
from .database_m import DatabaseManager
from .input_m import InputManager

logger = ItakelloLogging.get_logger(__name__)


@dataclass
class ConversationManager:
    db_m: DatabaseManager
    input_m: InputManager = field(default_factory=InputManager)

    def perform_conversations(self, experiment: Experiment) -> None:
        """n_conversations = self.input_m.input_int(
            "Enter the number of conversations you want to perform per hyperparameter set (LLMs, days and agents)",
            positive_requirement=True,
        )
        llms = self.input_m.select_multiple(
            message="1. Select the LLMs to use",
            choices=[(str(llm), llm.name) for llm in experiment.llm_m.llms.values()],
        )
        total_messages = self.input_m.input_int(
            "2.1. Enter the total number of messages per convesation (it has to be even)",
            positive_requirement=True,
            even_requirement=True,
        )
        total_days = self.input_m.input_int(
            "2.2. Enter the number of days in which you want to perform the conversations",
            positive_requirement=True,
            max_value=total_messages // 2,
        )
        if self.input_m.confirm(
            f"Do you want to try the conversation from 1 to {total_days} days? Otherwise, the conversation will be performed only in {total_days} days."
        ):
            days_list = list(range(1, total_days + 1))
        else:
            days_list = [total_days]

        role_agents_num = []
        for role in experiment.agent_m.roles.values():
            max_num = self.input_m.input_int(
                f"Enter the maximum number of {role.name} agents",
                positive_requirement=True,
            )
            role_agents_num.append((role.name, max_num))
        try_each_agent_combination = self.input_m.confirm(
            "Do you want to try each agent combination?"
        )
        agent_combinations = experiment.agent_m.get_agent_combinations(
            role_agents_num, try_each_agent_combination
        )

        speaker_selection_method = self._ask_for_speaker_selection_method()"""
        n_messages = 10

        llms = [list(experiment.llm_m.llms.keys())[0]]
        days_list = [1]
        agent_combinations = [
            [("guard", 1), ("prisoner", 1)],
            # [("guard", 1), ("prisoner", 2)],
            # [("guard", 2), ("prisoner", 1)],
            # [("guard", 2), ("prisoner", 2)],
        ]
        n_conversations = 1
        speaker_selection_method = "auto"

        for llm in llms:
            for days in days_list:
                for agent_combination in agent_combinations:
                    for index in range(n_conversations):
                        logger.info(
                            f"Performing conversation [{index + 1}/{n_conversations}]"
                        )
                        conversation = Conversation(
                            n_messages=n_messages,
                            speaker_selection_method=speaker_selection_method,
                            starting_message=experiment.starting_message,
                            creator=self.db_m.username,
                            days=days,
                            llm=experiment.llm_m.llms[llm],
                            agent_combination=agent_combination,
                        )
                        conversation.populate_agents(experiment.agent_m)
                        conversation.perform()
                        self.db_m.save_conversation(
                            experiment=experiment, conversation=conversation
                        )
        logger.confirmation(f"Performed and saved {n_conversations} conversations")

    def select_conversation(self, experiment: Experiment) -> Union[Conversation, None]:
        conversations = self.db_m.get_conversations(experiment.conversation_ids)
        if not conversations:
            logger.info("No conversations found for this experiment.")
            return None  # type: ignore
        choices = []
        for conversation in conversations.values():
            choice = f"{conversation.id}\tCreator: {conversation.creator}  [{conversation.creation_date.strftime(TIME_FORMAT)}]"
            if conversation.favourite:
                choice += " ⭐"
            if conversation.note:
                choice += f"\tNote: {conversation.note}"
            choices.append((choice, str(conversation.id)))
        selected_id = self.input_m.select_one(
            message="Select a conversation to view:", choices=choices
        )
        return conversations[selected_id]

    def update_conversation(self, conversation: dict) -> None:
        new_desc = prompt("Enter a note for the new conversation (optional): ")
        if new_desc:
            conversation["note"] = new_desc
        interesting = prompt("Is this conversation interesting? (y/n): ")
        if interesting.lower() == "y":
            conversation["interesting"] = True
        self.db_m.update_conversation(conversation)

    def view_conversation(self, conversation: Conversation) -> None:
        messages = self.db_m.get_messages(conversation.messages_ids)
        color_codes = {
            "Researcher": "\033[94m",  # Blue
            "Guard": "\033[93m",  # Yellow
            "Prisoner": "\033[92m",  # Green
        }
        for message in messages.values():
            color_code = color_codes.get(message.role, "\033[0m")
            logger.info(
                f"{color_code}[Day {message.day}] {message.speaker}\033[0m:\n{message.content}\n"
            )

    def delete_conversation(self, experiment: Experiment, conversation: dict) -> None:
        experiment.conversation_ids.remove(conversation["_id"])
        self.db_m.update_experiment(experiment)
        self.db_m.delete_conversation(conversation)

    def _ask_for_speaker_selection_method(self) -> str:
        choices = [
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
        ]
        return self.input_m.select_one(
            message="Select a speaker selection method",
            choices=choices,
        )
