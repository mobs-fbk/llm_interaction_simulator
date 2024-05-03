from dataclasses import InitVar, dataclass, field
from datetime import datetime

from bson.objectid import ObjectId
from itakello_logging import ItakelloLogging

from ...abstracts.mongo_model import MongoModel
from ...utility.consts import TIME_FORMAT
from ..conversation.agent import Agent
from ..conversation.conversation import Conversation
from ..llm.llm import LLM
from ..placeholder.placeholder import Placeholder
from ..role.role import Role
from ..section.section import Section

logger = ItakelloLogging().get_logger(__name__)


@dataclass
class Experiment(MongoModel):
    starting_message: str
    note: str
    favourite: bool
    creator: str

    llms: dict[str, LLM] = field(init=False)
    roles: dict[str, Role] = field(init=False)
    shared_sections: dict[str, Section] = field(init=False)
    summarizer_sections: dict[str, Section] = field(init=False)
    placeholders: dict[str, Placeholder] = field(init=False)

    llms_list: InitVar[list[LLM]]
    roles_list: InitVar[list[Role]]
    shared_sections_list: InitVar[list[Section]]
    summarizer_sections_list: InitVar[list[Section]]
    placeholders_list: InitVar[list[Placeholder]] = field(default=[])

    conversation_ids: list[ObjectId] = field(default_factory=list)
    id: ObjectId = field(default_factory=ObjectId)
    creation_date: datetime = field(default_factory=datetime.now)

    def __post_init__(
        self,
        llms_list: list[LLM],
        roles_list: list[Role],
        shared_sections_list: list[Section],
        summarizer_sections_list: list[Section],
        placeholders_list: list[Placeholder],
    ) -> None:
        self.llms = {llm.name: llm for llm in llms_list}
        self.roles = {role.name: role for role in roles_list}
        self.shared_sections = {
            section.title: section for section in shared_sections_list
        }
        self.summarizer_sections = {
            section.title: section for section in summarizer_sections_list
        }
        if not placeholders_list:
            placeholders_list = self._create_starting_placeholders()
        self.placeholders = {
            placeholder.tag: placeholder for placeholder in placeholders_list
        }
        logger.debug(
            "Created new experiment with:\n"
            + f"- {len(self.roles)} roles\n"
            + f"- {len(self.llms)} LLMs\n"
            + f"- {len(self.shared_sections)} shared sections\n"
            + f"- {len(self.summarizer_sections)} summarizer sections\n"
            + f"- {len(self.placeholders)} placeholders\n"
        )

    def _create_starting_placeholders(self) -> list[Placeholder]:
        return [
            Placeholder(tag=f"<AGENTS_NUM>"),
            Placeholder(tag=f"<ROLES_NUM>"),
        ]

    @classmethod
    def from_document(cls, doc: dict) -> "Experiment":
        return cls(
            starting_message=doc["starting_message"],
            llms_list=[LLM.from_document(llm) for llm in doc["llms"]],
            roles_list=[Role.from_document(role) for role in doc["roles"]],
            shared_sections_list=[
                Section.from_document(section) for section in doc["shared_sections"]
            ],
            summarizer_sections_list=[
                Section.from_document(section) for section in doc["summarizer_sections"]
            ],
            placeholders_list=[
                Placeholder.from_document(placeholder)
                for placeholder in doc["placeholders"]
            ],
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
            "llms": [llm.to_document() for llm in self.llms.values()],
            "roles": [role.to_document() for role in self.roles.values()],
            "shared_sections": [
                section.to_document() for section in self.shared_sections.values()
            ],
            "summarizer_sections": [
                section.to_document() for section in self.summarizer_sections.values()
            ],
            "placeholders": [
                placeholder.to_document() for placeholder in self.placeholders.values()
            ],
            "note": self.note,
            "favourite": self.favourite,
            "creator": self.creator,
            "conversation_ids": self.conversation_ids,
            "creation_date": self.creation_date,
        }

    def to_selection(self) -> str:
        selection = f"{self.id}\tNumber of conversations: {len(self.conversation_ids)}\tCreator: {self.creator} [{self.creation_date.strftime(TIME_FORMAT)}]"
        if self.favourite:
            selection += " ⭐"
        if self.note:
            selection += f"\tNote: {self.note}"
        return selection

    def __str__(self) -> str:
        llms = "\n- ".join(str(llm) for llm in self.llms.values())
        roles = "\n".join(str(role) for role in self.roles.values())
        shared_sections = "\n".join(
            str(section) for section in self.shared_sections.values()
        )
        summarizer_sections = "\n".join(
            str(section) for section in self.summarizer_sections.values()
        )
        placeholders = "\n- ".join(
            str(placeholder) for placeholder in self.placeholders.values()
        )
        return (
            f"\033[1mID\033[0m: {self.id}\n\n"
            + f"\033[1mStarting message\033[0m: {self.starting_message}\n\n"
            + f"\033[1mLLMs\033[0m:\n- {llms}\n\n"
            + f"\033[1mRoles\033[0m:\n{roles}\n\n"
            + f"\033[1mShared sections\033[0m:\n-----\n{shared_sections}-----\n\n"
            + f"\033[1mSummarizer sections\033[0m:\n-----\n{summarizer_sections}-----\n\n"
            + f"\033[1mPlaceholders\033[0m:\n- {placeholders}\n\n"
            + f"\033[1mNote\033[0m: {self.note}\n\n"
            + f"\033[1mFavourite\033[0m: {self.favourite}\n\n"
            + f"\033[1mCreator\033[0m: {self.creator}\n\n"
            + f"\033[1mNumber of conversations\033[0m: {len(self.conversation_ids)}\n"
            + f"\033[1mCreation date\033[0m: {self.creation_date.strftime(TIME_FORMAT)}\n\n"
        )

    def duplicate(self, creator: str) -> "Experiment":
        return Experiment(
            starting_message=self.starting_message,
            note=self.note,
            favourite=self.favourite,
            creator=creator,
            llms_list=[llm for llm in self.llms.values()],
            roles_list=[role for role in self.roles.values()],
            shared_sections_list=[section for section in self.shared_sections.values()],
            summarizer_sections_list=[
                section for section in self.summarizer_sections.values()
            ],
            placeholders_list=[
                placeholder for placeholder in self.placeholders.values()
            ],
        )
