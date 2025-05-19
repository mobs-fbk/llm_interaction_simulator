# -*- coding: utf-8 -*-


import pandas as pd
import difflib
import numpy as np
from matplotlib import pyplot as plt
import os
import sklearn as sk

np.set_printoptions(suppress=True)
%matplotlib qt
import matplotlib
matplotlib.rcParams['font.sans-serif'] = "Microsoft Sans Serif"
# Then, "ALWAYS use sans-serif fonts"
matplotlib.rcParams['font.family'] = "sans-serif"



''' TOXYGEN ROBERTA '''

# Load and prepare the data

df = pd.read_excel('toxicity_analysis_full_series_arrmay.xlsx')

'''ESCAPE PLOT'''

# Step 1: Filter the DataFrame
filtered_df = df[(df['goal'] == 'Escape') & 
                 (df['llm'].isin(['command-r:latest', 'llama3:latest', 'orca2:latest', 'gpt-4.1-2025-04-14']))]


# Replace the values in the 'llm' column
filtered_df['llm'] = filtered_df['llm'].replace({
    'command-r:latest': 'command-r',
    'llama3:latest': 'llama3',
    'orca2:latest': 'orca2',
    'gpt-4.1-2025-04-14': 'gpt4.1'
})

#import reliability
rel = pd.read_excel('updated_toxicity_analysis_scores_arrmay.xlsx')

# Rename the first column in each DataFrame to 'id'
filtered_df.rename(columns={filtered_df.columns[0]: 'id'}, inplace=True)
rel.rename(columns={rel.columns[0]: 'id'}, inplace=True)

# Step: Identify IDs in rel where goal_achieved is 'NAN'
ids_to_remove = set(rel[rel['goal_achieved'] == 'NAN']['id'])

# Step: Filter filtered_df to remove rows where id is in ids_to_remove
filtered_df = filtered_df[~filtered_df['id'].isin(ids_to_remove)]

# Step 2: Get unique combinations of personality_prisoner and personality_guard
unique_combinations = filtered_df[['personality_prisoner', 'personality_guard']].drop_duplicates()

# Step 3: Set up the subplot grid
n_rows = len(unique_combinations)
n_cols = filtered_df['llm'].nunique()


# Create the figure and subplots
fig, axes = plt.subplots(n_rows, n_cols, figsize=(4.5 * n_cols, 2.4 * n_rows), sharey=True)

# Flatten axes for easy iteration if there's more than one row or column
if n_rows > 1 or n_cols > 1:
    axes = axes.flatten()
else:
    axes = [axes]

# Step 4: Plot the data
for i, (index, row) in enumerate(unique_combinations.iterrows()):
    for j, llm in enumerate(filtered_df['llm'].unique()):
        subset = filtered_df[
            (filtered_df['personality_prisoner'] == row['personality_prisoner'])
            & (filtered_df['personality_guard'] == row['personality_guard'])
            & (filtered_df['llm'] == llm)
        ]

        # Modify personality names
        prisoner_personality_map = {
            "Blank Personalities": "Blank Personality Prisoner",
            "Good Prisoner": "Peaceful Prisoner",
            "Bad Prisoner": "Rebellious Prisoner",
        }
        guard_personality_map = {
            "Blank Personalities": "Blank Personality Guard",
            "Good Guard": "Respectful Guard",
            "Bad Guard": "Abusive Guard",
        }

        prisoner_personality = prisoner_personality_map.get(
            row["personality_prisoner"], row["personality_prisoner"]
        )
        guard_personality = guard_personality_map.get(
            row["personality_guard"], row["personality_guard"]
        )

        # Define columns and calculate averages
        pris_columns = [f"mess{k}_pris" for k in range(1, 10)]
        guard_columns = [f"mess{k}_guard" for k in range(1, 11)]

        pris_avg = [subset[col].mean() for col in pris_columns]
        guard_avg = [subset[col].mean() for col in guard_columns]

        # Calculate standard errors and confidence intervals
        pris_std = [subset[col].std() for col in pris_columns]
        pris_count = [subset[col].count() for col in pris_columns]
        pris_ci = [
            1.96 * (std / np.sqrt(count))
            for std, count in zip(pris_std, pris_count)
        ]

        guard_std = [subset[col].std() for col in guard_columns]
        guard_count = [subset[col].count() for col in guard_columns]
        guard_ci = [
            1.96 * (std / np.sqrt(count))
            for std, count in zip(guard_std, guard_count)
        ]

        # Turn labels
        turns = [f"{k}" for k in range(1, 11)]

        # Extend prisoner and guard averages with NaN for missing prisoner turn 10
        pris_avg.extend([np.nan])
        pris_ci.extend([np.nan])  # Extend confidence interval as well

        # Plot on the corresponding subplot
        ax = axes[i * n_cols + j]

        # Plot Prisoner line and confidence interval (only for 9 turns)
        ax.plot(turns[:9], pris_avg[:9], label="Prisoner Avg", color="blue")
        ax.fill_between(
            turns[:9],
            np.array(pris_avg[:9]) - np.array(pris_ci[:9]),
            np.array(pris_avg[:9]) + np.array(pris_ci[:9]),
            color="blue",
            alpha=0.3,
        )

        # Plot Guard line and confidence interval (for all 10 turns)
        ax.plot(turns, guard_avg, label="Guard Avg", color="red")
        ax.fill_between(
            turns,
            np.array(guard_avg) - np.array(guard_ci),
            np.array(guard_avg) + np.array(guard_ci),
            color="red",
            alpha=0.3,
        )

        # Update the title for each subplot with modified personality names
        personality_title = f"{prisoner_personality}, {guard_personality}"
        ax.set_title(personality_title, fontsize=13)  # Set personality title size to 14

        # Add the LLM title only for the first row and increase font size
        if i == 0:
            ax.text(0.5, 1.2, f"LLM: {llm}", transform=ax.transAxes, ha='center', fontsize=15)

        ax.set_xticks(turns)
        ax.set_xticklabels(turns, rotation=0, ha="right")
        ax.set_xlabel("Turn")
        ax.set_ylabel("Avg. Toxicity (with 95% CI)")

        # Add legend only to the first subplot
        if i == 0 and j == 0:
            ax.legend()
        else:
            ax.legend().set_visible(False)

