from dataclasses import dataclass, field

from itakello_logging import ItakelloLogging

from ..serializers.document_serializer import DocumentSerializer

logger = ItakelloLogging.get_logger(__name__)


@dataclass
class LLM(DocumentSerializer):
    model: str

    def __post_init__(self) -> None:
        self.model = self.model.lower()
        logger.debug(f"Created a new llm: {self.model}")

    def to_document(self) -> str:
        return self.model

    @classmethod
    def from_document(cls, doc: str) -> "LLM":
        return cls(model=doc)

    def __str__(self) -> str:
        return self.model
