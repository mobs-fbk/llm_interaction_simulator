from dataclasses import dataclass
from typing import cast

from autogen import Agent, GroupChat
from itakello_logging import ItakelloLogging

from .agent import CustomAgent

logger = ItakelloLogging().get_logger(__name__)


@dataclass
class Chat(GroupChat):

    def __init__(
        self,
        agents: list[CustomAgent],
        selection_method: str = "auto",
        round_number: int = 10,
    ) -> None:
        assert selection_method in (
            "auto",
            "manual",
            "random",
            "round_robin",
        ), logger.error(f"Invalid mode [{selection_method}]")
        super().__init__(
            agents=cast(list[Agent], agents),
            messages=[],  # no messages to start
            speaker_selection_method=selection_method,
            allow_repeat_speaker=False,
            max_round=round_number,
        )
        logger.debug(
            f"GroupChat created with {len(agents)} agents.\nSelection method: {selection_method}\nRounds number: {round_number}"
        )
