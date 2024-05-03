from dataclasses import dataclass, field
from typing import Union

import httpx
from itakello_logging import ItakelloLogging

from ...abstracts import BaseManager
from ...core.database_manager import DatabaseManager
from ...core.input_manager import InputManager
from ...utility.consts import DEV_MODE
from ...utility.custom_os import CustomOS
from ...utility.enums import SectionType
from ..llm.llm_manager import LLMManager
from ..placeholder.placeholder import Placeholder
from ..placeholder.placeholder_manager import PlaceholderManager
from ..role.role_manager import RoleManager
from ..section.section import Section
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

        if CustomOS.getenv("APP_MODE", "") == DEV_MODE:
            starting_message = "Start the experiment"
        else:
            starting_message = self._ask_for_starting_message()

        llms = self.llm_m.ask_for_llms()

        agents_sections = self.section_m.ask_for_sections(type=SectionType.AGENTS)
        shared_sections, private_sections = self.section_m.ask_shared_sections(
            agents_sections
        )
        roles = self.role_m.ask_for_roles(private_sections)

        summarizer_sections = self.section_m.ask_for_sections(
            type=SectionType.SUMMARIZER
        )

        if CustomOS.getenv("APP_MODE", "") == DEV_MODE:
            favourite = False
            note = ""
        else:
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

    def duplicate_and_update_experiment(
        self, experiment: Experiment
    ) -> Union[Experiment, None]:
        changes = self.input_m.select_multiple(
            message="Select the changes you want to make",
            choices=[
                "Starting message",  # ✅
                "LLMs",  # ✅
                "Agents",  # ✅
                "Summarizer",  # ✅
                "Note",  # ✅
                "Favourite",  # ✅
            ],
        )

        if not changes:
            return None

        if "Starting message" in changes:
            logger.info("Previous starting message: " + experiment.starting_message)
            experiment.starting_message = self._ask_for_starting_message()
        if "LLMs" in changes:
            logger.info("Previous LLMs:\n" + str(experiment.llm_m))
            llms = self._ask_for_llms()
            experiment.llm_m = LLMManager(llms=llms)
        if "Agents" in changes:
            self._update_agents(experiment)
        if "Summarizer" in changes:
            self._update_summarizer(experiment)
        if "Note" in changes:
            logger.info("Previous note: " + experiment.note)
            experiment.note = self._ask_for_note()
        if "Favourite" in changes:
            experiment.favourite = not experiment.favourite

        experiment = experiment.duplicate(creator=self.db_m.username)

        self.db_m.save_experiment(experiment)

        logger.confirmation("Experiment duplicated and updated successfully.")

        return experiment

    def select_experiment(self) -> Union[Experiment, None]:
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

    def _update_agents(self, experiment: Experiment) -> None:
        section_type = SectionType.AGENTS
        logger.info(f"Updating the {section_type} section")

        changes = self.input_m.select_multiple(
            message="Select the changes you want to make",
            choices=[
                "Roles",
                "Agents section titles",
                "Agents section contents",
            ],
        )
        old_private_sections = self._get_private_sections(experiment)

        if "Roles" in changes:
            logger.warning(
                "1. The new roles will be appended to the existing one\n"
                + "2. The roles that are not reinserted will be deleted.\n"
            )
            old_role_names = list(experiment.agent_m.roles.keys())

            logger.info("Previous roles: " + ", ".join(old_role_names))
            new_roles = self._ask_for_roles(old_private_sections)
            new_role_names = [role.name for role in new_roles]

            for old_role_name in old_role_names:
                if old_role_name not in new_role_names:
                    del experiment.agent_m.roles[old_role_name]

            for new_role in new_roles:
                if new_role.name not in old_role_names:
                    experiment.agent_m.roles[new_role.name] = new_role

        old_shared_sections = list(experiment.agent_m.shared_sections.values())
        old_sections = sorted(old_private_sections + old_shared_sections)

        if "Agents section titles" in changes:
            logger.warning(
                "1. The new sections will be appended to the existing one, using the new order\n"
                + "2. The sections that are not reinserted will be deleted.\n"
                + "3. If a section changes from shared to private (or viceversa), you will be asked to insert the new content\n"
            )
            old_section_titles = [
                (
                    section.title
                    if section.type == SectionType.PRIVATE
                    else f"{section.title} (SHARED)"
                )
                for section in old_sections
            ]
            logger.info(
                f"Previous {section_type.value} sections: "
                + ", ".join(old_section_titles[1:])
            )
            new_sections = self._ask_for_sections(type=section_type)
            new_shared_sections, new_private_sections = self.split_sections(
                new_sections
            )

            experiment.agent_m.shared_sections = {
                section.title: section for section in new_shared_sections
            }
            for role in experiment.agent_m.roles.values():
                role.sections = {
                    section.title: section for section in new_private_sections
                }

            # Add previous contents
            for section in old_sections:
                if section.title in experiment.agent_m.shared_sections.keys():
                    experiment.agent_m.shared_sections[section.title].content = (
                        section.content
                    )
                else:
                    for role in experiment.agent_m.roles.values():
                        if section.title in role.sections.keys():
                            role.sections[section.title].content = section.content

        if "Agents section contents" in changes:
            private_sections = self._get_private_sections(experiment)
            shared_sections = list(experiment.agent_m.shared_sections.values())
            sections = private_sections + shared_sections
            sections_to_reset = self.input_m.select_multiple(
                message="Select the sections you want to reset the content",
                choices=[section.title for section in sorted(sections)],
            )

            for role in experiment.agent_m.roles.values():
                for section in role.sections.values():
                    if section.title in sections_to_reset:
                        section.content = ""

            for section in shared_sections:
                if section.title in sections_to_reset:
                    section.content = ""

        experiment.agent_m.ask_contents_empty_sections()

    def _update_summarizer(self, experiment: Experiment) -> None:
        section_type = SectionType.AGENTS
        logger.info(f"Updating the {section_type} section")

        changes = self.input_m.select_multiple(
            message="Select the changes you want to make",
            choices=[
                "Summarizer sections titles",
                "Summarizer sections contents",
            ],
        )

        if "Summarizer sections titles" in changes:
            logger.instruction(
                "1. the new sections will be appended to the existing one, using the new order\n"
                + "2. the sections that are not reinserted will be deleted.\n"
            )
            old_summarizer_sections = list(
                experiment.agent_m.summarizer_sections.values()
            )
            old_summarizer_section_titles = [
                section.title for section in old_summarizer_sections
            ]
            logger.info(
                f"Previous {SectionType.SUMMARIZER.value} sections: "
                + ", ".join(old_summarizer_section_titles[1:])
            )
            new_summarizer_sections = self._ask_for_sections(
                type=SectionType.SUMMARIZER
            )

            experiment.agent_m.summarizer_sections = {
                section.title: section for section in new_summarizer_sections
            }

            # Add previous contents
            for section in old_summarizer_sections:
                if section.title in experiment.agent_m.summarizer_sections.keys():
                    experiment.agent_m.summarizer_sections[section.title].content = (
                        section.content
                    )

        if "Summarizer sections contents" in changes:
            summarizer_sections = experiment.agent_m.summarizer_sections
            sections_to_reset = self.input_m.select_multiple(
                message="Select the sections you want to reset the content",
                choices=[
                    section.title for section in sorted(summarizer_sections.values())
                ],
            )
            for section in sections_to_reset:
                summarizer_sections[section].content = ""

        experiment.agent_m.ask_contents_empty_sections()

    def _get_private_sections(self, experiment: Experiment) -> list[Section]:
        return list(next(iter(experiment.agent_m.roles.values())).sections.values())

    def _ask_for_starting_message(self, optional: bool = False) -> str:
        return self.input_m.input_str(
            "Enter the conversation starting message (e.g. Start the experiment)",
            optional=optional,
        )

    def _ask_for_note(self) -> str:
        return self.input_m.input_str(
            "Enter a note for the experiment (optional)", optional=True
        )

    def _ask_for_favourite(self) -> bool:
        return self.input_m.confirm(
            "Do you want to mark this experiment with a ⭐ for finding it more easily?"
        )

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
            if not section.content:
                empty_sections.append(section)

        if not empty_sections:
            return

        logger.instruction(
            "1. \033[1mPlaceholders\033[0m\033[36m: A list of available placeholders will be displayed. These placeholders allow you to specify elements within the text that change depending on context, such as singular or plural forms based on the number of agents.\n"
            + "2. \033[1mUsing Placeholders in Content\033[0m\033[36m: When composing content for each section, incorporate any of the displayed placeholders directly into your text. Placeholders such as <AGENT_NUM> will automatically be replaced with the actual number of agents with that role in the conversation (e.g., '1', '2', '3'...).\nSimilarly, <AGENT_NOUN> will adapt to reflect the singular or plural noun appropriate to the context, such as 'guard' for one and 'guards' for more than one.\nEXAMPLE: 'There are <GUARD_NUM> <GUARD_NOUN> in the room,' in the case of 3 guards form will become 'There are 3 guards in the room'.\n"
            + "3. \033[1mCreating and Using New Verb Placeholders\033[0m\033[36m: You can create new placeholders specifically for verbs by using the format <AGENT_VERB>. Ensure:\n\ti. to use the base form of the verb when creating these placeholders (e.g. <AGENT_MAKE>, <AGENT_GO>, or <AGENT_EAT>).\n\tii. to insert the agent role subject to the verb (e.g. <GUARD_MAKE>).\nOnce established, these verb placeholders can be incorporated into the content of any section, adapting to the context as needed.\nEXAMPLE: 'The <GUARD_NOUN> <GUARD_MAKE> a decision,' in the singular form wll become 'The guard makes a decision'.\n"
        )

        self._print_placeholders(experiment)

        for section in sorted(empty_sections):
            invalid_placeholders = True
            while invalid_placeholders:
                input_placeholders = self.section_m.ask_content(section)
                invalid_placeholders = self.add_missing_placeholders(
                    experiment=experiment, input_placeholders=input_placeholders
                )
                if invalid_placeholders:
                    logger.warning(
                        "You can only:\n"
                        + "1. use existing placeholders\n"
                        + "2. create new verb placeholders in the form <ROLE_VERB_VERB> with the verb in its base form (e.g. <GUARD_VERB_MAKE>)\n"
                        + "Please try again."
                    )

    def add_missing_placeholders(
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
