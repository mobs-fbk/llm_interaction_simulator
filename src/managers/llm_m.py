import logging
from dataclasses import dataclass, field

from ..classes.llm import LLM
from ..serializers.document_serializer import DocumentSerializer

logger = logging.getLogger(__name__)


@dataclass
class LLMManager(DocumentSerializer):
    llms: dict[str, LLM] = field(default_factory=dict)

    def __init__(self, llms: list[LLM]) -> None:
        self.llms = {llm.name: llm for llm in llms}
        logger.debug(f"Added {len(llms)} new llms")

    def to_document(self) -> list:
        return [llm.to_document() for llm in self.llms.values()]

    @classmethod
    def from_document(cls, doc: list) -> "LLMManager":
        return cls([LLM.from_document(llm) for llm in doc])

    def __str__(self) -> str:
        llms = "\n".join(["- " + str(llm) for llm in self.llms.values()])
        return "\033[1mLLMs\033[0m:\n" + llms
