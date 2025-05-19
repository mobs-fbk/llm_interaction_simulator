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

# filter out mixtral and mistral
df = df[df['llm'].isin(['command-r:latest', 'llama3:latest', 'orca2:latest', 'gpt-4.1-2025-04-14'])]

#rename llms
df['llm'] = df['llm'].replace({
    'command-r:latest': 'command-r',
    'llama3:latest': 'llama3',
    'orca2:latest': 'orca2',
    'gpt-4.1-2025-04-14': 'gpt4.1'
})

#rename personalities
# Rename values in 'personality_guard' column
df['personality_guard'] = df['personality_guard'].replace({
    'Good Guard': 'Respectful Guard',
    'Bad Guard': 'Abusive Guard',
    'Blank Personalities':'Blank Pers. Guard'
})

# Rename values in 'personality_prisoner' column
df['personality_prisoner'] = df['personality_prisoner'].replace({
    'Good Prisoner': 'Peaceful Prisoner',
    'Bad Prisoner': 'Rebellious Prisoner',
    'Blank Personalities': 'Blank Pers. Prisoner'
})


#import reliability
rel = pd.read_excel('updated_toxicity_analysis_scores_arrmay.xlsx')



# Rename the first column in each DataFrame to 'id'
df.rename(columns={df.columns[0]: 'id'}, inplace=True)
rel.rename(columns={rel.columns[0]: 'id'}, inplace=True)

# Step: Identify IDs in rel where goal_achieved is 'NAN'
ids_to_remove = set(rel[rel['goal_achieved'] == 'NAN']['id'])

# Step: Filter filtered_df to remove rows where id is in ids_to_remove
df = df[~df['id'].isin(ids_to_remove)]


# Rename 'unnamed' column to 'id'
df.rename(columns={'Unnamed: 0': 'id'}, inplace=True)

# Drop 'mess10_guard' column
df.drop(columns=['mess10_guard'], inplace=True)

# Prepare a list of columns for reshaping
guard_mess_cols = [f'mess{i}_guard' for i in range(1, 10)]
pris_mess_cols = [f'mess{i}_pris' for i in range(1, 10)]

# Melt the DataFrame to long format for guard messages
guard_mess_long = pd.melt(df, id_vars=['id', 'llm', 'Risks', 'Research Oversight', 'goal', 'personality_prisoner', 'personality_guard'],
                          value_vars=guard_mess_cols,
                          var_name='message_type',
                          value_name='guard_mess')

# Melt the DataFrame to long format for prisoner messages
pris_mess_long = pd.melt(df, id_vars=['id', 'llm', 'Risks', 'Research Oversight', 'goal', 'personality_prisoner', 'personality_guard'],
                         value_vars=pris_mess_cols,
                         var_name='message_type',
                         value_name='pris_mess')

# Extract the message number from 'message_type'
guard_mess_long['message_number'] = guard_mess_long['message_type'].str.extract(r'(\d+)').astype(int)
pris_mess_long['message_number'] = pris_mess_long['message_type'].str.extract(r'(\d+)').astype(int)

# Drop the 'message_type' column
guard_mess_long.drop(columns=['message_type'], inplace=True)
pris_mess_long.drop(columns=['message_type'], inplace=True)

# Merge the two long-format DataFrames on 'id' and 'message_number'
merged_df = pd.merge(guard_mess_long, pris_mess_long, on=['id', 'message_number'], how='inner')

# Optionally, sort the DataFrame by 'id' and 'message_number'
merged_df.sort_values(by=['id', 'message_number'], inplace=True)




# Reset index
merged_df.reset_index(drop=True, inplace=True)

# Display the reshaped DataFrame
print(merged_df.head())




'''granger'''


### check stationarity first:
from statsmodels.tsa.stattools import adfuller
# Initialize lists to store non-stationary ids
non_stationary_guard_ids = []
non_stationary_pris_ids = []

# Group by 'id'
for id_value, group in merged_df.groupby('id'):
    # Extract the time series for guard_mess and pris_mess
    guard_mess_series = group['guard_mess'].dropna()
    pris_mess_series = group['pris_mess'].dropna()
    
    # Perform ADF test on guard_mess
    guard_adf_result = adfuller(guard_mess_series)
    guard_is_stationary = guard_adf_result[1] < 0.05  # Stationary if p-value < 0.05
    
    # Perform ADF test on pris_mess
    pris_adf_result = adfuller(pris_mess_series)
    pris_is_stationary = pris_adf_result[1] < 0.05  # Stationary if p-value < 0.05
    
    # Check if guard_mess is non-stationary
    if not guard_is_stationary:
        non_stationary_guard_ids.append(id_value)
        
    # Check if pris_mess is non-stationary
    if not pris_is_stationary:
        non_stationary_pris_ids.append(id_value)
        
## difference those that are not stationary 
# Step 2: Apply differencing to non-stationary time series directly in the original columns

# Apply differencing to guard_mess for non-stationary ids
for id_value in non_stationary_guard_ids:
    mask = merged_df['id'] == id_value
    merged_df.loc[mask, 'guard_mess'] = merged_df.loc[mask, 'guard_mess'].diff()

# Apply differencing to pris_mess for non-stationary ids
for id_value in non_stationary_pris_ids:
    mask = merged_df['id'] == id_value
    merged_df.loc[mask, 'pris_mess'] = merged_df.loc[mask, 'pris_mess'].diff()

# Optionally, drop rows with NaN values that resulted from differencing (usually the first row per id)
merged_df.dropna(subset=['guard_mess', 'pris_mess'], inplace=True)



## now perform Granger (test whether guard causes prisoner)
from statsmodels.tsa.stattools import grangercausalitytests
# Initialize a list to store the results
results_guard = []

# Group by 'id'
for id_value, group in merged_df.groupby('id'):
    # Ensure we have data for the Granger causality test
    if len(group) < 2:
        continue  # Skip groups with insufficient data

    # Prepare data for Granger causality test
    time_series_data_guard = group[['guard_mess', 'pris_mess']].dropna()
    
    if len(time_series_data_guard) < 2:
        continue  # Skip if there are not enough observations after dropping NA

    # Perform Granger Causality Test
    try:
        test_result_guard = grangercausalitytests(time_series_data_guard, maxlag=1, verbose=False)
        
        # Extract results
        f_test_stat = test_result_guard[1][0]['ssr_ftest'][0]
        f_test_pvalue = test_result_guard[1][0]['ssr_ftest'][1]
        chi2_test_stat = test_result_guard[1][0]['ssr_chi2test'][0]
        chi2_test_pvalue = test_result_guard[1][0]['ssr_chi2test'][1]

        # Store results in a list
        results_guard.append({
            'id': id_value,
            'ssr_f_test_stat': f_test_stat,
            'ssr_f_test_pvalue': f_test_pvalue,
            'ssr_chi2_test_stat': chi2_test_stat,
            'ssr_chi2_test_pvalue': chi2_test_pvalue
        })
        
    except Exception as e:
        print(f"Error processing id={id_value}: {e}")
        continue

