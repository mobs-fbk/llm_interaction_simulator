from copy import deepcopy
from dataclasses import dataclass, field

import httpx
from itakello_logging import ItakelloLogging

from ...interfaces import BaseManager
from ...core.database_manager import DatabaseManager
from ...core.input_manager import InputManager
from ...utility.consts import DEV_MODE
from ...utility.custom_os import CustomOS
from ...utility.enums import SectionType
from ..llm.llm_manager import LLMManager
from ..placeholder.placeholder import Placeholder
from ..placeholder.placeholder_manager import PlaceholderManager
from ..role.role_manager import RoleManager
from ..section.section_manager import SectionManager
from .experiment import Experiment

logger = ItakelloLogging().get_logger(__name__)


@dataclass
class ExperimentManager(BaseManager):
    input_m: InputManager
    db_m: DatabaseManager

    llm_m: LLMManager = field(init=False)
    section_m: SectionManager = field(init=False)
    placeholder_m: PlaceholderManager = field(init=False)

    def __post_init__(self) -> None:
        self.llm_m = LLMManager(input_m=self.input_m)
        self.section_m = SectionManager(input_m=self.input_m)
        self.placeholder_m = PlaceholderManager(input_m=self.input_m)
        self.role_m = RoleManager(
            input_m=self.input_m,
            section_m=self.section_m,
            placeholder_m=self.placeholder_m,
        )
        super().__post_init__()

    def create_experiment(self, creator: str) -> Experiment:
        logger.info("Setting up a new experiment")

        starting_message = self._ask_for_starting_message()

        llms = self.llm_m.ask_for_llms()

        agents_sections = self.section_m.ask_for_sections(type=SectionType.ROLES)
        shared_sections, private_sections = self.section_m.ask_for_shared_sections(
            agents_sections
        )
        roles = self.role_m.ask_for_roles(private_sections)

        summarizer_sections = self.section_m.ask_for_sections(
            type=SectionType.SUMMARIZER
        )

        favourite = self._ask_for_favourite()
        note = self._ask_for_note()

        experiment = Experiment(
            starting_message=starting_message,
            note=note,
            favourite=favourite,
            creator=creator,
            llms_list=llms,
            roles_list=roles,
            shared_sections_list=shared_sections,
            summarizer_sections_list=summarizer_sections,
        )

        self._ask_contents_empty_sections(experiment)

        self.db_m.save_experiment(experiment)

        logger.confirmation("Experiment setup completed and saved successfully.")
        return experiment

    def delete_experiment(self, experiment: Experiment) -> None:
        self.db_m.delete_experiment(experiment)

    def update_experiment(self, experiment: Experiment) -> None:
        changes = self.input_m.select_multiple(
            message="Select the changes you want to make",
            choices=[
                "Note",
                "Favourite",
            ],
        )
        if not changes:
            return None

        if "Note" in changes:
            logger.info(
                "Previous note: " + experiment.note if experiment.note else "EMPTY"
            )
            experiment.note = self._ask_for_note()
        if "Favourite" in changes:
            experiment.favourite = not experiment.favourite

        self.db_m.update_experiment(experiment=experiment)

        logger.confirmation("Experiment updated successfully.")

    def duplicate_and_update_experiment(self, experiment: Experiment) -> None:
        if CustomOS.getenv("APP_MODE", "") == DEV_MODE:
            changes = CustomOS.getenv("UPDATE_EXPERIMENT_CHOICES").split(",")
        else:
            changes = self.input_m.select_multiple(
                message="Select the changes you want to make",
                choices=[
                    "Starting message",
                    "LLMs",
                    "Roles",
                    "Summarizer",
                ],
            )

        if not changes:
            return

        if "Starting message" in changes:
            experiment.starting_message = self._ask_for_starting_message(
                default=experiment.starting_message
            )
        if "LLMs" in changes:
            previous_llms = list(experiment.llms.values())
            llms_str = "\n- ".join(str(llm) for llm in previous_llms)
            logger.info(f"Previous LLMs:\n- {llms_str}")
            llms = self.llm_m.ask_for_llms(
                default=", ".join(llm.model for llm in previous_llms)
            )
            experiment.llms = {llm.name: llm for llm in llms}
        if "Roles" in changes:
            self._update_roles(experiment)
        if "Summarizer" in changes:
            self._update_summarizer(experiment)

        experiment = experiment.duplicate(creator=self.db_m.username)

        self.db_m.save_experiment(experiment)

        logger.confirmation("Experiment duplicated and updated successfully.")

    def select_experiment(self) -> Experiment | None:
        try:
            experiments = self.db_m.get_experiments()
        except httpx.ConnectError:
            logger.error("Ollama is not currently running. Please start it.")
            self.input_m.input_str(
                "Press Enter when Ollama is running again", optional=True
            )
            return None
        if not experiments:
            return None
        choices = []
        for experiment in experiments.values():
            choices.append((experiment.to_selection(), str(experiment.id)))
        selected_id = self.input_m.select_one(
            message="Select an experiment", choices=choices
        )
        return experiments[selected_id]

    def _update_roles(self, experiment: Experiment) -> None:
        section_type = SectionType.ROLES
        logger.info(f"Updating the [{section_type.value}] sections")

        if CustomOS.getenv("APP_MODE", "") == DEV_MODE:
            changes = CustomOS.getenv("UPDATE_ROLES_CHOICES").split(",")
        else:
            changes = self.input_m.select_multiple(
                message="Select the changes you want to make",
                choices=[
                    "Roles",
                    "Roles section titles",
                    "Roles section contents",
                ],
            )

        if "Roles" in changes:
            new_roles = self.role_m.ask_for_updated_roles(old_roles=experiment.roles)
            experiment.roles = {role.name: role for role in new_roles}

        if "Roles section titles" in changes:
            old_private_sections_copy = self.role_m.get_private_sections_copy(
                experiment.roles
            )
            old_private_sections_copy = {
                section.title: section for section in old_private_sections_copy
            }
            old_shared_sections_copy = deepcopy(experiment.shared_sections)
            old_sections_copy = {
                **old_private_sections_copy,
                **old_shared_sections_copy,
            }
            new_sections = self.section_m.ask_for_updated_sections(
                old_sections=old_sections_copy, type=section_type
            )
            default_shared_sections = [section for section in old_shared_sections_copy]
            new_shared_sections, new_private_sections = (
                self.section_m.ask_for_shared_sections(
                    new_sections,
                    default=default_shared_sections,
                )
            )

            # Add previous content - shared sections
            for section in new_shared_sections:
                if section.title in old_shared_sections_copy.keys():
                    old_section = old_shared_sections_copy[section.title]
                    section.content = old_section.content
            experiment.shared_sections = {
                section.title: section for section in new_shared_sections
            }

            # Add previous content - private sections
            for role in experiment.roles.values():
                new_sections = deepcopy(new_private_sections)
                old_sections = role.sections
                for section in new_sections:
                    section.role = role.name
                    section.type = SectionType.PRIVATE
                    if section.title in old_sections.keys():
                        section.content = old_sections[section.title].content
                experiment.roles[role.name].sections = {
                    section.title: section for section in new_sections
                }

        if "Roles section contents" in changes:
            private_sections = self.role_m.get_private_sections_copy(experiment.roles)
            shared_sections = list(experiment.shared_sections.values())
            sections = private_sections + shared_sections
            sections_to_reset = self.input_m.select_multiple(
                message="Select the sections you want to change the content",
                choices=[section.title for section in sorted(sections)],
            )

            for role in experiment.roles.values():
                for section in role.sections.values():
                    if section.title in sections_to_reset:
                        section.to_reset = True

            for section in shared_sections:
                if section.title in sections_to_reset:
                    section.to_reset = True

        self._ask_contents_empty_sections(experiment)

    def _update_summarizer(self, experiment: Experiment) -> None:
        section_type = SectionType.SUMMARIZER
        logger.info(f"Updating the {section_type} section")

        if CustomOS.getenv("APP_MODE", "") == DEV_MODE:
            changes = CustomOS.getenv("UPDATE_SUMMARIZER_CHOICES").split(",")
        else:
            changes = self.input_m.select_multiple(
                message="Select the changes you want to make",
                choices=[
                    "Summarizer sections titles",
                    "Summarizer sections contents",
                ],
            )

        if "Summarizer sections titles" in changes:
            old_sections_copy = deepcopy(experiment.summarizer_sections)
            new_sections = self.section_m.ask_for_updated_sections(
                old_sections=old_sections_copy, type=section_type
            )

            # Add previous content
            for section in new_sections:
                if section.title in old_sections_copy.keys():
                    section.content = old_sections_copy[section.title].content
            experiment.summarizer_sections = {
                section.title: section for section in new_sections
            }

        if "Summarizer sections contents" in changes:
            summarizer_sections = list(experiment.summarizer_sections.values())
            sections_to_reset = self.input_m.select_multiple(
                message="Select the sections you want to reset the content",
                choices=[section.title for section in sorted(summarizer_sections)],
            )
            for section in experiment.summarizer_sections.values():
                if section.title in sections_to_reset:
                    section.to_reset = True

        self._ask_contents_empty_sections(experiment)

    def _ask_for_starting_message(
        self, optional: bool = False, default: str = ""
    ) -> str:
        if CustomOS.getenv("APP_MODE", "") == DEV_MODE:
            starting_message = "Start the experiment"
        else:
            starting_message = self.input_m.input_str(
                "Enter the conversation starting message",
                optional=optional,
                example="Start the experiment",
                default=default,
            )
        return starting_message

    def _ask_for_note(self, default: str = "") -> str:
        if CustomOS.getenv("APP_MODE", "") == DEV_MODE:
            note = "Note test"
        else:
            note = self.input_m.input_str(
                "Enter a note for the experiment", optional=True, default=default
            )
        return note

    def _ask_for_favourite(self) -> bool:
        if CustomOS.getenv("APP_MODE", "") == DEV_MODE:
            favourite = True
        else:
            favourite = self.input_m.confirm(
                message="Do you want to mark this experiment as importat?"
            )
        return favourite

    def _ask_contents_empty_sections(
        self,
        experiment: Experiment,
    ) -> None:
        full_sections = []
        for role in experiment.roles.values():
            full_sections.extend(role.sections.values())
        full_sections.extend(experiment.shared_sections.values())
        full_sections.extend(experiment.summarizer_sections.values())

        empty_sections = []
        for section in full_sections:
            if not section.content or section.to_reset:
                empty_sections.append(section)

        if not empty_sections:
            return

        logger.instruction(
            instructions=[
                "\033[1mPlaceholders\033[0m\033[36m: A list of available placeholders will be displayed. These placeholders allow you to specify elements within the text that change depending on context, such as singular or plural forms based on the number of agents.",
                "\033[1mUsing Placeholders in Content\033[0m\033[36m: When composing content for each section, incorporate any of the displayed placeholders directly into your text. Placeholders such as <AGENT_NUM> will automatically be replaced with the actual number of agents with that role in the conversation (e.g., '1', '2', '3'...).\n"
                + "Similarly, <AGENT_NOUN> will adapt to reflect the singular or plural noun appropriate to the context, such as 'guard' for one and 'guards' for more than one.\n"
                + "EXAMPLE: 'There are <GUARD_NUM> <GUARD_NOUN> in the room,' in the case of 3 guards form will become 'There are 3 guards in the room'.",
                "\033[1mCreating and Using New Verb Placeholders\033[0m\033[36m: You can create new placeholders specifically for verbs by using the format <AGENT_VERB>. Ensure:\n"
                + "\ti. to use the base form of the verb when creating these placeholders (e.g. <AGENT_MAKE>, <AGENT_GO>, or <AGENT_EAT>).\n"
                + "\tii. to insert the agent role subject to the verb (e.g. <GUARD_MAKE>).\n"
                + "Once established, these verb placeholders can be incorporated into the content of any section, adapting to the context as needed.\n"
                + "EXAMPLE: 'The <GUARD_NOUN> <GUARD_MAKE> a decision,' in the singular form wll become 'The guard makes a decision'.",
            ]
        )

        self._print_placeholders(experiment)

        for section in sorted(empty_sections):
            invalid_placeholders = True
            while invalid_placeholders:
                if section.to_reset:
                    logger.info("Previous content: " + section.content)
                input_placeholders = self.section_m.ask_for_content(section)
                invalid_placeholders = self._add_missing_placeholders(
                    experiment=experiment, input_placeholders=input_placeholders
                )
                if invalid_placeholders:
                    logger.warning(
                        "You can only:\n"
                        + "1. use existing placeholders\n"
                        + "2. create new verb placeholders in the form <ROLE_VERB_VERB> with the verb in its base form (e.g. <GUARD_VERB_MAKE>)\n"
                        + "Please try again."
                    )

    def _add_missing_placeholders(
        self, experiment: Experiment, input_placeholders: set[str]
    ) -> bool:
        curr_placeholders = set()
        for role in experiment.roles.values():
            curr_placeholders.update(role.placeholders.keys())
        curr_placeholders.update(experiment.placeholders.keys())

        new_placeholders = input_placeholders - curr_placeholders

        for new_placeholder in new_placeholders:
            parts = new_placeholder[1:-1].split("_")
            parts = [part.lower() for part in parts]
            if (
                len(parts) != 3
                or parts[0] not in experiment.roles.keys()
                or parts[1] != "verb"
                or not Placeholder.is_verb(parts[2])
            ):
                logger.error(f"Invalid placeholder tag: {new_placeholder}")
                return True
            experiment.roles[parts[0]].placeholders[new_placeholder] = Placeholder(
                tag=new_placeholder
            )
        if new_placeholders:
            logger.warning(f"New placeholders created: {', '.join(new_placeholders)}")
        return False

    def _print_placeholders(self, experiment: Experiment) -> None:
        for role in experiment.roles.values():
            logger.info(f"Placeholders [{role.name}]:")
            for placeholder in role.placeholders.values():
                logger.info(f"- {placeholder}")
        logger.info("Placeholders [Shared]:")
        for placeholder in experiment.placeholders.values():
            logger.info(f"- {placeholder}")
