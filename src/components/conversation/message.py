from dataclasses import dataclass, field

from bson.objectid import ObjectId

from ...interfaces.mongo_model import MongoModel


@dataclass
class Message(MongoModel):
    index: int
    day: int
    role: str
    speaker: str
    content: str
    id: ObjectId = field(init=False, default_factory=ObjectId)

    @classmethod
    def from_document(cls, doc: dict) -> "Message":
        return cls(
            index=doc["index"],
            day=doc["day"],
            role=doc["role"],
            speaker=doc["speaker"],
            content=doc["content"],
        )

    def to_document(self) -> dict:
        return {
            "index": self.index,
            "day": self.day,
            "role": self.role,
            "speaker": self.speaker,
            "content": self.content,
        }