# Create a DataFrame from the results
results_guard_df = pd.DataFrame(results_guard)

# Display or save the results DataFrame
print(results_guard_df)

# Merge results_df with df on the 'id' column
results_guard_df = results_guard_df.merge(df[['id', 'llm', 'goal', 'personality_prisoner', 'personality_guard']], on='id', how='left')


###################### plot cumulative distribution
import seaborn as sns
# Create a new column combining personality_guard and personality_prisoner
results_guard_df['personality_comb'] = results_guard_df['personality_guard'] + ", " + results_guard_df['personality_prisoner']

desired_order = ['Blank Pers. Guard, Blank Pers. Prisoner', 'Respectful Guard, Rebellious Prisoner', 'Respectful Guard, Peaceful Prisoner',
                 'Abusive Guard, Peaceful Prisoner','Abusive Guard, Rebellious Prisoner']  # Replace with your desired combinations

results_guard_df['personality_comb'] = pd.Categorical(results_guard_df['personality_comb'], categories=desired_order, ordered=True)

# Sort the DataFrame by 'personality_comb' to ensure the plotting order matches
results_guard_df = results_guard_df.sort_values('personality_comb')
# Get the unique values of personality_comb and goal
personality_combinations = results_guard_df['personality_comb'].unique()
goals = results_guard_df['goal'].unique()

# Number of rows = number of unique combinations of personality_guard and personality_prisoner
# Number of columns = number of unique goal values
n_rows = len(personality_combinations)
n_cols = len(goals)

# Create the subplots grid
fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols * 6.5, n_rows * 2.5), sharex=True, sharey=True)

# Flatten the axes array for easy iteration
axes = axes.flatten()

# Loop through each personality_comb and goal, and create the cumulative distribution plot
for i, (personality_comb, goal) in enumerate([(p, g) for p in personality_combinations for g in goals]):
    
    # Subset the data based on current personality_comb and goal
    subset = results_guard_df[(results_guard_df['personality_comb'] == personality_comb) & 
                              (results_guard_df['goal'] == goal)]
    
    # Plot the cumulative distribution of ssr_f_test_pvalue hued by llm
    sns.ecdfplot(data=subset, x='ssr_f_test_pvalue', hue='llm', ax=axes[i])
    
    # Set the title and labels for the subplot
    axes[i].set_title(f'{personality_comb} - Goal: {goal}', size=16)
    axes[i].set_xlabel('F-test p-value', size=16)
    axes[i].set_ylabel('Cumulative Dist.', size=16)
    
    # Add a vertical dashed line at x = 0.05
    axes[i].axvline(x=0.05, color='red', linestyle='--', lw=1.5)
    
    # Increase the size of x and y ticks
    axes[i].tick_params(axis='both', which='major', labelsize=14)
    
# Show the legend only for the first subplot, with a larger font size
    if i == 0:
        handles, labels = axes[i].get_legend_handles_labels()
        if handles:  # Only add legend if there are handles
            legend = axes[i].legend(handles, labels, fontsize=12, title="LLM", title_fontsize=12)
    else:
        axes[i].get_legend().remove() 

# Adjust the layout for better spacing
plt.tight_layout()
#save
fig.savefig('granger_toxicity_guard_cause_prisoner.pdf') # Adjust layout to accommodate LLM titles at the top
# Show the plot
plt.show()

# calculate % of significant
# Calculate the number of rows where ssr_f_test_pvalue < 0.05
count_low_pvalue_guard = (results_guard_df['ssr_f_test_pvalue'] < 0.05).sum()

# Calculate the total number of rows
total_rows_guard = len(results_guard_df)

# Calculate the percentage
percentage_low_pvalue_guard = (count_low_pvalue_guard / total_rows_guard) * 100

# Print the result
print(f"Percentage of rows with ssr_f_test_pvalue < 0.05: {percentage_low_pvalue_guard:.2f}%")

# by group
# retrieve relevant columns from df for analysis
df = df.rename(columns={'Unnamed': 'id'})  # Rename 'Unnamed' to 'id' in df if not already done

# Merge results_df with df on the 'id' column
results_guard_df = results_guard_df.merge(df[['id', 'llm', 'goal', 'personality_prisoner', 'personality_guard']], on='id', how='left')


# calculate % by group
# Step 1: Group by 'llm', 'personality_prisoner', 'personality_guard', and 'goal'
grouped_guard = results_guard_df.groupby(['llm_x', 'personality_prisoner', 'personality_guard', 'goal'])

# Step 2: Calculate the percentage of rows with 'ssr_ftest_pvalue' < 0.05 for each group
percentage_df_guard = grouped_guard.apply(lambda x: (x['ssr_f_test_pvalue'] < 0.05).mean() * 100).reset_index()

# Step 3: Rename the columns for clarity
percentage_df_guard = percentage_df_guard.rename(columns={0: 'percentage_below_0.05_guard'})

############## now test effect of prisoner on guard

# Initialize a list to store the results

results_pris = []

# Group by 'id'
for id_value, group in merged_df.groupby('id'):
    # Ensure we have data for the Granger causality test
    if len(group) < 2:
        continue  # Skip groups with insufficient data

    # Prepare data for Granger causality test
    time_series_data_pris = group[['pris_mess', 'guard_mess']].dropna()
    
    if len(time_series_data_pris) < 2:
        continue  # Skip if there are not enough observations after dropping NA

    # Perform Granger Causality Test
    try:
        test_result_pris = grangercausalitytests(time_series_data_pris, maxlag=1, verbose=False)
        
        # Extract results
        f_test_stat = test_result_pris[1][0]['ssr_ftest'][0]
        f_test_pvalue = test_result_pris[1][0]['ssr_ftest'][1]
        chi2_test_stat = test_result_pris[1][0]['ssr_chi2test'][0]
        chi2_test_pvalue = test_result_pris[1][0]['ssr_chi2test'][1]

        # Store results in a list
        results_pris.append({
            'id': id_value,
            'ssr_f_test_stat': f_test_stat,
            'ssr_f_test_pvalue': f_test_pvalue,
            'ssr_chi2_test_stat': chi2_test_stat,
            'ssr_chi2_test_pvalue': chi2_test_pvalue
        })
        
    except Exception as e:
        print(f"Error processing id={id_value}: {e}")
        continue

# Create a DataFrame from the results
results_pris_df = pd.DataFrame(results_pris)

# Display or save the results DataFrame
print(results_pris_df)

# Merge results_df with df on the 'id' column
results_pris_df = results_pris_df.merge(df[['id', 'llm', 'goal', 'personality_prisoner', 'personality_guard']], on='id', how='left')

# Create a new column combining personality_pris and personality_prisoner
results_pris_df['personality_comb'] = results_pris_df['personality_guard'] + ", " + results_pris_df['personality_prisoner']

