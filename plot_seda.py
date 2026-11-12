import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

print("Loading data...")
df = pd.read_csv('tri_state_master_with_niche.csv')

print("Calculating Correlations...")
cols = ['SEDA_Absolute_Score', 'SEDA_Growth_Score', 'Predicted_Niche_Score', 'Median_Income_Est', 'Current_3BR_Price_Mean']
corr = df[cols].corr().round(2)
print("\n--- Correlations ---")
print(corr.to_string())

# Set up the plot
plt.figure(figsize=(12, 8))
sns.scatterplot(
    data=df, 
    x='SEDA_Absolute_Score', 
    y='SEDA_Growth_Score', 
    alpha=0.3, 
    color='grey',
    label='All NYC Metro Districts'
)

# Highlight Benchmarks
benchmarks = ['Scarsdale', 'Millburn', 'Roslyn', 'Ridgewood']
bench_df = df[df['District_Name'].str.contains('|'.join(benchmarks), case=False, na=False)]
sns.scatterplot(
    data=bench_df, 
    x='SEDA_Absolute_Score', 
    y='SEDA_Growth_Score', 
    s=150, 
    color='blue', 
    marker='*',
    label='Traditional Elites'
)

# Annotate benchmarks
for _, row in bench_df.iterrows():
    name = row['District_Name'].split(' ')[0]
    plt.annotate(name, (row['SEDA_Absolute_Score'] + 0.05, row['SEDA_Growth_Score']), fontsize=10, color='blue', weight='bold')

# Highlight Hidden Gems
gems = ['Highland Park', 'Cranbury', 'Maywood', 'Yorktown']
gems_df = df[df['District_Name'].str.contains('|'.join(gems), case=False, na=False)]
sns.scatterplot(
    data=gems_df, 
    x='SEDA_Absolute_Score', 
    y='SEDA_Growth_Score', 
    s=150, 
    color='green', 
    marker='D',
    label='Hidden Gems'
)

# Annotate gems
for _, row in gems_df.iterrows():
    name = row['District_Name'].split(' ')[0]
    if name == 'Yorktown': name = 'Yorktown Central'
    plt.annotate(name, (row['SEDA_Absolute_Score'] + 0.05, row['SEDA_Growth_Score']), fontsize=10, color='green', weight='bold')

plt.axhline(0, color='red', linestyle='--', alpha=0.5, label='National Average Growth')
plt.axvline(0, color='red', linestyle='--', alpha=0.5, label='National Average Proficiency')

plt.title('SEDA Absolute Proficiency vs. SEDA Academic Growth\n(NYC Metro School Districts)', fontsize=14, weight='bold')
plt.xlabel('SEDA Absolute Score (Standard Deviations above/below National Avg in Proficiency)', fontsize=12)
plt.ylabel('SEDA Growth Score (Standard Deviations above/below National Avg in Growth)', fontsize=12)
plt.legend()
plt.grid(True, alpha=0.3)

out_path = 'seda_scatter.png'
plt.savefig(out_path, dpi=300, bbox_inches='tight')
print(f"\nPlot saved to {out_path}")
