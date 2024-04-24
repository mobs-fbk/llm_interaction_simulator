import logging
from dataclasses import dataclass, field

from ..classes.section import Section

logger = logging.getLogger(__name__)


@dataclass
class SummarizerManager:
    sections: dict[str, Section] = field(default_factory=dict)

    def initialize_sections(self, titles: list[str]) -> None:
        self.sections["starting_prompt"] = Section(index=0, title="", content="")
        for i, title in enumerate(titles):
            self.sections[title] = Section(index=i + 1, title=title, content="")
        logger.debug(f"Added {len(titles)} new empty sections")