results_pris_df['personality_comb'] = pd.Categorical(results_pris_df['personality_comb'], categories=desired_order, ordered=True)

# Sort the DataFrame by 'personality_comb' to ensure the plotting order matches
results_pris_df = results_pris_df.sort_values('personality_comb')
# Get the unique values of personality_comb and goal
personality_combinations = results_pris_df['personality_comb'].unique()
goals = results_pris_df['goal'].unique()

# Number of rows = number of unique combinations of personality_pris and personality_prisoner
# Number of columns = number of unique goal values
n_rows = len(personality_combinations)
n_cols = len(goals)

# Create the subplots grid
fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols * 6.5, n_rows * 2.5), sharex=True, sharey=True)

# Flatten the axes array for easy iteration
axes = axes.flatten()

# Loop through each personality_comb and goal, and create the cumulative distribution plot
for i, (personality_comb, goal) in enumerate([(p, g) for p in personality_combinations for g in goals]):
    
    # Subset the data based on current personality_comb and goal
    subset = results_pris_df[(results_pris_df['personality_comb'] == personality_comb) & 
                              (results_pris_df['goal'] == goal)]
    
    # Plot the cumulative distribution of ssr_f_test_pvalue hued by llm
    sns.ecdfplot(data=subset, x='ssr_f_test_pvalue', hue='llm', ax=axes[i])
    
    # Set the title and labels for the subplot
    axes[i].set_title(f'{personality_comb} - Goal: {goal}', size=16)
    axes[i].set_xlabel('F-test p-value', size=16)
    axes[i].set_ylabel('Cumulative Dist.', size=16)
    
    # Add a vertical dashed line at x = 0.05
    axes[i].axvline(x=0.05, color='red', linestyle='--', lw=1.5)
    
    # Increase the size of x and y ticks
    axes[i].tick_params(axis='both', which='major', labelsize=14)
    
# Show the legend only for the first subplot, with a larger font size
    if i == 0:
        handles, labels = axes[i].get_legend_handles_labels()
        if handles:  # Only add legend if there are handles
            legend = axes[i].legend(handles, labels, fontsize=12, title="LLM", title_fontsize=12)
    else:
        axes[i].get_legend().remove() 

# Adjust the layout for better spacing
plt.tight_layout()
#save
fig.savefig('granger_toxicity_pris_cause_guard.pdf') # Adjust layout to accommodate LLM titles at the top
# Show the plot
plt.show()

# calculate % of significant
# Calculate the number of rows where ssr_f_test_pvalue < 0.05
count_low_pvalue_pris = (results_pris_df['ssr_f_test_pvalue'] < 0.05).sum()

# Calculate the total number of rows
total_rows_pris = len(results_pris_df)

# Calculate the percentage
percentage_low_pvalue_pris = (count_low_pvalue_pris / total_rows_pris) * 100

# Print the result
print(f"Percentage of rows with ssr_f_test_pvalue < 0.05: {percentage_low_pvalue_pris:.2f}%")

# calculate % by group

# Merge results_df with df on the 'id' column
results_pris_df = results_pris_df.merge(df[['id', 'llm', 'goal', 'personality_prisoner', 'personality_guard']], on='id', how='left')


# Step 1: Group by 'llm', 'personality_prisoner', 'personality_pris', and 'goal'
grouped_pris = results_pris_df.groupby(['llm', 'personality_prisoner', 'personality_guard', 'goal'])

# Step 2: Calculate the percentage of rows with 'ssr_ftest_pvalue' < 0.05 for each group
percentage_df_pris = grouped_pris.apply(lambda x: (x['ssr_f_test_pvalue'] < 0.05).mean() * 100).reset_index()

# Step 3: Rename the columns for clarity
percentage_df_pris = percentage_df_pris.rename(columns={0: 'percentage_below_0.05_pris'})

# combine the two
combined_df_granger_tox = pd.merge(percentage_df_pris, percentage_df_guard, 
                       on=['llm', 'personality_prisoner', 'personality_guard', 'goal'], 
                       how='inner')

# Round only numeric columns to two decimal places
combined_df_granger_tox_rounded = combined_df_granger_tox.copy()  # Make a copy of the original dataframe
combined_df_granger_tox_rounded = combined_df_granger_tox_rounded.apply(lambda x: x.round(2) if x.dtype == 'float' else x)




'''OPEN AI: HARASSMENT'''

# Load and prepare the data
df2 = pd.read_excel('openai_toxicity_analysis_full_arrmay.xlsx')

# filter out mixtral and mistral
df2 = df2[df2['llm'].isin(['command-r:latest', 'llama3:latest', 'orca2:latest', 'gpt-4.1-2025-04-14'])]

#rename llms
df2['llm'] = df2['llm'].replace({
    'command-r:latest': 'command-r',
    'llama3:latest': 'llama3',
    'orca2:latest': 'orca2',
    'gpt-4.1-2025-04-14':'gpt4.1'
})

#rename personalities
# Rename values in 'personality_guard' column
df2['personality_guard'] = df2['personality_guard'].replace({
    'Good Guard': 'Respectful Guard',
    'Bad Guard': 'Abusive Guard',
    'Blank Personalities':'Blank Pers. Guard'
})

# Rename values in 'personality_prisoner' column
df2['personality_prisoner'] = df2['personality_prisoner'].replace({
    'Good Prisoner': 'Peaceful Prisoner',
    'Bad Prisoner': 'Rebellious Prisoner',
    'Blank Personalities': 'Blank Pers. Prisoner'
})
# Step 2: Remove columns that contain "violence" in their names
columns_to_keep = [col for col in df2.columns if 'violence' not in col]

# Select the desired columns
df2 = df2.loc[:, columns_to_keep]

#import reliability
rel = pd.read_excel('updated_toxicity_analysis_scores_arrmay.xlsx')



# Rename the first column in each DataFrame to 'id'
df2.rename(columns={df2.columns[0]: 'id'}, inplace=True)
rel.rename(columns={rel.columns[0]: 'id'}, inplace=True)

# Step: Identify IDs in rel where goal_achieved is 'NAN'
ids_to_remove = set(rel[rel['goal_achieved'] == 'NAN']['id'])

# Step: Filter filtered_df to remove rows where id is in ids_to_remove
df2 = df2[~df2['id'].isin(ids_to_remove)]


# Rename 'unnamed' column to 'id'
df2.rename(columns={'Unnamed: 0': 'id'}, inplace=True)

# Drop 'mess10_guard' column
df2.drop(columns=['mess10_guard_harassment'], inplace=True)

# Prepare a list of columns for reshaping
guard_mess_cols_h = [f'mess{i}_guard_harassment' for i in range(1, 10)]
pris_mess_cols_h = [f'mess{i}_pris_harassment' for i in range(1, 10)]

# Melt the DataFrame to long format for guard messages
guard_mess_long_h = pd.melt(df2, id_vars=['id', 'llm', 'Risks', 'Research Oversight', 'goal', 'personality_prisoner', 'personality_guard'],
                          value_vars=guard_mess_cols_h,
                          var_name='message_type',
                          value_name='guard_mess')