plt.tight_layout(rect=[0, 0, 1, 0.98]) 
fig.savefig('temporal_desc_escape_toxigen.pdf') # Adjust layout to accommodate LLM titles at the top
plt.show()

'''YARD TIME PLOT'''
# Step 1: Filter the DataFrame
filtered_df = df[(df['goal'] == 'Yard Time') & 
                 (df['llm'].isin(['command-r:latest', 'llama3:latest', 'orca2:latest', 'gpt-4.1-2025-04-14']))]


# Replace the values in the 'llm' column
filtered_df['llm'] = filtered_df['llm'].replace({
    'command-r:latest': 'command-r',
    'llama3:latest': 'llama3',
    'orca2:latest': 'orca2',
    'gpt-4.1-2025-04-14': 'gpt4.1'
})

#import reliability
rel = pd.read_excel('updated_toxicity_analysis_scores_arrmay.xlsx')

# Rename the first column in each DataFrame to 'id'
filtered_df.rename(columns={filtered_df.columns[0]: 'id'}, inplace=True)
rel.rename(columns={rel.columns[0]: 'id'}, inplace=True)

# Step: Identify IDs in rel where goal_achieved is 'NAN'
ids_to_remove = set(rel[rel['goal_achieved'] == 'NAN']['id'])

# Step: Filter filtered_df to remove rows where id is in ids_to_remove
filtered_df = filtered_df[~filtered_df['id'].isin(ids_to_remove)]

# Step 2: Get unique combinations of personality_prisoner and personality_guard
unique_combinations = filtered_df[['personality_prisoner', 'personality_guard']].drop_duplicates()

# Step 3: Set up the subplot grid
n_rows = len(unique_combinations)
n_cols = filtered_df['llm'].nunique()


# Create the figure and subplots
fig, axes = plt.subplots(n_rows, n_cols, figsize=(4.5 * n_cols, 2.4 * n_rows), sharey=True)

# Flatten axes for easy iteration if there's more than one row or column
if n_rows > 1 or n_cols > 1:
    axes = axes.flatten()
else:
    axes = [axes]

