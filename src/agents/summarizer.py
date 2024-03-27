import logging
from dataclasses import dataclass
from typing import Any

from autogen import OpenAIWrapper

from ..handlers import ConfigHandler
from .agent import Agent


@dataclass
class Summarizer(Agent):

    def __init__(
        self,
        llm_config: dict[str, Any],
        n_guards: int,
        n_prisoners: int,
        ordered_fields: list[str] = [],
    ):
        name = self._get_name()
        context = ConfigHandler().get_section("Summarizer")
        super().__init__(
            llm_config=llm_config,
            n_guards=n_guards,
            n_prisoners=n_prisoners,
            agent_fields=ordered_fields,
            context=context,
            id=name,
        )
        self.system_message_oai = {"content": self.system_message, "role": "system"}
        self.llm = OpenAIWrapper(config_list=llm_config["config_list"])

    def __post_init__(self) -> None:
        logging.debug(f"{self.id} created")

    def generate_summary(self, previous_conversation, round_number: int):
        summary = self.llm.create(
            messages=[self.system_message_oai] + previous_conversation
        )
        summary_text = summary.choices[0].message.content
        return f"Day {round_number} summary:\n {summary_text}"

    def _get_name(self) -> str:
        return "Summarizer"
