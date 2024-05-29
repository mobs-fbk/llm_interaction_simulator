from dataclasses import dataclass, field

from itakello_logging import ItakelloLogging

from ...interfaces import BaseManager
from ...core.input_manager import InputManager

logger = ItakelloLogging().get_logger(__name__)


@dataclass
class PlaceholderManager(BaseManager):
    input_m: InputManager
