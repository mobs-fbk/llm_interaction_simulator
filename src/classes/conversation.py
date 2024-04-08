from dataclasses import dataclass, field

from ..serializers import DocumentSerializer
from .message import Message


@dataclass
class Conversation:

    messages: list[Message] = field(default_factory=list)

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

    def to_document(self) -> list[dict]:
        return []

    def load_from_db(self):
        pass

    def fetch_conversations(self):
        pass
