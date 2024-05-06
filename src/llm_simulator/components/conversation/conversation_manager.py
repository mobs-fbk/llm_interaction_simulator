from dataclasses import dataclass, field

from itakello_logging import ItakelloLogging

from ...abstracts import BaseManager
from ...core.database_manager import DatabaseManager
from ...core.input_manager import InputManager
from ...utility.consts import DEV_MODE, TIME_FORMAT
from ...utility.custom_os import CustomOS
from ..experiment.experiment import Experiment
from ..llm.llm import LLM
from ..llm.llm_manager import LLMManager
from ..role.role import Role
from ..section.section_manager import SectionManager
from .conversation import Conversation
from .summarizer import Summarizer

logger = ItakelloLogging().get_logger(__name__)


@dataclass
class ConversationManager(BaseManager):
    input_m: InputManager
    db_m: DatabaseManager

    section_m: SectionManager = field(init=False)
    llm_m: LLMManager = field(init=False)

    def __post_init__(self) -> None:
        self.section_m = SectionManager(input_m=self.input_m)
        self.llm_m = LLMManager(input_m=self.input_m)

    def perform_conversations(self, experiment: Experiment) -> None:
        n_conversations = self._ask_n_conversations()
        llms = self._ask_llms(available_llms=list(experiment.llms.values()))
        total_messages = self._ask_total_messages()
        days_list = self._ask_days_list(total_messages)
        agent_combinations = self._ask_agent_combinations(
            available_roles=list(experiment.roles.values())
        )
        speaker_selection_method = self._ask_for_speaker_selection_method()

        total_conversations = (
            n_conversations * len(llms) * len(days_list) * len(agent_combinations)
        )
        index_conv = 1
        for llm in llms:
            for days in days_list:
                for agent_combination in agent_combinations:
                    for _ in range(n_conversations):
                        logger.info(
                            f"--- Performing conversation [{index_conv}/{total_conversations}] ---\n"
                        )
                        index_conv += 1
                        conv_llm = experiment.llms[llm]
                        logger.info(
                            f"\033[1mLLM\033[0m: {conv_llm}\n\033[1mDays\033[0m: {days}\n\033[1mAgents\033[0m: {agent_combination}\n"
                        )
                        conversation = Conversation(
                            n_messages=total_messages,
                            speaker_selection_method=speaker_selection_method,
                            starting_message=experiment.starting_message,
                            creator=self.db_m.username,
                            days=days,
                            llm=conv_llm,
                            agent_combination=agent_combination,
                        )
                        placeholders = experiment.compose_placeholders(
                            agent_combination
                        )
                        conv_agents = conversation.generate_agents(
                            experiment, placeholders, conv_llm
                        )
                        summarizer = Summarizer(
                            sections=list(experiment.summarizer_sections.values()),
                            placeholders=placeholders,
                            llm=conv_llm,
                        )
                        messages = conversation.perform(
                            agents=conv_agents,
                            summarizer=summarizer,
                            llm_manager=conv_llm,
                        )
                        self.db_m.save_conversation(
                            experiment=experiment,
                            conversation=conversation,
                            messages=messages,
                        )
        logger.confirmation(f"Performed and saved {total_conversations} conversations")

    def select_conversation(self, experiment: Experiment) -> Conversation | None:
        conversations = self.db_m.get_conversations(experiment.conversation_ids)
        if not conversations:
            return None  # type: ignore
        choices = []
        for conversation in conversations.values():
            choices.append((conversation.to_selection(), str(conversation.id)))
        selected_id = self.input_m.select_one(
            message="Select a conversation to view:", choices=choices
        )
        return conversations[selected_id]

    def toggle_favourite(self, conversation: Conversation) -> None:
        conversation.favourite = not conversation.favourite
        self.db_m.update_conversation(conversation)

    def view_conversation(self, conversation: Conversation) -> None:
        messages = self.db_m.get_messages(conversation.messages_ids)
        roles = [role for role, _ in conversation.agent_combination]
        color_codes = {
            "\033[93m",  # Yellow
            "\033[92m",  # Green
            "\033[91m",  # Red
            "\033[95m",  # Purple
            "\033[96m",  # Cyan
        }
        if len(roles) + 1 > len(color_codes):
            raise ValueError("Too many roles to display in different colors.")
        agent_colors = {"Researcher": "\033[94m"}  # Blue
        for role in roles:
            agent_colors[role.capitalize()] = color_codes.pop()
        for message in messages.values():
            color_code = agent_colors.get(message.role, "\033[0m")
            logger.info(
                f"{color_code}[Day {message.day}] {message.speaker}\033[0m:\n{message.content}\n"
            )

    def delete_conversation(
        self, experiment: Experiment, conversation: Conversation
    ) -> None:
        experiment.conversation_ids.remove(conversation.id)
        self.db_m.update_experiment(experiment)
        self.db_m.delete_conversation(conversation)

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
        if CustomOS.getenv("APP_MODE", "") == DEV_MODE:
            speaker_selection_method = CustomOS.getenv("SPEAKER_SELECTION_METHOD")
        else:
            speaker_selection_method = self.input_m.select_one(
                message="Select a speaker selection method",
                choices=choices,
            )
        return speaker_selection_method

    def _ask_n_conversations(self) -> int:
        if CustomOS.getenv("APP_MODE", "") == DEV_MODE:
            n_conversations = CustomOS.getenv("N_CONVERSATIONS")
            n_conversations = int(n_conversations)
        else:
            n_conversations = self.input_m.input_int(
                "Enter the number of conversations you want to perform per hyperparameter set (LLMs, days and agents)",
                positive_requirement=True,
            )
        return n_conversations

    def _ask_llms(self, available_llms: list[LLM]) -> list[str]:
        if CustomOS.getenv("APP_MODE", "") == DEV_MODE:
            llms = CustomOS.getenv("LLMS").split(",")
        else:
            llms = self.input_m.select_multiple(
                message="1. Select the LLMs to use",
                choices=[(str(llm), llm.name) for llm in available_llms],
            )
        return llms

    def _ask_total_messages(self) -> int:
        if CustomOS.getenv("APP_MODE", "") == DEV_MODE:
            total_messages = CustomOS.getenv("TOTAL_MESSAGES")
            total_messages = int(total_messages)
        else:
            total_messages = self.input_m.input_int(
                "2.1. Enter the total number of messages per convesation (it has to be even)",
                positive_requirement=True,
                even_requirement=True,
            )
        return total_messages

    def _ask_days_list(self, total_messages: int) -> list[int]:
        if CustomOS.getenv("APP_MODE", "") == DEV_MODE:
            days_list = CustomOS.getenv("DAYS_LIST").split(",")
            days_list = [int(day) for day in days_list]
        else:
            total_days = self.input_m.input_int(
                "2.2. Enter the number of days in which you want to perform the conversations",
                positive_requirement=True,
                max_value=total_messages // 2,
            )
            if total_days > 1:
                if self.input_m.confirm(
                    f"Do you want to try the conversation from 1 to {total_days} days? Otherwise, the conversation will be performed only in {total_days} days."
                ):
                    days_list = list(range(1, total_days + 1))
                else:
                    days_list = [total_days]
            else:
                days_list = [total_days]
        return days_list

    def _ask_agent_combinations(
        self, available_roles: list[Role]
    ) -> list[list[tuple[str, int]]]:
        agent_combinations = []
        max_nums = 1
        if CustomOS.getenv("APP_MODE", "") == DEV_MODE:
            agent_max_nums = CustomOS.getenv("AGENT_NUMS").split(",")
            assert len(agent_max_nums) == len(available_roles)
            agent_combinations = [
                (role.name, int(num))
                for role, num in zip(available_roles, agent_max_nums)
            ]
        else:
            for role in available_roles:
                max_num = self.input_m.input_int(
                    f"3. Enter the maximum number of [{role.name.capitalize()}] agents",
                    positive_requirement=True,
                )
                agent_combinations.append((role.name, max_num))
                max_nums = max(max_nums, max_num)
        if max_nums > 1:
            if CustomOS.getenv("APP_MODE", "") == DEV_MODE:
                try_each_agent_combination = CustomOS.getenv(
                    "TRY_EACH_AGENT_COMBINATION"
                )
                try_each_agent_combination = (
                    True if try_each_agent_combination == "y" else False
                )
            else:
                try_each_agent_combination = self.input_m.confirm(
                    "Do you want to try each agent combination?"
                )
        else:
            try_each_agent_combination = False
        agent_combinations = self.section_m.get_agent_combinations(
            agent_combinations, try_each_agent_combination
        )
        return agent_combinations
