from dataclasses import InitVar, dataclass, field
import time
import openai
import httpx

from autogen import OpenAIWrapper
from itakello_logging import ItakelloLogging

from ..llm.llm import LLM
from ..section.section import Section

logger = ItakelloLogging().get_logger(__name__)


@dataclass
class Summarizer:
    system_message_dict: dict = field(init=False)
    model: OpenAIWrapper = field(init=False)

    sections: InitVar[list[Section]]
    placeholders: InitVar[dict[str, str]]
    llm: InitVar[LLM]

    def __post_init__(
        self, sections: list[Section], placeholders: dict[str, str], llm: LLM
    ) -> None:
        system_message = self._generate_system_message(sections, placeholders)
        self.system_message_oai = {"content": system_message, "role": "system"}
        self.model = OpenAIWrapper(config_list=[llm.config])
        logger.debug(f"Summarizer created")

    def _generate_system_message(
        self, sections: list[Section], placeholders: dict[str, str]
    ) -> str:
        final_contents = []
        for section in sorted(sections):
            final_content = str(section)
            for placeholder, value in placeholders.items():
                final_content = final_content.replace(placeholder, value)
            final_contents.append(final_content)
        system_message = "\n\n".join(final_contents)
        return system_message

    def generate_summary(self, previous_conversation, round_number: int) -> str:
        """
        Generate a summary with retry logic for transient LLM errors.
        """
        MAX_RETRIES = 3
        attempts = 0
        while True:
            try:
                summary_obj = self.model.create(
                    messages=[self.system_message_oai] + previous_conversation
                )
                break
            except (openai.error.OpenAIError, httpx.HTTPError) as e:
                attempts += 1
                if attempts >= MAX_RETRIES:
                    logger.error(f"Summary generation failed after {attempts} attempts: {e}")
                    raise
                logger.warning(f"Error generating summary (attempt {attempts}/{MAX_RETRIES}): {e}. Retrying...")
                time.sleep(2 ** attempts)
            except Exception as e:
                attempts += 1
                if attempts >= MAX_RETRIES:
                    logger.error(f"Unexpected error generating summary after {attempts} attempts: {e}")
                    raise
                logger.warning(f"Unexpected error generating summary (attempt {attempts}/{MAX_RETRIES}): {e}. Retrying...")
                time.sleep(2 ** attempts)
        summary_text = summary_obj.choices[0].message.content
        summary = f"Day {round_number} summary:\n {summary_text}"
        return summary

    @classmethod
    def _get_name(cls) -> str:
        return "Summarizer"
