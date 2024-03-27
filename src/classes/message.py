from dataclasses import dataclass, field

from ..handlers import DocumentSerializable


@dataclass
class Message(DocumentSerializable):

    def to_document(self) -> dict:
        return {}
