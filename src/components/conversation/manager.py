from dataclasses import dataclass

import autogen
from itakello_logging import ItakelloLogging

from .chat import Chat

logger = ItakelloLogging().get_logger(__name__)


@dataclass
class Manager(autogen.GroupChatManager):
    def __init__(self, groupchat: Chat, llm_config: dict) -> None:
        super().__init__(groupchat=groupchat, llm_config=llm_config)
        logger.debug("Manager created")

    def __hash__(self) -> int:
        return super().__hash__()
