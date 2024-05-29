from enum import Enum


class PlaceholderType(Enum):
    NUM = "NUM"
    NOUN = "NOUN"
    VERB = "VERB"
    POSS = "POSS"
    POSSPRON = "POSSPRON"
    PRON = "PRON"


class SectionType(Enum):
    ROLES = "Roles"
    PRIVATE = "Private"
    SHARED = "Shared"
    SUMMARIZER = "Summarizer"

    def __lt__(self, other) -> bool:
        if self.__class__ is other.__class__:
            members = list(self.__class__)
            return members.index(self) < members.index(other)
        return NotImplemented

    def __gt__(self, other) -> bool:
        if self.__class__ is other.__class__:
            members = list(self.__class__)
            return members.index(self) > members.index(other)
        return NotImplemented
