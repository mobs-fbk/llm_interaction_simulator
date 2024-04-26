from dataclasses import dataclass, field
from typing import Literal, Union

from bson.objectid import ObjectId
from itakello_logging import ItakelloLogging

from ..conversations.agent import Agent
from ..conversations.conversation import Conversation
from ..conversations.researcher import Researcher
from ..experiments.experiment import Experiment
from ..experiments.role import Role
from ..experiments.section import Section
from ..general.llm import LLM
from ..utility.consts import TIME_FORMAT
from ..utility.enums import SectionType
from .agent_m import AgentManager
from .database_m import DatabaseManager
from .input_m import InputManager
from .llm_m import LLMManager

logger = ItakelloLogging().get_logger(__name__)


@dataclass
class ExperimentManager:
    db_m: DatabaseManager
    input_m: InputManager = field(default_factory=InputManager)

    def create_experiment(self, creator: str) -> Experiment:

        logger.info("Setting up a new experiment")

        starting_message = self._ask_for_starting_message()

        llms = self._ask_for_llms()

        numerical_names = self._ask_for_numerical_names()

        sections = self._ask_for_sections(type=SectionType.AGENTS)
        shared_sections, private_sections = self._split_sections(sections)

        roles = self._ask_for_roles(private_sections)

        sections_summarizer = self._ask_for_sections(type=SectionType.SUMMARIZER)

        favourite = self._ask_for_favourite()
        note = self._ask_for_note()

        experiment = Experiment(
            starting_message=starting_message,
            numerical_names=numerical_names,
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

    def update_experiment(self, experiment: Experiment) -> Union[Experiment, None]:
        changes = self.input_m.select_multiple(
            message="Select the changes you want to make",
            choices=[
                "Starting message",  # ✅
                "LLMs",  # ✅
                "Numerical names",  # ✅
                "Agents",  # ✅
                "Summarizer",  # ✅
                "Note",  # ✅
                "Favourite",  # ✅
            ],
        )

        if not changes:
            return None

        logger.instruction(
            "\n\033[1mInstructions\033[0m\033[36m:\n"
            + "1. Leave empty to keep the current value.\n"
            + "2. In the cases where multiple values are requested (llms, roles and section titles):\n"
            + "- the new objects will be appended to the existing one\n"
            + "- the old values that are not inserted againg will be deleted.\n"
        )

        if "Starting message" in changes:
            logger.info("Previous starting message: " + experiment.starting_message)
            starting_message = self._ask_for_starting_message(optional=True)
            if starting_message:
                experiment.starting_message = starting_message
        if "LLMs" in changes:
            logger.info("Previous LLMs:\n" + str(experiment.llm_m))
            llms = self._ask_for_llms(optional=True)
            experiment.llm_m = LLMManager(llms=llms)
        if "Numerical names" in changes:
            logger.info(
                "Previous numerical names status: " + str(experiment.numerical_names)
            )
            experiment.numerical_names = self._ask_for_numerical_names()
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

        return experiment

    def select_experiment(self) -> Union[Experiment, None]:
        experiments = self.db_m.get_experiments()
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

    def perform_conversations(self, experiment: Experiment) -> list[ObjectId]:
        n_conversations = self.input_m.input_int(
            "Write how many conversations you want to perform",
            positive_requirement=True,
        )
        llms = self.input_m.select_multiple(
            message="Select the LLMs to use",
            choices=[llm for llm in experiment.llm_m.llms.keys()],
        )
        conversation_days = self.input_m.input_int(
            "Enter the number of days per conversation", positive_requirement=True
        )
        conversation_rounds = self.input_m.input_int(
            "Enter the number of rounds per conversation", positive_requirement=True
        )
        speaker_selection_method = self._ask_for_speaker_selection_method()

        agents = []
        for role in experiment.agent_m.roles.values():
            role_num = self.input_m.input_int(
                f"Enter the number of {role.name} agents", positive_requirement=True
            )
            agents.extend([Agent(role=role.name, index=i) for i in range(role_num)])

        conversations = []
        for llm in llms:
            for index in range(n_conversations):
                logger.warning(
                    f"Performing conversation [{index + 1}/{n_conversations}]"
                )
                conversation = Conversation(
                    conversation_days=conversation_days,
                    conversation_rounds=conversation_rounds,
                    speaker_selection_method=speaker_selection_method,
                    starting_message=experiment.starting_message,
                    creator=self.db_m.username,
                    llm=llm,
                )
                conversation = experiment.perform(conversation)
                self.db_m.save_conversation(
                    experiment=experiment, conversation=conversation
                )
        logger.info(f"Performed and saved {n_conversations} conversations")
        return conversations

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
        old_private_sections = self._get_private_sections(experiment).copy()

        if "Roles" in changes:
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

        old_shared_sections = list(experiment.agent_m.shared_sections.values()).copy()
        old_sections = sorted(old_private_sections + old_shared_sections)

        if "Agents section titles" in changes:
            old_section_titles = [section.title for section in old_sections]
            logger.info(
                f"Previous {section_type.value} sections: "
                + ", ".join(old_section_titles[1:])
            )
            new_sections = self._ask_for_sections(type=section_type)
            new_shared_sections, new_private_sections = self._split_sections(
                new_sections
            )

            # Remove old shared sections
            for old_shared_section in old_shared_sections:
                if old_shared_section not in new_shared_sections:
                    del experiment.agent_m.shared_sections[old_shared_section.title]

            # Add new shared sections
            for new_shared_section in new_shared_sections:
                if new_shared_section not in old_shared_sections:
                    experiment.agent_m.shared_sections[new_shared_section.title] = (
                        new_shared_section
                    )

            # Remove old private sections
            for old_private_section in old_private_sections:
                if old_private_section not in new_private_sections:
                    for role in experiment.agent_m.roles.values():
                        del role.sections[old_private_section.title]

            # Add new private sections
            for new_private_section in new_private_sections:
                for role in experiment.agent_m.roles.values():
                    new_section = Section(
                        index=new_private_section.index,
                        title=new_private_section.title,
                        content=new_private_section.content,
                        type=new_private_section.type,
                        role=role.name,
                    )
                    if new_private_section not in role.sections.values():
                        role.sections[new_private_section.title] = new_section

            # Update the indexes
            for section in new_sections:
                if section.type == SectionType.SHARED:
                    experiment.agent_m.shared_sections[section.title].index = (
                        section.index
                    )
                else:
                    for role in experiment.agent_m.roles.values():
                        role.sections[section.title].index = section.index

        if "Agents section contents" in changes:
            private_sections = list(
                next(iter((experiment.agent_m.roles.values()))).sections.values()
            )
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
        old_summarizer_sections = experiment.agent_m.summarizer_sections.copy()

        if "Summarizer sections titles" in changes:
            old_summarizer_section_titles = [
                section.title for section in old_summarizer_sections.values()
            ]
            logger.info(
                f"Previous {SectionType.SUMMARIZER.value} sections: "
                + ", ".join(old_summarizer_section_titles[1:])
            )
            new_summarizer_sections = self._ask_for_sections(
                type=SectionType.SUMMARIZER
            )

            # Remove old summarizer sections
            for old_summarizer_section in old_summarizer_sections.values():
                if old_summarizer_section not in new_summarizer_sections:
                    del experiment.agent_m.summarizer_sections[
                        old_summarizer_section.title
                    ]
            # Add new summarizer sections
            for new_summarizer_section in new_summarizer_sections:
                if new_summarizer_section not in old_summarizer_sections.values():
                    experiment.agent_m.summarizer_sections[
                        new_summarizer_section.title
                    ] = new_summarizer_section

            # Update the indexes
            for section in new_summarizer_sections:
                experiment.agent_m.summarizer_sections[section.title].index = (
                    section.index
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
            "Enter the conversation starting message (e.g. 'Start the experiment')",
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
        llms_names = self.input_m.input_list(
            "Enter the LLMs to use (comma-separated, e.g. mistral, llama2)",
            optional=optional,
        )
        return [LLM(model=name) for name in llms_names]

    def _ask_for_numerical_names(self) -> bool:
        return self.input_m.confirm(
            f"Do you want to use numeric names for agents (e.g. Guard_123)? Othwerwise, random names will be used (e.g. Guard_Alice)."
        )

    def _ask_for_roles(self, private_sections: list[Section]) -> list[Role]:
        assert all(
            section.type == SectionType.PRIVATE for section in private_sections
        ), logger.critical("Not all sections are of type PRIVATE")
        roles_names = self.input_m.input_list(
            "Enter the agent roles (comma-separated, e.g. guard, prisoner)"
        )
        roles = []
        for name in roles_names:
            role_sections = [
                Section(
                    index=section.index,
                    title=section.title,
                    content=section.content,
                    type=section.type,
                    role=name,
                )
                for section in private_sections
            ]
            new_role = Role(
                name=name,
                sections=role_sections,
            )
            roles.append(new_role)
        return roles

    def _ask_for_sections(
        self, type: Literal[SectionType.SUMMARIZER, SectionType.AGENTS]
    ) -> list[Section]:
        sections_titles = self.input_m.input_list(
            f"Enter the {type.value} section titles in the order you want them to appear in the system prompt (comma-separated, 'goal, personality, communication_rules, ...')"
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

    def _ask_for_speaker_selection_method(self) -> str:
        choices = [
            (
                "Auto: the next speaker is selected automatically by an LLM",
                "auto",
            ),
            (
                "Manual: the next speaker is selected manually by the user",
                "manual",
            ),
            ("Random: the next speaker is selected randomly", "random"),
            (
                "Round robin: the next speaker is selected in a round-robin fashion",
                "round_robin",
            ),
        ]
        return self.input_m.select_one(
            message="Select a speaker selection method",
            choices=choices,
        )
