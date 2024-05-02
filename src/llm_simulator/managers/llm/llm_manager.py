from dataclasses import dataclass, field

from itakello_logging import ItakelloLogging

from ...core.input_manager import InputManager
from ...utility.document_serializer import DocumentSerializer
from .llm import LLM

logger = ItakelloLogging.get_logger(__name__)


@dataclass
class LLMManager(DocumentSerializer):
    input_m: InputManager
    llms: dict[str, LLM] = field(default_factory=dict)

    def populate(self, llms: list[LLM]) -> None:
        self.llms = {llm.name: llm for llm in llms}
        logger.debug(f"Added {len(llms)} new llms")

    def to_document(self) -> list:
        return [llm.to_document() for llm in self.llms.values()]

    @classmethod
    def from_document(cls, doc: list) -> "LLMManager":
        obj = cls(input_m=InputManager())
        obj.populate([LLM.from_document(llm) for llm in doc])
        return obj

    def __str__(self) -> str:
        return "\n".join(["- " + str(llm) for llm in self.llms.values()])
