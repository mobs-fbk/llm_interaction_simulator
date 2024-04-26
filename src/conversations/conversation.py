from dataclasses import dataclass, field
from datetime import datetime

from bson.objectid import ObjectId
from itakello_logging import ItakelloLogging
from llm import LLM

from ..classes.researcher import Researcher
from ..serializers import DocumentSerializer
from ..messages.message import Message

logger = ItakelloLogging.get_logger(__name__)


@dataclass
class Conversation(DocumentSerializer):
    conversation_days: int
    conversation_rounds: int
    speaker_selection_method: str
    starting_message: str
    creator: str
    llm: LLM
    note: str = ""
    favourite: bool = False
    id: ObjectId = field(default_factory=ObjectId)
    creation_date: datetime = field(default_factory=datetime.now)
    messages_ids: list[ObjectId] = field(default_factory=list)

    def __post_init__(self) -> None:
        logger.debug(f"[{self.creator}] created a new conversation: {self.id}")

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

    @classmethod
    def from_document(cls, doc: dict) -> "Conversation":
        return cls(
            id=doc["_id"],
            conversation_days=doc["conversation_days"],
            conversation_rounds=doc["conversation_rounds"],
            speaker_selection_method=doc["speaker_selection_method"],
            starting_message=doc["starting_message"],
            llm=LLM.from_document(doc["llm"]),
            creator=doc["creator"],
            note=doc["note"],
            favourite=doc["favourite"],
            creation_date=doc["creation_date"],
            messages_ids=doc["messages_ids"],
        )

    def to_document(self) -> dict:
        return {
            "_id": self.id,
            "conversation_days": self.conversation_days,
            "conversation_rounds": self.conversation_rounds,
            "speaker_selection_method": self.speaker_selection_method,
            "starting_message": self.starting_message,
            "llm": self.llm.to_document(),
            "creator": self.creator,
            "note": self.note,
            "favourite": self.favourite,
            "creation_date": self.creation_date,
            "messages_ids": self.messages_ids,
        }

    def perform(self, researcher: Researcher, manager:) -> None:
        
