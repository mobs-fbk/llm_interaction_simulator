import logging

from itakello_logging import ItakelloLogging

from .utilities import ConfigHandler
from .utilities.utilities import *

ItakelloLogging(debug=True)

logging.info("hi")

settings = ConfigHandler().get_section("Experiment")

logging.debug(
    "Experiment settings:\n" + "\n".join(f"{k}:{v}" for k, v in settings.items())
)

llm_config = get_config_llm(settings["llm"])

logging.debug("LLM config:\n" + "\n".join(f"{k}:{v}" for k, v in llm_config.items()))

agents = get_prison_agents(
    n_guards=int(settings["n_guards"]),
    n_prisoners=int(settings["n_prisoners"]),
    agents_fields=[w.strip() for w in settings["agents_fields"].split(",")],
    llm_config=llm_config,
)

researcher = get_researcher()

group_chat = get_group_chat(
    agents=agents,
    round_number=int(settings["conversation_rounds"]),
    selection_method=settings["manager_selection_method"],
)

manager = get_manager(group_chat=group_chat, llm_config=llm_config)

summarizer = get_summarizer(
    llm_config=llm_config,
    n_guards=int(settings["n_guards"]),
    n_prisoners=int(settings["n_prisoners"]),
    summarizer_fields=settings["summarizer_fields"],
)

start_message = settings["researcher_initial_message"]

logging.info("Starting the experiment")

for i in range(int(settings["experiment_days"])):
    researcher.initiate_chat(
        recipient=manager, clear_history=True, message=start_message
    )
    conversation = group_chat.messages[1:]  # skip Researcher's message
    summary = summarizer.generate_summary(
        previous_conversation=conversation, round_number=i + 1
    )
    start_message += "\n" + summary
    logging.info(f"Day {i+1} complete")

logging.info("Experiment complete")
