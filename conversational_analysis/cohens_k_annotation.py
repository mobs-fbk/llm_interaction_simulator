# -*- coding: utf-8 -*-
"""
Created on Tue Oct  7 17:22:52 2025


"""

import os
import pandas as pd
from sklearn.metrics import cohen_kappa_score

# Set working directory
os.chdir(r'C:\Users\Gian Maria\Desktop\FBK\llm\no_mistral_mixtral\arr2025')

# List of Excel files
files = ['command-r.xlsx', 'gpt.xlsx', 'orca2.xlsx', 'llama3.xlsx']
#files = ['gpt.xlsx' ]

# Helper function to compute disagreement and Cohen's kappa
# MODIFICATION: Now returns n_total as the fourth value.
def compute_metrics(df, col1, col2):
    if col1 not in df.columns or col2 not in df.columns:
        return None, None, 0, 0 # Added 0 for n_total
    # Clean labels: lowercase and strip spaces
    # This subset 'sub' is used for Kappa/Disagreement calculation
    sub = df[[col1, col2]].dropna().astype(str).apply(lambda x: x.str.lower().str.strip())
    n_total = len(sub)
    n_disagree = (sub[col1] != sub[col2]).sum()
    percent_disagree = n_disagree / n_total * 100 if n_total > 0 else None
    kappa = cohen_kappa_score(sub[col1], sub[col2]) if n_total > 0 else None
    return n_disagree, percent_disagree, kappa, n_total

# Store results
results = []

for file in files:
    try:
        # Read all sheets and collapse
        sheet_names = pd.ExcelFile(file).sheet_names
        dfs = [pd.read_excel(file, sheet_name=sheet) for sheet in sheet_names]
        combined_df = pd.concat(dfs, ignore_index=True)

        # GOAL metrics (Disagreement and Kappa)
        # MODIFICATION: capturing n_total_goal
        n_dis_goal, pct_dis_goal, kappa_goal, n_total_goal = compute_metrics(combined_df, 'GOAL1', 'GOAL2')

        # TURN_DISCR metrics (Disagreement and Kappa)
        # MODIFICATION: capturing n_total_turn
        n_dis_turn, pct_dis_turn, kappa_turn, n_total_turn = compute_metrics(combined_df, 'TURN1_DISCR', 'TURN2_DISCR')

        # ----------------------------------------------------------------------
        # NEW: Numerical Difference metrics for TURN_DISCR
        # ----------------------------------------------------------------------
        diff_cols = ['TURN1_DISCR', 'TURN2_DISCR']
        
        # Select columns, drop NaNs, and make a copy to avoid warnings
        diff_df = combined_df[diff_cols].dropna().copy()
        
        # Convert to numeric, coercing any non-numeric strings/values to NaN
        diff_df[diff_cols] = diff_df[diff_cols].apply(pd.to_numeric, errors='coerce')
        
        # Drop rows where conversion resulted in NaN (i.e., truly non-numeric values)
        diff_df = diff_df.dropna() 
        
        n_total_diff = len(diff_df)
        
        if n_total_diff > 0:
            # Calculate absolute difference
            abs_diff = (diff_df['TURN1_DISCR'] - diff_df['TURN2_DISCR']).abs()
            mean_abs_diff = abs_diff.mean()
            std_abs_diff = abs_diff.std()
        else:
            mean_abs_diff = None
            std_abs_diff = None
        # ----------------------------------------------------------------------

        # Append results
        results.append({
            'Dataset': file,
            'N_total_GOAL': n_total_goal,
            'N_disagreement_GOAL': n_dis_goal,
            'Percent_disagreement_GOAL': pct_dis_goal,
            'Cohen_kappa_GOAL': kappa_goal,
            'N_total_TURN_DISCR': n_total_turn,
            'N_disagreement_TURN_DISCR': n_dis_turn,
            'Percent_disagreement_TURN_DISCR': pct_dis_turn,
            'Cohen_kappa_TURN_DISCR': kappa_turn,
            # NEW COLUMNS
            'N_total_TURN_DISCR_Numeric': n_total_diff,
            'Avg_Abs_Diff_TURN_DISCR': mean_abs_diff,
            'Std_Abs_Diff_TURN_DISCR': std_abs_diff
        })

    except Exception as e:
        results.append({
            'Dataset': file,
            'Error': str(e)
        })

# Combine and display results
summary_df = pd.DataFrame(results)
print(summary_df)

# Optionally save to CSV
summary_df.to_csv('cohen_kappa_disagreement_summary.csv', index=False)
