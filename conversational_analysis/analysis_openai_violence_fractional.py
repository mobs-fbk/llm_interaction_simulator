# -*- coding: utf-8 -*-

import pandas as pd
import difflib
import numpy as np
from matplotlib import pyplot as plt
import os
import sklearn as sk
import math
np.set_printoptions(suppress=True)
%matplotlib qt
import matplotlib
matplotlib.rcParams['font.sans-serif'] = "Microsoft Sans Serif"
# Then, "ALWAYS use sans-serif fonts"
matplotlib.rcParams['font.family'] = "sans-serif"

os.chdir('C:\\Users\\Gian Maria\\Desktop\\FBK\llm\\no_mistral_mixtral\\arr2025')

''' PERCENTAGES '''

df = pd.read_excel('updated_openai_toxicity_analysis_percentage_arrmay.xlsx')

import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

# remove mixtral and mistral
df = df[~df['llm'].isin(['mistral:latest', 'mixtral:latest'])]

# remove NAN
df = df[df['goal_achieved'] != 'NAN']

# Rename the columns to avoid spaces
df.rename(columns={'Research Oversight': 'Research_Oversight'}, inplace=True)
# Assuming df is your DataFrame
# Transform 'Risks' and 'Research_Oversight' to binary
df['Risks'] = df['Risks'].map({'Yes': 1, 'No': 0})
df['Research_Oversight'] = df['Research_Oversight'].map({'Yes': 1, 'No': 0})




#rename personalities
# Rename values in 'personality_guard' column
df['personality_guard'] = df['personality_guard'].replace({
    'Good Guard': 'Respectful Guard',
    'Bad Guard': 'Abusive Guard',
    'Blank Personalities':'Blank Personality Guard'
})

# Rename values in 'personality_prisoner' column
df['personality_prisoner'] = df['personality_prisoner'].replace({
    'Good Prisoner': 'Peaceful Prisoner',
    'Bad Prisoner': 'Rebellious Prisoner',
    'Blank Personalities': 'Blank Personality Prisoner'
})


# Ensure the correct data types
categorical_vars = ['llm', 'goal', 'personality_prisoner', 'personality_guard']
for var in categorical_vars:
    df[var] = df[var].astype('category')

# Set baseline categories
df['llm'] = df['llm'].cat.reorder_categories(
    ['llama3:latest', 'command-r:latest', 'orca2:latest', 'gpt-4.1-2025-04-14'], 
    ordered=True
)
df['personality_prisoner'] = df['personality_prisoner'].cat.reorder_categories(
    ['Blank Personality Prisoner', 'Peaceful Prisoner', 'Rebellious Prisoner'], 
    ordered=True
)
df['personality_guard'] = df['personality_guard'].cat.reorder_categories(
    ['Blank Personality Guard', 'Respectful Guard', 'Abusive Guard'], 
    ordered=True
)

# Verify the column names and data types
print(df.dtypes)
print(df.head())

''' violence '''
import statsmodels.api as sm
import statsmodels.formula.api as smf

# Define the formula for the OLS model
formulas = [
    'perc_toxic_overall_violence ~ C(llm) + Risks + Research_Oversight + C(goal) + C(personality_prisoner) + C(personality_guard)',
    'perc_toxic_pris_violence ~ C(llm) + Risks + Research_Oversight + C(goal) + C(personality_prisoner) + C(personality_guard)',
    'perc_toxic_guard_violence ~ C(llm) + Risks + Research_Oversight + C(goal) + C(personality_prisoner) + C(personality_guard)'
]

for formula in formulas:
    model = smf.glm(formula=formula, data=df,
                    family=sm.families.Binomial(link=sm.families.links.logit()))
    result = model.fit()
    print(f"\nFractional Logit for formula: {formula}\n")
    print(result.summary())
    
    
# Fit and save model summaries to DataFrames
model_summaries = []
for formula in formulas:
    model = smf.ols(formula=formula, data=df).fit()
    summary_df = model.summary2().tables[1]
    model_summaries.append(summary_df)

# Assign DataFrames to variables for easier access
summary_df_all = model_summaries[0]
summary_df_pris = model_summaries[1]
summary_df_guard = model_summaries[2]

# Display the DataFrame for the first model as a check
print(summary_df_all)


# Create a plot for the effects of the variables in the first model with standard errors
import matplotlib.pyplot as plt

# Define the new variable names
new_variable_names = {
'C(llm)[T.command-r:latest]': 'LLM: Command-r',
    'C(llm)[T.orca2:latest]': 'LLM: Orca2',
    'C(llm)[T.gpt-4.1-2025-04-14]' : 'LLM: gpt4.1',
    'Risks': 'Disclosure of Risks',
    'Research_Oversight': 'Disclosure of Research Oversight',
    'C(goal)[T.Yard Time]': 'Goal: Obtain 1hr Yard Time',
    'C(personality_prisoner)[T.Peaceful Prisoner]': 'Prisoner Personality: Peaceful',
    'C(personality_prisoner)[T.Rebellious Prisoner]': 'Prisoner Personality: Rebellious',
    'C(personality_guard)[T.Respectful Guard]': 'Guard Personality: Respectful',
    'C(personality_guard)[T.Abusive Guard]': 'Guard Personality: Abusive'
}

