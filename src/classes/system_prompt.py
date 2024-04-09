import logging
from dataclasses import dataclass, field

from ..handlers import config_handler

logger = logging.getLogger(__name__)


@dataclass
class SystemPrompt:
    content: str = field(init=False)

    def __init__(
        self,
        context: dict,
        fields: list[str],
        n_guards: int,
        n_prisoners: int,
    ) -> None:
        assert "starting_prompt" in context, logger.error(
            "starting_prompt is missing in the context"
        )
        temp_content = self._create_content(fields=fields, context=context)
        self.content = self._fill_plurals(temp_content, n_guards, n_prisoners)

    def _create_content(self, fields: list[str], context: dict) -> str:
        template = self._create_template(fields)
        filled_template = self._fill_template(template, context)
        content = context["starting_prompt"] + filled_template
        return content

    def _create_template(self, keys: list[str]) -> str:
        template = ""
        for key in keys:
            template += f"\n\n## {str.capitalize(key).replace('_', ' ')}\n{{{key}}}"
        return template

    def _fill_template(self, template: str, context: dict) -> str:
        try:
            template = template.format(**context)
        except KeyError as e:
            logging.error(f"KeyError: {e} in context")
        return template

    def _fill_plurals(self, temp_content: str, n_guards: int, n_prisoners: int) -> str:
        numbered_content = self._update_prompt_numbers(
            temp_content, n_guards, n_prisoners
        )
        final_content = self._update_prompt_tags(
            numbered_content, n_guards, n_prisoners
        )
        return final_content

    def _update_prompt_numbers(
        self, content: str, n_guards: int, n_prisoners: int
    ) -> str:
        number_to_word = {1: "one", 2: "two", 3: "three", 4: "four"}

        agents_number_word = number_to_word[n_guards + n_prisoners]
        prisoners_number_word = number_to_word[n_prisoners]
        guards_number_word = number_to_word[n_guards]

        content = content.replace("<AGENT_NUMBER_WORD>", agents_number_word)
        content = content.replace("<PRISONER_NUMBER_WORD>", prisoners_number_word)
        content = content.replace("<GUARD_NUMBER_WORD>", guards_number_word)
        return content

    def _update_prompt_tags(self, content: str, n_guards: int, n_prisoners: int):
        tags_strings = config_handler.get_section("Tags")

        tags_dict = {
            k: [tag.strip() for tag in v.split(",")] for k, v in tags_strings.items()
        }

        content = content.replace(
            "<PRISONER_NOUN>", tags_dict["prisoner_noun"][n_prisoners - 1]
        )
        content = content.replace(
            "<PRISONER_POSSESSIVE>", tags_dict["prisoner_possessive"][n_prisoners - 1]
        )
        content = content.replace("<GUARD_NOUN>", tags_dict["guard_noun"][n_guards - 1])
        content = content.replace(
            "<GUARD_POSSESSIVE>", tags_dict["guard_possessive"][n_guards - 1]
        )
        return content
