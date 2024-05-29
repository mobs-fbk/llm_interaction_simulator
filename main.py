from dotenv import load_dotenv
from itakello_logging import ItakelloLogging

from src.core.action_manager import ActionManager
from src.core.database_manager import DatabaseManager
from src.core.input_manager import InputManager
from src.core.output_manager import OutputManager

logger = ItakelloLogging.get_logger(__name__)


def main() -> None:
    logger.debug("[Test debug mode]")

    input_m = InputManager()
    db_m = DatabaseManager(input_m=input_m)
    output_m = OutputManager(db_m=db_m)

    action_m = ActionManager(input_m=input_m, db_m=db_m, output_m=output_m)

    while True:
        experiment = action_m.retrieve_experiment()
        logger.info(f"\nSelected experiment:\n\n{experiment.to_contents()}")
        while True:
            conversation, go_back = action_m.experiment_settings(experiment)
            if go_back:
                break
            if conversation == None:
                continue
            logger.info(f"\nSelected conversation:\n\n{conversation.to_content()}")
            while True:
                go_back = action_m.conversation_settings(experiment, conversation)
                if go_back:
                    break


if __name__ == "__main__":
    load_dotenv()
    ItakelloLogging(
        debug=False,
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
    main()
