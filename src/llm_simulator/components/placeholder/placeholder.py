from dataclasses import dataclass, field

import inflect
import nltk
from itakello_logging import ItakelloLogging
from nltk import pos_tag

from ...abstracts.mongo_model import MongoModel
from ...utility.enums import PlaceholderType

nltk.download("averaged_perceptron_tagger", quiet=True)

logger = ItakelloLogging().get_logger(__name__)


@dataclass
class Placeholder(MongoModel):
    tag: str
    role: str = field(init=False)
    type: PlaceholderType = field(init=False)
    verb: str = field(init=False)
    p: inflect.engine = field(default=inflect.engine(), init=False)

    def __post_init__(self) -> None:
        tag_parts = self.tag[1:-1].split("_")
        self.role = tag_parts[0].lower()
        self.type = PlaceholderType[tag_parts[1]]
        if self.type == PlaceholderType.VERB:
            if len(tag_parts) != 3:
                raise ValueError(f"Verb placeholder [{self.tag}] is missing a verb")
            self.verb = tag_parts[2]
        logger.debug(f"Created new placeholder: {self.tag}")

    def __str__(self) -> str:
        output = f"{self.tag}: "
        if self.type == PlaceholderType.NUM:
            output += f"{self.to_value(1)}, {self.to_value(2)}, {self.to_value(3)}, ..."
        else:
            output += f"{self.to_value(1)} ({self.to_value(2)})"
        return output

    def to_document(self) -> str:
        return self.tag

    @classmethod
    def from_document(cls, doc: str) -> "Placeholder":
        return cls(
            tag=doc,
        )

    def to_value(self, agent_number: int) -> str:
        singular = agent_number == 1
        if self.type == PlaceholderType.NUM:
            return str(agent_number)
        elif self.type == PlaceholderType.NOUN:
            if singular:
                return self.role
            return self.p.plural(self.role)  # type: ignore
        elif self.type == PlaceholderType.PRON:
            if singular:
                return "he/she"
            return "they"
        elif self.type == PlaceholderType.POSS:
            possessive = self.role
            if not singular:
                possessive = self.p.plural(possessive)  # type: ignore
            if possessive.endswith("s"):
                possessive += "'"
            else:
                possessive += "'s"
            return possessive
        elif self.type == PlaceholderType.POSSPRON:
            if singular:
                return "his/her"
            return "their"
        elif self.type == PlaceholderType.VERB:
            if singular:
                return self.verb
            return self.p.plural(self.verb)  # type: ignore
        else:
            raise NotImplementedError(f"Placeholder type {self.type} not implemented")

    @classmethod
    def is_verb(cls, verb: str) -> bool:
        full_sentence = f"I {verb} today"
        verb_tag = pos_tag(full_sentence.split())[1][1]
        if not verb_tag.startswith("VB"):
            logger.error(f"The verb [{verb}] is not a valid verb tag: {verb_tag}")
            return False
        if verb_tag == "VBZ":
            logger.error(f"The verb [{verb}] is an invalid third person verb")
            return False
        return True
