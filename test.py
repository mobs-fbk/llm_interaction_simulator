from classes.guard import Guard
from classes.prisoner import Prisoner
from src.utilities import *
from classes.context_field import Field

llm_config = get_config_llm("gpt-3.5-turbo-1106") # llmlite_model OR gpt-3.5-turbo-1106

def get_prison_agents(n_guards: int, n_prisoners: int, ordered_fields: list[str], llm_config: dict):
    agents = []
    n_agents = n_guards + n_prisoners
    for i in range(n_guards):
        agents.append(Guard(
            llm_config = llm_config,
            ordered_fields = ordered_fields,
            multiple_opponents = n_prisoners > 1,
            n_agents = n_agents
        ))
    for i in range(n_prisoners):
        agents.append(Prisoner(
            llm_config = llm_config,
            ordered_fields = ordered_fields,
            multiple_opponents = n_guards > 1,
            n_agents = n_agents
        ))
    return agents



print(agents)