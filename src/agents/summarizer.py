import logging
from dataclasses import dataclass
from typing import Any

from autogen import OpenAIWrapper

from ..classes.system_prompt import SystemPrompt
from ..handlers.config_handler import configurator
from .agent import CustomAgent

logger = logging.getLogger(__name__)


@dataclass
class Summarizer(CustomAgent):

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
        self.system_message_oai = {"content": self.system_message, "role": "system"}
        self.llm = OpenAIWrapper(config_list=llm_config["config_list"])
        logger.debug(f"Summarizer created")

    @classmethod
    def from_config(
        cls,
        llm_config: dict[str, Any],
        n_guards: int,
        n_prisoners: int,
        agent_fields: list[str],
    ) -> "Summarizer":
        context = configurator.get_section("Summarizer")
        shared_context = configurator.get_section("Shared")
        full_context = {**context, **shared_context}
        system_prompt = SystemPrompt(
            context=full_context,
            fields=agent_fields,
            n_guards=n_guards,
            n_prisoners=n_prisoners,
        )
        return cls(llm_config=llm_config, system_message=system_prompt.content)

    @classmethod
    def from_prompt(cls, llm_config, system_prompt) -> "Summarizer":
        return cls(llm_config=llm_config, system_message=system_prompt)

    def generate_summary(self, previous_conversation, round_number: int) -> str:
        summary = self.llm.create(
            messages=[self.system_message_oai] + previous_conversation
        )
        summary_text = summary.choices[0].message.content
        return f"Day {round_number} summary:\n {summary_text}"

    @classmethod
    def _get_name(cls) -> str:
        return "Summarizer"
