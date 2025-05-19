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
from matplotlib.font_manager import FontProperties  # Import FontProperties
matplotlib.rcParams['font.sans-serif'] = "Microsoft Sans Serif"
# Then, "ALWAYS use sans-serif fonts"
matplotlib.rcParams['font.family'] = "sans-serif"




### Persuasion

# Load and prepare the data
df = pd.read_excel('updated_toxicity_analysis_scores_arrmay.xlsx')


#rename llms
df['llm'] = df['llm'].replace({
    'command-r:latest': 'command-r',
    'llama3:latest': 'llama3',
    'orca2:latest': 'orca2',
    'gpt-4.1-2025-04-14': 'gpt4.1'
    
})

# Remove rows where 'goal_achieved' is equal to the text 'NAN'
df = df[df['goal_achieved'] != 'NAN']

################# Distribution plot
# Group by llm and goal, then calculate the percentage of each goal_achieved value
grouped = df.groupby(['llm', 'goal', 'goal_achieved']).size().reset_index(name='count')
total = df.groupby(['llm', 'goal']).size().reset_index(name='total')
grouped = pd.merge(grouped, total, on=['llm', 'goal'])
grouped['percent'] = (grouped['count'] / grouped['total']) * 100

# Prepare data for 'turn_goal_achieved' plot
mapping_dict = {
    0: 0,
    1: '1st 1/3',
    2: '2nd 1/3',
    3: '3rd 1/3'
}
df['turn_goal_achieved'] = df['turn_goal_achieved'].map(mapping_dict)
df_filtered = df[df['turn_goal_achieved'] != 0]

# Define unique values for 'llm' and 'turn_goal_achieved'
llm_values = df['llm'].unique()
goal_achieved_values = ['Yes', 'No', 'NotTried', 'NAN']  # Order for grouping
turn_goal_achieved_values = ['1st 1/3', '2nd 1/3', '3rd 1/3']
colors = ['skyblue', 'lightgreen', 'salmon', 'gold']  # Define colors for each goal_achieved value

# New colors for the second row subplots
second_row_colors = ['slategray', 'orchid', 'goldenrod']

# Create a figure with 2 rows and 3 columns of subplots
fig, axes = plt.subplots(nrows=2, ncols=4, figsize=(12, 8), sharex='col', sharey='row')

# Plotting the distribution of goal_achieved
for ax, llm in zip(axes[0], llm_values):
    subset = grouped[grouped['llm'] == llm]
    bar_width = 0.15
    bar_positions = np.arange(len(subset['goal'].unique()))  # x locations for the groups

    for idx, goal_achieved in enumerate(goal_achieved_values):
        data = subset[subset['goal_achieved'] == goal_achieved]
        if not data.empty:
            ax.bar(bar_positions + idx * bar_width, data['percent'], bar_width, label=goal_achieved, color=colors[idx])
    
    ax.set_title(f'{llm}', size=22)
    ax.set_xlabel('Goal', size=18)
    ax.set_ylabel('% Outcome Legit Exp.', size=20)
    ax.set_xticks(bar_positions + bar_width * 1.5)
    ax.set_xticklabels(subset['goal'].unique(), size=15)
    ax.set_ylim(0, 100)
    ax.tick_params(axis='y', labelsize=20)
    if ax == axes[0, 0]:
        ax.set_ylabel('% Outcome Legit Exp.', size=20)

# Plotting the distribution of turn_goal_achieved
for ax, llm in zip(axes[1], llm_values):
    subset = df_filtered[df_filtered['llm'] == llm]
    data = subset.groupby(['goal', 'turn_goal_achieved']).size().unstack(fill_value=0)
    
    if data.empty:
        continue  # Skip empty dataframes
    
    data = data.div(data.sum(axis=1), axis=0) * 100
    
    bar_width = 0.15
    goals = data.index
    bar_positions = np.arange(len(goals))
    
    for i, turn_goal in enumerate(turn_goal_achieved_values):
        if turn_goal in data.columns:
            ax.bar(bar_positions + i * bar_width, data[turn_goal], bar_width, label=turn_goal, color=second_row_colors[i])
    
    ax.set_title(f'{llm}', size=22)
    ax.set_xlabel('Goal', size=18)
    ax.set_ylabel('Goal Achieved (% Legit Exp.)', size=20)
    ax.set_xticks(bar_positions + bar_width * 1)
    ax.set_xticklabels(goals, size=20)
    ax.set_ylim(0, 100)
    ax.tick_params(axis='y', labelsize=20)
    
    if ax == axes[1, 0]:
        ax.set_ylabel('Goal Achieved (% Legit Exp.)', size=20)

