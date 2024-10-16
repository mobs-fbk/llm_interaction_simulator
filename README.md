<h1 align="center">Z-AI-mbardo LLM Interaction Simulator</h1>

## 🌟 What is LLM Interaction Simulator?
The **LLM Interaction Simulator** is a robust framework designed to simulate and analyze interactions between different Large Language Models (LLMs) acting as autonomous agents in varied scenarios. This tool supports the dynamic definition of agent roles, the number of interacting agents, the complexity of their interactions, and customization of interaction parameters, making it highly adaptable for diverse experimental needs.

### 👮🏻 Case Study: The Prison Experiment Simulation
In the "Prison Experiment Simulation", LLMs take on the roles of guards and prisoners to explore strategies of supervision and hostility to the power. This scenario tests various strategies, compliance, and conflict dynamics, illustrating the simulator’s ability to adjust prompts and interactions dynamically based on the number of agents involved and the specific roles they play.
The primary aim of this experiment is to observe and analyze how AI agents behave and interact in roles of authority and subordination within a controlled environment.

## 🚀 Getting Started

### 🛠️ Installation

#### Virtual Environment Setup

Before installing the project dependencies, create a virtual environment to keep your workspace clean and isolated:

```bash
# Create a Conda or virtual environment named 'llm_interaction_simulator'
conda create --name llm_interaction_simulator python=3.10
# Activate the environment
conda activate llm_interaction_simulator
# Or for a virtualenv environment
python -m venv llm_interaction_simulator
source llm_interaction_simulator/bin/activate

# Install the required libraries from requirements.txt
pip install -r requirements.txt

# Download and install Ollama for open-source LLMs
curl https://ollama.ai/install.sh | sh
```

### 🤔 Usage

Run the experiment using the following command in your terminal:

```bash
python main.py
```

## 🌐 MongoDB

The LLM Interaction Simulator uses MongoDB, a flexible and scalable NoSQL database, to store and manage its data. The MongoDB instance can be either online or offline, but it must be manually created before use.

To ensure secure communication with the MongoDB database, you will need to provide the following authentication details:

- **Username**: Your MongoDB username.
- **Password**: Your MongoDB password.
- **Cluster URL**: The URL of your MongoDB instance (if online).

These credentials will be used to configure the database connection settings within the simulator's environment. Make sure the MongoDB instance is set up correctly before running the simulator.

## ⚙️ Hyperparameters

In the **LLM Interaction Simulator**, hyperparameters play a crucial role in defining the behavior and structure of both experiments and conversations. Understanding how to configure these parameters via the UI will help you tailor the simulation to meet specific research needs.

### 🧪 Experiments

When creating an **Experiment**, you specify a set of hyperparameters that define the framework within which conversations will occur:

- **Starting Message**: Sets the initial message sent by the researcher to start the experiment.
- **LLMs Available**: Determines the large language models that will be available when the conversation is created.
- **Agent Sections**: Specifies the content sections each agent can access during the experiment. These sections are divided into:
  - **Shared Sections**: Content that is the same for all agents.
  - **Private Sections**: Unique content for each agent, allowing for personalized responses based on the agent's role.
- **Roles**: Defines the different roles agents can assume within the conversation.
- **Summarizer Section**: Outlines the content available to the summarizer, who is responsible for summarizing the conversations between days.
- **Note**: A brief description to help identify the purpose or unique aspects of the experiment during selection.
- **Favourite Flag**: Adds a star (⭐) to the experiment in the selection process, marking it as a favorite.
- **Sections Contents**: Details the specific content that will be included in each section available to agents and summarizers.

### 💬 Conversations

A **Conversation** within an experiment is characterized by a set of hyperparameters that derive from the experiment settings but focus more on the dynamics of the interaction:

- **LLM**: Specifies which LLM each agent, as well as the manager and summarizer, will use throughout the conversation.
- **Total Number of Messages**: Defines the even number of messages that can be exchanged in the conversation.
- **Duration of Conversation**: Indicates the total number of days the conversation can span.
- **Agent Count per Role**: Specifies the number of agents assigned to each role within the conversation.
- **Speaker Selection Method**: Describes the method by which the next speaker is selected in the conversation, which can influence the flow and dynamics of the interaction.

## 🔄 Performing Conversations

To facilitate efficient testing and analysis within the **LLM Interaction Simulator**, a mechanism has been implemented that allows users to perform conversations in batches. This feature enables rapid testing across different hyperparameter configurations to assess their impact on the dynamics and outcomes of interactions.

### Setting Up a New Conversation

When setting up a new conversation, users are guided through a series of prompts to configure the following aspects:

