import json
import logging
from dataclasses import dataclass, field

import autogen

from ..agents import Agent, Guard, Prisoner, Summarizer
from ..handlers import ConfigHandler
from ..serializers import DocumentSerializable
from . import Conversation

logger = logging.getLogger(__name__)


@dataclass
class Experiment(DocumentSerializable):
    config: dict = field(init=False)
    agents: list[Agent] = field(init=False)
    researcher: autogen.UserProxyAgent = field(init=False)
    group_chat: autogen.GroupChat = field(init=False)
    manager: autogen.GroupChatManager = field(init=False)
    summarizer: Summarizer = field(init=False)

    def __post_init__(self):
        self.config = ConfigHandler().get_section("Experiment")
        llm_config = self._get_config_llm(self.config["llm"])
        self.researcher = self._get_researcher()
        self.agents = self._get_prison_agents(llm_config)
        self.group_chat = self._get_group_chat(self.agents)
        self.manager = self._get_manager(self.group_chat, llm_config)
        self.summarizer = self._get_summarizer(llm_config)
        logger.info(
            f"Experiment created with config:\n{json.dumps(self.config, indent=2)}"
        )

    def to_document(self) -> dict:
        doc = self.config.copy()
        return doc

    def perform(self) -> Conversation:
        start_message = self.config["researcher_initial_message"]
        for i in range(int(self.config["experiment_days"])):
            self.researcher.initiate_chat(
                recipient=self.manager, clear_history=True, message=start_message
            )
            conversation = self.group_chat.messages[1:]
            summary = self.summarizer.generate_summary(
                previous_conversation=conversation, round_number=i + 1
            )
            start_message += "\n" + summary
        raise NotImplementedError("Finish this method")
        logger.info("Experiment complete")
        return Conversation(messages=self.group_chat.messages)

    def _get_config_llm(self, model: str) -> dict:
        config_list = autogen.config_list_from_json(
            env_or_file="config/OAI_CONFIG_LIST", filter_dict={"model": [model]}
        )
        llm_config = {
            "config_list": config_list,
            "cache_seed": None,  # set to None to disable caching and have a new conversation every time
        }
        return llm_config

    def _get_summarizer(self, llm_config: dict) -> Summarizer:
        summarizer = Summarizer(
            llm_config=llm_config,
            n_guards=int(self.config["n_guards"]),
            n_prisoners=int(self.config["n_prisoners"]),
        )
        return summarizer

    def _get_manager(
        self, group_chat: autogen.GroupChat, llm_config: dict
    ) -> autogen.GroupChatManager:
        manager = autogen.GroupChatManager(
            groupchat=group_chat,
            llm_config=llm_config,
        )
        return manager

    def _get_group_chat(
        self,
        agents: list[autogen.Agent],
        selection_method: str = "auto",
        round_number: int = 10,
    ) -> autogen.GroupChat:
        assert selection_method in (
            "auto",
            "manual",
            "random",
            "round_robin",
        ), "Invalid mode"

        group_chat = autogen.GroupChat(
            agents=agents,
            messages=[],  # no messages to start
            speaker_selection_method=selection_method,
            allow_repeat_speaker=False,
            max_round=round_number,
        )
        return group_chat

    def _get_researcher(self) -> autogen.UserProxyAgent:
        researcher = autogen.UserProxyAgent(
            name="Researcher",
            human_input_mode="TERMINATE",
            code_execution_config={"use_docker": False},
        )
        return researcher

    def _get_prison_agents(
        self,
        llm_config: dict,
    ):
        agents = []
        n_guards = int(self.config["n_guards"])
        n_prisoners = int(self.config["n_prisoners"])
        agents_fields = [w.strip() for w in self.config["agents_fields"].split(",")]
        for _ in range(n_guards):
            agents.append(
                Guard(
                    llm_config=llm_config,
                    n_guards=n_guards,
                    n_prisoners=n_prisoners,
                    agent_fields=agents_fields,
                )
            )
        for _ in range(n_prisoners):
            agents.append(
                Prisoner(
                    llm_config=llm_config,
                    n_guards=n_guards,
                    n_prisoners=n_prisoners,
                    agent_fields=agents_fields,
                )
            )
        return agents
