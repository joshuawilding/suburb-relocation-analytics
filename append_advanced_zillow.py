import pandas as pd
import numpy as np

print("Loading Zillow ZHVI Overall Data...")
zillow_overall = "Zip_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv"
df_overall = pd.read_csv(zillow_overall, dtype={'RegionName': str})
df_overall['RegionName'] = df_overall['RegionName'].str.zfill(5)

# Get the latest date column
date_cols_overall = [c for c in df_overall.columns if '-' in c and c[:4].isdigit()]
latest_col_overall = sorted(date_cols_overall)[-1]
df_overall['Overall_Home_Price'] = df_overall[latest_col_overall]
df_overall_metrics = df_overall[['RegionName', 'Overall_Home_Price']].copy()

print("Loading Zillow Inventory Data...")
zillow_inv = "Zip_invt_fs_uc_sfrcondo_sm_month.csv"
df_inv = pd.read_csv(zillow_inv, dtype={'RegionName': str})
df_inv['RegionName'] = df_inv['RegionName'].str.zfill(5)

date_cols_inv = [c for c in df_inv.columns if '-' in c and c[:4].isdigit()]
latest_col_inv = sorted(date_cols_inv)[-1]
df_inv['Active_Inventory'] = df_inv[latest_col_inv]
df_inv_metrics = df_inv[['RegionName', 'Active_Inventory']].copy()

print("Loading NCES LEA to ZIP Crosswalk...")
df_cross = pd.read_excel('GRF21/grf21_lea_zcta5ce20.xlsx', dtype={'LEAID': str, 'ZCTA5CE20': str})
df_cross['ZCTA5CE20'] = df_cross['ZCTA5CE20'].str.zfill(5)

# Merge
df_merged = df_cross.merge(df_overall_metrics, left_on='ZCTA5CE20', right_on='RegionName', how='inner')
df_merged = df_merged.merge(df_inv_metrics, left_on='ZCTA5CE20', right_on='RegionName', how='left')

# Aggregate by LEAID
df_agg = df_merged.groupby('LEAID').agg({
    'Overall_Home_Price': 'mean',
    'Active_Inventory': 'mean'
}).reset_index()

df_agg.rename(columns={
    'Overall_Home_Price': 'Overall_Home_Price_Mean',
    'Active_Inventory': 'Active_Inventory_Mean'
}, inplace=True)

df_agg['Overall_Home_Price_Mean'] = df_agg['Overall_Home_Price_Mean'].round(0)
df_agg['Active_Inventory_Mean'] = df_agg['Active_Inventory_Mean'].round(1)

print("Merging into Master SEDA Dataset...")
df_seda = pd.read_csv('../brain/1aa0d3c1-7a3f-4417-9041-18ac4fb2f2a3/tri_state_master_with_niche.csv', dtype={'sedaadmin': str})

cols_to_drop = ['Overall_Home_Price_Mean', 'Active_Inventory_Mean']
df_seda.drop(columns=[c for c in cols_to_drop if c in df_seda.columns], inplace=True)

df_seda = df_seda.merge(df_agg, left_on='sedaadmin', right_on='LEAID', how='left').drop(columns=['LEAID'], errors='ignore')

# Identify 3BR Premium (Is a 3BR a starter home or a mansion here?)
# If Current_3BR_Price_Mean / Overall_Home_Price_Mean is < 1.0, 3BRs are cheaper than the town average (town is mostly mansions).
if 'Current_3BR_Price_Mean' in df_seda.columns:
    df_seda['3BR_vs_Overall_Ratio'] = (df_seda['Current_3BR_Price_Mean'] / df_seda['Overall_Home_Price_Mean']).round(2)

df_seda.to_csv('../brain/1aa0d3c1-7a3f-4417-9041-18ac4fb2f2a3/tri_state_master_with_niche.csv', index=False)
print("Advanced Zillow Enhancements Saved!")
