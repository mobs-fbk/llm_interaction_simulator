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
        n_conversations = self.input_m.input_int(
            "Enter the number of conversations you want to perform",
            positive_requirement=True,
        )
        llms = self.input_m.select_multiple(
            message="Select the LLMs to use",
            choices=[llm for llm in experiment.llm_m.llms.keys()],
        )
        conversation_days = self.input_m.input_int(
            "Enter the number of days per conversation", positive_requirement=True
        )
        conversation_rounds = self.input_m.input_int(
            "Enter the number of rounds per conversation", positive_requirement=True
        )
        speaker_selection_method = self._ask_for_speaker_selection_method()

        agents = []
        for role in experiment.agent_m.roles.values():
            role_num = self.input_m.input_int(
                f"Enter the number of {role.name} agents", positive_requirement=True
            )
            agents.extend([Agent(role=role.name, index=i) for i in range(role_num)])

        conversations = []
        for llm in llms:
            for index in range(n_conversations):
                logger.warning(
                    f"Performing conversation [{index + 1}/{n_conversations}]"
                )
                conversation = Conversation(
                    conversation_days=conversation_days,
                    conversation_rounds=conversation_rounds,
                    speaker_selection_method=speaker_selection_method,
                    starting_message=experiment.starting_message,
                    creator=self.db_m.username,
                    llm=llm,
                )
                conversation = experiment.perform(conversation)
                self.db_m.save_conversation(
                    experiment=experiment, conversation=conversation
                )
        logger.info(f"Performed and saved {n_conversations} conversations")
        return conversations

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
