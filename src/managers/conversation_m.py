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