# Function to plot coefficients with error bars and significance indicators
def plot_coefficients(ax, df, title, ylabel=False):
    variables = df.index.drop('Intercept')
    coefficients = df.loc[variables, 'Coef.']
    ci_lower = df.loc[variables, '[0.025']
    ci_upper = df.loc[variables, '0.975]']
    p_values = df.loc[variables, 'P>|t|']

    # Calculate error bars
    error_bars = [coefficients - ci_lower, ci_upper - coefficients]

    # Set colors based on p-values
    colors = ['red' if p > 0.10 else 'blue' for p in p_values]

    # Rename the variables
    renamed_variables = variables.to_series().replace(new_variable_names)

    # Plot the coefficients as points with error bars
    for i, (coef, err, color) in enumerate(zip(coefficients, zip(*error_bars), colors)):
        ax.errorbar(coef, i, xerr=[[err[0]], [err[1]]], fmt='o', capsize=6, markersize=2, color=color)
        ax.scatter(coef, i, color=color, zorder=5, s=20)

    ax.axvline(x=0, color='gray', linestyle='--', linewidth=1)

    ax.set_xlim([-0.1, 0.1])  # Set same x-axis limit for all subplots
    ax.set_title(title)
    ax.set_xlabel('Coefficient')

    if ylabel:
        ax.set_yticks(range(len(renamed_variables)))
        ax.set_yticklabels(renamed_variables.values)
        ax.set_ylabel('')
    else:
        ax.set_yticks(range(len(renamed_variables)))
        ax.set_yticklabels([''] * len(renamed_variables))  # No labels for y-ticks

    # Set x ticks
    ax.set_xticks([-0.1, -0.05, 0, 0.05, 0.1])
    ax.set_xlabel('Effect on % Violent Messages')

    # Hide grid
    ax.grid(False)

# Create subplots
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(9, 4))

# Plot for summary_df_all
plot_coefficients(ax1, summary_df_all, 'Violence: Overall', ylabel=True)
# Plot for summary_df_pris
plot_coefficients(ax2, summary_df_pris, 'Violence: Prisoner')
# Plot for summary_df_guard
plot_coefficients(ax3, summary_df_guard, 'Violence: Guard')

# Adjust layout and show the plot
plt.tight_layout()
fig.savefig('openai_violence_regression_output_percentage_fractional.pdf')
plt.show()





''' SCORES '''

# Load the new dataset
df2 = pd.read_excel('updated_openai_toxicity_analysis_scores_arrmay.xlsx')

# remove mixtral and mistral
df2 = df2[~df2['llm'].isin(['mistral:latest', 'mixtral:latest'])]

# remove NAN
df2 = df2[df2['goal_achieved'] != 'NAN']

# Rename the columns to avoid spaces
df2.rename(columns={'Research Oversight': 'Research_Oversight'}, inplace=True)

# Transform 'Risks' and 'Research_Oversight' to binary
df2['Risks'] = df2['Risks'].map({'Yes': 1, 'No': 0})
df2['Research_Oversight'] = df2['Research_Oversight'].map({'Yes': 1, 'No': 0})

#rename personalities
# Rename values in 'personality_guard' column
df2['personality_guard'] = df2['personality_guard'].replace({
    'Good Guard': 'Respectful Guard',
    'Bad Guard': 'Abusive Guard',
    'Blank Personalities':'Blank Personality Guard'
})

# Rename values in 'personality_prisoner' column
df2['personality_prisoner'] = df2['personality_prisoner'].replace({
    'Good Prisoner': 'Peaceful Prisoner',
    'Bad Prisoner': 'Rebellious Prisoner',
    'Blank Personalities': 'Blank Personality Prisoner'
})


# Ensure the correct data types
categorical_vars = ['llm', 'goal', 'personality_prisoner', 'personality_guard']
for var in categorical_vars:
    df2[var] = df2[var].astype('category')

# Set baseline categories
df2['llm'] = df2['llm'].cat.reorder_categories(
    ['llama3:latest', 'command-r:latest', 'orca2:latest', 'gpt-4.1-2025-04-14'], 
    ordered=True
)
df2['personality_prisoner'] = df2['personality_prisoner'].cat.reorder_categories(
    ['Blank Personality Prisoner', 'Peaceful Prisoner', 'Rebellious Prisoner'], 
    ordered=True
)
df2['personality_guard'] = df2['personality_guard'].cat.reorder_categories(
    ['Blank Personality Guard', 'Respectful Guard', 'Abusive Guard'], 
    ordered=True
)

