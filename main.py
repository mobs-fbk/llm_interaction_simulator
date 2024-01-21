from src.utilities import *
from classes.context_field import Field
from classes.summarizer import Summarizer

llm_config = get_config_llm("gpt-3.5-turbo-1106")

agents = get_prison_agents(
    n_guards = 1,
    n_prisoners = 1,
    ordered_fields = [
        Field.STARTING_PROMPT,
        Field.GOAL,
        Field.PERSONALITY,
        Field.RISKS,
        Field.RESEARCH_OVERSIGHT,
        Field.COMMUNICATION_RULES,
        Field.ENVIRONMENT,
        Field.STUDY
        ],
    llm_config = llm_config
    )

researcher = get_researcher()

group_chat = get_group_chat(
    agents = agents,
    round_number = 10,
    selection_method = "round_robin" # round_robin OR auto
    )

manager = get_manager(
    group_chat = group_chat,
    llm_config = llm_config
    )

summarizer = Summarizer(
    llm_config = llm_config,
    n_agents = len(agents),
    ordered_fields = [
        Field.STARTING_PROMPT,
        Field.GOAL,
        Field.RULES
        ]
    )

start_message = "Start the experiment"

print("Starting the experiment")

for i in range(5):
    researcher.initiate_chat(
        recipient = manager,
        clear_history=True,
        message = start_message
        )
    conversation = group_chat.messages[1:] # skip Researcher's message
    summary = summarizer.generate_summary(
                                          previous_conversation=conversation,
                                          round_number=i+1)
    start_message += "\n" + summary
    print(f"Day {i+1} complete")

print("Experiment complete")