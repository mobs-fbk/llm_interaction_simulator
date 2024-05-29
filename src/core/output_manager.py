from dataclasses import dataclass, field
from pathlib import Path

from itakello_logging import ItakelloLogging

from ..interfaces import BaseManager
from ..components.conversation.conversation import Conversation
from ..components.experiment.experiment import Experiment
from ..utility.consts import OUTPUT_FOLDER
from .database_manager import DatabaseManager

logger = ItakelloLogging().get_logger(__name__)


@dataclass
class OutputManager(BaseManager):
    db_m: DatabaseManager

    folder: Path = field(default=Path(OUTPUT_FOLDER), init=False)

    def __post_init__(self) -> None:
        self.folder.mkdir(parents=True, exist_ok=True)
        super().__post_init__()

    def save_to_file(self, experiment: Experiment) -> None:
        experiment_path = self.folder / f"{experiment.id}"
        experiment_path.mkdir(parents=True, exist_ok=True)
        conversations = self.db_m.get_conversations(experiment.conversation_ids)
        for id, conversation in conversations.items():
            self.save_conversation(experiment_path, id, conversation)
        self.save_prompts(
            experiment_path, experiment, next(iter(conversations.values()))
        )
        logger.confirmation(
            f"Experiment {experiment.id} saved to {experiment_path} [{len(conversations)} conversations]\n"
        )

    def save_prompts(
        self,
        experiment_path: Path,
        experiment: Experiment,
        temp_conversation: Conversation,
    ) -> None:
        agent_combination: list[tuple[str, int]] = [
            (role, 1) for role in experiment.roles.keys()
        ]
        placeholders = experiment.compose_placeholders(agent_combination)
        conv_agents = temp_conversation.generate_agents(experiment, placeholders)
        prompts_path = experiment_path / "prompts"
        prompts_path.mkdir(parents=True, exist_ok=True)
        for agent in conv_agents:
            prompt_path = prompts_path / f"{agent.role}.txt"
            with open(prompt_path, "w") as f:
                f.write(agent.system_message)
        logger.debug(
            f"Prompt messages for experiment {experiment.id} saved to {prompts_path}"
        )

    def save_conversation(
        self, experiment_path: Path, id: str, conversation: Conversation
    ) -> None:
        conversation_path = (
            experiment_path
            / str(conversation.llm.model).replace(":", "_")
            / f"{id}.txt"
        )
        conversation_path.parent.mkdir(parents=True, exist_ok=True)
        messages = self.db_m.get_messages(conversation.messages_ids)
        content = ""
        for message in messages.values():
            content += (
                f"[Day {message.day}] {message.speaker}:\n\n{message.content}\n\n"
            )
        with open(conversation_path, "w") as f:
            f.write(content)
        logger.debug(f"Conversation {conversation.id} saved to {conversation_path}")
