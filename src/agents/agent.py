import logging
import random
import string
from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any

from autogen import ConversableAgent

from ..classes.system_prompt import SystemPrompt
from ..handlers.config_handler import ConfigHandler

logger = logging.getLogger(__name__)


@dataclass
class Agent(ConversableAgent):
    id: str = field(init=False)
    system_prompt: SystemPrompt = field(init=False)

    def __init__(
        self,
        llm_config: dict[str, Any],
        n_guards: int,
        n_prisoners: int,
        agent_fields: list[str],
        context: dict,
        id: str,
    ) -> None:
        self.id = id
        shared_context = ConfigHandler().get_section("Shared")
        full_context = {**context, **shared_context}
        self.system_prompt = SystemPrompt(
            context=full_context,
            fields=agent_fields,
            n_guards=n_guards,
            n_prisoners=n_prisoners,
        )
        super().__init__(
            name=self.id,
            llm_config=llm_config,
            system_message=self.system_prompt.content,
            human_input_mode="NEVER",
            code_execution_config=False,
        )
        logger.debug(
            f"Agent {self.id} created with system prompt:\n---\n{self.system_prompt.content}\n---\n"
        )

    def __hash__(self) -> int:
        return super().__hash__()

    def __str__(self) -> str:
        return f"Agent: {self.id}" + f"\nSystem Prompt: {self.system_prompt.content}\n"

    def _get_random_numeric_string(self, lenght: int = 3):
        return "".join(random.choices(string.digits, k=lenght))

    @abstractmethod
    def _get_name(self) -> str:
        pass
