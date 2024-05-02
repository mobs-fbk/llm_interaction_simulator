from dataclasses import dataclass, field

from itakello_logging import ItakelloLogging

from .input_manager import InputManager

logger = ItakelloLogging.get_logger(__name__)


@dataclass
class ActionManager:
    input_m: InputManager

    def __post_init__(self) -> None:
        logger.debug("Action manager initialized")

    def select_initial_action(self) -> str:
        return self.input_m.select_one(
            message="Select starting action",
            choices=["Create new experiment", "Select experiment", "Exit"],
        )

    def select_experiment_action(self) -> str:
        return self.input_m.select_one(
            message="Select experiment action",
            choices=[
                "Perform new conversations",
                "Duplicate and update experiment",
                "Select old conversations",
                "Delete experiment",
                "Go back",
            ],
        )

    def select_conversation_action(self) -> str:
        return self.input_m.select_one(
            message="Select conversation action",
            choices=[
                "View conversation",
                "Update conversation",
                "Delete conversation",
                "Go back",
            ],
        )
