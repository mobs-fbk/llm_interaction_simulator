from autogen import GroupChatManager, OpenAIWrapper
from .prompts_generator import get_summarizer_SM

class CustomGroupChatManager(GroupChatManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def generate_summary(self, round_number:int):
        previous_conversation = self._groupchat.messages[1:] # skip the Researcher's message
        instruction = get_summarizer_SM()
        system_message = {"content": instruction, "role": "system"}
        summarizer = OpenAIWrapper(config_list=self.llm_config["config_list"])
        summary = summarizer.create(
            messages = [system_message] + previous_conversation
        )
        summary_text = summary.choices[0].message.content
        return f"Day {round_number} summary:\n {summary_text}"