# Step 4: Plot the data
for i, (index, row) in enumerate(unique_combinations.iterrows()):
    for j, llm in enumerate(filtered_df['llm'].unique()):
        subset = filtered_df[
            (filtered_df['personality_prisoner'] == row['personality_prisoner'])
            & (filtered_df['personality_guard'] == row['personality_guard'])
            & (filtered_df['llm'] == llm)
        ]

        # Modify personality names
        prisoner_personality_map = {
            "Blank Personalities": "Blank Personality Prisoner",
            "Good Prisoner": "Peaceful Prisoner",
            "Bad Prisoner": "Rebellious Prisoner",
        }
        guard_personality_map = {
            "Blank Personalities": "Blank Personality Guard",
            "Good Guard": "Respectful Guard",
            "Bad Guard": "Abusive Guard",
        }

        prisoner_personality = prisoner_personality_map.get(
            row["personality_prisoner"], row["personality_prisoner"]
        )
        guard_personality = guard_personality_map.get(
            row["personality_guard"], row["personality_guard"]
        )

        # Define columns and calculate averages
        pris_columns = [f"mess{k}_pris" for k in range(1, 10)]
        guard_columns = [f"mess{k}_guard" for k in range(1, 11)]

        pris_avg = [subset[col].mean() for col in pris_columns]
        guard_avg = [subset[col].mean() for col in guard_columns]

        # Calculate standard errors and confidence intervals
        pris_std = [subset[col].std() for col in pris_columns]
        pris_count = [subset[col].count() for col in pris_columns]
        pris_ci = [
            1.96 * (std / np.sqrt(count))
            for std, count in zip(pris_std, pris_count)
        ]

        guard_std = [subset[col].std() for col in guard_columns]
        guard_count = [subset[col].count() for col in guard_columns]
        guard_ci = [
            1.96 * (std / np.sqrt(count))
            for std, count in zip(guard_std, guard_count)
        ]

        # Turn labels
        turns = [f"{k}" for k in range(1, 11)]

        # Extend prisoner and guard averages with NaN for missing prisoner turn 10
        pris_avg.extend([np.nan])
        pris_ci.extend([np.nan])  # Extend confidence interval as well

        # Plot on the corresponding subplot
        ax = axes[i * n_cols + j]

        # Plot Prisoner line and confidence interval (only for 9 turns)
        ax.plot(turns[:9], pris_avg[:9], label="Prisoner Avg", color="blue")
        ax.fill_between(
            turns[:9],
            np.array(pris_avg[:9]) - np.array(pris_ci[:9]),
            np.array(pris_avg[:9]) + np.array(pris_ci[:9]),
            color="blue",
            alpha=0.3,
        )

        # Plot Guard line and confidence interval (for all 10 turns)
        ax.plot(turns, guard_avg, label="Guard Avg", color="red")
        ax.fill_between(
            turns,
            np.array(guard_avg) - np.array(guard_ci),
            np.array(guard_avg) + np.array(guard_ci),
            color="red",
            alpha=0.3,
        )

        # Update the title for each subplot with modified personality names
        personality_title = f"{prisoner_personality}, {guard_personality}"
        ax.set_title(personality_title, fontsize=13)  # Set personality title size to 14

        # Add the LLM title only for the first row and increase font size
        if i == 0:
            ax.text(0.5, 1.2, f"LLM: {llm}", transform=ax.transAxes, ha='center', fontsize=15)

        ax.set_xticks(turns)
        ax.set_xticklabels(turns, rotation=0, ha="right")
        ax.set_xlabel("Turn")
        ax.set_ylabel("Avg. Toxicity (with 95% CI)")

        # Add legend only to the first subplot
        if i == 0 and j == 0:
            ax.legend()
        else:
            ax.legend().set_visible(False)

plt.tight_layout(rect=[0, 0, 1, 0.98]) 
fig.savefig('temporal_desc_yard_toxigen.pdf') # Adjust layout to accommodate LLM titles at the top
plt.show()




''' OPEN AI PLOTS: HARASSMENT '''

'''escape plot'''

# Load and prepare the data
df2 = pd.read_excel('openai_toxicity_analysis_full_arrmay.xlsx')

# Step 1: Filter the DataFrame based on 'goal' and 'llm' conditions
filtered_df2 = df2[(df2['goal'] == 'Escape') & 
                   (df2['llm'].isin(['command-r:latest', 'llama3:latest', 'orca2:latest', 'gpt-4.1-2025-04-14']))]

# Replace the values in the 'llm' column
filtered_df['llm'] = filtered_df['llm'].replace({
    'command-r:latest': 'command-r',
    'llama3:latest': 'llama3',
    'orca2:latest': 'orca2',
    'gpt-4.1-2025-04-14': 'gpt4.1'
})

# Step 2: Remove columns that contain "violence" in their names
columns_to_keep = [col for col in filtered_df2.columns if 'violence' not in col]

# Select the desired columns
filtered_df2 = filtered_df2.loc[:, columns_to_keep]

#import reliability
rel = pd.read_excel('updated_toxicity_analysis_scores_arrmay.xlsx')

# Rename the first column in each DataFrame to 'id'
filtered_df2.rename(columns={filtered_df2.columns[0]: 'id'}, inplace=True)
rel.rename(columns={rel.columns[0]: 'id'}, inplace=True)

# Step: Identify IDs in rel where goal_achieved is 'NAN'
ids_to_remove = set(rel[rel['goal_achieved'] == 'NAN']['id'])

# Step: Filter filtered_df to remove rows where id is in ids_to_remove
filtered_df2 = filtered_df2[~filtered_df2['id'].isin(ids_to_remove)]


# Step 2b: Get unique combinations of personality_prisoner and personality_guard
unique_combinations = filtered_df2[['personality_prisoner', 'personality_guard']].drop_duplicates()

