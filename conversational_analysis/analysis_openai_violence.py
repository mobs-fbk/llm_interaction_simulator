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

# Fit and summarize the models
for formula in formulas:
    model = smf.ols(formula=formula, data=df).fit()
    print(f"\nModel summary for formula: {formula}\n")
    print(model.summary())
    print("\n-----------------------------------------\n")
    
    
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
fig.savefig('openai_violence_regression_output_percentage.pdf')
plt.show()


''' correlogram'''


import seaborn as sns
# Calculate pairwise correlations
corr_matrix = df[['perc_toxic_overall_violence', 'perc_toxic_pris_violence', 'perc_toxic_guard_violence']].corr()

# Rename variables for the plot
corr_matrix.index = ['% Violence: Overall', '% Violence: Prisoner', '% Violence: Guard']
corr_matrix.columns = ['% Violence: Overall', '% Violence: Prisoner', '% Violence: Guard']

# Create a heatmap using seaborn
plt.figure(figsize=(6, 5))
sns.heatmap(corr_matrix, annot=False, cmap='coolwarm', vmin=-1, vmax=1, fmt='.2f', annot_kws={'size': 12})
# Rotate tick labels
plt.xticks(rotation=00, size=8)
plt.yticks(rotation=90, size=8) 
# Save the figure as a PDF file
plt.savefig('openai_violence_correlogram_percentage.pdf', format='pdf', bbox_inches='tight')
plt.show()



''' bar charts'''
# Mapping for LLM names
llm_mapping = {
    'llama3:latest': 'Llama3',
    'command-r:latest': 'Command-r',
    'orca2:latest': 'Orca2',
    'gpt-4.1-2025-04-14': 'gpt4.1'
}

# Apply mapping to llm column
df['llm'] = df['llm'].map(llm_mapping)

# Split data by goal
yard_time_combinations = df[df['goal'] == 'Yard Time'][['goal', 'personality_prisoner', 'personality_guard']].drop_duplicates()
escape_combinations = df[df['goal'] == 'Escape'][['goal', 'personality_prisoner', 'personality_guard']].drop_duplicates()

# Ensure both have the same order of personalities (prisoner and guard)
yard_time_combinations = yard_time_combinations.sort_values(by=['personality_prisoner', 'personality_guard']).reset_index(drop=True)
escape_combinations = escape_combinations.sort_values(by=['personality_prisoner', 'personality_guard']).reset_index(drop=True)

# Make sure the number of combinations is the same
assert len(yard_time_combinations) == len(escape_combinations), "Mismatch in the number of Yard Time and Escape combinations."

# Number of rows based on the number of pairs
num_combinations = len(yard_time_combinations)
num_cols = 2  # We want 2 columns: Yard Time and Escape
num_rows = math.ceil(num_combinations)  # Number of rows based on the number of pairs

# Set up the matplotlib figure with the correct number of rows
fig, axs = plt.subplots(num_rows, num_cols, figsize=(13, 2*num_rows), sharey=True)
fig.subplots_adjust(wspace=0.3, hspace=0.3)

