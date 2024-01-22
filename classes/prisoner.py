from .agent import Agent
from dataclasses import dataclass
from src.config_handler import ConfigHandler

@dataclass
class Prisoner(Agent):
    
    def __init__(self, llm_config: dict, n_guards: int, n_prisoners: int, agent_fields: list[str] = []):
        name = self._get_name()
        context = ConfigHandler().get_section("Prisoner")
        super().__init__(
            llm_config = llm_config,
            n_guards = n_guards,
            n_prisoners = n_prisoners,
            agent_fields = agent_fields,
            context = context,
            id = name
        )
        
    def __hash__(self) -> int:
        return super().__hash__()

    def _get_name(self):
        prefix = "Prisoner_P-"
        random_string = self._get_random_numeric_string()
        return prefix + random_string