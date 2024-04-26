from dataclasses import dataclass, field

from itakello_logging import ItakelloLogging

from ..serializers.document_serializer import DocumentSerializer
from .placeholder import Placeholder
from .section import Section

logger = ItakelloLogging.get_logger(__name__)


@dataclass
class Role(DocumentSerializer):
    name: str
    sections: dict[str, Section] = field(default_factory=dict)
    placeholders: dict[str, Placeholder] = field(default_factory=dict)

    def __init__(
        self,
        name: str,
        sections: list[Section],
        placeholders: list[Placeholder] = [],
    ) -> None:
        self.name = name
        self.sections = {section.title: section for section in sections}
        if not placeholders:
            placeholders = self._create_starting_placeholders()
        self.placeholders = {
            placeholder.tag: placeholder for placeholder in placeholders
        }
        logger.debug(
            f"Created new role [{self.name}] with:\n"
            + f"- {len(self.sections)} private sections\n"
            + f"- {len(self.placeholders)} placeholders"
        )

    def __str__(self) -> str:
        sections = "\n".join([str(section) for section in self.sections.values()])
        placeholders = "\n".join(
            [str(placeholder) for placeholder in self.placeholders.values()]
        )
        return (
            "----------------------------------------\n"
            + f"\033[1mName\033[0m: {self.name}\n"
            + f"\033[1mPrivate sections\033[0m:\n{sections}\n"
            + f"\033[1mPlaceholders\033[0m:\n{placeholders}\n"
            + "----------------------------------------"
        )

    @classmethod
    def from_document(cls, doc: dict) -> "Role":
        return cls(
            name=doc["name"],
            sections=[Section.from_document(section) for section in doc["sections"]],
            placeholders=[
                Placeholder.from_document(placeholder)
                for placeholder in doc["placeholders"]
            ],
        )

    def to_document(self) -> dict:
        return {
            "name": self.name,
            "sections": [section.to_document() for section in self.sections.values()],
            "placeholders": [
                placeholder.to_document() for placeholder in self.placeholders.values()
            ],
        }

    def print_placeholders(self) -> None:
        placeholders = "\n".join(
            [str(placeholder) for placeholder in self.placeholders.values()]
        )
        logger.info(
            f"Available placeholders for {self.name.upper()} agent:\n{placeholders}\n"
        )

    def _create_starting_placeholders(self) -> list[Placeholder]:
        return [
            Placeholder(tag=f"<{self.name.upper()}_NOUN>"),
            Placeholder(tag=f"<{self.name.upper()}_POSS>"),
            Placeholder(tag=f"<{self.name.upper()}_POSSPRON>"),
            Placeholder(tag=f"<{self.name.upper()}_PRON>"),
            Placeholder(tag=f"<{self.name.upper()}_NUM>"),
        ]

    # def _get_name_addition(self, numerical_name: bool) -> str:
    #    addition = "_"
    #    if numerical_name:
    #        addition += self._get_random_numeric_string()
    #    else:
    #        addition += self._get_random_name()
    #    return addition

    # def _get_random_numeric_string(self, lenght: int = 3) -> str:
    #    return "".join(random.choices(string.digits, k=lenght))

    # def _get_random_name(self) -> str:
    #    random_names = "John, Mary, Alice, Bob, Charlie, David, Eve, Frank, Grace, Helen, Ian, Jack, Kate, Liam, Megan, Nick, Olivia, Peter, Queen, Rachel, Steve, Tina, Victor, Wendy, Xavier, Yvonne, Zack".split(
    #        ", "
    #    )

    #    return random.choice(random_names)
