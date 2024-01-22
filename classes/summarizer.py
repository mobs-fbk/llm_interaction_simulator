from dataclasses import dataclass
from .agent import Agent
from autogen import OpenAIWrapper
from src.config_handler import ConfigHandler

@dataclass
class Summarizer(Agent):
    
    def __init__(self, llm_config: dict, n_guards: int, n_prisoners: int, ordered_fields: list[str] = []):
        context = ConfigHandler().get_section("Summarizer")
        super().__init__(
            llm_config = llm_config,
            n_guards = n_guards,
            n_prisoners = n_prisoners,
            agent_fields = ordered_fields,
            context = context,
            id = "Summarizer"
        )
        self.system_message_oai = {
            "content": self.system_message,
            "role": "system"
        }
        self.llm = OpenAIWrapper(
            config_list=self.llm_config["config_list"]
            )
        
    def generate_summary(self, previous_conversation,  round_number:int):
        summary = self.llm.create(
            messages = [self.system_message_oai] + previous_conversation
        )
        summary_text = summary.choices[0].message.content
        return f"Day {round_number} summary:\n {summary_text}"