# Melt the DataFrame to long format for prisoner messages
pris_mess_long_h = pd.melt(df2, id_vars=['id', 'llm', 'Risks', 'Research Oversight', 'goal', 'personality_prisoner', 'personality_guard'],
                         value_vars=pris_mess_cols_h,
                         var_name='message_type',
                         value_name='pris_mess')

# Extract the message number from 'message_type'
guard_mess_long_h['message_number'] = guard_mess_long_h['message_type'].str.extract(r'(\d+)').astype(int)
pris_mess_long_h['message_number'] = pris_mess_long_h['message_type'].str.extract(r'(\d+)').astype(int)

# Drop the 'message_type' column
guard_mess_long_h.drop(columns=['message_type'], inplace=True)
pris_mess_long_h.drop(columns=['message_type'], inplace=True)

# Merge the two long-format DataFrames on 'id' and 'message_number'
merged_df2_h = pd.merge(guard_mess_long_h, pris_mess_long_h, on=['id', 'message_number'], how='inner')

# Optionally, sort the DataFrame by 'id' and 'message_number'
merged_df2_h.sort_values(by=['id', 'message_number'], inplace=True)




# Reset index
merged_df2_h.reset_index(drop=True, inplace=True)

# Display the reshaped DataFrame
print(merged_df2_h.head())


'''granger'''


### check stationarity first:
from statsmodels.tsa.stattools import adfuller
# Initialize lists to store non-stationary ids
non_stationary_guard_ids_h = []
non_stationary_pris_ids_h = []

# Group by 'id'
for id_value, group in merged_df2_h.groupby('id'):
    # Extract the time series for guard_mess and pris_mess
    guard_mess_series = group['guard_mess'].dropna()
    pris_mess_series = group['pris_mess'].dropna()
    
    # Perform Adf2 test on guard_mess
    guard_adf_result = adfuller(guard_mess_series)
    guard_is_stationary = guard_adf_result[1] < 0.05  # Stationary if p-value < 0.05
    
    # Perform Adf2 test on pris_mess
    pris_adf_result = adfuller(pris_mess_series)
    pris_is_stationary = pris_adf_result[1] < 0.05  # Stationary if p-value < 0.05
    
    # Check if guard_mess is non-stationary
    if not guard_is_stationary:
        non_stationary_guard_ids_h.append(id_value)
        
    # Check if pris_mess is non-stationary
    if not pris_is_stationary:
        non_stationary_pris_ids_h.append(id_value)
        
## difference those that are not stationary 
# Step 2: Apply differencing to non-stationary time series directly in the original columns

# Apply differencing to guard_mess for non-stationary ids
for id_value in non_stationary_guard_ids:
    mask = merged_df2_h['id'] == id_value
    merged_df2_h.loc[mask, 'guard_mess'] = merged_df2_h.loc[mask, 'guard_mess'].diff()

# Apply differencing to pris_mess for non-stationary ids
for id_value in non_stationary_pris_ids:
    mask = merged_df2_h['id'] == id_value
    merged_df2_h.loc[mask, 'pris_mess'] = merged_df2_h.loc[mask, 'pris_mess'].diff()

# Optionally, drop rows with NaN values that resulted from differencing (usually the first row per id)
merged_df2_h.dropna(subset=['guard_mess', 'pris_mess'], inplace=True)


## now perform Granger (test whether guard causes prisoner)
from statsmodels.tsa.stattools import grangercausalitytests
# Initialize a list to store the results
results_guard_h = []

# Group by 'id'
for id_value, group in merged_df2_h.groupby('id'):
    # Ensure we have data for the Granger causality test
    if len(group) < 2:
        continue  # Skip groups with insufficient data

    # Prepare data for Granger causality test
    time_series_data_guard_h = group[['guard_mess', 'pris_mess']].dropna()
    
    if len(time_series_data_guard_h) < 2:
        continue  # Skip if there are not enough observations after dropping NA

    # Perform Granger Causality Test
    try:
        test_result_guard_h = grangercausalitytests(time_series_data_guard_h, maxlag=1, verbose=False)
        
        # Extract results
        f_test_stat = test_result_guard_h[1][0]['ssr_ftest'][0]
        f_test_pvalue = test_result_guard_h[1][0]['ssr_ftest'][1]
        chi2_test_stat = test_result_guard_h[1][0]['ssr_chi2test'][0]
        chi2_test_pvalue = test_result_guard_h[1][0]['ssr_chi2test'][1]

        # Store results in a list
        results_guard_h.append({
            'id': id_value,
            'ssr_f_test_stat': f_test_stat,
            'ssr_f_test_pvalue': f_test_pvalue,
            'ssr_chi2_test_stat': chi2_test_stat,
            'ssr_chi2_test_pvalue': chi2_test_pvalue
        })
        
    except Exception as e:
        print(f"Error processing id={id_value}: {e}")
        continue

# Create a DataFrame from the results
results_guard_df2_h = pd.DataFrame(results_guard_h)

#### plot cumulative distribution
# Merge results_df with df on the 'id' column
results_guard_df2_h = results_guard_df2_h.merge(df2[['id', 'llm', 'goal', 'personality_prisoner', 'personality_guard']], on='id', how='left')

import seaborn as sns
# Create a new column combining personality_guard and personality_prisoner
results_guard_df2_h['personality_comb'] = results_guard_df2_h['personality_guard'] + ", " + results_guard_df2_h['personality_prisoner']
results_guard_df2_h['personality_comb'] = pd.Categorical(results_guard_df2_h['personality_comb'], categories=desired_order, ordered=True)

# Sort the DataFrame by 'personality_comb' to ensure the plotting order matches
results_guard_df2_h = results_guard_df2_h.sort_values('personality_comb')
# Get the unique values of personality_comb and goal
personality_combinations = results_guard_df2_h['personality_comb'].unique()
goals = results_guard_df2_h['goal'].unique()

# Number of rows = number of unique combinations of personality_guard and personality_prisoner
# Number of columns = number of unique goal values
n_rows = len(personality_combinations)
n_cols = len(goals)

# Create the subplots grid
fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols * 6.5, n_rows * 2.5), sharex=True, sharey=True)

# Flatten the axes array for easy iteration
axes = axes.flatten()

# Loop through each personality_comb and goal, and create the cumulative distribution plot
for i, (personality_comb, goal) in enumerate([(p, g) for p in personality_combinations for g in goals]):
    
    # Subset the data based on current personality_comb and goal
    subset = results_guard_df2_h[(results_guard_df2_h['personality_comb'] == personality_comb) & 
                              (results_guard_df2_h['goal'] == goal)]
    
    # Plot the cumulative distribution of ssr_f_test_pvalue hued by llm
    sns.ecdfplot(data=subset, x='ssr_f_test_pvalue', hue='llm', ax=axes[i])
    
    # Set the title and labels for the subplot
    axes[i].set_title(f'{personality_comb} - Goal: {goal}', size=16)
    axes[i].set_xlabel('F-test p-value', size=16)
    axes[i].set_ylabel('Cumulative Dist.', size=16)
    
    # Add a vertical dashed line at x = 0.05
    axes[i].axvline(x=0.05, color='red', linestyle='--', lw=1.5)
    
    # Increase the size of x and y ticks
    axes[i].tick_params(axis='both', which='major', labelsize=14)
    
