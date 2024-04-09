from dataclasses import dataclass, field
from typing import Union

from bson.objectid import ObjectId

from ..serializers import DocumentSerializer
from .message import Message


@dataclass
class Conversation(DocumentSerializer):
    id: ObjectId = field(init=False)
    completed: bool = False
    description: str = ""
    interesting: bool = False
    messages: list[Union[ObjectId, Message]] = field(default_factory=list)

    def add_daily_conversation(self, raw_conversation: list[dict], day: int) -> None:
        messages = []
        for i, message in enumerate(raw_conversation):
            messages.append(
                Message(
                    index=i,
                    day=day,
                    role=message["name"].split("_")[0],
                    speaker=message["name"],
                    content=message["content"],
                )
            )
        self.messages.extend(messages)

    def to_document(self) -> dict:
        return {}

    def fetch_messages(self) -> None:
        pass
