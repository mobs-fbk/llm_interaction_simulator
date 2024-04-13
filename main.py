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
            "openai._base_client",  # Remove to see API requests debug logs
        ],
    )
    cli = CLIHandler()

    while True:
        action = cli.select_main_action()  # ✅
        if action == "Create a new experiment":
            experiment = cli.create_experiment()  # ✅
        elif action == "Select an experiment":
            experiment = cli.select_experiment()  # ✅
        else:
            break  # Exit the application
        while True:
            action = cli.select_experiment_action()  # ✅
            if action == "Perform new conversations":
                new_conversations = cli.perform_conversations(experiment)  # ✅
                experiment.conversations_ids.extend(new_conversations)
                continue
            elif action == "Select old conversations":
                conversation_dict = cli.select_conversation(experiment)  # ✅
                if conversation_dict == None:
                    continue
            elif action == "Update experiment":
                cli.update_experiment(experiment)  # ✅
                continue
            elif action == "Delete experiment":
                cli.delete_experiment(experiment)  # ✅
                break
            else:  # Go back
                break
            while True:
                action = cli.select_conversation_action()  # ✅
                if action == "View conversation":
                    cli.view_conversation(conversation_dict)  # ✅
                elif action == "Update conversation":
                    cli.update_conversation(conversation_dict)  # ✅
                elif action == "Delete conversation":
                    cli.delete_conversation(experiment, conversation_dict)  # ✅
                    break
                else:  # Go back
                    break


if __name__ == "__main__":
    main()