# Step 3: Set up the subplot grid
n_rows = len(unique_combinations)
n_cols = filtered_df2['llm'].nunique()

# Create the figure and subplots
# Create the figure and subplots
fig, axes = plt.subplots(n_rows, n_cols, figsize=(4.5 * n_cols, 2.4 * n_rows), sharey=True)

# Flatten axes for easy iteration if there's more than one row or column
if n_rows > 1 or n_cols > 1:
    axes = axes.flatten()
else:
    axes = [axes]

# Step 4: Plot the data
for i, (index, row) in enumerate(unique_combinations.iterrows()):
    for j, llm in enumerate(filtered_df2['llm'].unique()):
        subset = filtered_df2[
            (filtered_df2['personality_prisoner'] == row['personality_prisoner'])
            & (filtered_df2['personality_guard'] == row['personality_guard'])
            & (filtered_df2['llm'] == llm)
        ]

        # Modify personality names
        prisoner_personality_map = {
            "Blank Personalities": "Blank Personality Prisoner",
            "Good Prisoner": "Peaceful Prisoner",
            "Bad Prisoner": "Rebellious Prisoner",
        }
        guard_personality_map = {
            "Blank Personalities": "Blank Personality Guard",
            "Good Guard": "Respectful Guard",
            "Bad Guard": "Abusive Guard",
        }

        prisoner_personality = prisoner_personality_map.get(
            row["personality_prisoner"], row["personality_prisoner"]
        )
        guard_personality = guard_personality_map.get(
            row["personality_guard"], row["personality_guard"]
        )

        # Define columns and calculate averages
        pris_columns = [f"mess{k}_pris_harassment" for k in range(1, 10)]
        guard_columns = [f"mess{k}_guard_harassment" for k in range(1, 11)]

        pris_avg = [subset[col].mean() for col in pris_columns]
        guard_avg = [subset[col].mean() for col in guard_columns]

        # Calculate standard errors and confidence intervals
        pris_std = [subset[col].std() for col in pris_columns]
        pris_count = [subset[col].count() for col in pris_columns]
        pris_ci = [
            1.96 * (std / np.sqrt(count))
            for std, count in zip(pris_std, pris_count)
        ]

        guard_std = [subset[col].std() for col in guard_columns]
        guard_count = [subset[col].count() for col in guard_columns]
        guard_ci = [
            1.96 * (std / np.sqrt(count))
            for std, count in zip(guard_std, guard_count)
        ]

        # Turn labels
        turns = [f"{k}" for k in range(1, 11)]

        # Extend prisoner and guard averages with NaN for missing prisoner turn 10
        pris_avg.extend([np.nan])
        pris_ci.extend([np.nan])  # Extend confidence interval as well

        # Plot on the corresponding subplot
        ax = axes[i * n_cols + j]

        # Plot Prisoner line and confidence interval (only for 9 turns)
        ax.plot(turns[:9], pris_avg[:9], label="Prisoner Avg", color="blue")
        ax.fill_between(
            turns[:9],
            np.array(pris_avg[:9]) - np.array(pris_ci[:9]),
            np.array(pris_avg[:9]) + np.array(pris_ci[:9]),
            color="blue",
            alpha=0.3,
        )

        # Plot Guard line and confidence interval (for all 10 turns)
        ax.plot(turns, guard_avg, label="Guard Avg", color="red")
        ax.fill_between(
            turns,
            np.array(guard_avg) - np.array(guard_ci),
            np.array(guard_avg) + np.array(guard_ci),
            color="red",
            alpha=0.3,
        )

        # Update the title for each subplot with modified personality names
        personality_title = f"{prisoner_personality}, {guard_personality}"
        ax.set_title(personality_title, fontsize=13)  # Set personality title size to 14

        # Add the LLM title only for the first row and increase font size
        if i == 0:
            ax.text(0.5, 1.2, f"LLM: {llm}", transform=ax.transAxes, ha='center', fontsize=15)

        ax.set_xticks(turns)
        ax.set_xticklabels(turns, rotation=0, ha="right")
        ax.set_xlabel("Turn")
        ax.set_ylabel("Avg. Harassment (with 95% CI)")

        # Add legend only to the first subplot
        if i == 0 and j == 0:
            ax.legend()
        else:
            ax.legend().set_visible(False)

plt.tight_layout(rect=[0, 0, 1, 0.98]) 
fig.savefig('temporal_desc_escape_harass_openai.pdf') # Adjust layout to accommodate LLM titles at the top
plt.show()

'''yard time plot'''

# Load and prepare the data
df2 = pd.read_excel('openai_toxicity_analysis_full_arrmay.xlsx')

