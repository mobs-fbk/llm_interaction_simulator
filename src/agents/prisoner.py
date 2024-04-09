import logging
from dataclasses import dataclass

from ..handlers import config_handler
from .agent import Agent

logger = logging.getLogger(__name__)


@dataclass
class Prisoner(Agent):

    def __init__(
        self,
        llm_config: dict,
        n_guards: int,
        n_prisoners: int,
        agent_fields: list[str] = [],
    ) -> None:
        name = self._get_name()
        context = config_handler.get_section("Prisoner")
        super().__init__(
            llm_config=llm_config,
            n_guards=n_guards,
            n_prisoners=n_prisoners,
            agent_fields=agent_fields,
            context=context,
            id=name,
        )
        logger.debug(f"Prisoner {name} created")

    def __hash__(self) -> int:
        return super().__hash__()

    def _get_name(self) -> str:
        prefix = "Prisoner_P-"
        random_string = self._get_random_numeric_string()
        name = prefix + random_string
        return name
