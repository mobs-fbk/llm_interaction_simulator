import random
import string
from dataclasses import dataclass, field

from itakello_logging import ItakelloLogging

from ..llm.llm import LLM
from ..placeholder.placeholder import Placeholder
from ..section.section import Section
from .custom_conv_agent import CustomConversableAgent

logger = ItakelloLogging().get_logger(__name__)


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

    def get_conversable_agent(
        self, llm: LLM, warns: list[str]
    ) -> CustomConversableAgent:
        return CustomConversableAgent(
            name=self.name,
            llm_config=llm.config,
            system_message=self.system_message,
            warns=warns,
        )

    def _get_random_numeric_string(self, lenght: int = 3) -> str:
        return "".join(random.choices(string.digits, k=lenght))
