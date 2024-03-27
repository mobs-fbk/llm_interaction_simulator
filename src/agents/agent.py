import logging
import random
import string
from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any

from autogen import ConversableAgent

from ..handlers import ConfigHandler


@dataclass
class Agent(ConversableAgent):
    id: str
    system_prompt: str = field(init=False)
    shared_context = ConfigHandler().get_section("Shared")

    def __init__(
        self,
        llm_config: dict[str, Any],
        n_guards: int,
        n_prisoners: int,
        agent_fields: list[str],
        context: dict,
        id: str,
    ):
        self.id = id
        self._build_system_prompt(agent_fields, context)
        self._update_prompt(n_guards, n_prisoners)
        super().__init__(
            name=self.id,
            llm_config=llm_config,
            system_message=self.system_prompt,
            human_input_mode="NEVER",
            code_execution_config=False,
        )

    def __post_init__(self) -> None:
        logging.debug(f"Agent {self.id} created")

    def __hash__(self) -> int:
        return super().__hash__()

    def __str__(self) -> str:
        return "Agent: " + self.id + "\nSystem Prompt: " + self.system_prompt + "\n"

    def _build_system_prompt(self, context_fields: list[str], context: dict):
        self.system_prompt = context["starting_prompt"]
        self._add_template(context_fields)
        self._fill_template(context)
        return

    def _add_template(self, keys: list[str]):
        for key in keys:
            self.system_prompt += (
                f"\n\n## {str.capitalize(key).replace('_', ' ')}\n{{{key}}}"
            )

    def _fill_template(self, context: dict):
        merged_context = {**context, **self.shared_context}
        try:
            self.system_prompt = self.system_prompt.format(**merged_context)
        except KeyError as e:
            raise Exception(
                f"Missing field {e} inside the {self.id.split('_')[0]} context."
            )

    def _update_prompt(self, n_guards: int, n_prisoners: int):
        self._update_prompt_numbers(n_guards, n_prisoners)
        self._update_prompt_tags(n_guards, n_prisoners)

    def _update_prompt_numbers(self, n_guards: int, n_prisoners: int):
        number_to_word = {1: "one", 2: "two", 3: "three", 4: "four"}

        agents_number_word = number_to_word[n_guards + n_prisoners]
        prisoners_number_word = number_to_word[n_prisoners]
        guards_number_word = number_to_word[n_guards]

        self.system_prompt = self.system_prompt.replace(
            "<AGENT_NUMBER_WORD>", agents_number_word
        )
        self.system_prompt = self.system_prompt.replace(
            "<PRISONER_NUMBER_WORD>", prisoners_number_word
        )
        self.system_prompt = self.system_prompt.replace(
            "<GUARD_NUMBER_WORD>", guards_number_word
        )

    def _update_prompt_tags(self, n_guards: int, n_prisoners: int):
        tags_strings = ConfigHandler().get_section("Tags")

        tags_dict = {
            k: [tag.strip() for tag in v.split(",")] for k, v in tags_strings.items()
        }

        self.system_prompt = self.system_prompt.replace(
            "<PRISONER_NOUN>", tags_dict["prisoner_noun"][n_prisoners - 1]
        )
        self.system_prompt = self.system_prompt.replace(
            "<PRISONER_POSSESSIVE>", tags_dict["prisoner_possessive"][n_prisoners - 1]
        )
        self.system_prompt = self.system_prompt.replace(
            "<GUARD_NOUN>", tags_dict["guard_noun"][n_guards - 1]
        )
        self.system_prompt = self.system_prompt.replace(
            "<GUARD_POSSESSIVE>", tags_dict["guard_possessive"][n_guards - 1]
        )

    def _get_random_numeric_string(self, lenght: int = 3):
        return "".join(random.choices(string.digits, k=lenght))

    # @abstractmethod
    # def _update_plurals(self):
    #    pass

    @abstractmethod
    def _get_name(self) -> str:
        pass
