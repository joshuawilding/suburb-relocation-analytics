import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import warnings
warnings.filterwarnings('ignore')

print("Loading data...")
# Load master dataset
df_master = pd.read_csv('tri_state_master_with_niche.csv')

# Load and merge political data
df_tracts = pd.read_csv('nyc_metro_tract_unified_metrics.csv', dtype={'TractFIPS': str})
df_crosswalk = pd.read_excel('GRF21/grf21_lea_tract.xlsx', dtype={'LEAID': str, 'TRACT': str})
df_tracts['TRACT'] = df_tracts['TractFIPS']
df_merged = df_crosswalk.merge(df_tracts, on='TRACT', how='inner')
df_pol_agg = df_merged.groupby('LEAID').agg({'Dem_Vote_Share_2020': 'mean'}).reset_index()

df_master['sedaadmin'] = df_master['sedaadmin'].astype(str).str.zfill(7)
df_master = df_master.merge(df_pol_agg, left_on='sedaadmin', right_on='LEAID', how='left')

# Define core dimensions
cols = [
    'SEDA_Absolute_Score', 'SEDA_Growth_Score', 
    'perwht', 'perasn', 'baplusavgall', 
    'Dem_Vote_Share_2020', 'Current_3BR_Price_Mean', 
    'Drive_Mins_To_Manhattan'
]

# Ensure numeric and drop NaNs for these cols
df = df_master[cols].apply(pd.to_numeric, errors='coerce').dropna()

# Convert percentages to actual 0-100 scale if they are 0-1
if df['perwht'].max() <= 1.0:
    df['perwht'] = df['perwht'] * 100
    df['perasn'] = df['perasn'] * 100
    df['baplusavgall'] = df['baplusavgall'] * 100

print("\n--- DISTRIBUTIONS & PERCENTILES (For Intentional Cutoffs) ---")
percentiles = [0.10, 0.25, 0.50, 0.75, 0.90]
desc = df.describe(percentiles=percentiles).T
print(desc[['min', '10%', '25%', '50%', '75%', '90%', 'max']].round(2).to_string())

print("\n--- FULL CORRELATION MATRIX ---")
corr = df.corr().round(2)
print(corr.to_string())

# Generate Pairplot for visual relationships
plt.figure(figsize=(15, 15))
# Sample down to make pairplot readable and fast
sns_plot = sns.pairplot(df, corner=True, plot_kws={'alpha': 0.3})
sns_plot.fig.suptitle("Relationships Between All Filtering Dimensions", y=1.02, fontsize=16, weight='bold')

out_path = 'dimensions_pairplot.png'
sns_plot.savefig(out_path, dpi=200, bbox_inches='tight')
print(f"\nPairplot saved to {out_path}")