# Show the legend only for the first subplot, with a larger font size
    if i == 0:
        handles, labels = axes[i].get_legend_handles_labels()
        if handles:  # Only add legend if there are handles
            legend = axes[i].legend(handles, labels, fontsize=12, title="LLM", title_fontsize=12)
    else:
        axes[i].get_legend().remove() 

# Adjust the layout for better spacing
plt.tight_layout()
#save
fig.savefig('granger_harass_guard_cause_pris.pdf') # Adjust layout to accommodate LLM titles at the top
# Show the plot
plt.show()

# Display or save the results DataFrame
print(results_guard_df2_h)

# calculate % of significant
# Calculate the number of rows where ssr_f_test_pvalue < 0.05
count_low_pvalue_guard_h = (results_guard_df2_h['ssr_f_test_pvalue'] < 0.05).sum()

# Calculate the total number of rows
total_rows_guard_h = len(results_guard_df2_h)

# Calculate the percentage
percentage_low_pvalue_guard_h = (count_low_pvalue_guard_h / total_rows_guard_h) * 100

# Print the result
print(f"Percentage of rows with ssr_f_test_pvalue < 0.05: {percentage_low_pvalue_guard_h:.2f}%")

# by group
# retrieve relevant columns from df for analysis
df2 = df2.rename(columns={'Unnamed': 'id'})  # Rename 'Unnamed' to 'id' in df if not already done

# Merge results_df with df on the 'id' column
results_guard_df2_h = results_guard_df2_h.merge(df2[['id', 'llm', 'goal', 'personality_prisoner', 'personality_guard']], on='id', how='left')


# calculate % by group
# Step 1: Group by 'llm', 'personality_prisoner', 'personality_guard', and 'goal'
grouped_guard_h = results_guard_df2_h.groupby(['llm', 'personality_prisoner', 'personality_guard', 'goal'])

# Step 2: Calculate the percentage of rows with 'ssr_ftest_pvalue' < 0.05 for each group
percentage_df_guard_h = grouped_guard_h.apply(lambda x: (x['ssr_f_test_pvalue'] < 0.05).mean() * 100).reset_index()

# Step 3: Rename the columns for clarity
percentage_df_guard_h = percentage_df_guard_h.rename(columns={0: 'percentage_below_0.05_guard_h'})

############## now test effect of prisoner on guard

# Initialize a list to store the results

results_pris_h = []

# Group by 'id'
for id_value, group in merged_df2_h.groupby('id'):
    # Ensure we have data for the Granger causality test
    if len(group) < 2:
        continue  # Skip groups with insufficient data

    # Prepare data for Granger causality test
    time_series_data_pris_h = group[['pris_mess', 'guard_mess']].dropna()
    
    if len(time_series_data_pris_h) < 2:
        continue  # Skip if there are not enough observations after dropping NA

    # Perform Granger Causality Test
    try:
        test_result_pris_h = grangercausalitytests(time_series_data_pris_h, maxlag=1, verbose=False)
        
        # Extract results
        f_test_stat = test_result_pris_h[1][0]['ssr_ftest'][0]
        f_test_pvalue = test_result_pris_h[1][0]['ssr_ftest'][1]
        chi2_test_stat = test_result_pris_h[1][0]['ssr_chi2test'][0]
        chi2_test_pvalue = test_result_pris_h[1][0]['ssr_chi2test'][1]

        # Store results in a list
        results_pris_h.append({
            'id': id_value,
            'ssr_f_test_stat': f_test_stat,
            'ssr_f_test_pvalue': f_test_pvalue,
            'ssr_chi2_test_stat': chi2_test_stat,
            'ssr_chi2_test_pvalue': chi2_test_pvalue
        })
        
    except Exception as e:
        print(f"Error processing id={id_value}: {e}")
        continue

# Create a DataFrame from the results
results_pris_df2_h = pd.DataFrame(results_pris_h)

# Display or save the results DataFrame
print(results_pris_df2_h)

#### plot cumulative distribution
# Merge results_df with df on the 'id' column
results_pris_df2_h = results_pris_df2_h.merge(df2[['id', 'llm', 'goal', 'personality_prisoner', 'personality_guard']], on='id', how='left')

import seaborn as sns
# Create a new column combining personality_pris and personality_prisoner
results_pris_df2_h['personality_comb'] = results_pris_df2_h['personality_guard'] + ", " + results_pris_df2_h['personality_prisoner']

results_pris_df2_h['personality_comb'] = pd.Categorical(results_pris_df2_h['personality_comb'], categories=desired_order, ordered=True)

# Sort the DataFrame by 'personality_comb' to ensure the plotting order matches
results_pris_df2_h = results_pris_df2_h.sort_values('personality_comb')
# Get the unique values of personality_comb and goal
personality_combinations = results_pris_df2_h['personality_comb'].unique()
goals = results_pris_df2_h['goal'].unique()

# Number of rows = number of unique combinations of personality_pris and personality_prisoner
# Number of columns = number of unique goal values
n_rows = len(personality_combinations)
n_cols = len(goals)

# Create the subplots grid
fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols * 6.5, n_rows * 2.5), sharex=True, sharey=True)

# Flatten the axes array for easy iteration
axes = axes.flatten()

# Loop through each personality_comb and goal, and create the cumulative distribution plot
for i, (personality_comb, goal) in enumerate([(p, g) for p in personality_combinations for g in goals]):
    
    # Subset the data based on current personality_comb and goal
    subset = results_pris_df2_h[(results_pris_df2_h['personality_comb'] == personality_comb) & 
                              (results_pris_df2_h['goal'] == goal)]
    
    # Plot the cumulative distribution of ssr_f_test_pvalue hued by llm
    sns.ecdfplot(data=subset, x='ssr_f_test_pvalue', hue='llm', ax=axes[i])
    
    # Set the title and labels for the subplot
    axes[i].set_title(f'{personality_comb} - Goal: {goal}', size=16)
    axes[i].set_xlabel('F-test p-value', size=16)
    axes[i].set_ylabel('Cumulative Dist.', size=16)
    
    # Add a vertical dashed line at x = 0.05
    axes[i].axvline(x=0.05, color='red', linestyle='--', lw=1.5)
    
    # Increase the size of x and y ticks
    axes[i].tick_params(axis='both', which='major', labelsize=14)
    
