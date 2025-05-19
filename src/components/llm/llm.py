import asyncio
import os
import tempfile
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Mapping

import ollama
from itakello_logging import ItakelloLogging
from tqdm import tqdm

from ...interfaces.mongo_model import MongoModel
from ...utility.consts import MAX_CONTEXT_LEN

logger = ItakelloLogging().get_logger(__name__)


@dataclass
class LLM(MongoModel):
    model: str
    temperature: float = 0.7
    top_k: int = 40
    top_p: float = 0.9
    name: str = field(init=False)
    config: dict = field(init=False)

    def __post_init__(self) -> None:
        self.model = self.model.lower()

        # If this is an OpenAI GPT model, configure for OpenAI API instead of Ollama
        if self.model.startswith("gpt-"):
            # Configure for OpenAI API (e.g., gpt-3.5-turbo) and set instance name
            self.config = {
                "model": self.model,
                "api_key": os.getenv("OPENAI_API_KEY", ""),
                "base_url": os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"),
                "cache_seed": None,
            }
            # Use the model identifier as the name for token-summary lookup and selection
            self.name = self.model
            logger.debug(f"Created an OpenAI LLM instance: {self.model}")
            return

        # Otherwise, treat as an Ollama model
        if ":" not in self.model:
            self.model = f"{self.model}:latest"

        self.create_custom_model()
        self.config = {
            "model": self.model,
            "base_url": "http://localhost:11434/v1",
            "api_key": "ollama",
            "cache_seed": None,
            # Price per 1k tokens: [prompt_price_per_1k, completion_price_per_1k]
            # Local models are free by default
            "price": [0.0, 0.0],
        }
        logger.debug(f"Created a new Ollama LLM instance: {self.model}")

    @classmethod
    def from_document(cls, doc: dict) -> "LLM":
        return cls(
            model=doc["model"],
            temperature=doc["temperature"],
            top_k=doc["top_k"],
            top_p=doc["top_p"],
        )

    def __str__(self) -> str:
        return f"{self.model} (temperature: {self.temperature}, top_k: {self.top_k}, top_p: {self.top_p})"

    def to_document(self) -> dict:
        return {
            "model": self.model,
            "temperature": self.temperature,
            "top_k": self.top_k,
            "top_p": self.top_p,
        }

    async def show_async_progress_tqdm(self, iterator: AsyncIterator) -> None:
        pbar = None
        async for update in iterator:
            # Initialize the progress bar upon receiving the total size
            if "total" in update and pbar is None:
                pbar = tqdm(
                    total=update["total"] / 1e9,
                    bar_format="{l_bar}{bar}| {n:.3f}/{total:.3f} {unit} [elapsed: {elapsed}]",
                    unit="GB",
                    colour="green",
                )
            # Update the progress bar based on the 'completed' bytes
            if pbar is not None and "completed" in update:
                pbar.n = update["completed"] / 1e9
                pbar.refresh()

        if pbar is not None:
            pbar.clear()
            pbar.close()

    async def _download_model(self) -> None:
        iterator = await ollama.AsyncClient().pull(model=self.model, stream=True)
        if isinstance(iterator, Mapping):
            raise TypeError("Error while pulling the model")
        await self.show_async_progress_tqdm(iterator)

    def create_custom_model(self) -> None:
        available_models = ollama.list()["models"]
        if not available_models:
            curr_models = []
        else:
            # The 'model' attribute holds the model name in the Ollama list response
            curr_models = [model["model"] for model in available_models]
        if self.model not in curr_models:
            logger.warning(
                f"Model [{self.model}] does not exist, pulling it. Please wait..."
            )
            asyncio.run(self._download_model())
            logger.confirmation(f"Model [{self.model}] pulled successfully")
        self.name = self._create_name()
        if self.name not in curr_models:
            self._create_vai_modelfile()
            logger.debug(f"Model [{self.name}] created successfully")

    def _create_vai_modelfile(self) -> None:
        modelfile_content = (
            f"FROM {self.model}\n"
            f"PARAMETER temperature {self.temperature}\n"
            f"PARAMETER top_k {self.top_k}\n"
            f"PARAMETER top_p {self.top_p}\n"
            f"PARAMETER num_ctx {MAX_CONTEXT_LEN}\n"
        )
        # Write the Modelfile to a temporary file
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
            tmp.write(modelfile_content)
            tmp_path = tmp.name
        # Upload the Modelfile blob and create a custom model from it
        # Use the same client instance for blob upload and model creation
        client = ollama.Client()
        digest = client.create_blob(tmp_path)
        # Create the custom model from the uploaded Modelfile blob
        client.create(model=self.name, from_=self.model, files={"Modelfile": digest})
        os.remove(tmp_path)

    def _create_name(self) -> str:
        # Replace colons with underscores in the model name
        safe_model_name = self.model.replace(":", "_")
        return f"{safe_model_name}_{self.temperature}_{self.top_k}_{self.top_p}"
