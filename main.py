from itakello_logging import ItakelloLogging

from src.managers.ui_m import UIManager


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
    ui_m = UIManager()
    db_m = ui_m.authenticate_user()
    selected_db = ui_m.select_database(db_m.list_databases())
    db_m.select_database(selected_db)

    while True:
        action = ui_m.select_initial_action()  # ✅
        if action == "Create a new experiment":
            experiment = ui_m.create_experiment(db_m.username)  # ✅
            db_m.save_experiment(experiment)
        elif action == "Select an experiment":
            available_experiments = db_m.get_experiments()  # ⚒️
            experiment = ui_m.select_experiment(available_experiments)  # ❌
        else:
            break  # Exit the application
        while True:
            action = ui_m.select_experiment_action()  # ❌
            if action == "Perform new conversations":
                new_conversations = ui_m.perform_conversations(experiment)  # ❌
                # experiment.conversations_ids.extend(new_conversations)
                continue
            elif action == "Select old conversations":
                conversation_dict = ui_m.select_conversation(experiment)  # ❌
                if conversation_dict == None:
                    continue
            elif action == "Update experiment":
                ui_m.update_experiment(experiment)  # ❌
                continue
            elif action == "Delete experiment":
                ui_m.delete_experiment(experiment)  # ❌
                break
            else:  # Go back
                break
            while True:
                action = ui_m.select_conversation_action()  # ❌
                if action == "View conversation":
                    ui_m.view_conversation(conversation_dict)  # ❌
                elif action == "Update conversation":
                    ui_m.update_conversation(conversation_dict)  # ❌
                elif action == "Delete conversation":
                    ui_m.delete_conversation(experiment, conversation_dict)  # ❌
                    break
                else:  # Go back
                    break


if __name__ == "__main__":
    main()
