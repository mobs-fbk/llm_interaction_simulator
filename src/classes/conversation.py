from dataclasses import dataclass, field
from datetime import datetime
from typing import Union

from bson.objectid import ObjectId

from ..serializers import DocumentSerializer
from .message import Message


@dataclass
class Conversation(DocumentSerializer):
    id: ObjectId = field(init=False)
    creation_date: datetime = field(default_factory=datetime.now)
    note: str = ""
    interesting: bool = False
    messages_ids: list[Union[ObjectId, Message]] = field(default_factory=list)

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
        self.messages_ids.extend(messages)

    def to_document(self) -> dict:
        messages = []
        for message in self.messages_ids:
            if isinstance(message, Message):
                messages.append(message.id)
            else:
                messages.append(message)
        return {
            "note": self.note,
            "creation_date": self.creation_date.strftime("%Y-%m-%d %H:%M:%S"),
            "interesting": self.interesting,
            "messages": messages,
        }

    def fetch_messages(self) -> None:
        pass
