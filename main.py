from itakello_logging import ItakelloLogging

from src.handlers import CLIHandler


def main() -> None:
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
        ],
    )
    cli_handler = CLIHandler()

    while True:
        action = cli_handler.select_main_action()  # ✅
        if action == "Create a new experiment":
            experiment = cli_handler.create_experiment()  # ✅
        elif action == "Select an experiment":
            experiment = cli_handler.select_experiment()  # ❌
        else:
            break  # Exit the application
        while True:
            action = cli_handler.select_experiment_action()  # ✅
            if action == "Perform new conversations":
                cli_handler.perform_conversations(experiment)  # ❌
                continue
            elif action == "View old conversations":
                conversation = cli_handler.select_conversation(experiment)  # ❌
            elif action == "Update experiment description":
                cli_handler.update_experiment_description(experiment)  # ❌
                continue
            elif action == "Delete experiment":
                cli_handler.delete_experiment(experiment)  # ❌
                break
            else:  # Go back
                break
            while True:
                action = cli_handler.select_conversation_action()  # ✅
                if action == "View conversation":
                    cli_handler.view_conversation(conversation)  # ❌
                elif action == "Update conversation":
                    cli_handler.update_conversation(conversation)  # ❌
                elif action == "Delete conversation":
                    cli_handler.delete_conversation(conversation)  # ❌
                else:  # Go back
                    break


if __name__ == "__main__":
    main()
