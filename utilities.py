from autogen import ConversableAgent
from autogen.agentchat.contrib.compressible_agent import CompressibleAgent


def create_conversable_agent(name:str, llm_config:dict, system_message:str):
    return CompressibleAgent(
        name = name,
        llm_config = llm_config,
        system_message = system_message,
        human_input_mode = "NEVER",
        code_execution_config = False
    )