from dataclasses import dataclass

from itakello_logging import ItakelloLogging

from ..abstracts import BaseManager
from ..utility.consts import DEV_MODE
from ..utility.custom_os import CustomOS
from .input_manager import InputManager

logger = ItakelloLogging().get_logger(__name__)


@dataclass
class ActionManager(BaseManager):
    input_m: InputManager

    def select_initial_action(
        self,
    ) -> str:
        choices = ["Create new experiment", "Select experiment", "Exit"]
        if CustomOS.getenv("APP_MODE", "") == DEV_MODE:
            choice_index = CustomOS.getenv("ACTION_1_INDEX")
            return choices[int(choice_index)]
        return self.input_m.select_one(
            message="Select starting action",
            choices=choices,
        )

    def select_experiment_action(self) -> str:
        choices = [
            "Perform new conversations",
            "Duplicate and update experiment",
            "Update experiment (Favourites and Notes)",
            "Select old conversations",
            "Delete experiment",
            "Go back",
        ]
        if CustomOS.getenv("APP_MODE", "") == DEV_MODE:
            choice_index = CustomOS.getenv("ACTION_2_INDEX")
            return choices[int(choice_index)]
        return self.input_m.select_one(
            message="Select experiment action",
            choices=choices,
        )

    def select_conversation_action(self) -> str:
        choices = [
            "View conversation",
            "Set as favourite",
            "Delete conversation",
            "Go back",
        ]
        if CustomOS.getenv("APP_MODE", "") == DEV_MODE:
            choice_index = CustomOS.getenv("ACTION_3_INDEX")
            return choices[int(choice_index)]
        return self.input_m.select_one(
            message="Select conversation action",
            choices=choices,
        )