# Show the legend only for the first subplot, with a larger font size
    if i == 0:
        handles, labels = axes[i].get_legend_handles_labels()
        if handles:  # Only add legend if there are handles
            legend = axes[i].legend(handles, labels, fontsize=12, title="LLM", title_fontsize=12)
    else:
        axes[i].get_legend().remove() 

# Adjust the layout for better spacing
plt.tight_layout()
#save
fig.savefig('granger_harass_pris_cause_guard.pdf') # Adjust layout to accommodate LLM titles at the top
#show
plt.show()

# calculate % of significant
# Calculate the number of rows where ssr_f_test_pvalue < 0.05
count_low_pvalue_pris_h = (results_pris_df2_h['ssr_f_test_pvalue'] < 0.05).sum()

# Calculate the total number of rows
total_rows_pris_h = len(results_pris_df2_h)

# Calculate the percentage
percentage_low_pvalue_pris_h = (count_low_pvalue_pris_h / total_rows_pris_h) * 100

# Print the result
print(f"Percentage of rows with ssr_f_test_pvalue < 0.05: {percentage_low_pvalue_pris_h:.2f}%")

# calculate % by group

# Merge results_df with df on the 'id' column
results_pris_df2_h = results_pris_df2_h.merge(df2[['id', 'llm', 'goal', 'personality_prisoner', 'personality_guard']], on='id', how='left')


# Step 1: Group by 'llm', 'personality_prisoner', 'personality_pris', and 'goal'
grouped_pris_h = results_pris_df2_h.groupby(['llm', 'personality_prisoner', 'personality_guard', 'goal'])

# Step 2: Calculate the percentage of rows with 'ssr_ftest_pvalue' < 0.05 for each group
percentage_df_pris_h = grouped_pris_h.apply(lambda x: (x['ssr_f_test_pvalue'] < 0.05).mean() * 100).reset_index()

# Step 3: Rename the columns for clarity
percentage_df_pris_h = percentage_df_pris_h.rename(columns={0: 'percentage_below_0.05_pris'})

# combine the two
combined_df_granger_har = pd.merge(percentage_df_pris_h, percentage_df_guard_h, 
                       on=['llm', 'personality_prisoner', 'personality_guard', 'goal'], 
                       how='inner')


''' OPEN AI VIOLENCE'''

# Load and prepare the data
df3 = pd.read_excel('openai_toxicity_analysis_full_arrmay.xlsx')

# filter out mixtral and mistral
df3 = df3[df3['llm'].isin(['command-r:latest', 'llama3:latest', 'orca2:latest', 'gpt-4.1-2025-04-14'])]

#rename llms
df3['llm'] = df3['llm'].replace({
    'command-r:latest': 'command-r',
    'llama3:latest': 'llama3',
    'orca2:latest': 'orca2',
    'gpt-4.1-2025-04-14':'gpt4.1'
})

#rename personalities
# Rename values in 'personality_guard' column
df3['personality_guard'] = df3['personality_guard'].replace({
    'Good Guard': 'Respectful Guard',
    'Bad Guard': 'Abusive Guard',
    'Blank Personalities':'Blank Pers. Guard'
})

# Rename values in 'personality_prisoner' column
df3['personality_prisoner'] = df3['personality_prisoner'].replace({
    'Good Prisoner': 'Peaceful Prisoner',
    'Bad Prisoner': 'Rebellious Prisoner',
    'Blank Personalities': 'Blank Pers. Prisoner'
})

# Step 2: Remove columns that contain "violence" in their names
columns_to_keep = [col for col in df3.columns if 'harassment' not in col]

# Select the desired columns
df3 = df3.loc[:, columns_to_keep]

#import reliability
rel = pd.read_excel('updated_toxicity_analysis_scores_arrmay.xlsx')



# Rename the first column in each DataFrame to 'id'
df3.rename(columns={df3.columns[0]: 'id'}, inplace=True)
rel.rename(columns={rel.columns[0]: 'id'}, inplace=True)

# Step: Identify IDs in rel where goal_achieved is 'NAN'
ids_to_remove = set(rel[rel['goal_achieved'] == 'NAN']['id'])

# Step: Filter filtered_df to remove rows where id is in ids_to_remove
df3 = df3[~df3['id'].isin(ids_to_remove)]


# Rename 'unnamed' column to 'id'
df3.rename(columns={'Unnamed: 0': 'id'}, inplace=True)

# Drop 'mess10_guard' column
df3.drop(columns=['mess10_guard_violence'], inplace=True)

# Prepare a list of columns for reshaping
guard_mess_cols_v = [f'mess{i}_guard_violence' for i in range(1, 10)]
pris_mess_cols_v = [f'mess{i}_pris_violence' for i in range(1, 10)]

# Melt the DataFrame to long format for guard messages
guard_mess_long_v = pd.melt(df3, id_vars=['id', 'llm', 'Risks', 'Research Oversight', 'goal', 'personality_prisoner', 'personality_guard'],
                          value_vars=guard_mess_cols_v,
                          var_name='message_type',
                          value_name='guard_mess')

# Melt the DataFrame to long format for prisoner messages
pris_mess_long_v = pd.melt(df3, id_vars=['id', 'llm', 'Risks', 'Research Oversight', 'goal', 'personality_prisoner', 'personality_guard'],
                         value_vars=pris_mess_cols_v,
                         var_name='message_type',
                         value_name='pris_mess')

# Extract the message number from 'message_type'
guard_mess_long_v['message_number'] = guard_mess_long_v['message_type'].str.extract(r'(\d+)').astype(int)
pris_mess_long_v['message_number'] = pris_mess_long_v['message_type'].str.extract(r'(\d+)').astype(int)

# Drop the 'message_type' column
guard_mess_long_v.drop(columns=['message_type'], inplace=True)
pris_mess_long_v.drop(columns=['message_type'], inplace=True)

# Merge the two long-format DataFrames on 'id' and 'message_number'
merged_df3_v = pd.merge(guard_mess_long_v, pris_mess_long_v, on=['id', 'message_number'], how='inner')

# Optionally, sort the DataFrame by 'id' and 'message_number'
merged_df3_v.sort_values(by=['id', 'message_number'], inplace=True)




# Reset index
merged_df3_v.reset_index(drop=True, inplace=True)

# Display the reshaped DataFrame
print(merged_df3_v.head())


'''granger'''


### check stationarity first:
from statsmodels.tsa.stattools import adfuller
# Initialize lists to store non-stationary ids
non_stationary_guard_ids_v = []
non_stationary_pris_ids_v = []

# Group by 'id'
for id_value, group in merged_df3_v.groupby('id'):
    # Extract the time series for guard_mess and pris_mess
    guard_mess_series = group['guard_mess'].dropna()
    pris_mess_series = group['pris_mess'].dropna()
    
    # Perform Adf3 test on guard_mess
    guard_adf_result = adfuller(guard_mess_series)
    guard_is_stationary = guard_adf_result[1] < 0.05  # Stationary if p-value < 0.05
    
    # Perform Adf3 test on pris_mess
    pris_adf_result = adfuller(pris_mess_series)
    pris_is_stationary = pris_adf_result[1] < 0.05  # Stationary if p-value < 0.05
    
    # Check if guard_mess is non-stationary
    if not guard_is_stationary:
        non_stationary_guard_ids_v.append(id_value)
        
    # Check if pris_mess is non-stationary
    if not pris_is_stationary:
        non_stationary_pris_ids_v.append(id_value)
        