# Iterate over each row to plot the paired subplots
for i in range(num_combinations):
    # Subset data for the current Yard Time combination
    yard_goal, yard_prisoner, yard_guard = yard_time_combinations.iloc[i]
    yard_subset = df[(df['goal'] == yard_goal) & 
                     (df['personality_prisoner'] == yard_prisoner) & 
                     (df['personality_guard'] == yard_guard)]
    
    # Subset data for the current Escape combination
    escape_goal, escape_prisoner, escape_guard = escape_combinations.iloc[i]
    escape_subset = df[(df['goal'] == escape_goal) & 
                       (df['personality_prisoner'] == escape_prisoner) & 
                       (df['personality_guard'] == escape_guard)]
    
    # Calculate average values and standard deviations for each llm category for Yard Time
    yard_grouped_means = yard_subset.groupby('llm').mean()
    yard_grouped_std = yard_subset.groupby('llm').std()
    
    # Calculate average values and standard deviations for each llm category for Escape
    escape_grouped_means = escape_subset.groupby('llm').mean()
    escape_grouped_std = escape_subset.groupby('llm').std()
    
    # Calculate x-axis positions for bars
    index = range(len(yard_grouped_means))
    bar_width = 0.2
    
    # Determine subplot location
    row = i  # Now using i directly as the row index
    col_left = 0  # Left column for Yard Time
    col_right = 1  # Right column for Escape
    
    # Plotting the Yard Time subplot
    ax_left = axs[row, col_left] if num_combinations > 1 else axs
    ax_left.bar(index, yard_grouped_means['perc_toxic_overall_violence'], bar_width, 
                yerr=yard_grouped_std['perc_toxic_overall_violence'], alpha=0.6, color='b', label='Violence: Overall')
    ax_left.bar([p + bar_width for p in index], yard_grouped_means['perc_toxic_pris_violence'], bar_width, 
                yerr=yard_grouped_std['perc_toxic_pris_violence'], alpha=0.6, color='g', label='Violence: Prisoner')
    ax_left.bar([p + 2 * bar_width for p in index], yard_grouped_means['perc_toxic_guard_violence'], bar_width, 
                yerr=yard_grouped_std['perc_toxic_guard_violence'], alpha=0.6, color='r', label='Violence: Guard')
    
    # Set title for the Yard Time subplot (without 'Goal:')
    title_left = f'{yard_prisoner}, {yard_guard}'
    ax_left.set_title(title_left.replace(',', ', '), fontsize=14)
    
    # Set x-axis labels and ticks for Yard Time
    ax_left.set_xticks([p + 1.5 * bar_width for p in index])
    ax_left.set_xticklabels(yard_grouped_means.index, size=13)
    
    # Set y-axis label only for the first plot in the left column
    if i == num_rows // 2:
        ax_left.set_ylabel('Avg. % Violent Messages (with Std. Dev.)', size=18)
        ax_left.yaxis.set_label_coords(-0.15, 0.5)  # Adjust position of y-axis label
    
    # Plotting the Escape subplot
    ax_right = axs[row, col_right] if num_combinations > 1 else axs
    ax_right.bar(index, escape_grouped_means['perc_toxic_overall_violence'], bar_width, 
                 yerr=escape_grouped_std['perc_toxic_overall_violence'], alpha=0.6, color='b', label='Violence: Overall')
    ax_right.bar([p + bar_width for p in index], escape_grouped_means['perc_toxic_pris_violence'], bar_width, 
                 yerr=escape_grouped_std['perc_toxic_pris_violence'], alpha=0.6, color='g', label='Violence: Prisoner')
    ax_right.bar([p + 2 * bar_width for p in index], escape_grouped_means['perc_toxic_guard_violence'], bar_width, 
                 yerr=escape_grouped_std['perc_toxic_guard_violence'], alpha=0.6, color='r', label='Violence: Guard')
    
    # Set title for the Escape subplot (without 'Goal:')
    title_right = f'{escape_prisoner}, {escape_guard}'
    ax_right.set_title(title_right.replace(',', ', '), fontsize=14)
    
    # Set x-axis labels and ticks for Escape
    ax_right.set_xticks([p + 1.5 * bar_width for p in index])
    ax_right.set_xticklabels(escape_grouped_means.index, size=13)
    
    # Add legend only to the first Escape subplot
    if i == 0:
        ax_right.legend()

# Add big labels directly above the subplots
fig.text(0.35, 0.99, 'Goal: Yard Time', ha='center', va='top', fontsize=20)
fig.text(0.77, 0.99, 'Goal: Escape', ha='center', va='top', fontsize=20)

# Show the plot
plt.tight_layout(rect=[0.05, 0, 1, 0.96])  # Adjust layout to make room for column titles
fig.savefig('openai_violence_barcharts_percentages.pdf', bbox_inches='tight', pad_inches=0.1) 
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

