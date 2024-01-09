import autogen


def create_conversable_agent(name:str, llm_config:dict, system_message:str):
    return autogen.ConversableAgent(
        name = name,
        llm_config = llm_config,
        system_message = system_message,
        human_input_mode = "NEVER",
        code_execution_config = False
    )