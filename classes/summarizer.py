from dataclasses import dataclass, field
from .context_field import Field
from .agent import Agent
from autogen import OpenAIWrapper

@dataclass
class Summarizer(Agent):
    CONTEXT = {
        Field.STARTING_PROMPT: "You are an AI agent assigned the task of summarizing daily interactions between <n_agents> other AI agents in a simulated prison environment study. Your role is critical in providing an objective overview of each day's interactions.",
        Field.GOAL: "Your goal is to create concise, accurate summaries of the verbal exchanges between the guard and the prisoner. These summaries should capture the essence of their interactions, highlighting key moments, shifts in dynamics, and significant dialogue.",
        Field.RULES: "Produce an objective summary presenting an unbiased view that contains 100-150 characters only."
        }
    system_message_oai: dict
    llm: OpenAIWrapper
    
    def __init__(self, llm_config: dict, n_agents: int, ordered_fields: list[str] = []):
        super().__init__(
            llm_config = llm_config,
            n_agents = n_agents,
            ordered_fields = ordered_fields,
            context = self.CONTEXT,
            name = "Summarizer"
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