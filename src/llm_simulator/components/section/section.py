from dataclasses import dataclass

from itakello_logging import ItakelloLogging

from ...abstracts.mongo_model import MongoModel
from ...utility.enums import SectionType

logger = ItakelloLogging().get_logger(__name__)


@dataclass
class Section(MongoModel):
    index: int
    title: str
    content: str
    type: SectionType
    to_reset: bool = False
    role: str = ""

    def __post_init__(self) -> None:
        self.title = self.title.replace("_", " ").capitalize()
        self.content = self.content.strip()
        logger.debug(f"Created new section: {self.title}")

    @classmethod
    def from_document(cls, doc: dict) -> "Section":
        role = doc.get("role", "")
        return cls(
            index=doc["index"],
            title=doc["title"],
            content=doc["content"],
            type=SectionType(doc["type"]),
            role=role,
        )

    def set_content(self, content: str) -> set[str]:
        placeholders_tags = set(
            [
                word
                for word in content.split()
                if word.startswith("<") and word.endswith(">")
            ]
        )
        self.content = content
        self.to_reset = False
        return placeholders_tags

    def to_document(self) -> dict:
        doc = {
            "index": self.index,
            "title": self.title,
            "content": self.content,
            "type": self.type.value,
        }
        if self.role:
            doc["role"] = self.role
        return doc

    def __str__(self) -> str:
        output = f"{self.content}\n"
        if self.title != "Starting prompt":
            output = f"## {self.title}\n\n" + output
        return output

    def __lt__(self, other: "Section") -> bool:
        if self.index == 0 or other.index == 0:
            return self.index < other.index
        if self.type == other.type:
            if self.index == other.index:
                return self.role < other.role
            return self.index < other.index
        return self.type < other.type

    def __eq__(self, other: "Section") -> bool:  # type: ignore
        return self.title == other.title
