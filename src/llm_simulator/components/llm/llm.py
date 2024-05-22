import asyncio
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
        if ":" not in self.model:
            self.model = f"{self.model}:latest"
        self.create_custom_model()
        self.config = {
            "model": self.name,
            "base_url": "http://localhost:11434/v1",
            "api_key": "ollama",
            "cache_seed": None,
        }
        logger.debug(f"Created a new LLM instance: {self.model}")

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
            curr_models = [model["name"] for model in available_models]
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
        modelfile = (
            f"FROM {self.model}\n"
            + f"PARAMETER temperature {self.temperature}\n"
            + f"PARAMETER top_k {self.top_k}\n"
            + f"PARAMETER top_p {self.top_p}\n"
            + f"PARAMETER num_ctx {MAX_CONTEXT_LEN}\n"
        )
        ollama.create(model=self.name, modelfile=modelfile)

    def _create_name(self) -> str:
        return f"{self.model}_{self.temperature}_{self.top_k}_{self.top_p}"
