import logging
from dataclasses import dataclass, field

from ..classes.placeholder import Placeholder
from ..classes.role import Role
from ..classes.section import Section
from ..serializers.document_serializer import DocumentSerializer
from ..utility.enums import PlaceholderType

logger = logging.getLogger(__name__)


@dataclass
class AgentManager(DocumentSerializer):
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
            f"\033[1mRoles\033[0m:\n{roles}\n\n"
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

    def print_placeholders(self) -> None:
        placeholders = "\n".join(
            [str(placeholder) for placeholder in self.placeholders.values()]
        )
        logger.info(f"Available general placeholders:\n{placeholders}\n")

    def print_all_placeholders(self) -> None:
        for role in self.roles.values():
            role.print_placeholders()
        self.print_placeholders()

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
                    or parts[1] != PlaceholderType.VERB.value.lower()
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
