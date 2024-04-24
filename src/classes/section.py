import logging
from dataclasses import dataclass

from ..serializers.document_serializer import DocumentSerializer

logger = logging.getLogger(__name__)


@dataclass
class Section(DocumentSerializer):
    index: int
    title: str
    content: str

    def __post_init__(self) -> None:
        self.title = self.title.replace("_", " ").capitalize()
        self.content = self.content.strip()
        logger.debug(f"Created new section: {self.title}")

    @classmethod
    def from_document(cls, doc: dict) -> "Section":
        return cls(index=doc["index"], title=doc["title"], content=doc["content"])

    def set_content(self, content: str) -> set[str]:
        placeholders_tags = set(
            [
                word
                for word in content.split()
                if word.startswith("<") and word.endswith(">")
            ]
        )
        self.content = content
        return placeholders_tags

    def to_document(self) -> dict:
        return {
            "index": self.index,
            "title": self.title,
            "content": self.content,
        }

    def __str__(self) -> str:
        output = f"{self.content}"
        if self.title != "Starting prompt":
            output = f"##{self.title}\n\n" + output
        output = f"---\n{output}\n---"
        return output

    def __lt__(self, other: "Section") -> bool:
        return self.index < other.index

    def __gt__(self, other: "Section") -> bool:
        return self.index > other.index
