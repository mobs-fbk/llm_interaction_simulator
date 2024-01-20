from re import S
from src.utilities import *

llm_config = get_config_llm("llmlite_model") # llmlite_model OR gpt-3.5-turbo-1106

prisoner, guard, prisoner_2, guard_2, researcher = get_experiment_agents(llm_config)

group_chat = get_group_chat(
    agents = [guard, prisoner],
    round_number = 6
    )

manager = get_manager(
    group_chat = group_chat,
    llm_config = llm_config
    )

start_message = "Start the experiment"

print("Starting the experiment")

for i in range(10):
    # Initiate conversation
    researcher.initiate_chat(
        recipient = manager,
        clear_history=True,
        message = start_message
        )
    # Make the summary
    summary = manager.generate_summary(i+1)
    start_message += "\n" + summary
    print(f"Day {i+1} complete")

print("Experiment complete")