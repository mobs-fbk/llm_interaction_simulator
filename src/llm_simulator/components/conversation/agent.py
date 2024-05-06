import random
import string
from dataclasses import InitVar, dataclass
from typing import Any, Dict, List, Optional, Union

from autogen import ConversableAgent
from autogen.agentchat.agent import Agent
from itakello_logging import ItakelloLogging

from ..llm.llm import LLM
from ..section.section import Section

logger = ItakelloLogging().get_logger(__name__)


@dataclass
class CustomAgent(ConversableAgent):
    role: str
    full_roles: list[str]

    placeholders: InitVar[dict[str, str]]
    sections: InitVar[list[Section]]
    llm: InitVar[LLM]

    def __post_init__(
        self, placeholders: dict[str, str], sections: list[Section], llm: LLM
    ) -> None:
        name = self.role.capitalize() + "_" + self._get_random_numeric_string()
        system_message = self._generate_system_message(sections, placeholders)
        super().__init__(
            name=name,
            llm_config=llm.config,
            system_message=system_message,
            human_input_mode="NEVER",
            code_execution_config=False,
            # description=f"A {self.role} named {name}",
        )

    def _generate_system_message(
        self, sections: list[Section], placeholders: dict[str, str]
    ) -> str:
        final_contents = []
        for section in sorted(sections):
            final_content = str(section)
            for placeholder, value in placeholders.items():
                final_content = final_content.replace(placeholder, value)
            final_contents.append(final_content)
        system_message = "\n\n".join(final_contents)
        return system_message

    def _get_random_numeric_string(self, lenght: int = 3) -> str:
        return "".join(random.choices(string.digits, k=lenght))

    def generate_reply(
        self,
        messages: Optional[List[Dict[str, Any]]] = None,
        sender: Optional[Union["Agent", None]] = None,
        **kwargs: Any,
    ) -> Union[str, Dict, None]:
        reply = super().generate_reply(messages=messages, sender=sender, **kwargs)
        reply = str(reply).strip()
        # logger.debug(f"Raw reply:\n---\n{reply}\n---\n")
        for w in self.full_roles:
            if w == reply[: len(w)]:
                reply = reply[len(w) :]
        for w in self.full_roles:
            if w in reply:
                reply = reply.split(w)[0]
        reply = reply.strip()
        # logger.debug(f"Processed reply:\n---\n{reply}\n---\n")
        return reply

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other) -> bool:
        return isinstance(other, Agent) and self.name == other.name
