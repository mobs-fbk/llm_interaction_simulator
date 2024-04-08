from itakello_logging import ItakelloLogging

from src.handlers import CLIHandler


def main() -> None:
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
            elif action == "View old conversations":
                cli_handler.view_conversations(experiment)  # ❌
            elif action == "Update experiment description":
                cli_handler.update_experiment_description(experiment)  # ❌
            elif action == "Delete experiment":
                cli_handler.delete_experiment(experiment)  # ❌
                break  # After deleting, go back to the main menu
            elif action == "Go back":  # ✅
                break  # Return to the main menu


if __name__ == "__main__":
    main()
