import os

import autogen

from prompts_generator import get_guard_SM, get_prisoner_SM
from utilities import *

openai_api_key = os.environ.get("OPENAI_API_KEY")

config_list = autogen.config_list_from_json(
    env_or_file = "OAI_CONFIG_LIST",
    filter_dict= {"model":"gpt-3.5-turbo-1106"}
    )
llm_config = {"config_list": config_list, "cache_seed": None}

prisoner = create_conversable_agent("prisoner", llm_config, get_prisoner_SM())
guard = create_conversable_agent("guard", llm_config, get_guard_SM())

researcher = autogen.UserProxyAgent(
    name="Researcher",
    human_input_mode="TERMINATE",
)

group_chat = autogen.GroupChat(
    agents = [guard, prisoner],
    messages=[], # no messages to start
    speaker_selection_method = "round_robin",
    allow_repeat_speaker = False,
    max_round=12
    )

manager = autogen.GroupChatManager(
    groupchat = group_chat,
    llm_config = llm_config,
    )

researcher.initiate_chat(
    recipient = manager,
    clear_history=True,
    message = "Start the experiment"
    )