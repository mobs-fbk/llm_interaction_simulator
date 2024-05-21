from dataclasses import dataclass, field

from itakello_logging import ItakelloLogging

from ..abstracts import BaseManager
from ..components.conversation.conversation import Conversation
from ..components.conversation.conversation_manager import ConversationManager
from ..components.experiment.experiment import Experiment
from ..components.experiment.experiment_manager import ExperimentManager
from ..utility.consts import DEV_MODE
from ..utility.custom_os import CustomOS
from .database_manager import DatabaseManager
from .input_manager import InputManager
from .output_manager import OutputManager

logger = ItakelloLogging().get_logger(__name__)


@dataclass
class ActionManager(BaseManager):
    input_m: InputManager
    db_m: DatabaseManager
    output_m: OutputManager

    experiment_m: ExperimentManager = field(init=False)
    conversation_m: ConversationManager = field(init=False)

    def __post_init__(self) -> None:
        self.experiment_m = ExperimentManager(input_m=self.input_m, db_m=self.db_m)
        self.conversation_m = ConversationManager(input_m=self.input_m, db_m=self.db_m)
        super().__post_init__()

    def retrieve_experiment(self) -> Experiment:
        action = self._select_initial_action()
        if action == "Create new experiment":
            experiment = self.experiment_m.create_experiment(creator=self.db_m.username)
        elif action == "Select experiment":
            experiment = self.experiment_m.select_experiment()
            if experiment == None:
                logger.warning("No experiments available. Please create a new one.")
                experiment = self.retrieve_experiment()
        else:  # Exit the application
            exit()
        return experiment

    def experiment_settings(
        self, experiment: Experiment
    ) -> tuple[Conversation | None, bool]:
        action = self._select_experiment_action()
        conversation = None
        go_back = False
        if action == "Perform new conversations":
            self.conversation_m.perform_conversations(experiment)
        elif action == "Duplicate and update experiment":
            self.experiment_m.duplicate_and_update_experiment(experiment)
            if experiment != None:
                logger.info(
                    f"\nDuplicated and updated experiment:\n\n{experiment.to_contents()}"
                )
                go_back = True
        elif action == "Update experiment (Favourites and Notes)":
            if experiment.creator != self.db_m.username:
                logger.warning(
                    "You are not the creator of this experiment. You cannot modify it."
                )
            self.experiment_m.update_experiment(experiment)
        elif action == "Select old conversations":
            conversation = self.conversation_m.select_conversation(experiment)
            if conversation == None:
                logger.warning(
                    "No conversations available for this experiment. Please perform new ones."
                )
                conversation, go_back = self.experiment_settings(experiment)
        elif action == "Save experiment to file":
            self.output_m.save_to_file(experiment)
        elif action == "Delete experiment":
            if experiment.creator != self.db_m.username:
                logger.warning(
                    "You are NOT the creator of this experiment. You cannot delete it."
                )
            elif self.input_m.confirm(
                "Are you sure you want to delete this experiment?"
            ):
                self.experiment_m.delete_experiment(experiment)
                go_back = True
        else:  # Go back
            go_back = True
        return conversation, go_back

    def _select_initial_action(
        self,
    ) -> str:
        choices = ["Create new experiment", "Select experiment", "Exit"]
        if CustomOS.getenv("APP_MODE", "") == DEV_MODE:
            choice_index = CustomOS.getenv("ACTION_1_INDEX")
            return choices[int(choice_index)]
        return self.input_m.select_one(
            message="Select starting action",
            choices=choices,
        )

    def _select_experiment_action(self) -> str:
        choices = [
            "Perform new conversations",
            "Duplicate and update experiment",
            "Update experiment (Favourites and Notes)",
            "Save experiment to file",
            "Select old conversations",
            "Delete experiment",
            "Go back",
        ]
        if CustomOS.getenv("APP_MODE", "") == DEV_MODE:
            choice_index = CustomOS.getenv("ACTION_2_INDEX")
            return choices[int(choice_index)]
        return self.input_m.select_one(
            message="Select experiment action",
            choices=choices,
        )

    def conversation_settings(
        self, experiment: Experiment, conversation: Conversation
    ) -> bool:
        action = self._select_conversation_action()
        go_back = False
        if action == "View conversation":
            self.conversation_m.view_conversation(conversation)
        elif action == "Set as favourite":
            if experiment.creator != self.db_m.username:
                logger.warning(
                    "You are not the creator of this conversastion. You cannot modify it."
                )
            else:
                self.conversation_m.toggle_favourite(conversation)
        elif action == "Delete conversation":
            if conversation.creator != self.db_m.username:
                logger.warning(
                    "You are not the creator of this conversation. You cannot delete it."
                )
            elif self.input_m.confirm(
                "Are you sure you want to delete this conversation?"
            ):
                self.conversation_m.delete_conversation(experiment, conversation)
                go_back = True
        else:  # Go back
            go_back = True
        return go_back

    def _select_conversation_action(self) -> str:
        choices = [
            "View conversation",
            "Set as favourite",
            "Delete conversation",
            "Go back",
        ]
        if CustomOS.getenv("APP_MODE", "") == DEV_MODE:
            choice_index = CustomOS.getenv("ACTION_3_INDEX")
            return choices[int(choice_index)]
        return self.input_m.select_one(
            message="Select conversation action",
            choices=choices,
        )
