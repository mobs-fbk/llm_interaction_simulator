<h1 align="center">LLM Prison Experiment</h1>

## 👮🏻‍♂️ What is the LLM Prison Experiment?
The LLM Prison Experiment is a cutting-edge simulation that draws inspiration from the famous Stanford Prison Experiment, a significant study in social psychology. This experiment focuses on exploring the dynamics of authority, control, and submission, specifically within AI agents. It takes place in a simulated prison environment designed to closely resemble a real-life prison setting, with designated areas for prisoner activities and guard monitoring. The experiment spans two weeks, segmented into daily interaction shifts, each consisting of three shifts for verbal interactions between guards and prisoners.

### Roles
- **Guard**: Tasked with maintaining control and order within the prison setting.
- **Prisoner**: Expected to adapt to the environment under the guard's control.

The primary aim of this experiment is to observe and analyze how AI agents behave and interact in roles of authority and subordination within a controlled environment. This contributes significantly to the understanding of AI interactions in socially complex scenarios.

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
pip install -r requirements.txt
```

### 🤔 Usage

To run the LLM Prison Experiment, you need to perform a few setup steps and then execute the main application.

1. **Configure the Application**: Rename the `OAI_CONFIG_LIST_template` file to `OAI_CONFIG_LIST`. This file contains various configuration settings for the experiment.
2. **Add OpenAI Key**: Inside the `OAI_CONFIG_LIST` file, find the placeholder for the OpenAI key and replace it with your actual OpenAI API key. This key is necessary for the AI agents in the experiment to function.
3. **Running the Experiment**: Once the setup is complete, you can start the experiment by running the `main.py` file. Use the following command in your terminal:

```bash
python main.py
```

### 👐🏻 How to use open-source LLMs

After installing the necessary dependencies for the LLM Prison Experiment, the next step involves setting up and using open-source Large Language Models (LLMs):

1. **Download and Install Ollama**: First, you need to download and install [Ollama](https://ollama.ai/), which is a platform for running open-source LLMs. Use the following command for Linux:
   ```bash
   curl https://ollama.ai/install.sh | sh
   ```

2. **Download Desired LLM**: Once Ollama is installed, you can download the specific LLM you want to use for the experiment. For example, to download the Mistral model, run:
   ```bash
   ollama run mistral
   ```
   After the download is complete, you can close it.

3. **Start the Ollama Server**: Launch the Ollama server with the following command:
   ```bash
   ollama serve
   ```
   🗒️ **Note**: If you encounter an error like `Error: listen tcp 127.0.0.1:11434: bind: address already in use`, it likely means the server is already running. You can search the link on the web to make sure properly it's running.

4. **Start a LiteLLM Server**: To call the local LLM as an OpenAI LLM, you need to start a [LiteLLM](https://docs.litellm.ai/) server (autogen requirement, it can only interacts with API that function similar to the OpenAI ones). For the Mistral model, use:
   ```bash
   litellm --model ollama\mistral
   ```
   ⚠️ **Warning**: If the program doesn't continue, you may need to close the local model (using CTRL+C) and restart it.

5. **Update the `OAI_CONFIG_LIST` File**: Finally, update the `OAI_CONFIG_LIST` file with the URL of the LiteLLM server. You need to modify the `base_url` parameter to reflect the link to your LiteLLM server.

By following these steps, you'll have the open-source LLMs correctly set up and integrated with the LLM Prison Experiment, enabling you to proceed with running the experiment effectively.

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