# Step 1: Filter the DataFrame based on 'goal' and 'llm' conditions
filtered_df2 = df2[(df2['goal'] == 'Yard Time') & 
                   (df2['llm'].isin(['command-r:latest', 'llama3:latest', 'orca2:latest', 'gpt-4.1-2025-04-14']))]

# Replace the values in the 'llm' column
filtered_df['llm'] = filtered_df['llm'].replace({
    'command-r:latest': 'command-r',
    'llama3:latest': 'llama3',
    'orca2:latest': 'orca2',
    'gpt-4.1-2025-04-14': 'gpt4.1'
})

# Step 2: Remove columns that contain "violence" in their names
columns_to_keep = [col for col in filtered_df2.columns if 'violence' not in col]

# Select the desired columns
filtered_df2 = filtered_df2.loc[:, columns_to_keep]

#import reliability
rel = pd.read_excel('updated_toxicity_analysis_scores_arrmay.xlsx')

# Rename the first column in each DataFrame to 'id'
filtered_df2.rename(columns={filtered_df2.columns[0]: 'id'}, inplace=True)
rel.rename(columns={rel.columns[0]: 'id'}, inplace=True)

# Step: Identify IDs in rel where goal_achieved is 'NAN'
ids_to_remove = set(rel[rel['goal_achieved'] == 'NAN']['id'])

# Step: Filter filtered_df to remove rows where id is in ids_to_remove
filtered_df2 = filtered_df2[~filtered_df2['id'].isin(ids_to_remove)]



# Step 2b: Get unique combinations of personality_prisoner and personality_guard
unique_combinations = filtered_df2[['personality_prisoner', 'personality_guard']].drop_duplicates()

# Step 3: Set up the subplot grid
n_rows = len(unique_combinations)
n_cols = filtered_df2['llm'].nunique()

# Create the figure and subplots
# Create the figure and subplots
fig, axes = plt.subplots(n_rows, n_cols, figsize=(4.5 * n_cols, 2.4 * n_rows), sharey=True)

# Flatten axes for easy iteration if there's more than one row or column
if n_rows > 1 or n_cols > 1:
    axes = axes.flatten()
else:
    axes = [axes]

# Step 4: Plot the data
for i, (index, row) in enumerate(unique_combinations.iterrows()):
    for j, llm in enumerate(filtered_df2['llm'].unique()):
        subset = filtered_df2[
            (filtered_df2['personality_prisoner'] == row['personality_prisoner'])
            & (filtered_df2['personality_guard'] == row['personality_guard'])
            & (filtered_df2['llm'] == llm)
        ]

        # Modify personality names
        prisoner_personality_map = {
            "Blank Personalities": "Blank Personality Prisoner",
            "Good Prisoner": "Peaceful Prisoner",
            "Bad Prisoner": "Rebellious Prisoner",
        }
        guard_personality_map = {
            "Blank Personalities": "Blank Personality Guard",
            "Good Guard": "Respectful Guard",
            "Bad Guard": "Abusive Guard",
        }

        prisoner_personality = prisoner_personality_map.get(
            row["personality_prisoner"], row["personality_prisoner"]
        )
        guard_personality = guard_personality_map.get(
            row["personality_guard"], row["personality_guard"]
        )

        # Define columns and calculate averages
        pris_columns = [f"mess{k}_pris_harassment" for k in range(1, 10)]
        guard_columns = [f"mess{k}_guard_harassment" for k in range(1, 11)]

        pris_avg = [subset[col].mean() for col in pris_columns]
        guard_avg = [subset[col].mean() for col in guard_columns]

        # Calculate standard errors and confidence intervals
        pris_std = [subset[col].std() for col in pris_columns]
        pris_count = [subset[col].count() for col in pris_columns]
        pris_ci = [
            1.96 * (std / np.sqrt(count))
            for std, count in zip(pris_std, pris_count)
        ]

        guard_std = [subset[col].std() for col in guard_columns]
        guard_count = [subset[col].count() for col in guard_columns]
        guard_ci = [
            1.96 * (std / np.sqrt(count))
            for std, count in zip(guard_std, guard_count)
        ]

        # Turn labels
        turns = [f"{k}" for k in range(1, 11)]

        # Extend prisoner and guard averages with NaN for missing prisoner turn 10
        pris_avg.extend([np.nan])
        pris_ci.extend([np.nan])  # Extend confidence interval as well

        # Plot on the corresponding subplot
        ax = axes[i * n_cols + j]

        # Plot Prisoner line and confidence interval (only for 9 turns)
        ax.plot(turns[:9], pris_avg[:9], label="Prisoner Avg", color="blue")
        ax.fill_between(
            turns[:9],
            np.array(pris_avg[:9]) - np.array(pris_ci[:9]),
            np.array(pris_avg[:9]) + np.array(pris_ci[:9]),
            color="blue",
            alpha=0.3,
        )

        # Plot Guard line and confidence interval (for all 10 turns)
        ax.plot(turns, guard_avg, label="Guard Avg", color="red")
        ax.fill_between(
            turns,
            np.array(guard_avg) - np.array(guard_ci),
            np.array(guard_avg) + np.array(guard_ci),
            color="red",
            alpha=0.3,
        )

        # Update the title for each subplot with modified personality names
        personality_title = f"{prisoner_personality}, {guard_personality}"
        ax.set_title(personality_title, fontsize=13)  # Set personality title size to 14

        # Add the LLM title only for the first row and increase font size
        if i == 0:
            ax.text(0.5, 1.2, f"LLM: {llm}", transform=ax.transAxes, ha='center', fontsize=15)

        ax.set_xticks(turns)
        ax.set_xticklabels(turns, rotation=0, ha="right")
        ax.set_xlabel("Turn")
        ax.set_ylabel("Avg. Harassment (with 95% CI)")

        # Add legend only to the first subplot
        if i == 0 and j == 0:
            ax.legend()
        else:
            ax.legend().set_visible(False)

