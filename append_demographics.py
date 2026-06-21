import pandas as pd
import numpy as np

print("Loading Master Dataset and SEDA Covariates...")
df_master = pd.read_csv('../brain/1aa0d3c1-7a3f-4417-9041-18ac4fb2f2a3/tri_state_master_with_niche.csv', dtype={'sedaadmin': str})
df_cov = pd.read_csv('seda_cov.csv', dtype={'sedaadmin': str})

# Select specific deep demographics
demo_cols = [
    'sedaadmin', 
    'perwht', 'perhsp', 'perblk', 'perasn', 
    'baplusavgall', 'unempavgall', 'povertyavgall', 'single_momavgall', 'lninc50avgall'
]

df_demo = df_cov[demo_cols].copy()

# Convert percentages from decimals (0.50) to strict Percentages (50.0)
pct_cols = ['perwht', 'perhsp', 'perblk', 'perasn', 'baplusavgall', 'unempavgall', 'povertyavgall', 'single_momavgall']
for col in pct_cols:
    df_demo[col] = (df_demo[col] * 100).round(1)

# Convert Log Income to absolute dollars
df_demo['Median_Income_Est'] = np.exp(df_demo['lninc50avgall']).round(-3) # Round to nearest thousand

# Drop existing columns in master if they exist (idempotency)
cols_to_drop = [c for c in df_demo.columns if c in df_master.columns and c != 'sedaadmin']
if cols_to_drop:
    df_master.drop(columns=cols_to_drop, inplace=True)

# Merge
df_master = df_master.merge(df_demo.drop(columns=['lninc50avgall']), on='sedaadmin', how='left')

# Save
df_master.to_csv('../brain/1aa0d3c1-7a3f-4417-9041-18ac4fb2f2a3/tri_state_master_with_niche.csv', index=False)
print("Phase 4: Advanced Demographics successfully merged!")

# Print top 15 most educated districts
df_edu = df_master.sort_values(by='baplusavgall', ascending=False)
print("\nTop 15 Most Educated Districts (BA+ %):")
cols_to_show = ['State', 'District_Name', 'baplusavgall', 'Median_Income_Est', 'perwht', 'perasn', 'perblk', 'perhsp', 'Predicted_Niche_Score']
print(df_edu[cols_to_show].head(15).to_string(index=False))