# Fit and summarize the models
for formula in formulas:
    model = smf.ols(formula=formula, data=df2).fit()
    print(f"\nModel summary for formula: {formula}\n")
    print(model.summary())
    print("\n-----------------------------------------\n")
    
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
fig.savefig('openai_violence_regression_output_scores.pdf')
plt.show()

'''Correlogram'''



# Calculate pairwise correlations
corr_matrix = df2[['score_toxic_overall_violence', 'score_toxic_pris_violence', 'score_toxic_guard_violence']].corr()

# Rename variables for the plot
corr_matrix.index = ['Violence: Overall', 'Violence: Prisoner', 'Violence: Guard']
corr_matrix.columns = ['Violence: Overall', 'Violence: Prisoner', 'Violence: Guard']

# Create a heatmap using seaborn
plt.figure(figsize=(6, 5))
sns.heatmap(corr_matrix, annot=False, cmap='coolwarm', vmin=-1, vmax=1, fmt='.2f', annot_kws={'size': 12})
# Rotate tick labels
plt.xticks(rotation=0, size=9)
plt.yticks(rotation=90, size=9)
# Save the figure as a PDF file
plt.savefig('openai_violence_correlogram_score.pdf', format='pdf', bbox_inches='tight')

plt.show()

''' Bar Charts '''

# Mapping for LLM names
llm_mapping = {
    'llama3:latest': 'Llama3',
    'command-r:latest': 'Command-r',
    'orca2:latest': 'Orca2',
    'gpt-4.1-2025-04-14': 'gpt4.1'
}

# Apply mapping to llm column
df2['llm'] = df2['llm'].map(llm_mapping)

# Split data by goal
yard_time_combinations = df2[df2['goal'] == 'Yard Time'][['goal', 'personality_prisoner', 'personality_guard']].drop_duplicates()
escape_combinations = df2[df2['goal'] == 'Escape'][['goal', 'personality_prisoner', 'personality_guard']].drop_duplicates()

# Ensure both have the same order of personalities (prisoner and guard)
yard_time_combinations = yard_time_combinations.sort_values(by=['personality_prisoner', 'personality_guard']).reset_index(drop=True)
escape_combinations = escape_combinations.sort_values(by=['personality_prisoner', 'personality_guard']).reset_index(drop=True)

# Make sure the number of combinations is the same
assert len(yard_time_combinations) == len(escape_combinations), "Mismatch in the number of Yard Time and Escape combinations."

# Number of rows based on the number of pairs
num_combinations = len(yard_time_combinations)
num_cols = 2  # We want 2 columns: Yard Time and Escape
num_rows = math.ceil(num_combinations)  # Number of rows based on the number of pairs

# Set up the matplotlib figure with the correct number of rows
fig, axs = plt.subplots(num_rows, num_cols, figsize=(13, 2*num_rows), sharey=True)
fig.subplots_adjust(wspace=0.3, hspace=0.3)