plt.tight_layout(rect=[0, 0, 1, 0.98]) 
fig.savefig('temporal_desc_yardtime_harass_openai.pdf') # Adjust layout to accommodate LLM titles at the top
plt.show()





''' OPEN AI PLOTS: VIOLENCE '''

'''escape plot'''

# Load and prepare the data
df2 = pd.read_excel('openai_toxicity_analysis_full_arrmay.xlsx')

# Step 1: Filter the DataFrame based on 'goal' and 'llm' conditions
filtered_df3 = df2[(df2['goal'] == 'Escape') & 
                   (df2['llm'].isin(['command-r:latest', 'llama3:latest', 'orca2:latest', 'gpt-4.1-2025-04-14']))]

# Replace the values in the 'llm' column
filtered_df['llm'] = filtered_df['llm'].replace({
    'command-r:latest': 'command-r',
    'llama3:latest': 'llama3',
    'orca2:latest': 'orca2',
    'gpt-4.1-2025-04-14': 'gpt4.1'
})

# Step 2: Remove columns that contain "violence" in their names
columns_to_keep = [col for col in filtered_df3.columns if 'harassment' not in col]

# Select the desired columns
filtered_df3 = filtered_df3.loc[:, columns_to_keep]

#import reliability
rel = pd.read_excel('updated_toxicity_analysis_scores_arrmay.xlsx')

# Rename the first column in each DataFrame to 'id'
filtered_df3.rename(columns={filtered_df3.columns[0]: 'id'}, inplace=True)
rel.rename(columns={rel.columns[0]: 'id'}, inplace=True)

# Step: Identify IDs in rel where goal_achieved is 'NAN'
ids_to_remove = set(rel[rel['goal_achieved'] == 'NAN']['id'])

# Step: Filter filtered_df to remove rows where id is in ids_to_remove
filtered_df3 = filtered_df3[~filtered_df3['id'].isin(ids_to_remove)]


# Step 2b: Get unique combinations of personality_prisoner and personality_guard
unique_combinations = filtered_df3[['personality_prisoner', 'personality_guard']].drop_duplicates()

# Step 3: Set up the subplot grid
n_rows = len(unique_combinations)
n_cols = filtered_df3['llm'].nunique()

# Create the figure and subplots
# Create the figure and subplots
fig, axes = plt.subplots(n_rows, n_cols, figsize=(4.5 * n_cols, 2.4 * n_rows), sharey=True)

# Flatten axes for easy iteration if there's more than one row or column
if n_rows > 1 or n_cols > 1:
    axes = axes.flatten()
else:
    axes = [axes]

