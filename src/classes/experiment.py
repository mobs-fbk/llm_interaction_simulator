from dataclasses import dataclass, field
from datetime import datetime

from bson.objectid import ObjectId

from ..managers.agent_m import AgentManager
from ..managers.llm_m import LLMManager
from ..serializers.document_serializer import DocumentSerializer
from ..utility.consts import TIME_FORMAT
from .summarizer import Summarizer


@dataclass
class Experiment(DocumentSerializer):
    starting_message: str
    llm_m: LLMManager
    agent_m: AgentManager
    note: str
    favourite: bool
    creator: str
    conversations: list[ObjectId] = field(default_factory=list)
    id: ObjectId = field(default_factory=ObjectId)
    creation_date: datetime = field(default_factory=datetime.now)
    summarizer: Summarizer = field(init=False)

    @classmethod
    def from_document(cls, doc: dict) -> "Experiment":
        return cls(
            id=doc["_id"],
            creation_date=doc["creation_date"],
            starting_message=doc["starting_message"],
            llm_m=LLMManager.from_document(doc["llms"]),
            agent_m=AgentManager.from_document(doc["agents"]),
            note=doc["note"],
            favourite=doc["favourite"],
            creator=doc["creator"],
            conversations=doc["conversations"],
        )

    def to_document(self) -> dict:
        return {
            "_id": self.id,
            "creation_date": self.creation_date,
            "starting_message": self.starting_message,
            "llms": self.llm_m.to_document(),
            "agents": self.agent_m.to_document(),
            "note": self.note,
            "favourite": self.favourite,
            "creator": self.creator,
            "conversations": self.conversations,
        }

    def __str__(self) -> str:
        return (
            f"\033[1mID\033[0m: {self.id}\n\n"
            + f"\033[1mCreation date\033[0m: {self.creation_date.strftime(TIME_FORMAT)}\n\n"
            + f"\033[1mStarting message\033[0m: {self.starting_message}\n\n"
            + f"{str(self.llm_m)}\n\n"
            + f"{str(self.agent_m)}\n\n"
            + f"\033[1mNote\033[0m: {self.note}\n\n"
            + f"\033[1mFavourite\033[0m: {self.favourite}\n\n"
            + f"\033[1mCreator\033[0m: {self.creator}\n\n"
            + f"\033[1mNumber of conversations\033[0m: {len(self.conversations)}\n"
        )
