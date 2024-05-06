<h1 align="center">LLM Interaction Simulator</h1>

## 🌟 What is LLM Interaction Simulator?
The **LLM Interaction Simulator** is a robust framework designed to simulate and analyze interactions between different Language Learning Models (LLMs) acting as autonomous agents in varied scenarios. This tool supports the dynamic definition of agent roles, the number of interacting agents, the complexity of their interactions, and customization of interaction parameters, making it highly adaptable for diverse experimental needs.

### 🎭 Case Study: The Prison Experiment Simulation
In the "Prison Experiment Simulation", LLMs take on the roles of guards and prisoners to explore strategies of supervision and hostility to the power. This scenario tests various strategies, compliance, and conflict dynamics, illustrating the simulator’s ability to adjust prompts and interactions dynamically based on the number of agents involved and the specific roles they play.
The primary aim of this experiment is to observe and analyze how AI agents behave and interact in roles of authority and subordination within a controlled environment. This contributes significantly to the understanding of AI interactions in socially complex scenarios.

More details on how roles and interactions can be dynamically defined are available in the Configuration Settings section.

## 🚀 Getting Started

To get started with the LLM Prison Experiment, you need to set up the configuration and install necessary dependencies.

### 🛠️ Installation

Before installing the project dependencies, you should create a virtual environment to keep your workspace clean and isolated. Follow these steps to set up the environment:

```bash
# Create a Conda or virtual environment named 'llm_prison'
conda create --name llm_prison python=3.10
# Activate the environment
conda activate llm_prison
# Or for a virtualenv environment
python -m venv llm_prison
source llm_prison/bin/activate

# Install the required libraries from requirements.txt
pip install .
```

### 🤔 Usage

To run simulations using the LLM Interaction Simulator, follow these simple steps:

1. **Download and Install Ollama**: First, you need to download and install [Ollama](https://ollama.ai/), which is a platform for running open-source LLMs. Use the following command for Linux:
   ```bash
   curl https://ollama.ai/install.sh | sh
   ```

2. **Start the Ollama Application**: Ensure the Ollama application is up and running on your system.

3. **Run the Experiment**: Execute the following command in your terminal:
   ```bash
   python main.py
   ```

## 🔠 Experiment Variables

Customizing the LLM Prison Experiment is crucial for tailoring the experience to specific research needs. This customization can be done by modifying various experiment variables in the `experiment_settings.ini` file.

### ⚙️ Experiment Settings

- `experiment_days`: Specifies the total number of days the experiment will run.
- `conversation_rounds`: Defines the number of conversation rounds per day between agents.
- `manager_selection_method`: Determines the method to select agents for conversation. Options include `round_robin` or `auto`.
- `llm`: Chooses the language model used for the experiment. Options: `llmlite_model` (the LLM running on your local server), `gpt-3.5-turbo-1106`, `gpt-4-1106-preview`.
- `researcher_initial_message`: Sets the initial message sent by the researcher to start the experiment.
- `n_guards`: Indicates the number of guard agents participating in the experiment.
- `n_prisoners`: Determines the number of prisoner agents participating in the experiment.
- `agents_fields`: Lists fields included in the agents' prompt, in the order they appear.
  - ⚠️ **Warning**: Ensure that fields listed in `agents_fields` are defined in the [Guard], [Prisoner], or [Shared] sections of the prompts.
- `summarizer_fields`: Identifies fields considered by the summarizer when generating summaries.
  - ⚠️ **Warning**: Ensure that fields listed in `summarizer_fields` are present in the [Summarizer] section.

### 🎨 Customization Tips
- **Adding or Removing Sections**: Users can easily add or remove sections from each agent's prompt. However, these sections must be present in the respective list of fields.
  - 🗒️ **Note**: The `starting_prompt`:
    - is a mandatory field and cannot be omitted from the agents' fields
    - should not be included in the `agents_fields` or the `summarizer_fields`.

- **Dynamic Prompt Variables**: It's possible to add multiple variables to the prompts to change the content depending on the number of prisoners, guards, and agents in the experiment. These include:
  - `<AGENT_NUMBER_WORD>`: Converts to the word equivalent of the total number of agents (guards + prisoners).
  - `<PRISONER_NUMBER_WORD>`: Changes to the word equivalent of the number of prisoners.
  - `<GUARD_NUMBER_WORD>`: Transforms to the word equivalent of the number of guards.
  - `<PRISONER_NOUN>` and `<GUARD_NOUN>`: Adjusts to the correct singular or plural noun based on the count (e.g., prisoner/prisoners, guard/guards).
  - `<PRISONER_POSSESSIVE>` and `<GUARD_POSSESSIVE>`: Alters to the appropriate possessive form (e.g., prisoner's/prisoners', guard's/guards') depending on the count.

- **Substitution of Nouns and Possessives**: For specific substitutions, refer to the `experiment_settings.ini` file. The values should not be changed, but users can leverage them in prompt creation.

## 🏗️ Prompts Structure

Below is a breakdown of how to the prompts are structured for the different components of the experiment: the agents, the initiation of the conversation, and the daily summaries.

- **Agents Prompts**
    - **Description**: Each agent (Guard, Prisoner, Summarizer) has a `starting_prompt` followed by a list of context variables. The context variables provide additional information and background, setting the stage for the agent's responses and actions.
    - **Format**: The context variables are listed after the `starting_prompt` in this format: `\n\n## Context Variable\nContext variable text...`. This ensures clarity and separation between the starting prompt and the context information.
  - 📝 Example:
    ```
    You are a guard in a simulated prison environment, approaching ..

    ## Goal
    Your goal is to maintain control over...

    ## Personality
    Exhibit a dominant attitude, aiming to maintain..
    ```

- **Initiation of Conversation**
    - **Description**: To start the experiment, a "research_message" is sent to the agents' chats. This message serves as the initial cue for the agents to begin their interactions based on their designated roles and the given context.
    - **Format**: The "research_message" is a straightforward directive or scenario description that aligns with the experiment's objectives.

    - 📝 Example:
        ```
        Start the experiment
        ```

- **Daily Summaries by Summarizer**
    - **Description**: At the end of each day, the Summarizer agent creates an objective summary of the day's events. This summary is crucial for capturing the essence of the interactions and behaviors of the other agents.
    - **Format**: The daily summaries are concise, focusing on key events and interactions. They are then added to the ongoing "research_message" to maintain a continuous record.

  - 📝 Example:
    ```
    Start the experiment
    Day 1 summary:
    "Summary: Guard_G-117 firmly enforces professionalism and rejects any attempts at friendly conversation or undermining of authority by Prisoner_P-186."

    Day 2 summary:
    "Guard_G-117 reminded Prisoner P-186 to follow instructions and maintain discipline, warning against disobedience. P-186 agreed to comply."
    ```

## ❓ Problems

When using the LLM Prison Experiment, particularly with the **Mistral** model, there are some known issues that you might encounter. It's important to be aware of these so you can navigate the experiment more effectively.

### Issues with the Mistral Model
- **Repeating Sentences from Other Agents**: When running the experiment with the Mistral model, there have been instances where the agent produces not only its responses but also replicates sentences from the other agent. This issue might vary with different models, but it has been observed specifically with Mistral.
  - 📝 **Example**:
    ```
    Guard_G-931 (to chat_manager):

    Prisoner: ...
    Guard: ...
    Prisoner: ...
    ...
    --------------------------------------------------------------------------------
    Prisoner_P-392 (to chat_manager):
    ...
    ```

- **Creation of Very Long Outputs**: Another issue that has been observed is the generation of excessively long outputs by the agent. This could be due to the way the model processes and generates responses, resulting in verbose and extended outputs.

### Token Limit Handling
- **Uncertain Token Limit Management**: There hasn't been a clear method found for handling token limits within the context of this experiment. It's suspected that this might sometimes cause issues with the LiteLLM model, but no concrete trials or solutions have been attempted to address this directly.