# Step 4: Plot the data
for i, (index, row) in enumerate(unique_combinations.iterrows()):
    for j, llm in enumerate(filtered_df3['llm'].unique()):
        subset = filtered_df3[
            (filtered_df3['personality_prisoner'] == row['personality_prisoner'])
            & (filtered_df3['personality_guard'] == row['personality_guard'])
            & (filtered_df3['llm'] == llm)
        ]

        # Modify personality names
        prisoner_personality_map = {
            "Blank Personalities": "Blank Personality Prisoner",
            "Good Prisoner": "Peaceful Prisoner",
            "Bad Prisoner": "Rebellious Prisoner",
        }
        guard_personality_map = {
            "Blank Personalities": "Blank Personality Guard",
            "Good Guard": "Respectful Guard",
            "Bad Guard": "Abusive Guard",
        }

        prisoner_personality = prisoner_personality_map.get(
            row["personality_prisoner"], row["personality_prisoner"]
        )
        guard_personality = guard_personality_map.get(
            row["personality_guard"], row["personality_guard"]
        )

        # Define columns and calculate averages
        pris_columns = [f"mess{k}_pris_violence" for k in range(1, 10)]
        guard_columns = [f"mess{k}_guard_violence" for k in range(1, 11)]

        pris_avg = [subset[col].mean() for col in pris_columns]
        guard_avg = [subset[col].mean() for col in guard_columns]

        # Calculate standard errors and confidence intervals
        pris_std = [subset[col].std() for col in pris_columns]
        pris_count = [subset[col].count() for col in pris_columns]
        pris_ci = [
            1.96 * (std / np.sqrt(count))
            for std, count in zip(pris_std, pris_count)
        ]

        guard_std = [subset[col].std() for col in guard_columns]
        guard_count = [subset[col].count() for col in guard_columns]
        guard_ci = [
            1.96 * (std / np.sqrt(count))
            for std, count in zip(guard_std, guard_count)
        ]

        # Turn labels
        turns = [f"{k}" for k in range(1, 11)]

        # Extend prisoner and guard averages with NaN for missing prisoner turn 10
        pris_avg.extend([np.nan])
        pris_ci.extend([np.nan])  # Extend confidence interval as well

        # Plot on the corresponding subplot
        ax = axes[i * n_cols + j]

        # Plot Prisoner line and confidence interval (only for 9 turns)
        ax.plot(turns[:9], pris_avg[:9], label="Prisoner Avg", color="blue")
        ax.fill_between(
            turns[:9],
            np.array(pris_avg[:9]) - np.array(pris_ci[:9]),
            np.array(pris_avg[:9]) + np.array(pris_ci[:9]),
            color="blue",
            alpha=0.3,
        )

        # Plot Guard line and confidence interval (for all 10 turns)
        ax.plot(turns, guard_avg, label="Guard Avg", color="red")
        ax.fill_between(
            turns,
            np.array(guard_avg) - np.array(guard_ci),
            np.array(guard_avg) + np.array(guard_ci),
            color="red",
            alpha=0.3,
        )

        # Update the title for each subplot with modified personality names
        personality_title = f"{prisoner_personality}, {guard_personality}"
        ax.set_title(personality_title, fontsize=13)  # Set personality title size to 14

        # Add the LLM title only for the first row and increase font size
        if i == 0:
            ax.text(0.5, 1.2, f"LLM: {llm}", transform=ax.transAxes, ha='center', fontsize=15)

        ax.set_xticks(turns)
        ax.set_xticklabels(turns, rotation=0, ha="right")
        ax.set_xlabel("Turn")
        ax.set_ylabel("Avg. Violence (with 95% CI)")

        # Add legend only to the first subplot
        if i == 0 and j == 0:
            ax.legend()
        else:
            ax.legend().set_visible(False)

plt.tight_layout(rect=[0, 0, 1, 0.98]) 
fig.savefig('temporal_desc_escape_violence_openai.pdf') # Adjust layout to accommodate LLM titles at the top
plt.show()

'''yard time plot'''

# Load and prepare the data
df2 = pd.read_excel('openai_toxicity_analysis_full_arrmay.xlsx')

# Step 1: Filter the DataFrame based on 'goal' and 'llm' conditions
filtered_df3 = df2[(df2['goal'] == 'Yard Time') & 
                   (df2['llm'].isin(['command-r:latest', 'llama3:latest', 'orca2:latest','gpt-4.1-2025-04-14']))]

# Replace the values in the 'llm' column
filtered_df['llm'] = filtered_df['llm'].replace({
    'command-r:latest': 'command-r',
    'llama3:latest': 'llama3',
    'orca2:latest': 'orca2',
    'gpt-4.1-2025-04-14': 'gpt4.1'
})

# Step 2: Remove columns that contain "violence" in their names
columns_to_keep = [col for col in filtered_df3.columns if 'harassment' not in col]

# Select the desired columns
filtered_df3 = filtered_df3.loc[:, columns_to_keep]

#import reliability
rel = pd.read_excel('updated_toxicity_analysis_scores_arrmay.xlsx')

# Rename the first column in each DataFrame to 'id'
filtered_df3.rename(columns={filtered_df3.columns[0]: 'id'}, inplace=True)
rel.rename(columns={rel.columns[0]: 'id'}, inplace=True)

# Step: Identify IDs in rel where goal_achieved is 'NAN'
ids_to_remove = set(rel[rel['goal_achieved'] == 'NAN']['id'])

# Step: Filter filtered_df to remove rows where id is in ids_to_remove
filtered_df3 = filtered_df3[~filtered_df3['id'].isin(ids_to_remove)]


