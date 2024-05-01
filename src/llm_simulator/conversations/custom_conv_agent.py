import random
import string
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from autogen import ConversableAgent
from autogen.agentchat.agent import Agent
from itakello_logging import ItakelloLogging

# from autogen.agentchat.agent import Agent

logger = ItakelloLogging().get_logger(__name__)


@dataclass
class CustomConversableAgent(ConversableAgent):

    def __init__(
        self, name: str, llm_config: dict, system_message: str, warns: list[str]
    ) -> None:
        super().__init__(
            name=name,
            llm_config=llm_config,
            system_message=system_message,
            human_input_mode="NEVER",
            code_execution_config=False,
        )
        self.warns = warns
        logger.info(
            f"Agent {name} created with system prompt:\n---\n{system_message}\n---\n"
        )

    def generate_reply(
        self,
        messages: Optional[List[Dict[str, Any]]] = None,
        sender: Optional[Union["Agent", None]] = None,
        **kwargs: Any,
    ) -> Union[str, Dict, None]:
        reply = super().generate_reply(messages=messages, sender=sender, **kwargs)
        reply = str(reply).strip()
        logger.debug(f"Raw reply:\n---\n{reply}\n---\n")
        for w in self.warns:
            if w == reply[: len(w)]:
                reply = reply[len(w) :]
        for w in self.warns:
            if w in reply:
                reply = reply.split(w)[0]
        reply = reply.strip()
        logger.debug(f"Processed reply:\n---\n{reply}\n---\n")
        return reply

    def __hash__(self) -> int:
        return super().__hash__()
