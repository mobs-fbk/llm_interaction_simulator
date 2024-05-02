from dataclasses import dataclass, field
from datetime import datetime

from bson.objectid import ObjectId
from itakello_logging import ItakelloLogging

from ...components.agent import Agent
from ...components.chat import Chat
from ...components.manager import Manager
from ...components.message import Message
from ...components.researcher import Researcher
from ...utility.document_serializer import DocumentSerializer
from ..agent.agent_manager import AgentManager
from ..llm.llm import LLM

logger = ItakelloLogging.get_logger(__name__)


@dataclass
class Conversation(DocumentSerializer):
    n_messages: int
    days: int
    speaker_selection_method: str
    starting_message: str
    llm: LLM
    agent_combination: list[tuple[str, int]]
    creator: str
    note: str = ""
    favourite: bool = False
    agents: list[Agent] = field(init=False, default_factory=list)
    id: ObjectId = field(default_factory=ObjectId)
    creation_date: datetime = field(default_factory=datetime.now)
    messages_ids: list[ObjectId] = field(default_factory=list)

    def __post_init__(self) -> None:
        logger.debug(f"[{self.creator}] created a new conversation: {self.id}")

    def populate_agents(self, agent_m: AgentManager) -> None:
        self.agents = []
        placeholders = agent_m.compose_placeholders(self.agent_combination)
        for role, num in self.agent_combination:
            for _ in range(num):
                self.agents.append(
                    Agent(
                        role=role,
                        placeholders=placeholders,
                        sections=list(agent_m.shared_sections.values())
                        + list(agent_m.roles[role].sections.values()),
                    )
                )

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
            # llm=LLM.from_document(doc["llm"]),
            creator=doc["creator"],
            note=doc["note"],
            favourite=doc["favourite"],
            creation_date=doc["creation_date"],
            messages_ids=doc["messages_ids"],
        )

    def to_document(self) -> dict:
        return {
            "_id": self.id,
            "conversation_days": self.n_messages,
            "conversation_rounds": self.total_days,
            "speaker_selection_method": self.speaker_selection_method,
            "starting_message": self.starting_message,
            # "llm": self.llm.to_document(),
            "creator": self.creator,
            "note": self.note,
            "favourite": self.favourite,
            "creation_date": self.creation_date,
            "messages_ids": self.messages_ids,
        }
