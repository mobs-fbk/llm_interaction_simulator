import logging
from dataclasses import dataclass

import autogen

from .chat import Chat

logger = logging.getLogger(__name__)


@dataclass
class Manager(autogen.GroupChatManager):
    def __init__(self, groupchat: Chat, llm_config: dict) -> None:
        super().__init__(groupchat=groupchat, llm_config=llm_config)
        logger.debug("Manager created")

    def __hash__(self) -> int:
        return super().__hash__()