## difference those that are not stationary 
# Step 2: Apply differencing to non-stationary time series directly in the original columns

# Apply differencing to guard_mess for non-stationary ids
for id_value in non_stationary_guard_ids_v:
    mask = merged_df3_v['id'] == id_value
    merged_df3_v.loc[mask, 'guard_mess'] = merged_df3_v.loc[mask, 'guard_mess'].diff()

# Apply differencing to pris_mess for non-stationary ids
for id_value in non_stationary_pris_ids_v:
    mask = merged_df3_v['id'] == id_value
    merged_df3_v.loc[mask, 'pris_mess'] = merged_df3_v.loc[mask, 'pris_mess'].diff()

# Optionally, drop rows with NaN values that resulted from differencing (usually the first row per id)
merged_df3_v.dropna(subset=['guard_mess', 'pris_mess'], inplace=True)


## now perform Granger (test whether guard causes prisoner)
from statsmodels.tsa.stattools import grangercausalitytests
# Initialize a list to store the results
results_guard_v = []

# Group by 'id'
for id_value, group in merged_df3_v.groupby('id'):
    # Ensure we have data for the Granger causality test
    if len(group) < 2:
        continue  # Skip groups with insufficient data

    # Prepare data for Granger causality test
    time_series_data_guard_v = group[['guard_mess', 'pris_mess']].dropna()
    
    if len(time_series_data_guard_v) < 2:
        continue  # Skip if there are not enough observations after dropping NA

    # Perform Granger Causality Test
    try:
        test_result_guard_v = grangercausalitytests(time_series_data_guard_v, maxlag=1, verbose=False)
        
        # Extract results
        f_test_stat = test_result_guard_v[1][0]['ssr_ftest'][0]
        f_test_pvalue = test_result_guard_v[1][0]['ssr_ftest'][1]
        chi2_test_stat = test_result_guard_v[1][0]['ssr_chi2test'][0]
        chi2_test_pvalue = test_result_guard_v[1][0]['ssr_chi2test'][1]

        # Store results in a list
        results_guard_v.append({
            'id': id_value,
            'ssr_f_test_stat': f_test_stat,
            'ssr_f_test_pvalue': f_test_pvalue,
            'ssr_chi2_test_stat': chi2_test_stat,
            'ssr_chi2_test_pvalue': chi2_test_pvalue
        })
        
    except Exception as e:
        print(f"Error processing id={id_value}: {e}")
        continue

# Create a DataFrame from the results
results_guard_df3_v = pd.DataFrame(results_guard_v)

# Display or save the results DataFrame
print(results_guard_df3_v)


#### plot cumulative distribution
# Merge results_df with df on the 'id' column
results_guard_df3_v = results_guard_df3_v.merge(df3[['id', 'llm', 'goal', 'personality_prisoner', 'personality_guard']], on='id', how='left')

import seaborn as sns
# Create a new column combining personality_guard and personality_prisoner
results_guard_df3_v['personality_comb'] = results_guard_df3_v['personality_guard'] + ", " + results_guard_df3_v['personality_prisoner']
results_guard_df3_v['personality_comb'] = pd.Categorical(results_guard_df3_v['personality_comb'], categories=desired_order, ordered=True)

# Sort the DataFrame by 'personality_comb' to ensure the plotting order matches
results_guard_df3_v = results_guard_df3_v.sort_values('personality_comb')
# Get the unique values of personality_comb and goal
personality_combinations = results_guard_df3_v['personality_comb'].unique()
goals = results_guard_df3_v['goal'].unique()

# Number of rows = number of unique combinations of personality_guard and personality_prisoner
# Number of columns = number of unique goal values
n_rows = len(personality_combinations)
n_cols = len(goals)

# Create the subplots grid
fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols * 6.5, n_rows * 2.5), sharex=True, sharey=True)

# Flatten the axes array for easy iteration
axes = axes.flatten()

# Loop through each personality_comb and goal, and create the cumulative distribution plot
for i, (personality_comb, goal) in enumerate([(p, g) for p in personality_combinations for g in goals]):
    
    # Subset the data based on current personality_comb and goal
    subset = results_guard_df3_v[(results_guard_df3_v['personality_comb'] == personality_comb) & 
                              (results_guard_df3_v['goal'] == goal)]
    
    # Plot the cumulative distribution of ssr_f_test_pvalue hued by llm
    sns.ecdfplot(data=subset, x='ssr_f_test_pvalue', hue='llm', ax=axes[i])
    
    # Set the title and labels for the subplot
    axes[i].set_title(f'{personality_comb} - Goal: {goal}', size=16)
    axes[i].set_xlabel('F-test p-value', size=16)
    axes[i].set_ylabel('Cumulative Dist.', size=16)
    
    # Add a vertical dashed line at x = 0.05
    axes[i].axvline(x=0.05, color='red', linestyle='--', lw=1.5)
    
    # Increase the size of x and y ticks
    axes[i].tick_params(axis='both', which='major', labelsize=14)
    
# Show the legend only for the first subplot, with a larger font size
    if i == 0:
        handles, labels = axes[i].get_legend_handles_labels()
        if handles:  # Only add legend if there are handles
            legend = axes[i].legend(handles, labels, fontsize=12, title="LLM", title_fontsize=12)
    else:
        axes[i].get_legend().remove() 

# Adjust the layout for better spacing
plt.tight_layout()
#save
fig.savefig('granger_violence_guard_cause_pris.pdf') # Adjust layout to accommodate LLM titles at the top
# Show the plot
plt.show()

# calculate % of significant
# Calculate the number of rows where ssr_f_test_pvalue < 0.05
count_low_pvalue_guard_v = (results_guard_df3_v['ssr_f_test_pvalue'] < 0.05).sum()

# Calculate the total number of rows
total_rows_guard_v = len(results_guard_df3_v)

# Calculate the percentage
percentage_low_pvalue_guard_v = (count_low_pvalue_guard_v / total_rows_guard_v) * 100

# Print the result
print(f"Percentage of rows with ssr_f_test_pvalue < 0.05: {percentage_low_pvalue_guard_v:.2f}%")

# by group
# retrieve relevant columns from df for analysis
df3 = df3.rename(columns={'Unnamed': 'id'})  # Rename 'Unnamed' to 'id' in df if not already done

# Merge results_df with df on the 'id' column
results_guard_df3_v = results_guard_df3_v.merge(df3[['id', 'llm', 'goal', 'personality_prisoner', 'personality_guard']], on='id', how='left')





