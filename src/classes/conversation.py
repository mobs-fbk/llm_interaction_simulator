from dataclasses import dataclass, field

from ..serializers import DocumentSerializable


@dataclass
class Conversation(DocumentSerializable):
    messages: list[dict] = field(default_factory=list)

    def to_document(self) -> dict:
        return {"messages": self.messages}
