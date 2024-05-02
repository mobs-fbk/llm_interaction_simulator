from copy import deepcopy
from dataclasses import dataclass
from typing import Literal, Union

import httpx
import ollama
from itakello_logging import ItakelloLogging

from ...core.database_manager import DatabaseManager
from ...core.input_manager import InputManager

# from ...conversations.agent import Agent
# from ...conversations.conversation import Conversation
from ...components.role import Role
from ...components.section import Section
from ...utility.consts import TIME_FORMAT
from ...utility.enums import SectionType
from ..agent.agent_manager import AgentManager
from ..llm.llm import LLM
from ..llm.llm_manager import LLMManager
from .experiment import Experiment

logger = ItakelloLogging().get_logger(__name__)


@dataclass
class ExperimentManager:
    input_m: InputManager
    db_m: DatabaseManager

    def __post_init__(self) -> None:
        logger.debug("Experiment manager initialized")

    def create_experiment(self, creator: str) -> Experiment:

        logger.info("Setting up a new experiment")

        starting_message = self._ask_for_starting_message()

        llms = self._ask_for_llms()

        sections = self._ask_for_sections(type=SectionType.AGENTS)
        shared_sections, private_sections = self._split_sections(sections)

        roles = self._ask_for_roles(private_sections)

        sections_summarizer = self._ask_for_sections(type=SectionType.SUMMARIZER)

        favourite = self._ask_for_favourite()
        note = self._ask_for_note()

        experiment = Experiment(
            starting_message=starting_message,
            note=note,
            favourite=favourite,
            creator=creator,
            llm_m=LLMManager(llms=llms),
            agent_m=AgentManager(
                roles=roles,
                shared_sections=shared_sections,
                summarizer_sections=sections_summarizer,
            ),
            conversation_ids=[],
        )

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
            return None
        if not experiments:
            return None
        choices = []
        for experiment in experiments.values():
            choice = f"{experiment.id}\tNumber of conversations: {len(experiment.conversation_ids)}\tCreator: {experiment.creator} [{experiment.creation_date.strftime(TIME_FORMAT)}]"
            if experiment.favourite:
                choice += " ⭐"
            if experiment.note:
                choice += f"\tNote: {experiment.note}"
            choices.append((choice, str(experiment.id)))
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
            new_shared_sections, new_private_sections = self._split_sections(
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

    def _ask_for_llms(self, optional: bool = False) -> list[LLM]:
        logger.instruction(
            "1. To find the available LLMs -> https://ollama.com/library\n"
            + "2. If you want to use the same LLM with different parameters (temperature, top_p and/or top_k) insert it multiple times\n"
        )
        while True:
            llms_names = self.input_m.input_list(
                message="Enter the LLMs to use:",
                example="mistral, mistral, llama2",
                optional=optional,
                avoid_duplicates=False,
            )
            try:
                llms = [LLM(model=name) for name in llms_names]
                break
            except httpx.ConnectError:
                logger.error("Ollama is not currently running. Please start it.")
                self.input_m.input_str(
                    "Press Enter when Ollama is running again", optional=True
                )
                continue
            except ollama.ResponseError as e:
                logger.error(e)
        for llm in llms:
            llm.set_parameters()
        return llms

    def _ask_for_numerical_names(self) -> bool:
        return self.input_m.confirm(
            f"Enter 'y' if you want to use numeric names for agents (e.g. Guard_123)? Othwerwise, random names will be used (e.g. Guard_Alice)."
        )

    def _ask_for_roles(self, private_sections: list[Section]) -> list[Role]:
        assert all(
            section.type == SectionType.PRIVATE for section in private_sections
        ), logger.critical(
            f"Not all sections are of type {SectionType.PRIVATE.value.upper()}"
        )
        roles_names = self.input_m.input_list(
            "Enter the agent roles", example="guard, prisoner"
        )
        roles = []
        for name in roles_names:
            role_sections = deepcopy(private_sections)
            for section in role_sections:
                section.role = name
            new_role = Role(
                name=name,
                sections=role_sections,
            )
            roles.append(new_role)
        return roles

    def _ask_for_sections(
        self, type: Literal[SectionType.SUMMARIZER, SectionType.AGENTS]
    ) -> list[Section]:
        logger.instruction(
            "1. The sections will be ordered by the order you insert them\n"
            + "2. A 'Starting prompt' section without title will be dynamically added to the prompt\n"
            + f"3. The inserted sections will be used only for the {type.value}\n"
        )
        sections_titles = self.input_m.input_list(
            f"Enter the {type.value.upper()} section titles:",
            example="goal, personality, communication_rules, ...",
        )
        sections_titles.insert(0, "starting_prompt")
        sections = [
            Section(index=i, title=title, content="", type=type)
            for i, title in enumerate(sections_titles)
        ]
        return sections

    def _split_sections(
        self, sections: list[Section]
    ) -> tuple[list[Section], list[Section]]:

        assert all(
            section.type == SectionType.AGENTS for section in sections
        ), logger.critical("Not all sections are of type AGENTS")

        shared_section_titles = self.input_m.select_multiple(
            message="Select shared sections between the agents",
            choices=[section.title for section in sorted(sections)],
        )

        shared_sections = []
        private_sections = []
        for section in sections:
            if section.title in shared_section_titles:
                section.type = SectionType.SHARED
                shared_sections.append(section)
            else:
                section.type = SectionType.PRIVATE
                private_sections.append(section)
        return shared_sections, private_sections
