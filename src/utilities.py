import autogen

from .custom_manager import CustomGroupChatManager
from .prompts_generator import get_guard_SM, get_prisoner_SM

def create_conversable_agent(name:str, llm_config:dict, system_message:str):
    return autogen.ConversableAgent(
        name = name,
        llm_config = llm_config,
        system_message = system_message,
        human_input_mode = "NEVER",
        code_execution_config = False
    )
    
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

def get_experiment_agents(llm_config:dict):
    prisoner = create_conversable_agent(
        name = "prisoner",
        llm_config = llm_config,
        system_message = get_prisoner_SM()
        )
    prisoner_2 = create_conversable_agent(
        name = "prisoner-2",
        llm_config = llm_config,
        system_message = get_prisoner_SM()
        )
    guard = create_conversable_agent(
        name = "guard",
        llm_config = llm_config,
        system_message = get_guard_SM()
        )
    guard_2 = create_conversable_agent(
        name = "guard-2",
        llm_config = llm_config,
        system_message = get_guard_SM()
        )
    researcher = autogen.UserProxyAgent(
        name="Researcher",
        human_input_mode="TERMINATE",
    )
    return prisoner, guard, prisoner_2, guard_2, researcher
    
def get_group_chat(agents:list[autogen.ConversableAgent], round_number:int):
    group_chat = autogen.GroupChat(
        agents = agents,
        messages=[], # no messages to start
        speaker_selection_method = "round_robin",
        allow_repeat_speaker = False,
        max_round = round_number
        )
    return group_chat

def get_manager(group_chat:autogen.GroupChat, llm_config:dict):
    manager = CustomGroupChatManager(
        groupchat = group_chat,
        llm_config = llm_config,
        )
    return manager