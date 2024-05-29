from dataclasses import dataclass, field

import httpx
import ollama
from itakello_logging import ItakelloLogging

from ...interfaces import BaseManager
from ...core.input_manager import InputManager
from ...utility.custom_os import CustomOS
from .llm import LLM

logger = ItakelloLogging().get_logger(__name__)


@dataclass
class LLMManager(BaseManager):
    input_m: InputManager

    def ask_for_llms(
        self, optional: bool = False, default: str = "mistral, mistral, llama2"
    ) -> list[LLM]:
        logger.instruction(
            instructions=[
                "To find the available LLMs -> https://ollama.com/library",
                "If you want to use the same LLM with different parameters (temperature, top_p and/or top_k) insert it multiple times",
            ]
        )
        while True:
            if CustomOS.getenv("APP_MODE", "") == "development":
                llms_names = CustomOS.getenv("LLMS")
                llms_names = llms_names.split(",")
            else:
                llms_names = self.input_m.input_list(
                    message="Enter the LLMs to use",
                    example="mistral, mistral, llama2",
                    optional=optional,
                    avoid_duplicates=False,
                    default=default,
                )
            try:
                llms = [LLM(model=name) for name in llms_names]
                break
            except httpx.ConnectError:
                logger.error("Ollama is not currently running. Please start it.")
                self.input_m.input_str(
                    "Press Enter when Ollama is running again", optional=True
                )
                continue
            except ollama.ResponseError as e:
                logger.error(e)
        if CustomOS.getenv("APP_MODE", "") == "development":
            set_parameters = CustomOS.getenv("SET_PARAMETERS")
            set_parameters = True if set_parameters == "y" else False
        else:
            set_parameters = self.input_m.confirm(
                "Do you want to set the parameters for the LLMs?"
            )
        if set_parameters:
            for llm in llms:
                self._ask_for_parameters(llm)
        return llms

    def _ask_for_parameters(self, llm: LLM) -> None:
        logger.info(f"Setting parameters for [{llm.model}]")
        llm.temperature = self.input_m.input_float(
            f"Enter temperature (default: {llm.temperature})",
            positive_requirement=True,
            max_value=1,
        )
        llm.top_k = self.input_m.input_int(
            f"Enter top_k (default: {llm.top_k})", positive_requirement=True
        )
        llm.top_p = self.input_m.input_float(
            f"Enter top_p (default: {llm.top_p})",
            positive_requirement=True,
            max_value=1,
        )
        llm.create_custom_model()