# Iterate over each row to plot the paired subplots
for i in range(num_combinations):
    # Subset data for the current Yard Time combination
    yard_goal, yard_prisoner, yard_guard = yard_time_combinations.iloc[i]
    yard_subset = df2[(df2['goal'] == yard_goal) & 
                     (df2['personality_prisoner'] == yard_prisoner) & 
                     (df2['personality_guard'] == yard_guard)]
    
    # Subset data for the current Escape combination
    escape_goal, escape_prisoner, escape_guard = escape_combinations.iloc[i]
    escape_subset = df2[(df2['goal'] == escape_goal) & 
                       (df2['personality_prisoner'] == escape_prisoner) & 
                       (df2['personality_guard'] == escape_guard)]
    
    # Calculate average values and standard deviations for each llm category for Yard Time
    yard_grouped_means = yard_subset.groupby('llm').mean()
    yard_grouped_std = yard_subset.groupby('llm').std()
    
    # Calculate average values and standard deviations for each llm category for Escape
    escape_grouped_means = escape_subset.groupby('llm').mean()
    escape_grouped_std = escape_subset.groupby('llm').std()
    
    # Calculate x-axis positions for bars
    index = range(len(yard_grouped_means))
    bar_width = 0.2
    
    # Determine subplot location
    row = i  # Now using i directly as the row index
    col_left = 0  # Left column for Yard Time
    col_right = 1  # Right column for Escape
    
    # Plotting the Yard Time subplot
    ax_left = axs[row, col_left] if num_combinations > 1 else axs
    ax_left.bar(index, yard_grouped_means['score_toxic_overall_violence'], bar_width, 
                yerr=yard_grouped_std['score_toxic_overall_violence'], alpha=0.6, color='b', label='Violence: Overall')
    ax_left.bar([p + bar_width for p in index], yard_grouped_means['score_toxic_pris_violence'], bar_width, 
                yerr=yard_grouped_std['score_toxic_pris_violence'], alpha=0.6, color='g', label='Violence: Prisoner')
    ax_left.bar([p + 2 * bar_width for p in index], yard_grouped_means['score_toxic_guard_violence'], bar_width, 
                yerr=yard_grouped_std['score_toxic_guard_violence'], alpha=0.6, color='r', label='Violence: Guard')
    
    # Set title for the Yard Time subplot (without 'Goal:')
    title_left = f'{yard_prisoner}, {yard_guard}'
    ax_left.set_title(title_left.replace(',', ', '), fontsize=14)
    
    # Set x-axis labels and ticks for Yard Time
    ax_left.set_xticks([p + 1.5 * bar_width for p in index])
    ax_left.set_xticklabels(yard_grouped_means.index, size=13)
    
    # Set y-axis label only for the first plot in the left column
    if i == num_rows // 2:
        ax_left.set_ylabel('Avg. Violence (with Std. Dev.)', size=18)
        ax_left.yaxis.set_label_coords(-0.15, 0.5)  # Adjust position of y-axis label
    
    # Plotting the Escape subplot
    ax_right = axs[row, col_right] if num_combinations > 1 else axs
    ax_right.bar(index, escape_grouped_means['score_toxic_overall_violence'], bar_width, 
                 yerr=escape_grouped_std['score_toxic_overall_violence'], alpha=0.6, color='b', label='Violence: Overall')
    ax_right.bar([p + bar_width for p in index], escape_grouped_means['score_toxic_pris_violence'], bar_width, 
                 yerr=escape_grouped_std['score_toxic_pris_violence'], alpha=0.6, color='g', label='Violence: Prisoner')
    ax_right.bar([p + 2 * bar_width for p in index], escape_grouped_means['score_toxic_guard_violence'], bar_width, 
                 yerr=escape_grouped_std['score_toxic_guard_violence'], alpha=0.6, color='r', label='Violence: Guard')
    
    # Set title for the Escape subplot (without 'Goal:')
    title_right = f'{escape_prisoner}, {escape_guard}'
    ax_right.set_title(title_right.replace(',', ', '), fontsize=14)
    
    # Set x-axis labels and ticks for Escape
    ax_right.set_xticks([p + 1.5 * bar_width for p in index])
    ax_right.set_xticklabels(escape_grouped_means.index, size=13)
    
    # Add legend only to the first Escape subplot
    if i == 0:
        ax_right.legend()

# Add big labels directly above the subplots
fig.text(0.35, 0.99, 'Goal: Yard Time', ha='center', va='top', fontsize=20)
fig.text(0.77, 0.99, 'Goal: Escape', ha='center', va='top', fontsize=20)

# Show the plot
plt.tight_layout(rect=[0.05, 0, 1, 0.96])  # Adjust layout to make room for column titles
fig.savefig('openai_violence_barcharts_scores.pdf', bbox_inches='tight', pad_inches=0.1) 
plt.show()
