from dataclasses import dataclass, field
from datetime import datetime

from bson.objectid import ObjectId
from itakello_logging import ItakelloLogging

from ..conversations.agent import Agent
from ..conversations.chat import Chat
from ..conversations.conversation import Conversation
from ..conversations.manager import Manager
from ..conversations.researcher import Researcher
from ..managers.agent_m import AgentManager
from ..managers.llm_m import LLMManager
from ..serializers.document_serializer import DocumentSerializer
from ..utility.consts import TIME_FORMAT

logger = ItakelloLogging.get_logger(__name__)


@dataclass
class Experiment(DocumentSerializer):
    starting_message: str
    llm_m: LLMManager
    agent_m: AgentManager
    note: str
    favourite: bool
    creator: str
    conversation_ids: list[ObjectId] = field(default_factory=list)
    id: ObjectId = field(default_factory=ObjectId)
    creation_date: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        logger.debug(f"[{self.creator}] created a new experiment: {self.id}")

    @classmethod
    def from_document(cls, doc: dict) -> "Experiment":
        return cls(
            starting_message=doc["starting_message"],
            llm_m=LLMManager.from_document(doc["llms"]),
            agent_m=AgentManager.from_document(doc["agents"]),
            note=doc["note"],
            favourite=doc["favourite"],
            creator=doc["creator"],
            conversation_ids=doc["conversation_ids"],
            id=doc["_id"],
            creation_date=doc["creation_date"],
        )

    def to_document(self) -> dict:
        return {
            "_id": self.id,
            "starting_message": self.starting_message,
            "llms": self.llm_m.to_document(),
            "agents": self.agent_m.to_document(),
            "note": self.note,
            "favourite": self.favourite,
            "creator": self.creator,
            "conversation_ids": self.conversation_ids,
            "creation_date": self.creation_date,
        }

    def __str__(self) -> str:
        return (
            f"\033[1mID\033[0m: {self.id}\n\n"
            + f"\033[1mStarting message\033[0m: {self.starting_message}\n\n"
            + f"\033[1mLLMs\033[0m:\n{str(self.llm_m)}\n\n"
            + f"\033[1mRoles\033[0m:\n{str(self.agent_m)}\n\n"
            + f"\033[1mNote\033[0m: {self.note}\n\n"
            + f"\033[1mFavourite\033[0m: {self.favourite}\n\n"
            + f"\033[1mCreator\033[0m: {self.creator}\n\n"
            + f"\033[1mNumber of conversations\033[0m: {len(self.conversation_ids)}\n"
            + f"\033[1mCreation date\033[0m: {self.creation_date.strftime(TIME_FORMAT)}\n\n"
        )

    def duplicate(self, creator: str) -> "Experiment":
        return Experiment(
            starting_message=self.starting_message,
            llm_m=self.llm_m,
            agent_m=self.agent_m,
            note=self.note,
            favourite=self.favourite,
            creator=creator,
        )

    def perform(self, conversation: Conversation, agents: list[Agent]) -> Conversation:
        # agents = []
        # for role in self.agent_m.roles.values():
        #    #role_num = self.input_m.

        # researcher = Researcher()
        # chat = Chat(
        #    agents=agents,
        #    selection_method=conversation.speaker_selection_method,
        #    round_number=conversation.conversation_rounds,
        # )
        # manager = Manager(groupchat=chat, llm_config=llm_config)
        return Conversation()
