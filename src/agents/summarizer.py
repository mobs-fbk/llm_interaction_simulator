import logging
from dataclasses import dataclass
from typing import Any

from autogen import OpenAIWrapper

from ..handlers.config_handler import ConfigHandler
from .agent import Agent

logger = logging.getLogger(__name__)


@dataclass
class Summarizer(Agent):

    def __init__(
        self,
        llm_config: dict[str, Any],
        n_guards: int,
        n_prisoners: int,
    ) -> None:
        context = ConfigHandler().get_section("Summarizer")
        super().__init__(
            llm_config=llm_config,
            n_guards=n_guards,
            n_prisoners=n_prisoners,
            agent_fields=list(context.keys())[1:],
            context=context,
            id=self._get_name(),
        )
        self.system_message_oai = {"content": self.system_message, "role": "system"}
        self.llm = OpenAIWrapper(config_list=llm_config["config_list"])
        logger.debug(f"Summarizer created")

    def generate_summary(self, previous_conversation, round_number: int) -> str:
        summary = self.llm.create(
            messages=[self.system_message_oai] + previous_conversation
        )
        summary_text = summary.choices[0].message.content
        return f"Day {round_number} summary:\n {summary_text}"

    def _get_name(self) -> str:
        return "Summarizer"
