import pandas as pd
import numpy as np
import nbformat as nbf
from datetime import datetime
from dateutil.relativedelta import relativedelta

print("Loading Zillow ZHVI 3-Bedroom Data...")
zillow_file = "Zip_zhvi_bdrmcnt_3_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv"
df_zillow = pd.read_csv(zillow_file, dtype={'RegionName': str})

# Ensure Zip Codes are 5 digits
df_zillow['RegionName'] = df_zillow['RegionName'].str.zfill(5)

# Identify the Date Columns
# Zillow date columns look like '2000-01-31', '2024-04-30', etc.
date_cols = [c for c in df_zillow.columns if '-' in c and c[:4].isdigit()]
latest_date_col = sorted(date_cols)[-1]

# Calculate the closest date column to exactly 3 years ago and 10 years ago
latest_dt = datetime.strptime(latest_date_col, "%Y-%m-%d")
date_3yr_ago = latest_dt - relativedelta(years=3)
date_10yr_ago = latest_dt - relativedelta(years=10)

def get_closest_date_col(target_dt, cols):
    closest_col = None
    min_diff = float('inf')
    for c in cols:
        dt = datetime.strptime(c, "%Y-%m-%d")
        diff = abs((dt - target_dt).days)
        if diff < min_diff:
            min_diff = diff
            closest_col = c
    return closest_col

col_3yr = get_closest_date_col(date_3yr_ago, date_cols)
col_10yr = get_closest_date_col(date_10yr_ago, date_cols)

print(f"Using Dates:\nLatest: {latest_date_col}\n3-Yr Baseline: {col_3yr}\n10-Yr Baseline: {col_10yr}")

# Calculate Growth metrics for each ZIP Code
df_zillow['Current_3BR_Price'] = df_zillow[latest_date_col]
df_zillow['Growth_3yr'] = (df_zillow[latest_date_col] - df_zillow[col_3yr]) / df_zillow[col_3yr] * 100.0
df_zillow['Growth_10yr'] = (df_zillow[latest_date_col] - df_zillow[col_10yr]) / df_zillow[col_10yr] * 100.0

# Keep only the target metrics
df_zillow_metrics = df_zillow[['RegionName', 'Current_3BR_Price', 'Growth_3yr', 'Growth_10yr']].copy()

print("\nLoading NCES LEA to ZIP Crosswalk...")
df_cross = pd.read_excel('GRF21/grf21_lea_zcta5ce20.xlsx', dtype={'LEAID': str, 'ZCTA5CE20': str})
df_cross['ZCTA5CE20'] = df_cross['ZCTA5CE20'].str.zfill(5)

# Merge Crosswalk and Zillow
df_merged = df_cross.merge(df_zillow_metrics, left_on='ZCTA5CE20', right_on='RegionName', how='inner')

# Aggregate by LEAID (School District) getting Min, Max, Avg
agg_funcs = {
    'Current_3BR_Price': ['min', 'max', 'mean'],
    'Growth_3yr': ['min', 'max', 'mean'],
    'Growth_10yr': ['min', 'max', 'mean']
}
df_agg = df_merged.groupby('LEAID').agg(agg_funcs).reset_index()

# Flatten MultiIndex Columns
df_agg.columns = [f"{col[0]}_{col[1].capitalize()}" if col[1] else col[0] for col in df_agg.columns]

# Round the values
df_agg['Current_3BR_Price_Min'] = df_agg['Current_3BR_Price_Min'].round(0)
df_agg['Current_3BR_Price_Max'] = df_agg['Current_3BR_Price_Max'].round(0)
df_agg['Current_3BR_Price_Mean'] = df_agg['Current_3BR_Price_Mean'].round(0)

for metric in ['Growth_3yr', 'Growth_10yr']:
    df_agg[f"{metric}_Min"] = df_agg[f"{metric}_Min"].round(1)
    df_agg[f"{metric}_Max"] = df_agg[f"{metric}_Max"].round(1)
    df_agg[f"{metric}_Mean"] = df_agg[f"{metric}_Mean"].round(1)

print("\nMerging into Master SEDA Dataset...")
df_seda = pd.read_csv('../brain/1aa0d3c1-7a3f-4417-9041-18ac4fb2f2a3/tri_state_master_with_niche.csv', dtype={'sedaadmin': str})

# Drop old affordability columns if they exist (for idempotency)
affordability_cols = [c for c in df_seda.columns if 'Price' in c or 'Growth' in c]
# Wait, SEDA_Growth_Score contains "Growth". Let's be explicit
affordability_cols = ['Current_3BR_Price_Min', 'Current_3BR_Price_Max', 'Current_3BR_Price_Mean',
                      'Growth_3yr_Min', 'Growth_3yr_Max', 'Growth_3yr_Mean',
                      'Growth_10yr_Min', 'Growth_10yr_Max', 'Growth_10yr_Mean']
for col in affordability_cols:
    if col in df_seda.columns:
        df_seda.drop(columns=[col], inplace=True)

df_seda = df_seda.merge(df_agg, left_on='sedaadmin', right_on='LEAID', how='left').drop(columns=['LEAID'], errors='ignore')

# Save updated dataset
df_seda.to_csv('../brain/1aa0d3c1-7a3f-4417-9041-18ac4fb2f2a3/tri_state_master_with_niche.csv', index=False)
print(f"Appended Affordability data to {df_seda['Current_3BR_Price_Mean'].notna().sum()} districts!")

# Update Notebook with Step 10
notebook_path = "School_District_Analysis.ipynb"
with open(notebook_path, 'r') as f:
    nb = nbf.read(f, as_version=4)

markdown_cell = nbf.v4.new_markdown_cell("""## Step 10: Affordability & Market Momentum (Zillow ZHVI)
We mapped the Zillow Home Value Index (ZHVI) specifically for **3-Bedroom Homes** into our districts using the NCES School District-to-ZIP crosswalk.
Because many school districts span multiple ZIP codes (e.g. varying wealth tiers in a single town), we calculated the `Min`, `Max`, and `Average` metrics across all underlying neighborhoods.
- `Current_3BR_Price`: Absolute baseline affordability.
- `Growth_3yr`: Short-term post-COVID market momentum / "hotness".
- `Growth_10yr`: Long-term historical stability and equity appreciation.""")

code_cell = nbf.v4.new_code_cell("""import pandas as pd

df_seda = pd.read_csv(output_path)

print("Top 15 Most Expensive School Districts for a 3-Bedroom Home:")
cols = ['State', 'District_Name', 'Current_3BR_Price_Mean', 'Current_3BR_Price_Min', 'Current_3BR_Price_Max', 'Growth_3yr_Mean', 'Growth_10yr_Mean', 'Predicted_Niche_Score']

df_expensive = df_seda.sort_values(by='Current_3BR_Price_Mean', ascending=False)
df_expensive[cols].head(15)
""")

# Remove any existing Step 10 if present
new_cells = [c for c in nb.cells if not (c.cell_type == 'markdown' and 'Step 10: Affordability' in c.source)]
new_cells.extend([markdown_cell, code_cell])
nb.cells = new_cells

with open(notebook_path, 'w') as f:
    nbf.write(nb, f)

print("Notebook Updated with Step 10!")
