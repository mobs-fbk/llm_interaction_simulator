from dataclasses import dataclass, field

from bson.objectid import ObjectId

from ..serializers import DocumentSerializer


@dataclass
class Message(DocumentSerializer):
    id: ObjectId = field(init=False)
    index: int
    day: int
    role: str
    speaker: str
    content: str

    def to_document(self) -> dict:
        return {
            "index": self.index,
            "day": self.day,
            "role": self.role,
            "speaker": self.speaker,
            "content": self.content,
        }
