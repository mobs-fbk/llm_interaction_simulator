# -*- coding: utf-8 -*-
"""
Created on Wed Oct  8 12:04:09 2025


"""
import pandas as pd
import os
from pathlib import Path
# Set working directory



# Load the Excel file
df = pd.read_excel('updated_toxicity_analysis_scores_arrmay.xlsx')

# Standardize column names
df.columns = df.columns.str.strip()

# Convert relevant columns to string and clean spaces
for col in ['goal_achieved', 'llm', 'Risks', 'Research Oversight', 
            'goal', 'personality_prisoner', 'personality_guard']:
    df[col] = df[col].astype(str).str.strip()

# Define failure condition
failures = df[df['goal_achieved'] == 'NAN']

# Grouping columns for full scenario
group_cols = ['llm', 'Risks', 'Research Oversight', 
              'goal', 'personality_prisoner', 'personality_guard']

# Count failures per scenario
failure_table = failures.groupby(group_cols).size().reset_index(name='n_failures')

# Count total runs per scenario
total_table = df.groupby(group_cols).size().reset_index(name='n_total')

# Merge to compute % failures per scenario
summary_table = pd.merge(total_table, failure_table, on=group_cols, how='left').fillna(0)
summary_table['percent_failures'] = (summary_table['n_failures'] / summary_table['n_total'] * 100).round(2)

# Sort
summary_table = summary_table.sort_values(group_cols).reset_index(drop=True)

# Create a dictionary of DataFrames per LLM with marginal failure %
llm_tables = {}
for llm_name, group_df in summary_table.groupby('llm'):
    group_df = group_df.reset_index(drop=True)
    
    # Compute total failures for this LLM
    total_failures_llm = group_df['n_failures'].sum()
    
    # Compute marginal failure % relative to total failures for the LLM
    group_df['marginal_failure_percent'] = (group_df['n_failures'] / total_failures_llm * 100).round(2)
    
    # Store the table
    llm_tables[llm_name] = group_df



# Optional: save each table to CSV
for llm_name, table in llm_tables.items():
    safe_name = llm_name.replace(":", "_").replace("/", "_").replace(" ", "_")
    table.to_csv(f'failures_by_full_scenario_{safe_name}.csv', index=False)
    
    
''' breakdown by personality, per llm'''
# ---------- Helper to robustly find a column ----------
def find_column(df, candidates):
    cols = list(df.columns)
    for c in candidates:
        if c in cols:
            return c
    # normalized fallback
    def norm(s): return ''.join(ch for ch in s.lower() if ch.isalnum() or ch == '_')
    norm_cols = {norm(c): c for c in cols}
    for c in candidates:
        key = norm(c)
        if key in norm_cols:
            return norm_cols[key]
    return None

# ---------- Load original dataset ----------
df = pd.read_excel('updated_toxicity_analysis_scores_arrmay.xlsx')
df.columns = df.columns.str.strip()  # trim whitespace

# ---------- Find & rename relevant columns (robust) ----------
llm_col = find_column(df, ['llm', 'model', 'model_name'])
goal_col = find_column(df, ['goal', 'task', 'goal_type'])
goal_achieved_col = find_column(df, ['goal_achieved', 'goal result', 'goal_result', 'goalachieved'])
prisoner_col = find_column(df, [
    'personality_prisoner', 'personality prisoner', 'prisoner_personality', 'prisoner personality'
])
guard_col = find_column(df, [
    'personality_guard', 'personality guard', 'guard_personality', 'guard personality'
])

required = {
    'llm': llm_col, 'goal': goal_col, 'goal_achieved': goal_achieved_col,
    'personality_prisoner': prisoner_col, 'personality_guard': guard_col
}
missing = [k for k, v in required.items() if v is None]
if missing:
    raise ValueError(f"Required columns not found in file: {missing}. Actual columns:\n{df.columns.tolist()}")

df = df.rename(columns={
    llm_col: 'llm',
    goal_col: 'goal',
    goal_achieved_col: 'goal_achieved',
    prisoner_col: 'personality_prisoner',
    guard_col: 'personality_guard'
})

# ---------- Clean & normalize text columns ----------
for c in ['llm', 'goal', 'goal_achieved', 'personality_prisoner', 'personality_guard']:
    df[c] = df[c].astype(str).str.strip()

# Normalize common variants of goal_achieved into canonical tokens
def canonical_goal_status(x):
    s = str(x).strip().lower()
    if s in {'yes', 'y', 'true', '1'}:
        return 'Yes'
    if s in {'no', 'n', 'false', '0'}:
        return 'No'
    if s in {'not tried', 'nottried', 'not_tried', 'not-tried', 'not tried '}:
        return 'NotTried'
    if s in {'nan', 'none', 'na', 'n/a', ''}:
        return 'NAN'
    # fallback: keep original capitalized-ish value
    return x.strip()

df['goal_achieved'] = df['goal_achieved'].apply(canonical_goal_status)

# ---------- Build summary grouped by (llm, goal, prisoner, guard) ----------
group_cols = ['llm', 'goal', 'personality_prisoner', 'personality_guard']

# Only rows with legitimate outcomes for totals:
valid_df = df[df['goal_achieved'].isin(['Yes', 'No', 'NotTried'])].copy()

# Totals (include NotTried in n_total)
totals = valid_df.groupby(group_cols).size().reset_index(name='n_total')

# Attempts = Yes or No
attempts = valid_df[valid_df['goal_achieved'].isin(['Yes', 'No'])] \
    .groupby(group_cols).size().reset_index(name='n_attempts')

# Successes = Yes
successes = valid_df[valid_df['goal_achieved'] == 'Yes'] \
    .groupby(group_cols).size().reset_index(name='n_success')

# Merge counts
summary = totals.merge(attempts, on=group_cols, how='left') \
                .merge(successes, on=group_cols, how='left') \
                .fillna(0)

# Compute probabilities (percent)
summary['P_attempt'] = (summary['n_attempts'] / summary['n_total'] * 100).round(2)
# Avoid division by zero for P_success_given_attempt
summary['P_success_given_attempt'] = (
    summary['n_success'] / summary['n_attempts'].replace(0, pd.NA) * 100
).round(2).fillna(0)

# Sort for readability
summary = summary.sort_values(group_cols).reset_index(drop=True)

# ---------- Create per-LLM tables (guaranteeing personality columns are present) ----------
out_dir = Path('attempt_success_by_goal_and_personality_tables')
out_dir.mkdir(exist_ok=True)
llm_tables = {}

for llm_name, subset in summary.groupby('llm'):
    # Keep personality columns in the output
    cols_order = [
        'goal', 'personality_prisoner', 'personality_guard',
        'n_total', 'n_attempts', 'n_success', 'P_attempt', 'P_success_given_attempt'
    ]
    sub = subset[cols_order].reset_index(drop=True)
    llm_tables[llm_name] = sub
    safe_name = str(llm_name).replace(':', '_').replace('/', '_').replace(' ', '_')
    sub.to_csv(out_dir / f"attempt_success_{safe_name}.csv", index=False)
    print(f"Saved CSV for LLM='{llm_name}' -> {out_dir / f'attempt_success_{safe_name}.csv'} (rows: {len(sub)})")

# ---------- Quick check / display for one LLM (example) ----------
example_llm = list(llm_tables.keys())[0]  # pick first available LLM
print(f"\nExample table for LLM: {example_llm}")
display(llm_tables[example_llm].head(12))
