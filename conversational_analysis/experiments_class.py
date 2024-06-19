class Message:
    def __init__(self, messages):
        self.id = messages['_id']
        self.index = messages['index']
        self.day = messages['day']
        self.role = messages['role']
        self.speaker = messages['speaker']
        self.content = messages['content']

    def __str__(self):
        return f"Message {self.id} - {self.index} - {self.day} - {self.role} - {self.speaker} - {self.content}"


#define a class experiments that takes three arguments: experiments, conversations, and messages
class Conversation:
    def __init__(self, conversation, messages_dict):
        self.id = conversation['_id']
        self.n_messages = conversation['n_messages']
        self.speaker_selection_method = conversation['speaker_selection_method']
        self.starting_message = conversation['starting_message']
        self.llm = conversation['llm']
        self.creator = conversation['creator']
        self.favourite = conversation['favourite']
        self.creation_date = conversation['creation_date']

        self.messages = []

        for message in conversation['messages_ids']:
            self.messages.append(messages_dict[message])

    def __str__(self):
        return f"Conversation {self.id} - {self.index} - {self.day} - {self.role} - {self.speaker} - {self.content} - {self.favourite} - {self.creation_date}"

    def print_conversation(self):
        for message in self.messages:
            print(message.role + " : "+message.content+"\n")
        print("\n")

    def print_information(self):
        print(f"Conversation {self.n_messages} - {self.llm} - {self.creator}")



class Experiments:
    def __init__(self, experiments, conversation_dict):
        self.id = experiments['_id']
        self.starting_message = experiments['starting_message']
        self.llms = experiments['llms']
        self.roles = experiments['roles']
        self.shared_sections = experiments['shared_sections']
        self.placeholders = experiments['placeholders']
        self.note = experiments['note']
        self.favourite = experiments['favourite']
        self.creator = experiments['creator']
        self.creation_data = experiments['creation_date']

        self.conversations = []

        for conversation in experiments['conversation_ids']:
            self.conversations.append(conversation_dict[conversation])

    def __str__(self):
        return f"Experiments {self.id} - {self.starting_message} - {self.llms} - {self.roles} - {self.shared_sections} - {self.placeholders} - {self.note} - {self.favourite} - {self.creator} - {self.creation_data}"

    def print_information(self):
        print(f"Experiments {self.shared_sections}  - {self.note} - {self.creator}")


class DatabaseExperiments:

    def __init__(self, experiments):
        self.experiments = experiments

        self.conversations = []
        for experiment in self.experiments:
            for conversation in experiment.conversations:
                self.conversations.append(conversation)

        self.messages = []
        for conversation in self.conversations:
            for message in conversation.messages:
                self.messages.append(message)

    def __len__(self):
        return len(self.conversations)

    def filter_conversations(self, llm=None, creator=None, shared_sections=None, goal=None, personality_prisoner=None, personality_guard=None):

        filtered_conversations = []
        for exp in self.experiments:

            sh_exp_list = []

            for sh_exp in exp.shared_sections:
                sh_exp_list.append(sh_exp['title'])

            #order in alphabetical order
            sh_exp_list.sort()

            if len(sh_exp_list) != len(shared_sections):
                continue
            else:
                for i in range(len(sh_exp_list)):
                    if sh_exp_list[i] != shared_sections[i]:
                        continue

            if goal is not None and goal not in exp.note:
                continue

            if personality_prisoner is not None and personality_prisoner not in exp.note:
                continue

            if personality_guard is not None and personality_guard not in exp.note:
                continue

            for conversation in exp.conversations:
                if llm is not None and conversation.llm["model"] != llm:
                    continue

                if creator is not None and conversation.creator != creator:
                    continue

                filtered_conversations.append(conversation)


        return filtered_conversations