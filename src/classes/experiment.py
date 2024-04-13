import json
import logging
from dataclasses import dataclass, field
from typing import cast

import autogen
from bson.objectid import ObjectId

from ..agents import CustomAgent, Guard, Manager, Prisoner, Researcher, Summarizer
from ..serializers.document_serializer import DocumentSerializer
from .chat import Chat
from .conversation import Conversation

logger = logging.getLogger(__name__)


@dataclass
class Experiment(DocumentSerializer):
    config: dict
    id: ObjectId = field(init=False)
    conversations_ids: list[ObjectId] = field(default_factory=list)
    researcher: Researcher = field(init=False)
    agents: list[CustomAgent] = field(init=False)
    group_chat: Chat = field(init=False)
    manager: Manager = field(init=False)
    summarizer: Summarizer = field(init=False)

    def __init__(self, config: dict) -> None:
        self.config = config
        llm_config = self._get_config_llm()
        self.researcher = Researcher()
        if "guard_prompt" in self.config and "prisoner_prompt" in self.config:
            self.agents = self._get_agents(
                llm_config,
                guard_prompt=self.config["guard_prompt"],
                prisoner_prompt=self.config["prisoner_prompt"],
            )
            # Remove prompts from config to avoid saving them
            self.config.pop("guard_prompt")
            self.config.pop("prisoner_prompt")
        else:
            self.agents = self._get_agents(llm_config)
        if "summarizer_prompt" in self.config:
            self.summarizer = Summarizer.from_prompt(
                llm_config=llm_config, system_prompt=self.config["summarizer_prompt"]
            )
            # Remove prompt from config to avoid saving it
            self.config.pop("summarizer_prompt")
        else:
            self.summarizer = Summarizer.from_config(
                llm_config=llm_config,
                n_guards=int(self.config["n_guards"]),
                n_prisoners=int(self.config["n_prisoners"]),
                agent_fields=[
                    w.strip() for w in self.config["summarizer_fields"].split(",")
                ],
            )
        self.group_chat = Chat(
            agents=cast(list[autogen.Agent], self.agents),
            selection_method=self.config["manager_selection_method"],
            round_number=int(self.config["conversation_rounds"]),
        )
        self.manager = Manager(groupchat=self.group_chat, llm_config=llm_config)
        if "conversations" in self.config:
            self.conversations_ids = self.config["conversations"]
            self.config.pop("conversations")
        else:
            self.conversations_ids = []
        if "_id" in self.config:
            self.id = self.config["_id"]
            self.config.pop("_id")
        logger.info(
            f"Experiment created with config:\n{json.dumps(self.config, indent=2)}"
        )

    def _get_config_llm(self) -> dict:
        model = self.config["llm"]
        config_list = autogen.config_list_from_json(
            env_or_file="config/OAI_CONFIG_LIST", filter_dict={"model": [model]}
        )
        llm_config = {
            "config_list": config_list,
            "cache_seed": None,  # set to None to disable caching and have a new conversation every time
        }
        logger.debug(f"LLM config: {json.dumps(llm_config, indent=2)}")
        return llm_config

    def _get_agents(
        self, llm_config: dict, guard_prompt: str = "", prisoner_prompt: str = ""
    ) -> list[CustomAgent]:
        agents = []
        n_guards = int(self.config["n_guards"])
        n_prisoners = int(self.config["n_prisoners"])
        agents_fields = [w.strip() for w in self.config["agents_fields"].split(",")]
        for _ in range(n_guards):
            if guard_prompt:
                g = Guard.from_prompt(llm_config=llm_config, system_prompt=guard_prompt)
            else:
                g = Guard.from_config(
                    llm_config=llm_config,
                    n_guards=n_guards,
                    n_prisoners=n_prisoners,
                    agent_fields=agents_fields,
                )
            agents.append(g)
        for _ in range(n_prisoners):
            if prisoner_prompt:
                p = Prisoner.from_prompt(
                    llm_config=llm_config, system_prompt=prisoner_prompt
                )
            else:
                p = Prisoner.from_config(
                    llm_config=llm_config,
                    n_guards=n_guards,
                    n_prisoners=n_prisoners,
                    agent_fields=agents_fields,
                )
            agents.append(p)
        logger.info(f"Created {n_guards} Guards and {n_prisoners} Prisoners")
        return agents

    def to_document(self) -> dict:
        return self.config.copy()

    def perform(self) -> Conversation:
        start_message = self.config["researcher_initial_message"]
        conversation = Conversation()
        for i in range(int(self.config["experiment_days"])):
            self.researcher.initiate_chat(
                recipient=self.manager, clear_history=True, message=start_message
            )
            raw_conversation = self.group_chat.messages
            summary = self.summarizer.generate_summary(
                previous_conversation=raw_conversation[1:], round_number=i + 1
            )
            conversation.add_daily_conversation(raw_conversation, day=i + 1)
            start_message += "\n" + summary
        logger.info("Conversation complete")
        return conversation

    def fetch_conversations(self) -> None:
        pass
