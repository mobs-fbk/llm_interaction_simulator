from abc import ABC
from dataclasses import dataclass

from itakello_logging import ItakelloLogging

logger = ItakelloLogging().get_logger(__name__)


@dataclass
class BaseManager(ABC):

    def __post_init__(self) -> None:
        logger.debug(f"--{self.__class__.__name__} initialized--")
