from dotenv import load_dotenv
from itakello_logging import ItakelloLogging

from llm_simulator.core.action_manager import ActionManager
from llm_simulator.core.database_manager import DatabaseManager
from llm_simulator.core.input_manager import InputManager
from llm_simulator.managers.agent.agent_manager import AgentManager
from llm_simulator.managers.conversation.conversation_manager import ConversationManager
from llm_simulator.managers.experiment.experiment_manager import ExperimentManager
from llm_simulator.managers.llm.llm_manager import LLMManager

load_dotenv()

ItakelloLogging(
    debug=True,
    excluded_modules=[
        "docker.utils.config",
        "docker.auth",
        "httpx",
        "httpcore.connection",
        "httpcore.http11",
        "autogen.io.base",
        "asyncio",
        "openai._base_client",  # Remove to see API requests debug logs
    ],
)

logger = ItakelloLogging().get_logger(__name__)


def main() -> None:
    input_m = InputManager()
    db_m = DatabaseManager(input_m=input_m)
    actions_m = ActionManager(input_m=input_m)
    # agent_m = AgentManager(input_m=input_m)
    llm_m = LLMManager(input_m=input_m)
    experiment_m = ExperimentManager(input_m=input_m, db_m=db_m)
    conversation_m = ConversationManager(input_m=input_m, db_m=db_m)
    # message_m = MessageManager(input_m=input_m, db_m=db_m)

    while True:
        action = actions_m.select_initial_action()
        if action == "Create new experiment":  # ✅
            experiment = experiment_m.create_experiment(creator=db_m.username)
        elif action == "Select experiment":  # ✅
            experiment = experiment_m.select_experiment()
            if experiment == None:
                logger.warning("No experiments available. Please create a new one.")
                continue
        else:  # Exit the application
            break
        logger.info(f"\nSelected experiment:\n\n{experiment}")
        while True:
            action = actions_m.select_experiment_action()
            if action == "Perform new conversations":  # ⚒️
                conversation_m.perform_conversations(experiment)
                continue
            elif action == "Duplicate and update experiment":  # ✅
                experiment = experiment_m.duplicate_and_update_experiment(experiment)
                if experiment != None:
                    logger.info(f"\nUpdated experiment:\n\n{experiment}")
                break
            elif action == "Select old conversations":  # ✅
                conversation = conversation_m.select_conversation(experiment)
            elif action == "Delete experiment":  # ✅
                if experiment.creator != db_m.username:
                    logger.warning(
                        "You are not the creator of this experiment. You cannot delete it."
                    )
                    continue
                if input_m.confirm("Are you sure you want to delete this experiment?"):
                    experiment_m.delete_experiment(experiment)
                    break
                continue
            else:  # Go back
                break
            while True:
                action = actions_m.select_conversation_action()
                if action == "View conversation":  # ❌
                    # ui_m.view_conversation(conversation_dict)
                    pass
                elif action == "Update conversation":  # ❌
                    # ui_m.update_conversation(conversation_dict)
                    pass
                elif action == "Delete conversation":  # ❌
                    if conversation.creator != db_m.username:
                        logger.warning(
                            "You are not the creator of this conversation. You cannot delete it."
                        )
                        continue
                    if input_m.confirm(
                        "Are you sure you want to delete this conversation?"
                    ):
                        conversation_m.delete_conversation(experiment, conversation)
                    break
                else:  # Go back
                    break


if __name__ == "__main__":
    main()
