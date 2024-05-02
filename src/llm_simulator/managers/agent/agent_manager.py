from dataclasses import dataclass, field
from typing import Any

from itakello_logging import ItakelloLogging

from ...components.placeholder import Placeholder

# from ..conversations.agent import Agent
from ...components.role import Role
from ...components.section import Section
from ...core.input_manager import InputManager
from ...utility.document_serializer import DocumentSerializer
from ...utility.enums import SectionType

logger = ItakelloLogging().get_logger(__name__)


@dataclass
class AgentManager(DocumentSerializer):
    input_m: InputManager = field(init=False)
    roles: dict[str, Role] = field(default_factory=dict)
    shared_sections: dict[str, Section] = field(default_factory=dict)
    summarizer_sections: dict[str, Section] = field(default_factory=dict)
    placeholders: dict[str, Placeholder] = field(default_factory=dict)

    def __init__(
        self,
        roles: list[Role],
        shared_sections: list[Section],
        summarizer_sections: list[Section],
        placeholders: list[Placeholder] = [],
    ) -> None:
        self.input_m = InputManager()
        self.roles = {role.name: role for role in roles}
        self.shared_sections = {section.title: section for section in shared_sections}
        self.summarizer_sections = {
            section.title: section for section in summarizer_sections
        }
        if not placeholders:
            placeholders = self._create_starting_placeholders()
        self.placeholders = {
            placeholder.tag: placeholder for placeholder in placeholders
        }
        self.ask_contents_empty_sections()
        logger.debug(
            f"Added:\n"
            + f"- {len(roles)} roles\n"
            + f"- {len(shared_sections)} shared sections\n"
            + f"- {len(summarizer_sections)} summarizer sections\n"
            + f"- {len(placeholders)} placeholders"
        )

    def __str__(self) -> str:
        roles = "\n".join([str(role) for role in self.roles.values()])
        shared_sections = "\n".join(
            [str(section) for section in self.shared_sections.values()]
        )
        summarizer_sections = "\n".join(
            [str(section) for section in self.summarizer_sections.values()]
        )
        placeholders = "\n".join(
            [str(placeholder) for placeholder in self.placeholders.values()]
        )
        return (
            f"{roles}\n\n"
            + f"\033[1mShared sections\033[0m:\n{shared_sections}\n\n"
            + f"\033[1mSummarizer sections\033[0m:\n{summarizer_sections}\n\n"
            + f"\033[1mGlobal placeholders\033[0m:\n{placeholders}"
        )

    @classmethod
    def from_document(cls, doc: dict) -> "AgentManager":
        return cls(
            roles=[Role.from_document(role) for role in doc["roles"]],
            shared_sections=[
                Section.from_document(section) for section in doc["shared_sections"]
            ],
            summarizer_sections=[
                Section.from_document(section) for section in doc["summarizer_sections"]
            ],
            placeholders=[
                Placeholder.from_document(placeholder)
                for placeholder in doc["placeholders"]
            ],
        )

    def to_document(self) -> dict:
        return {
            "roles": [role.to_document() for role in self.roles.values()],
            "shared_sections": [
                section.to_document() for section in self.shared_sections.values()
            ],
            "summarizer_sections": [
                section.to_document() for section in self.summarizer_sections.values()
            ],
            "placeholders": [
                placeholder.to_document() for placeholder in self.placeholders.values()
            ],
        }

    def ask_contents_empty_sections(self) -> None:
        private_sections = [
            section
            for role in self.roles.values()
            for section in role.sections.values()
            if not section.content
        ]
        shared_sections = [
            section for section in self.shared_sections.values() if not section.content
        ]
        summarizer_sections = [
            section
            for section in self.summarizer_sections.values()
            if not section.content
        ]
        empty_sections = private_sections + shared_sections + summarizer_sections

        if not empty_sections:
            return

        logger.instruction(
            "1. \033[1mPlaceholders\033[0m\033[36m: A list of available placeholders will be displayed. These placeholders allow you to specify elements within the text that change depending on context, such as singular or plural forms based on the number of agents.\n"
            + "2. \033[1mUsing Placeholders in Content\033[0m\033[36m: When composing content for each section, incorporate any of the displayed placeholders directly into your text. Placeholders such as <AGENT_NUM> will automatically be replaced with the actual number of agents with that role in the conversation (e.g., '1', '2', '3'...).\nSimilarly, <AGENT_NOUN> will adapt to reflect the singular or plural noun appropriate to the context, such as 'guard' for one and 'guards' for more than one.\nEXAMPLE: 'There are <GUARD_NUM> <GUARD_NOUN> in the room,' in the case of 3 guards form will become 'There are 3 guards in the room'.\n"
            + "3. \033[1mCreating and Using New Verb Placeholders\033[0m\033[36m: You can create new placeholders specifically for verbs by using the format <AGENT_VERB>. Ensure:\n\ti. to use the base form of the verb when creating these placeholders (e.g. <AGENT_MAKE>, <AGENT_GO>, or <AGENT_EAT>).\n\tii. to insert the agent role subject to the verb (e.g. <GUARD_MAKE>).\nOnce established, these verb placeholders can be incorporated into the content of any section, adapting to the context as needed.\nEXAMPLE: 'The <GUARD_NOUN> <GUARD_MAKE> a decision,' in the singular form wll become 'The guard makes a decision'.\n"
        )
        self._print_all_placeholders()

        for section in sorted(empty_sections):
            self.ask_section_content(section)

    def ask_section_content(self, section: Section) -> None:
        invalid_placeholders = True
        while invalid_placeholders:
            message = f"Enter the content for the {section.type.value} {section.title} section"
            if section.type == SectionType.PRIVATE:
                assert section.role, logger.error("Private section without role")
                message += f" of {section.role.capitalize()} agents"
            content = self.input_m.input_str(message)
            new_placeholders = section.set_content(content)
            invalid_placeholders = self.add_missing_placeholders(new_placeholders)
            if invalid_placeholders:
                logger.warning(
                    "You can only:\n"
                    + "1. use existing placeholders\n"
                    + "2. create new verb placeholders in the form <ROLE_VERB_VERB> with the verb in its base form (e.g. <GUARD_VERB_MAKE>)\n"
                    + "Please try again."
                )

    def _print_placeholders(self) -> None:
        placeholders = "\n".join(
            [str(placeholder) for placeholder in self.placeholders.values()]
        )
        logger.info(f"Available general placeholders:\n{placeholders}\n")

    def _print_all_placeholders(self) -> None:
        for role in self.roles.values():
            role.print_placeholders()
        self._print_placeholders()

    def add_missing_placeholders(self, tags: set[str]) -> bool:
        curr_tags = set()
        for role in self.roles.values():
            curr_tags.update(role.placeholders.keys())
        curr_tags.update(self.placeholders.keys())
        new_tags = []
        for tag in tags:
            if tag not in curr_tags:
                parts = tag[1:-1].split("_")
                parts = [part.lower() for part in parts]
                if (
                    len(parts) != 3
                    or parts[0] not in self.roles.keys()
                    or parts[1] != "VERB"
                    or not Placeholder.is_verb(parts[2])
                ):
                    logger.error(f"Invalid placeholder tag: {tag}")
                    return True
                self.roles[parts[0]].placeholders[tag] = Placeholder(tag=tag)
                new_tags.append(tag)
        if new_tags:
            logger.warning(f"New placeholders created: {', '.join(new_tags)}")
        logger.debug(f"Added {len(new_tags)} new placeholders")
        return False

    def _create_starting_placeholders(self) -> list[Placeholder]:
        return [
            Placeholder(tag=f"<AGENTS_NUM>"),
            Placeholder(tag=f"<ROLES_NUM>"),
        ]

    def get_agent_combinations(
        self, role_agents_num: list[tuple[str, int]], try_each_combination: bool
    ) -> list[list[tuple[str, int]]]:
        agent_combinations = []
        if try_each_combination:
            self.generate_combinations(role_agents_num, [], 0, agent_combinations)
        else:
            agent_combinations.append(role_agents_num)
        return agent_combinations

    def generate_combinations(
        self,
        nums: list[Any],
        current_combination: list[Any],
        index: int,
        result: list[list[tuple[str, int]]],
    ) -> None:
        if index == len(nums):
            result.append(current_combination.copy())
            return
        for i in range(1, nums[index][1] + 1):
            current_combination.append((nums[index][0], i))
            self.generate_combinations(nums, current_combination, index + 1, result)
            current_combination.pop()

    def list_combinations(
        self, nums: list[tuple[str, int]]
    ) -> list[list[tuple[str, int]]]:
        result = []
        self.generate_combinations(nums, [], 0, result)
        return result

    def compose_placeholders(
        self, agent_combination: list[tuple[str, int]]
    ) -> dict[str, str]:
        placeholders = {}
        total_agents = 0
        for role, num in agent_combination:
            total_agents += num
            for placeholder in self.roles[role].placeholders.values():
                placeholders[placeholder.tag] = placeholder.to_value(num)
        for placeholder in self.placeholders.values():
            if placeholder.role == "roles":
                placeholders[placeholder.tag] = placeholder.to_value(
                    len(agent_combination)
                )

            elif placeholder.role == "agents":
                placeholders[placeholder.tag] = placeholder.to_value(total_agents)
            else:
                logger.error(f"Invalid placeholder role: {placeholder.role}")
                exit()
        return placeholders