# Create FontProperties object to adjust legend size
font_props = FontProperties(size=16)  # Set the desired font size

# Add legends with larger title font size
axes[0, 2].legend(title='Goal Achieved', loc='upper right', prop=font_props, title_fontsize=13)
axes[1, 2].legend(title='Turn Goal Ach.', loc='upper right', prop=font_props, title_fontsize=13)

# Adjust layout
plt.tight_layout()
fig.savefig('persuasion_outcomes_desc.pdf')

plt.show()





''' Logistic Regression'''

# remove NAN (failed experiments)
df2 = df[df['goal_achieved'] != 'NAN']
df2 = df[df['goal_achieved'] != 'NotTried']

import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

# remove mixtral and mistral
df2 = df2[~df2['llm'].isin(['mistral:latest', 'mixtral:latest'])]


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

# create personality combination
df2['personality_combination'] = df2['personality_guard'].astype(str) + ', ' + df2['personality_prisoner'].astype(str)

# Ensure the correct data types
categorical_vars = ['llm', 'goal', 'personality_prisoner', 'personality_guard', 'personality_combination']
for var in categorical_vars:
    df2[var] = df2[var].astype('category')

# Set baseline categories
df2['llm'] = df2['llm'].cat.reorder_categories(
    ['llama3', 'command-r', 'orca2', 'gpt4.1'], 
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
df2['personality_combination'] = df2['personality_combination'].cat.reorder_categories(
    ['Blank Personality Guard, Blank Personality Prisoner', 'Respectful Guard, Peaceful Prisoner', 'Respectful Guard, Rebellious Prisoner',
     'Abusive Guard, Peaceful Prisoner', 'Abusive Guard, Rebellious Prisoner'], 
    ordered=True
)



# Verify the column names and data types
print(df2.dtypes)
print(df2.head())


# logistic regression
import statsmodels.api as sm
# Convert 'goal_achieved' to binary (1 for 'Yes', 0 for 'No')
df2['goal_achieved'] = df2['goal_achieved'].apply(lambda x: 1 if x == 'Yes' else 0)






# Define the logistic regression formula
formula = 'goal_achieved ~ Risks + Research_Oversight + goal + C(personality_combination) + C(llm)'

# Fit the logistic regression model
model = smf.logit(formula=formula, data=df2)
result = model.fit(cov_type='HC0')  # Use heteroscedasticity-robust standard errors
# Print the summary of the model
print(result.summary())
# Transform coefficients to odds ratios
odds_ratios = pd.DataFrame({
    'OR': result.params.apply(np.exp),
    'Lower CI': result.conf_int()[0].apply(np.exp),
    'Upper CI': result.conf_int()[1].apply(np.exp),
    'p-value': result.pvalues
})


print("\nOdds Ratios with 95% CI:")
print(odds_ratios)

# plotting coefficients
odds_ratios.reset_index(inplace=True)

# rename vars for plotting
new_variable_names = {

    'C(llm)[T.command-r]': 'LLM: Command-r',
    'C(llm)[T.orca2]': 'LLM: Orca2',
    'C(llm)[T.gpt4.1]': 'LLM: gpt4.1',
    'Risks': 'Discl. of Risks',
    'Research_Oversight': 'Discl. of Research Oversight',
    'goal[T.Yard Time]': 'Goal: Yard Time',
    'C(personality_combination)[T.Abusive Guard, Rebellious Prisoner]': 'Abusive G., Rebel. Pris.',
    'C(personality_combination)[T.Abusive Guard, Peaceful Prisoner]': 'Abusive G., Peaceful Pris.',
    'C(personality_combination)[T.Respectful Guard, Rebellious Prisoner]': 'Resp. G., Rebel. Pris.',
    'C(personality_combination)[T.Respectful Guard, Peaceful Prisoner]': 'Resp. G., Peaceful Pris.'
}

# Replace the values in the 'index' column
odds_ratios['index'] = odds_ratios['index'].replace(new_variable_names)

# Define the desired order
desired_order = [
    'LLM: Orca2',
    'LLM: Command-r',
    'LLM: gpt4.1',
    'Goal: Yard Time',
    'Abusive G., Rebel. Pris.',
    'Abusive G., Peaceful Pris.',
    'Resp. G., Rebel. Pris.',
    'Resp. G., Peaceful Pris.',
    'Discl. of Research Oversight',
    'Discl. of Risks',
    'Intercept'
]

# Create a dictionary mapping the desired order to indices
order_dict = {name: i for i, name in enumerate(desired_order)}

# Add a new column to the DataFrame that holds these indices
odds_ratios['order'] = odds_ratios['index'].map(order_dict)

# Sort the DataFrame based on the new column
odds_ratios = odds_ratios.sort_values('order')

# Create the plot
fig=plt.figure(figsize=(8, 6))
plt.errorbar(odds_ratios['OR'], odds_ratios['order'], 
             xerr=[odds_ratios['OR'] - odds_ratios['Lower CI'], odds_ratios['Upper CI'] - odds_ratios['OR']], 
             fmt='o', color='black', ecolor='black', capsize=6, markersize=6)

# Customize the plot
plt.axvline(1, linestyle='--', color='gray')
plt.yticks(ticks=odds_ratios['order'], labels=odds_ratios['index'], size=18)
plt.xticks(size=17)
plt.ylabel('Covariates', size=19)
plt.xlabel('OR (with 95% CI)', size=19)
plt.tight_layout()
fig.savefig('logistic_outcomes_persuasion.pdf')
# Show the plot
plt.show()




'''''''



import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Load and process the data as described
df1 = pd.read_excel('updated_toxicity_analysis_percentage_arrmay.xlsx')
df2 = pd.read_excel('updated_openai_toxicity_analysis_percentage_arrmay.xlsx')

#rename llm column
df1['llm'] = df1['llm'].replace({
    'command-r:latest': 'command-r',
    'llama3:latest': 'llama3',
    'orca2:latest': 'orca2',
    'gpt-4.1-2025-04-14': 'gpt4.1'
})

df2['llm'] = df2['llm'].replace({
    'command-r:latest': 'command-r',
    'llama3:latest': 'llama3',
    'orca2:latest': 'orca2',
    'gpt-4.1-2025-04-14': 'gpt4.1'
})

# Ensure the merging column is named properly for both datasets
df1.rename(columns={'Unnamed: 0': 'key'}, inplace=True)
df2.rename(columns={'Unnamed: 0': 'key'}, inplace=True)

# Merge the datasets based on the 'key' column
merged_df = pd.merge(df1, df2, on='key')

# rename personality
# Replace values in the 'personality_prisoner_x' column
merged_df['personality_prisoner_x'] = merged_df['personality_prisoner_x'].replace({
    'Good Prisoner': 'Peaceful Prisoner',
    'Bad Prisoner': 'Rebellious Prisoner'
})

# Replace values in the 'personality_guard_x' column
merged_df['personality_guard_x'] = merged_df['personality_guard_x'].replace({
    'Good Guard': 'Respectful Guard',
    'Bad Guard': 'Abusive Guard'
})

# Remove 'NAN' values
merged_df = merged_df[merged_df['goal_achieved_x'].str.upper() != 'NAN']

# Filter columns
columns_to_keep = [
    'llm_x', 'goal_x', 'goal_achieved_x', 'personality_prisoner_x', 'personality_guard_x', 
    'perc_toxic_all', 'perc_toxic_pris', 'perc_toxic_guard',
    'perc_toxic_overall_harassment', 'perc_toxic_pris_harassment', 
    'perc_toxic_guard_harassment', 'perc_toxic_overall_violence', 
    'perc_toxic_pris_violence', 'perc_toxic_guard_violence'
]

# Keep only the specified columns
filtered_df = merged_df[columns_to_keep]

# Reset the index to ensure unique indexing
filtered_df.reset_index(drop=True, inplace=True)

# Concatenate personality_guard_x and personality_prisoner_x
filtered_df['combined_personalities'] = filtered_df['personality_guard_x'] + ', ' + filtered_df['personality_prisoner_x']

# Replace "Blank Personalities, Blank Personalities" with "Blank Pers. Guard, Blank Pers. Prisoner"
filtered_df['combined_personalities'] = filtered_df['combined_personalities'].replace(
    'Blank Personalities, Blank Personalities', 'Blank Pers. Guard, Blank Pers. Prisoner'
)

# Multiply all toxicity scores by 100 to convert them to percentages
toxicity_columns = [
    'perc_toxic_all', 'perc_toxic_pris', 'perc_toxic_guard',
    'perc_toxic_overall_harassment', 'perc_toxic_pris_harassment', 
    'perc_toxic_guard_harassment', 'perc_toxic_overall_violence', 
    'perc_toxic_pris_violence', 'perc_toxic_guard_violence'
]
filtered_df[toxicity_columns] = filtered_df[toxicity_columns] * 100

# Calculate average toxicity values and standard deviation for each combined_personalities group
avg_df = filtered_df.groupby(['llm_x', 'goal_achieved_x', 'combined_personalities']).agg(['mean', 'std']).reset_index()

# Flatten the multi-level column index
avg_df.columns = ['_'.join(col).strip('_') for col in avg_df.columns.values]

# Ensure "Blank Pers. Guard, Blank Pers. Prisoner" is always the first one
def reorder_personalities(df):
    order = ["Blank Pers. Guard, Blank Pers. Prisoner"] + [p for p in df['combined_personalities'] if p != "Blank Pers. Guard, Blank Pers. Prisoner"]
    df['combined_personalities'] = pd.Categorical(df['combined_personalities'], categories=order, ordered=True)
    return df.sort_values('combined_personalities')

# Define unique values for llm_x and goal_achieved_x
llm_values = filtered_df['llm_x'].unique()
goal_achieved_values = filtered_df['goal_achieved_x'].unique()

# Modify goal_achieved_x labels
goal_labels = {
    'Yes': 'Goal Achieved: Yes',
    'No': 'Goal Achieved: No',
    'NotTried': 'Goal Achieved: Not Tried'
}
goal_achieved_values = [goal_labels[val] for val in goal_achieved_values]

# Define font sizes
label_fontsize = 17  # For x and y labels
tick_fontsize = 15   # For x-ticks and y-ticks
title_fontsize = 18  # For subplot titles
legend_fontsize = 14 # for legend



################################# overall plot
# Create a grid of subplots
fig, axes = plt.subplots(nrows=len(goal_achieved_values), ncols=len(llm_values), figsize=(19, 12), sharex=True, sharey=True)

# Define colors for the error bars and dots
colors = {
    'perc_toxic_all': 'dimgray',
    'perc_toxic_overall_harassment': 'brown',
    'perc_toxic_overall_violence': 'teal'
}

# Initialize lists for legend handles and labels
handles, labels = [], []

# Plot in each subplot
for i, goal in enumerate(goal_achieved_values):
    for j, llm in enumerate(llm_values):
        ax = axes[i, j]
        subset = avg_df[(avg_df['llm_x'] == llm) & (avg_df['goal_achieved_x'] == list(goal_labels.keys())[list(goal_labels.values()).index(goal)])]
        subset = reorder_personalities(subset)
        
        # Convert combined_personalities to categorical type for proper plotting
        y_ticks = np.arange(len(subset['combined_personalities']))
        
        # Plotting the average values with error bars
        offsets = np.linspace(-0.2, 0.2, num=3)  # Offsets for three toxicity types
        for k, (toxicity_type, color) in enumerate(colors.items()):
            error = ax.errorbar(
                subset[toxicity_type + '_mean'], 
                y_ticks + offsets[k],  # Offset to separate points
                xerr=subset[toxicity_type + '_std'], 
                fmt='o', 
                color=color,
                capsize=4,
                alpha=0.7  # Add shading to error bars
            )
            if j == 0 and i == 0:  # Only add legend handles and labels in the first subplot
                handles.append(error)
                labels.append({
                    'perc_toxic_all': 'Overall Toxicity TR',
                    'perc_toxic_overall_harassment': 'Overall Harass. OpenAI',
                    'perc_toxic_overall_violence': 'Overall Violence OpenAI'
                }[toxicity_type])
        
        ax.set_yticks(y_ticks)
        ax.set_yticklabels(subset['combined_personalities'], fontsize=tick_fontsize)  # Y-tick labels font size
        ax.set_xlim(-10, 100)  # Set x-axis limits to -10 to 100
        
        # Titles and labels
        if i == 0:
            ax.set_title(llm, fontsize=title_fontsize)  # Set subplot title size
        if j == 0:
            ax.set_ylabel(goal, fontsize=label_fontsize)  # Y-axis label font size
        if i == len(goal_achieved_values) - 1:
            ax.set_xlabel('Avg. % Anti-Social Mess. (w/SD)', fontsize=label_fontsize)  # X-axis label font size
        
        # Set x and y tick font sizes
        ax.tick_params(axis='x', labelsize=tick_fontsize)
        ax.tick_params(axis='y', labelsize=tick_fontsize)

# Adjust layout
plt.tight_layout()

# Add legend to the upper right of the first subplot
axes[0, 0].legend(handles, labels, loc='upper right', borderaxespad=0., fontsize=legend_fontsize)
fig.savefig('overall_persuasion_toxicity.pdf')

plt.show()



################################# prisoner plot

# Create a grid of subplots
fig, axes = plt.subplots(nrows=len(goal_achieved_values), ncols=len(llm_values), figsize=(19, 12), sharex=True, sharey=True)

# Define colors for the error bars and dots
colors = {
    'perc_toxic_pris': 'dimgray',
    'perc_toxic_pris_harassment': 'brown',
    'perc_toxic_pris_violence': 'teal'
}

# Initialize lists for legend handles and labels
handles, labels = [], []

# Plot in each subplot
for i, goal in enumerate(goal_achieved_values):
    for j, llm in enumerate(llm_values):
        ax = axes[i, j]
        subset = avg_df[(avg_df['llm_x'] == llm) & (avg_df['goal_achieved_x'] == list(goal_labels.keys())[list(goal_labels.values()).index(goal)])]
        subset = reorder_personalities(subset)
        
        # Convert combined_personalities to categorical type for proper plotting
        y_ticks = np.arange(len(subset['combined_personalities']))
        
        # Plotting the average values with error bars
        offsets = np.linspace(-0.2, 0.2, num=3)  # Offsets for three toxicity types
        for k, (toxicity_type, color) in enumerate(colors.items()):
            error = ax.errorbar(
                subset[toxicity_type + '_mean'], 
                y_ticks + offsets[k],  # Offset to separate points
                xerr=subset[toxicity_type + '_std'], 
                fmt='o', 
                color=color,
                capsize=4,
                alpha=0.7  # Add shading to error bars
            )
            if j == 0 and i == 0:  # Only add legend handles and labels in the first subplot
                handles.append(error)
                labels.append({
                    'perc_toxic_pris': 'Prisoner Toxicity TR',
                    'perc_toxic_pris_harassment': 'Prisoner Harass. OpenAI',
                    'perc_toxic_pris_violence': 'Prisoner Violence OpenAI'
                }[toxicity_type])
        
        ax.set_yticks(y_ticks)
        ax.set_yticklabels(subset['combined_personalities'])
        ax.set_xlim(-20, 100)  # Set x-axis limits to -10 to 100
        
        # Titles and labels
        if i == 0:
            ax.set_title(llm, fontsize=title_fontsize)  # Set subplot title size
        if j == 0:
            ax.set_ylabel(goal, fontsize=label_fontsize)  # Y-axis label font size
        if i == len(goal_achieved_values) - 1:
            ax.set_xlabel('Avg. % Anti-Social Mess. (w/SD)', fontsize=label_fontsize)  # X-axis label font size
        
        # Set x and y tick font sizes
        ax.tick_params(axis='x', labelsize=tick_fontsize)
        ax.tick_params(axis='y', labelsize=tick_fontsize)

# Adjust layout
plt.tight_layout()

# Add legend to the upper right of the first subplot
axes[0, 0].legend(handles, labels, loc='upper right', borderaxespad=0., fontsize=12)
fig.savefig('prisoner_persuasion_toxicity.pdf')

plt.show()


############################## guard plot
fig, axes = plt.subplots(nrows=len(goal_achieved_values), ncols=len(llm_values), figsize=(19, 12), sharex=True, sharey=True)

# Define colors for the error bars and dots
colors = {
    'perc_toxic_guard': 'dimgray',
    'perc_toxic_guard_harassment': 'brown',
    'perc_toxic_guard_violence': 'teal'
}

# Initialize lists for legend handles and labels
handles, labels = [], []

# Plot in each subplot
for i, goal in enumerate(goal_achieved_values):
    for j, llm in enumerate(llm_values):
        ax = axes[i, j]
        subset = avg_df[(avg_df['llm_x'] == llm) & (avg_df['goal_achieved_x'] == list(goal_labels.keys())[list(goal_labels.values()).index(goal)])]
        subset = reorder_personalities(subset)
        
        # Convert combined_personalities to categorical type for proper plotting
        y_ticks = np.arange(len(subset['combined_personalities']))
        
        # Plotting the average values with error bars
        offsets = np.linspace(-0.2, 0.2, num=3)  # Offsets for three toxicity types
        for k, (toxicity_type, color) in enumerate(colors.items()):
            error = ax.errorbar(
                subset[toxicity_type + '_mean'], 
                y_ticks + offsets[k],  # Offset to separate points
                xerr=subset[toxicity_type + '_std'], 
                fmt='o', 
                color=color,
                capsize=4,
                alpha=0.7  # Add shading to error bars
            )
            if j == 0 and i == 0:  # Only add legend handles and labels in the first subplot
                handles.append(error)
                labels.append({
                    'perc_toxic_guard': 'Guard Toxicity TR',
                    'perc_toxic_guard_harassment': 'Guard Harass. OpenAI',
                    'perc_toxic_guard_violence': 'Guard Violence OpenAI'
                }[toxicity_type])
        
        ax.set_yticks(y_ticks)
        ax.set_yticklabels(subset['combined_personalities'])
        ax.set_xlim(-15, 118)  # Set x-axis limits to -10 to 100
        
        # Titles and labels
        if i == 0:
            ax.set_title(llm, fontsize=title_fontsize)  # Set subplot title size
        if j == 0:
            ax.set_ylabel(goal, fontsize=label_fontsize)  # Y-axis label font size
        if i == len(goal_achieved_values) - 1:
            ax.set_xlabel('Avg. % Anti-Social Mess. (w/SD)', fontsize=label_fontsize)  # X-axis label font size
        
        # Set x and y tick font sizes
        ax.tick_params(axis='x', labelsize=tick_fontsize)
        ax.tick_params(axis='y', labelsize=tick_fontsize)

# Add legend to the upper right of the first subplot
axes[0, 0].legend(handles, labels, loc='upper right', borderaxespad=0., fontsize=12)
# Adjust layout
plt.tight_layout()

fig.savefig('guard_persuasion_toxicity.pdf')

plt.show()