# Step 2b: Get unique combinations of personality_prisoner and personality_guard
unique_combinations = filtered_df3[['personality_prisoner', 'personality_guard']].drop_duplicates()

# Step 3: Set up the subplot grid
n_rows = len(unique_combinations)
n_cols = filtered_df3['llm'].nunique()

# Create the figure and subplots
# Create the figure and subplots
fig, axes = plt.subplots(n_rows, n_cols, figsize=(4.5 * n_cols, 2.4 * n_rows), sharey=True)

# Flatten axes for easy iteration if there's more than one row or column
if n_rows > 1 or n_cols > 1:
    axes = axes.flatten()
else:
    axes = [axes]

# Step 4: Plot the data
for i, (index, row) in enumerate(unique_combinations.iterrows()):
    for j, llm in enumerate(filtered_df3['llm'].unique()):
        subset = filtered_df3[
            (filtered_df3['personality_prisoner'] == row['personality_prisoner'])
            & (filtered_df3['personality_guard'] == row['personality_guard'])
            & (filtered_df3['llm'] == llm)
        ]

        # Modify personality names
        prisoner_personality_map = {
            "Blank Personalities": "Blank Personality Prisoner",
            "Good Prisoner": "Peaceful Prisoner",
            "Bad Prisoner": "Rebellious Prisoner",
        }
        guard_personality_map = {
            "Blank Personalities": "Blank Personality Guard",
            "Good Guard": "Respectful Guard",
            "Bad Guard": "Abusive Guard",
        }

        prisoner_personality = prisoner_personality_map.get(
            row["personality_prisoner"], row["personality_prisoner"]
        )
        guard_personality = guard_personality_map.get(
            row["personality_guard"], row["personality_guard"]
        )

        # Define columns and calculate averages
        pris_columns = [f"mess{k}_pris_violence" for k in range(1, 10)]
        guard_columns = [f"mess{k}_guard_violence" for k in range(1, 11)]

        pris_avg = [subset[col].mean() for col in pris_columns]
        guard_avg = [subset[col].mean() for col in guard_columns]

        # Calculate standard errors and confidence intervals
        pris_std = [subset[col].std() for col in pris_columns]
        pris_count = [subset[col].count() for col in pris_columns]
        pris_ci = [
            1.96 * (std / np.sqrt(count))
            for std, count in zip(pris_std, pris_count)
        ]

        guard_std = [subset[col].std() for col in guard_columns]
        guard_count = [subset[col].count() for col in guard_columns]
        guard_ci = [
            1.96 * (std / np.sqrt(count))
            for std, count in zip(guard_std, guard_count)
        ]

        # Turn labels
        turns = [f"{k}" for k in range(1, 11)]

        # Extend prisoner and guard averages with NaN for missing prisoner turn 10
        pris_avg.extend([np.nan])
        pris_ci.extend([np.nan])  # Extend confidence interval as well

        # Plot on the corresponding subplot
        ax = axes[i * n_cols + j]

        # Plot Prisoner line and confidence interval (only for 9 turns)
        ax.plot(turns[:9], pris_avg[:9], label="Prisoner Avg", color="blue")
        ax.fill_between(
            turns[:9],
            np.array(pris_avg[:9]) - np.array(pris_ci[:9]),
            np.array(pris_avg[:9]) + np.array(pris_ci[:9]),
            color="blue",
            alpha=0.3,
        )

        # Plot Guard line and confidence interval (for all 10 turns)
        ax.plot(turns, guard_avg, label="Guard Avg", color="red")
        ax.fill_between(
            turns,
            np.array(guard_avg) - np.array(guard_ci),
            np.array(guard_avg) + np.array(guard_ci),
            color="red",
            alpha=0.3,
        )

        # Update the title for each subplot with modified personality names
        personality_title = f"{prisoner_personality}, {guard_personality}"
        ax.set_title(personality_title, fontsize=13)  # Set personality title size to 14

        # Add the LLM title only for the first row and increase font size
        if i == 0:
            ax.text(0.5, 1.2, f"LLM: {llm}", transform=ax.transAxes, ha='center', fontsize=15)

        ax.set_xticks(turns)
        ax.set_xticklabels(turns, rotation=0, ha="right")
        ax.set_xlabel("Turn")
        ax.set_ylabel("Avg. Violence (with 95% CI)")

        # Add legend only to the first subplot
        if i == 0 and j == 0:
            ax.legend()
        else:
            ax.legend().set_visible(False)

plt.tight_layout(rect=[0, 0, 1, 0.98]) 
fig.savefig('temporal_desc_yardtime_violence_openai.pdf') # Adjust layout to accommodate LLM titles at the top
plt.show()