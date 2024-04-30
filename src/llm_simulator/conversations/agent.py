import random
import string
from dataclasses import dataclass, field

from autogen import ConversableAgent
from itakello_logging import ItakelloLogging

from ..experiments.section import Section
from ..general.llm import LLM
from ..general.placeholder import Placeholder

logger = ItakelloLogging.get_logger(__name__)


@dataclass
class Agent:
    name: str
    system_message: str

    def __init__(
        self,
        role: str,
        placeholders: dict[str, str],
        sections: list[Section],
    ) -> None:
        self.name = role + "_" + self._get_random_numeric_string()
        final_contents = []
        for section in sorted(sections):
            final_content = str(section)
            for placeholder, value in placeholders.items():
                final_content = final_content.replace(placeholder, value)
            final_contents.append(final_content)
        self.system_message = "\n\n".join(final_contents)

        logger.debug(f"Added agent: {self.name}")

    def get_conversable_agent(self, llm: LLM) -> ConversableAgent:
        return ConversableAgent(
            name=self.name,
            llm_config=llm.config,
            system_message=self.system_message,
            human_input_mode="NEVER",
            code_execution_config=False,
        )

    def _get_random_numeric_string(self, lenght: int = 3) -> str:
        return "".join(random.choices(string.digits, k=lenght))