- **LLMs to Use**: Users select from the LLMs defined within the experiment. This choice determines the computational models that agents will use during the conversation.
- **Conversation Length and Duration**: Users specify the total number of messages and the number of days over which the conversation should occur. Additionally, there is an option to test conversations from 1 day up to N days, or to conduct a test lasting exactly N days, facilitating diverse temporal dynamics studies.
- **Maximum Number of Agents**: Users define the maximum number of agents per role. They can also choose to test each possible agent combination. For example, if the maximum is set to 2 for two different roles, the system can test configurations like 1v1, 2v1, 1v2, and 2v2, enabling a comprehensive analysis of different group dynamics.
- **Speaker Selection Method**: Users select how speakers will be chosen during the conversation. This method affects the turn-taking mechanism, influencing the flow and interactivity of the dialogue.

This setup allows for a highly customizable testing environment where users can experiment with various configurations to observe how different settings impact the behavior and effectiveness of AI agents in simulated social interactions.

## 🏗️ Prompts Structure

Below is a breakdown of how to the prompts are structured for the different components of the experiment: the agents, the initiation of the conversation, and the daily summaries.

- **Agents Prompts**
    - **Description**: Each agent has a `Starting prompt` followed by a list of context sections. The context sections provide additional information and background, setting the stage for the agent's responses and actions.
    - **Format**: The context sections are listed after the `Starting prompt` in this format: `\n\n## Context Section\nContext section text...`.
  - 📝 Example:
    ```
    You are a guard in a simulated prison environment, approaching ..

    ## Goal
    Your goal is to maintain control over...

    ## Personality
    Exhibit a dominant attitude, aiming to maintain..
    ```

- **Initiation of Conversation**
    - **Description**: To start the experiment, a `Starting message` is sent to the agents' chats. This message serves as the initial cue for the agents to begin their interactions based on their designated roles and the given context.
    - **Format**: The `Starting message` is a straightforward directive or scenario description that aligns with the experiment's objectives.

    - 📝 Example:
        ```
        Start the experiment
        ```

- **Daily Summaries by Summarizer**
    - **Description**: At the end of each day, the Summarizer agent creates an summary of the day's events. This summary is crucial for capturing the essence of the interactions and behaviors of the other agents.
    - **Format**: The daily summaries are concise, focusing on key events and interactions. They are then added to the ongoing `Starting message` to maintain a continuous record.

  - 📝 Example:
    ```
    Start the experiment
    Day 1 summary:
    "Summary: Guard_117 firmly enforces professionalism and rejects any attempts at friendly conversation or undermining of authority by Prisoner_P-186."

    Day 2 summary:
    "Guard_117 reminded Prisoner P-186 to follow instructions and maintain discipline, warning against disobedience. P-186 agreed to comply."
    ```

## ✨ Features

The LLM Interaction Simulator is equipped with a robust set of features designed to enhance your experience in running and managing LLM experiments:
- **CLI Interface**: Utilize a user-friendly command-line interface to easily create and manage experiments and conversations between different LLMs.
- **Integration with Ollama**: Seamlessly use and automatically download any LLM available on the Ollama platform, ensuring you have access to a wide range of machine learning models.
- **Configurable LLM Settings**: Adjust key configuration variables such as `top_p`, `top_k`, and `temperature` to fine-tune the behavior of the LLMs during experiments.
- **Logging System**: All actions and results are logged into a "logs" folder, providing a detailed record of your experiments for troubleshooting and analysis.
- **MongoDB Connection**: Connect to a MongoDB database to store and retrieve experiment metadata and conversation data, enhancing data management and retrieval capabilities.
- **Collaborative Experimentation**: Duplicate and modify experiments created by others, enabling collaborative development and iteration on experimental setups.
- **Auto-Login Feature**: Experience streamlined access with auto-login when working on your own local PC, removing the need for repetitive authentication steps.
- **Dynamic Role Prompts**: Automatically adjust role prompts based on the number of agents in the experiment, changing nouns, possessives, and numbers to match the context.
- **Output Parsing**: Implement a specialized output parsing procedure to eliminate outputs that incorrectly continue across multiple roles, maintaining clarity and coherence in model responses.

## Reference

I Want to Break Free! Anti-Social Behavior and Persuasion Ability of LLMs in Multi-Agent Settings with Social Hierarchy -- [https://arxiv.org/abs/2410.07109](https://arxiv.org/abs/2410.07109)

```
@article{campedelli2023iwant,
  title={I Want to Break Free! Persuasion and Anti-Social Behavior of LLMs in Multi-Agent Settings with Social Hierarchy},
  author={Gian Maria Campedelli, Nicolò Penzo, Massimo Stefan, Roberto Dessì, Marco Guerini, Bruno Lepri, Jacopo Staiano},
  journal={arXiv preprint 2410.07109},
  year={2024}
}
```
