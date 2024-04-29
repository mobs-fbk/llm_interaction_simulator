from dataclasses import dataclass, field
from typing import Union

import inquirer
from inquirer.render.console import ConsoleRender
from inquirer.themes import GreenPassion
from itakello_logging import ItakelloLogging

logger = ItakelloLogging.get_logger(__name__)


@dataclass
class InputManager:
    render: ConsoleRender = field(init=False)

    def __post_init__(self) -> None:
        self.render = ConsoleRender(theme=GreenPassion())

    def confirm(self, message: str) -> bool:
        return inquirer.confirm(message, render=self.render)

    def input_int(
        self,
        question: str,
        positive_requirement: bool = False,
    ) -> int:
        while True:
            user_input = inquirer.text(question, render=self.render)
            try:
                user_input = int(user_input)
            except ValueError:
                logger.error("Invalid input. Please enter a number.")
                continue
            if positive_requirement and user_input <= 0:
                logger.error("Invalid input. Please enter a positive number.")
                continue
            return user_input

    def input_float(
        self, message: str, positive_requirement: bool = False, max_value: float = 0
    ) -> float:
        while True:
            user_input = inquirer.text(message, render=self.render)
            try:
                user_input = float(user_input)
            except ValueError:
                logger.error("Invalid input. Please enter a float number.")
                continue
            if positive_requirement and user_input < 0:
                logger.error("Invalid input. Please enter a positive number.")
                continue
            if max_value and user_input > max_value:
                logger.error(
                    f"Invalid input. Please enter a number not greater than {max_value}."
                )
                continue
            return user_input

    def input_str(
        self,
        message: str,
        optional: bool = False,
        example: str = "",
    ) -> str:
        while True:
            if example:
                message += f" (e.g. {example})"
            user_input = inquirer.text(message, render=self.render)
            if not optional and not user_input:
                logger.error("Invalid input. Please enter a value.")
                continue
            return user_input

    def input_list(
        self,
        message: str,
        optional: bool = False,
        example: str = "",
        avoid_duplicates: bool = True,
    ) -> list[str]:
        message += " [comma-separated list]"
        if example:
            message += f" (e.g. {example})"
        while True:
            user_input = inquirer.text(message, render=self.render)
            items = [item.strip() for item in user_input.split(",")]
            if avoid_duplicates and len(set(items)) != len(items):
                logger.error("Invalid input. Please ensure all items are different.")
                continue
            if "" in items:
                if len(items) == 1 and not optional:
                    logger.error("Invalid input. Please enter at least one value.")
                else:
                    logger.error(
                        "Invalid input. Please ensure there are no empty values."
                    )
                continue
            return items

    def select_one(
        self, message: str, choices: Union[list[str], list[tuple[str, str]]]
    ) -> str:
        return inquirer.list_input(message=message, choices=choices, render=self.render)

    def select_multiple(
        self, message: str, choices: Union[list[str], list[tuple[str, str]]]
    ) -> list[str]:
        return inquirer.checkbox(message=message, choices=choices, render=self.render)

    def password(self, message: str) -> str:
        return inquirer.password(message, render=self.render)