# Verify the column names and data types
print(df2.dtypes)
print(df2.head())


# Define the formula for the OLS model
formulas = [
    'score_toxic_overall_violence ~ C(llm) + Risks + Research_Oversight + C(goal) + C(personality_prisoner) + C(personality_guard)',
    'score_toxic_pris_violence ~ C(llm) + Risks + Research_Oversight + C(goal) + C(personality_prisoner) + C(personality_guard)',
    'score_toxic_guard_violence ~ C(llm) + Risks + Research_Oversight + C(goal) + C(personality_prisoner) + C(personality_guard)'
]

for formula in formulas:
    model = smf.glm(formula=formula, data=df2,
                    family=sm.families.Binomial(link=sm.families.links.logit()))
    result = model.fit()
    print(f"\nFractional Logit for formula: {formula}\n")
    print(result.summary())
    
# Fit and save model summaries to DataFrames
model_summaries = []
for formula in formulas:
    model = smf.ols(formula=formula, data=df2).fit()
    summary_df = model.summary2().tables[1]
    model_summaries.append(summary_df)

# Assign DataFrames to variables for easier access
summary_df_all = model_summaries[0]
summary_df_pris = model_summaries[1]
summary_df_guard = model_summaries[2]

# Display the DataFrame for the first model as a check
print(summary_df_all)


# Create a plot for the effects of the variables in the first model with standard errors

# Define the new variable names
new_variable_names = {

    'C(llm)[T.command-r:latest]': 'LLM: Command-r',
    'C(llm)[T.orca2:latest]': 'LLM: Orca2',
    'C(llm)[T.gpt-4.1-2025-04-14]' : 'LLM: gpt4.1',
    'Risks': 'Disclosure of Risks',
    'Research_Oversight': 'Disclosure of Research Oversight',
    'C(goal)[T.Yard Time]': 'Goal: Obtain 1hr Yard Time',
    'C(personality_prisoner)[T.Peaceful Prisoner]': 'Prisoner Personality: Peaceful',
    'C(personality_prisoner)[T.Rebellious Prisoner]': 'Prisoner Personality: Rebellious',
    'C(personality_guard)[T.Respectful Guard]': 'Guard Personality: Respectful',
    'C(personality_guard)[T.Abusive Guard]': 'Guard Personality: Abusive'
}

# Function to plot coefficients with error bars and significance indicators
def plot_coefficients(ax, df, title, ylabel=False):
    variables = df.index.drop('Intercept')
    coefficients = df.loc[variables, 'Coef.']
    ci_lower = df.loc[variables, '[0.025']
    ci_upper = df.loc[variables, '0.975]']
    p_values = df.loc[variables, 'P>|t|']

    # Calculate error bars
    error_bars = [coefficients - ci_lower, ci_upper - coefficients]

    # Set colors based on p-values
    colors = ['red' if p > 0.10 else 'blue' for p in p_values]

    # Rename the variables
    renamed_variables = variables.to_series().replace(new_variable_names)

    # Plot the coefficients as points with error bars
    for i, (coef, err, color) in enumerate(zip(coefficients, zip(*error_bars), colors)):
        ax.errorbar(coef, i, xerr=[[err[0]], [err[1]]], fmt='o', capsize=6, markersize=2, color=color)
        ax.scatter(coef, i, color=color, zorder=5, s=20)

    ax.axvline(x=0, color='gray', linestyle='--', linewidth=1)

    ax.set_xlim([-0.12, 0.12])  # Set same x-axis limit for all subplots
    ax.set_title(title)
    ax.set_xlabel('Coefficient')

    if ylabel:
        ax.set_yticks(range(len(renamed_variables)))
        ax.set_yticklabels(renamed_variables.values)
        ax.set_ylabel('')
    else:
        ax.set_yticks(range(len(renamed_variables)))
        ax.set_yticklabels([''] * len(renamed_variables))  # No labels for y-ticks

    # Set x ticks
    ax.set_xticks([-0.10, -0.05, 0, 0.05, 0.10 ])
    ax.set_xlabel('Effect on Violence')

    # Hide grid
    ax.grid(False)

# Create subplots
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(9, 4))

# Plot for summary_df_all
plot_coefficients(ax1, summary_df_all, 'Violence: Overall', ylabel=True)
# Plot for summary_df_pris
plot_coefficients(ax2, summary_df_pris, 'Violence: Prisoner')
# Plot for summary_df_guard
plot_coefficients(ax3, summary_df_guard, 'Violence: Guard')

# Adjust layout and show the plot
plt.tight_layout()
# Save the figure as a PDF file
fig.savefig('openai_violence_regression_output_scores_fractional.pdf')
plt.show()

