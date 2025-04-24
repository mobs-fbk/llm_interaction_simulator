import random
import string
from dataclasses import InitVar, dataclass
from typing import Any, Dict, List, Optional, Union
import time
import openai
import httpx
import ollama

from autogen import ConversableAgent
from autogen.agentchat.agent import Agent
from itakello_logging import ItakelloLogging

from ..llm.llm import LLM
from ..section.section import Section

logger = ItakelloLogging().get_logger(__name__)


@dataclass
class CustomAgent(ConversableAgent):
    role: str
    # full_roles: list[str]
    llm: LLM

    placeholders: InitVar[dict[str, str]]
    sections: InitVar[list[Section]]

    def __post_init__(
        self, placeholders: dict[str, str], sections: list[Section]
    ) -> None:
        name = self.role.capitalize() + "_" + self._get_random_numeric_string()
        system_message = self._generate_system_message(sections, placeholders)
        super().__init__(
            name=name,
            llm_config=self.llm.config,
            system_message=system_message,
            human_input_mode="NEVER",
            code_execution_config=False,
            # description=f"A {self.role} named {name}",
        )

    def _generate_system_message(
        self, sections: list[Section], placeholders: dict[str, str]
    ) -> str:
        final_contents = []
        for section in sorted(sections):
            final_content = str(section)
            for placeholder, value in placeholders.items():
                final_content = final_content.replace(placeholder, value)
            final_contents.append(final_content)
        system_message = "\n".join(final_contents)
        return system_message

    def _get_random_numeric_string(self, lenght: int = 3) -> str:
        return "".join(random.choices(string.digits, k=lenght))

    def generate_reply(
        self,
        messages: Optional[List[Dict[str, Any]]] = None,
        sender: Optional[Union["Agent", None]] = None,
        **kwargs: Any,
    ) -> Union[str, Dict, None]:
        """
        Generate a reply with retry logic for transient LLM errors.
        """
        MAX_RETRIES = 3
        attempts = 0
        while True:
            try:
                reply = super().generate_reply(messages=messages, sender=sender, **kwargs)
                break
            except (openai.error.OpenAIError, httpx.HTTPError, ollama.ResponseError) as e:
                attempts += 1
                if attempts >= MAX_RETRIES:
                    logger.error(f"LLM generation failed after {attempts} attempts: {e}")
                    raise
                logger.warning(f"Error generating reply (attempt {attempts}/{MAX_RETRIES}): {e}. Retrying...")
                time.sleep(2 ** attempts)
            except Exception as e:
                attempts += 1
                if attempts >= MAX_RETRIES:
                    logger.error(f"Unexpected error generating reply after {attempts} attempts: {e}")
                    raise
                logger.warning(f"Unexpected error generating reply (attempt {attempts}/{MAX_RETRIES}): {e}. Retrying...")
                time.sleep(2 ** attempts)
        # Log token usage if available
        logger.debug(str(self.client.total_usage_summary))  # type: ignore
        # Clean up reply text
        reply = str(reply).strip()
        return reply

    def send(
        self,
        message: Union[Dict, str],
        recipient: Agent,
        request_reply: Optional[bool] = None,
        silent: Optional[bool] = False,
    ) -> None:
        super().send(message, recipient, request_reply, silent)
        token_summary = self.client.total_usage_summary  # type: ignore
        if token_summary:
            # Determine token-usage key. Start with the configured model identifier
            model_key = self.llm.model
            # If exact key not found, try to match any summary key that starts with the model id
            if model_key not in token_summary:
                for key in token_summary:
                    if key.startswith(f"{self.llm.model}"):
                        model_key = key
                        break
            # Next, fallback to custom model name
            if model_key not in token_summary and getattr(self.llm, "name", None) in token_summary:
                model_key = self.llm.name
            # If still not found, log a warning and skip
            if model_key not in token_summary:
                available = list(token_summary.keys())
                logger.warning(
                    f"Token usage summary keys {available} do not include model '{self.llm.model}' or name '{getattr(self.llm, 'name', None)}'"
                )
                return
            usage = token_summary[model_key]
            logger.info(
                f"Previous tokens: {usage.get('prompt_tokens')} | New tokens: {usage.get('completion_tokens')} | Total tokens: {usage.get('total_tokens')}"
            )

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other) -> bool:
        return isinstance(other, Agent) and self.name == other.name
