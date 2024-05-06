from dataclasses import dataclass, field
from datetime import datetime

from bson.objectid import ObjectId
from itakello_logging import ItakelloLogging

from ...abstracts.mongo_model import MongoModel
from ...utility.consts import TIME_FORMAT
from ..conversation.chat import Chat
from ..conversation.manager import Manager
from ..conversation.researcher import Researcher
from ..experiment.experiment import Experiment
from ..llm.llm import LLM
from ..section.section import Section
from .agent import CustomAgent
from .message import Message
from .summarizer import Summarizer

logger = ItakelloLogging().get_logger(__name__)


@dataclass
class Conversation(MongoModel):
    n_messages: int
    days: int
    speaker_selection_method: str
    starting_message: str
    llm: LLM
    agent_combination: list[tuple[str, int]]
    creator: str
    favourite: bool = False
    id: ObjectId = field(default_factory=ObjectId)
    creation_date: datetime = field(default_factory=datetime.now)
    messages_ids: list[ObjectId] = field(default_factory=list)

    def __post_init__(self) -> None:
        logger.debug(f"Created a new Conversation:\n{self}")

    def __str__(self) -> str:
        output = (
            f"- ID: {self.id}\n"
            + f"- creation time: {self.creation_date.strftime(TIME_FORMAT)}\n"
            + f"- speaker selection method: {self.speaker_selection_method}\n"
            + f"- starting message: {self.starting_message}\n"
            + f"- creator: {self.creator}\n"
            + f"- favourite: {self.favourite}\n"
            + f"- messages: {self.messages_ids}\n"
        )
        return output

    def generate_agents(
        self,
        experiment: Experiment,
        placeholders: dict[str, str],
        llm: LLM,
    ) -> list[CustomAgent]:
        agents = []
        full_roles = [f"{role.capitalize()}:" for role, _ in self.agent_combination]
        for role, num in self.agent_combination:
            for _ in range(num):
                agents.append(
                    CustomAgent(
                        role=role,
                        full_roles=full_roles,
                        placeholders=placeholders,
                        sections=list(experiment.shared_sections.values())
                        + list(experiment.roles[role].sections.values()),
                        llm=llm,
                    )
                )
        return agents

    def perform(
        self, agents: list[CustomAgent], summarizer: Summarizer, llm_manager: LLM
    ) -> list[Message]:
        start_message = self.starting_message
        researcher = Researcher()
        group_chat = Chat(
            agents=agents,
            selection_method=self.speaker_selection_method,
            round_number=self.n_messages // self.days,
        )
        manager = Manager(groupchat=group_chat, llm_config=llm_manager.config)
        messages = []
        for i in range(int(self.days)):
            researcher.initiate_chat(
                recipient=manager, clear_history=True, message=start_message
            )
            raw_conversation = group_chat.messages
            summary = summarizer.generate_summary(
                previous_conversation=raw_conversation[1:], round_number=i + 1
            )
            start_message += "\n" + summary
            new_messages = self.add_daily_conversation(raw_conversation, day=i + 1)
            messages.extend(new_messages)
        self.messages_ids = [message.id for message in messages]
        logger.confirmation("Conversation complete")
        return messages

    def to_selection(self) -> str:
        agent_combinations = ", ".join(
            f"{role.capitalize()}:{num}" for role, num in self.agent_combination
        )
        selection = (
            f"Number of messages: {self.n_messages}\t"
            + f"Creator: {self.creator}  [{self.creation_date.strftime(TIME_FORMAT)}]\t"
            + f"Speaker selection method: {self.speaker_selection_method}\t"
            + f"Days: {self.days}\t"
            + f"LLM: {self.llm}\t"
            + f"Agent combination: {agent_combinations}\t"
        )
        if self.favourite:
            selection += " ⭐"
        return selection

    def to_content(self) -> str:
        output = (
            f"\033[1mID\033[0m: {self.id}\n\n"
            + f"\033[1mCreation time\033[0m: {self.creation_date.strftime(TIME_FORMAT)}\n\n"
            + f"\033[1mSpeaker selection method\033[0m: {self.speaker_selection_method}\n\n"
            + f"\033[1mStarting message\033[0m: {self.starting_message}\n\n"
            + f"\033[1mCreator\033[0m: {self.creator}\n\n"
            + f"\033[1mFavourite\033[0m: {self.favourite}\n\n"
            + f"\033[1mNum messages\033[0m: {len(self.messages_ids)}\n\n"
        )
        return output

    def add_daily_conversation(
        self, raw_conversation: list[dict], day: int
    ) -> list[Message]:
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
        return messages

    @classmethod
    def from_document(cls, doc: dict) -> "Conversation":
        return cls(
            id=doc["_id"],
            n_messages=doc["n_messages"],
            days=doc["days"],
            speaker_selection_method=doc["speaker_selection_method"],
            starting_message=doc["starting_message"],
            llm=LLM.from_document(doc["llm"]),
            agent_combination=doc["agent_combination"],
            creator=doc["creator"],
            favourite=doc["favourite"],
            creation_date=doc["creation_date"],
            messages_ids=doc["messages_ids"],
        )

    def to_document(self) -> dict:
        return {
            "_id": self.id,
            "n_messages": self.n_messages,
            "days": self.days,
            "speaker_selection_method": self.speaker_selection_method,
            "starting_message": self.starting_message,
            "llm": self.llm.to_document(),
            "agent_combination": self.agent_combination,
            "creator": self.creator,
            "favourite": self.favourite,
            "creation_date": self.creation_date,
            "messages_ids": self.messages_ids,
        }