# calculate % by group
# Step 1: Group by 'llm', 'personality_prisoner', 'personality_guard', and 'goal'
grouped_guard_v = results_guard_df3_v.groupby(['llm', 'personality_prisoner', 'personality_guard', 'goal'])

# Step 2: Calculate the percentage of rows with 'ssr_ftest_pvalue' < 0.05 for each group
percentage_df_guard_v = grouped_guard_v.apply(lambda x: (x['ssr_f_test_pvalue'] < 0.05).mean() * 100).reset_index()

# Step 3: Rename the columns for clarity
percentage_df_guard_v = percentage_df_guard_v.rename(columns={0: 'percentage_below_0.05_guard_v'})

############## now test effect of prisoner on guard

# Initialize a list to store the results

results_pris_v = []

# Group by 'id'
for id_value, group in merged_df3_v.groupby('id'):
    # Ensure we have data for the Granger causality test
    if len(group) < 2:
        continue  # Skip groups with insufficient data

    # Prepare data for Granger causality test
    time_series_data_pris_v = group[['pris_mess', 'guard_mess']].dropna()
    
    if len(time_series_data_pris_v) < 2:
        continue  # Skip if there are not enough observations after dropping NA

    # Perform Granger Causality Test
    try:
        test_result_pris_v = grangercausalitytests(time_series_data_pris_v, maxlag=1, verbose=False)
        
        # Extract results
        f_test_stat = test_result_pris_v[1][0]['ssr_ftest'][0]
        f_test_pvalue = test_result_pris_v[1][0]['ssr_ftest'][1]
        chi2_test_stat = test_result_pris_v[1][0]['ssr_chi2test'][0]
        chi2_test_pvalue = test_result_pris_v[1][0]['ssr_chi2test'][1]

        # Store results in a list
        results_pris_v.append({
            'id': id_value,
            'ssr_f_test_stat': f_test_stat,
            'ssr_f_test_pvalue': f_test_pvalue,
            'ssr_chi2_test_stat': chi2_test_stat,
            'ssr_chi2_test_pvalue': chi2_test_pvalue
        })
        
    except Exception as e:
        print(f"Error processing id={id_value}: {e}")
        continue

# Create a DataFrame from the results
results_pris_df3_v = pd.DataFrame(results_pris_v)

# Display or save the results DataFrame
print(results_pris_df3_v)


#### plot cumulative distribution
# Merge results_df with df on the 'id' column
results_pris_df3_v = results_pris_df3_v.merge(df3[['id', 'llm', 'goal', 'personality_prisoner', 'personality_guard']], on='id', how='left')

import seaborn as sns
# Create a new column combining personality_pris and personality_prisoner
results_pris_df3_v['personality_comb'] = results_pris_df3_v['personality_guard'] + ", " + results_pris_df3_v['personality_prisoner']
results_pris_df3_v['personality_comb'] = pd.Categorical(results_pris_df3_v['personality_comb'], categories=desired_order, ordered=True)

# Sort the DataFrame by 'personality_comb' to ensure the plotting order matches
results_pris_df3_v = results_pris_df3_v.sort_values('personality_comb')
# Get the unique values of personality_comb and goal
personality_combinations = results_pris_df3_v['personality_comb'].unique()
goals = results_pris_df3_v['goal'].unique()

# Number of rows = number of unique combinations of personality_pris and personality_prisoner
# Number of columns = number of unique goal values
n_rows = len(personality_combinations)
n_cols = len(goals)

# Create the subplots grid
fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols * 6.5, n_rows * 2.5), sharex=True, sharey=True)

# Flatten the axes array for easy iteration
axes = axes.flatten()

# Loop through each personality_comb and goal, and create the cumulative distribution plot
for i, (personality_comb, goal) in enumerate([(p, g) for p in personality_combinations for g in goals]):
    
    # Subset the data based on current personality_comb and goal
    subset = results_pris_df3_v[(results_pris_df3_v['personality_comb'] == personality_comb) & 
                              (results_pris_df3_v['goal'] == goal)]
    
    # Plot the cumulative distribution of ssr_f_test_pvalue hued by llm
    sns.ecdfplot(data=subset, x='ssr_f_test_pvalue', hue='llm', ax=axes[i])
    
    # Set the title and labels for the subplot
    axes[i].set_title(f'{personality_comb} - Goal: {goal}', size=16)
    axes[i].set_xlabel('F-test p-value', size=16)
    axes[i].set_ylabel('Cumulative Dist.', size=16)
    
    # Add a vertical dashed line at x = 0.05
    axes[i].axvline(x=0.05, color='red', linestyle='--', lw=1.5)
    
    # Increase the size of x and y ticks
    axes[i].tick_params(axis='both', which='major', labelsize=14)
    
# Show the legend only for the first subplot, with a larger font size
    if i == 0:
        handles, labels = axes[i].get_legend_handles_labels()
        if handles:  # Only add legend if there are handles
            legend = axes[i].legend(handles, labels, fontsize=12, title="LLM", title_fontsize=12)
    else:
        axes[i].get_legend().remove() 

# Adjust the layout for better spacing
plt.tight_layout()
#save
fig.savefig('granger_violence_pris_cause_guard.pdf') # Adjust layout to accommodate LLM titles at the top
#show
plt.show()

# calculate % of significant
# Calculate the number of rows where ssr_f_test_pvalue < 0.05
count_low_pvalue_pris_v = (results_pris_df3_v['ssr_f_test_pvalue'] < 0.05).sum()

# Calculate the total number of rows
total_rows_pris_v = len(results_pris_df3_v)

# Calculate the percentage
percentage_low_pvalue_pris_v = (count_low_pvalue_pris_v / total_rows_pris_v) * 100

# Print the result
print(f"Percentage of rows with ssr_f_test_pvalue < 0.05: {percentage_low_pvalue_pris_h:.2f}%")

# calculate % by group

# Merge results_df with df on the 'id' column
results_pris_df3_v = results_pris_df3_v.merge(df3[['id', 'llm', 'goal', 'personality_prisoner', 'personality_guard']], on='id', how='left')


# Step 1: Group by 'llm', 'personality_prisoner', 'personality_pris', and 'goal'
grouped_pris_v = results_pris_df3_v.groupby(['llm', 'personality_prisoner', 'personality_guard', 'goal'])

# Step 2: Calculate the percentage of rows with 'ssr_ftest_pvalue' < 0.05 for each group
percentage_df_pris_v = grouped_pris_v.apply(lambda x: (x['ssr_f_test_pvalue'] < 0.05).mean() * 100).reset_index()

# Step 3: Rename the columns for clarity
percentage_df_pris_v = percentage_df_pris_v.rename(columns={0: 'percentage_below_0.05_pris'})

# combine the two
combined_df_granger_vio = pd.merge(percentage_df_pris_v, percentage_df_guard_v, 
                       on=['llm', 'personality_prisoner', 'personality_guard', 'goal'], 
                       how='inner')






