from dataclasses import dataclass

from autogen import ConversableAgent
from itakello_logging import ItakelloLogging

logger = ItakelloLogging.get_logger(__name__)


@dataclass
class Agent(ConversableAgent):
    def __init__(self, name: str, llm_config: dict, system_message: str) -> None:
        super().__init__(
            name=name,
            llm_config=llm_config,
            system_message=system_message,
            human_input_mode="NEVER",
            code_execution_config=False,
        )
        logger.debug(
            f"Agent {name} created with system prompt:\n---\n{system_message}\n---\n"
        )
