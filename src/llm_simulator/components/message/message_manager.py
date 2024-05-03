from dataclasses import dataclass, field

from itakello_logging import ItakelloLogging

from ...abstracts import BaseManager
from ...core.database_manager import DatabaseManager
from ...core.input_manager import InputManager

logger = ItakelloLogging().get_logger(__name__)


@dataclass
class MessageManager(BaseManager):
    input_m: InputManager
    db_m: DatabaseManager
