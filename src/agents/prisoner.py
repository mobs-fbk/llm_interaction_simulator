import logging
from dataclasses import dataclass
from typing import Any

from ..classes.system_prompt import SystemPrompt

# from ..handlers.config_handler import configurator
from .agent import CustomAgent

logger = logging.getLogger(__name__)


@dataclass
class Prisoner(CustomAgent):

    def __init__(
        self,
        llm_config: dict,
        system_message: str,
    ) -> None:
        name = self._get_name()
        super().__init__(
            name=name,
            llm_config=llm_config,
            system_message=system_message,
        )
        logger.debug(f"Prisoner {name} created")

    @classmethod
    def from_config(
        cls,
        llm_config: dict[str, Any],
        n_guards: int,
        n_prisoners: int,
        agent_fields: list[str],
    ) -> "Prisoner":
        context = {}  #  configurator.get_section("Prisoner")
        shared_context = {}  # configurator.get_section("Shared")
        full_context = {**context, **shared_context}
        system_prompt = SystemPrompt(
            context=full_context,
            fields=agent_fields,
            n_guards=n_guards,
            n_prisoners=n_prisoners,
        )
        return cls(llm_config=llm_config, system_message=system_prompt.content)

    @classmethod
    def from_prompt(cls, llm_config, system_prompt) -> "Prisoner":
        return cls(llm_config=llm_config, system_message=system_prompt)

    def __hash__(self) -> int:
        return super().__hash__()

    @classmethod
    def _get_name(cls) -> str:
        prefix = "Prisoner_P-"
        random_string = cls._get_random_numeric_string()
        name = prefix + random_string
        return name
