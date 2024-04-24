import logging
from dataclasses import dataclass, field

from ..serializers.document_serializer import DocumentSerializer

logger = logging.getLogger(__name__)


@dataclass
class LLM(DocumentSerializer):
    name: str

    def __post_init__(self) -> None:
        logger.debug(f"Created new llm: {self.name}")

    def to_document(self) -> str:
        return self.name

    @classmethod
    def from_document(cls, doc: str) -> "LLM":
        return cls(name=doc)

    def __str__(self) -> str:
        return self.name
