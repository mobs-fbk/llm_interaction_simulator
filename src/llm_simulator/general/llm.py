from dataclasses import dataclass, field

import ollama
from itakello_logging import ItakelloLogging

from ..managers.input_m import InputManager
from ..serializers.document_serializer import DocumentSerializer

logger = ItakelloLogging().get_logger(__name__)


@dataclass
class LLM(DocumentSerializer):
    model: str
    temperature: float = 0.7
    top_k: int = 40
    top_p: float = 0.9
    name: str = field(init=False)
    config: dict = field(init=False)
    input_m: InputManager = field(default_factory=InputManager)

    def __post_init__(self) -> None:
        self.model = self.model.lower()
        if ":" not in self.model:
            self.model = f"{self.model}:latest"
        self.create_custom_model()
        self.config = {
            "model": self.name,
            "base_url": "http://localhost:11434/v1",
            "api_key": "ollama",
        }
        logger.debug(f"Created a new LLM instance: {self.model}")

    def set_parameters(self) -> None:
        logger.info(f"Setting parameters for [{self.model}]")
        self.temperature = self.input_m.input_float(
            f"Enter temperature (default: {self.temperature})",
            positive_requirement=True,
            max_value=1,
        )
        self.top_k = self.input_m.input_int(
            f"Enter top_k (default: {self.top_k})", positive_requirement=True
        )
        self.top_p = self.input_m.input_float(
            f"Enter top_p (default: {self.top_p})",
            positive_requirement=True,
            max_value=1,
        )
        self.create_custom_model()

    def create_custom_model(self) -> None:
        curr_models = [model["name"] for model in ollama.list()["models"]]
        if self.model not in curr_models:
            logger.warning(
                f"Model [{self.model}] does not exist, pulling it. Please wait..."
            )
            ollama.pull(model=self.model)
            logger.confirmation(f"Model [{self.model}] pulled successfully")
        self.name = self._create_name()
        if self.name not in curr_models:
            modelfile = (
                f"FROM {self.model}\n"
                + f"PARAMETER temperature {self.temperature}\n"
                + f"PARAMETER top_k {self.top_k}\n"
                + f"PARAMETER top_p {self.top_p}"
            )
            ollama.create(model=self.name, modelfile=modelfile)
            logger.debug(f"Model [{self.name}] created successfully")

    def to_document(self) -> dict:
        return {
            "model": self.model,
            "temperature": self.temperature,
            "top_k": self.top_k,
            "top_p": self.top_p,
        }

    def _create_name(self) -> str:
        return f"{self.model}_{self.temperature}_{self.top_k}_{self.top_p}"

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
