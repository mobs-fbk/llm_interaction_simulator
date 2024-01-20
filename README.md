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