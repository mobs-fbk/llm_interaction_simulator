import autogen
from classes.guard import Guard
from classes.prisoner import Prisoner

def get_config_llm(model:str):
    config_list = autogen.config_list_from_json(
        env_or_file = "OAI_CONFIG_LIST",
        filter_dict = {"model":model}
        )
    llm_config = {
        "config_list": config_list, 
        "cache_seed": None # set to None to disable caching and have a new conversation every time
        }
    return llm_config

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

def get_researcher():
    researcher = autogen.UserProxyAgent(
        name="Researcher",
        human_input_mode="TERMINATE",
    )
    return researcher
    
def get_group_chat(agents:list[autogen.ConversableAgent], selection_method:str = "auto", round_number:int = 10):
    group_chat = autogen.GroupChat(
        agents = agents,
        messages=[], # no messages to start
        speaker_selection_method = selection_method,
        allow_repeat_speaker = False,
        max_round = round_number
        )
    return group_chat

def get_manager(group_chat:autogen.GroupChat, llm_config:dict):
    manager = autogen.GroupChatManager(
        groupchat = group_chat,
        llm_config = llm_config,
        )
    return manager