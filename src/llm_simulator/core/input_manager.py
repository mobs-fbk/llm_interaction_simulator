from dataclasses import dataclass, field
from typing import Union

import inquirer3
from inquirer3.render.console import ConsoleRender
from inquirer3.themes import GreenPassion
from itakello_logging import ItakelloLogging

from ..abstracts import BaseManager

logger = ItakelloLogging().get_logger(__name__)


@dataclass
class InputManager(BaseManager):
    render: ConsoleRender = field(init=False)

    def __post_init__(self) -> None:
        self.render = ConsoleRender(theme=GreenPassion())
        super().__post_init__()

    def confirm(self, message: str) -> bool:
        logger.debug(f"Message: {message}")
        user_input = inquirer3.confirm(message, render=self.render)
        logger.debug(f"Input: {user_input}")
        return user_input

    def input_int(
        self,
        message: str,
        max_value: int = 0,
        positive_requirement: bool = False,
        even_requirement: bool = False,
    ) -> int:
        logger.debug(f"Message: {message}")
        correct = False
        user_input = 0
        while not correct:
            user_input = inquirer3.text(message, render=self.render)
            try:
                user_input = int(user_input)
            except ValueError:
                logger.error("Invalid input. Please enter a number.")
                continue
            if positive_requirement and user_input <= 0:
                logger.error("Invalid input. Please enter a positive number.")
            elif even_requirement and user_input % 2 != 0:
                logger.error("Invalid input. Please enter an even number.")
            elif max_value and user_input > max_value:
                logger.error(
                    f"Invalid input. Please enter a number not greater than {max_value}."
                )
            else:
                correct = True
        logger.debug(f"Input: {user_input}")
        return user_input

    def input_float(
        self, message: str, positive_requirement: bool = False, max_value: float = 0
    ) -> float:
        logger.debug(f"Message: {message}")
        correct = False
        user_input = 0.0
        while not correct:
            user_input = inquirer3.text(message, render=self.render)
            try:
                user_input = float(user_input)
            except ValueError:
                logger.error("Invalid input. Please enter a float number.")
                continue
            if positive_requirement and user_input < 0:
                logger.error("Invalid input. Please enter a positive number.")
            elif max_value and user_input > max_value:
                logger.error(
                    f"Invalid input. Please enter a number not greater than {max_value}."
                )
            else:
                correct = True
        logger.debug(f"Input: {user_input}")
        return user_input

    def input_str(
        self,
        message: str,
        optional: bool = False,
        example: str = "",
    ) -> str:
        logger.debug(f"Message: {message}")
        correct = False
        user_input = ""
        while not correct:
            if example:
                message += f" (e.g. {example})"
            user_input = inquirer3.text(message, render=self.render)
            if not optional and not user_input:
                logger.error("Invalid input. Please enter a value.")
            else:
                correct = True
        logger.debug(f"Input: {user_input}")
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
        logger.debug(f"Message: {message}")
        correct = False
        items = []
        while not correct:
            user_input = inquirer3.text(message, render=self.render)
            items = [item.strip() for item in user_input.split(",")]
            if avoid_duplicates and len(set(items)) != len(items):
                logger.error("Invalid input. Please ensure all items are different.")
                continue
            if "" in items:
                if len(items) == 1:
                    if optional:
                        items = []
                        correct = True
                    else:
                        logger.error("Invalid input. Please enter at least one value.")
                else:
                    logger.error(
                        "Invalid input. Please ensure there are no empty values."
                    )
                continue
            else:
                correct = True
        logger.debug(f"Input: {items}")
        return items

    def select_one(
        self, message: str, choices: list[str] | list[tuple[str, str]]
    ) -> str:
        logger.debug(f"Message: {message}")
        user_input = inquirer3.list_input(
            message=message, choices=choices, render=self.render
        )
        logger.debug(f"Input: {user_input}")
        return user_input

    def select_multiple(
        self, message: str, choices: list[str] | list[tuple[str, str]]
    ) -> list[str]:
        logger.debug(f"Message: {message}")
        user_input = inquirer3.checkbox(
            message=message, choices=choices, render=self.render
        )
        logger.debug(f"Input: {user_input}")
        return user_input

    def password(self, message: str) -> str:
        logger.debug(f"Message: {message}")
        user_input = inquirer3.password(message, render=self.render)
        logger.debug(f"Input: {user_input}")
        return user_input


if __name__ == "__main__":
    input_m = InputManager()
    output = input_m.input_list("Enter a list of items", example="item1, item2, item3")
    print(output)
