import pandas as pd
import numpy as np

print("Loading datasets...")
# 1. Load Niche Master
df_master = pd.read_csv('tri_state_master_with_niche.csv')
# We need to map school districts to political/demographic data. 
# But df_master already has demographics (perwht, perasn, baplusavgall, SES_Index).
# We just need political leanings.
df_tracts = pd.read_csv('nyc_metro_tract_unified_metrics.csv', dtype={'TractFIPS': str})
df_crosswalk = pd.read_excel('GRF21/grf21_lea_tract.xlsx', dtype={'LEAID': str, 'TRACT': str})

print("Aggregating political data by School District...")
# Map Tracts to LEAID
df_tracts['TRACT'] = df_tracts['TractFIPS']
df_merged = df_crosswalk.merge(df_tracts, on='TRACT', how='inner')

# Aggregate Dem Vote Share by LEAID
df_pol_agg = df_merged.groupby('LEAID').agg({
    'Dem_Vote_Share_2020': 'mean',
    'Two_Party_Margin_2020': 'mean'
}).reset_index()

# Merge into Master
df_master['sedaadmin'] = df_master['sedaadmin'].astype(str).str.zfill(7)
df_master = df_master.merge(df_pol_agg, left_on='sedaadmin', right_on='LEAID', how='left')

# ---------------------------------------------------------
# BENCHMARKING TOP-TIER DISTRICTS
# ---------------------------------------------------------
benchmarks = ['Scarsdale', 'Millburn', 'Roslyn', 'Northern Valley', 'Ridgewood']
print("\n--- BENCHMARK TOP-TIER DISTRICTS ---")
for b in benchmarks:
    match = df_master[df_master['District_Name'].str.contains(b, case=False, na=False)]
    if not match.empty:
        row = match.iloc[0]
        def fmt_pct(val):
            if pd.isna(val): return "N/A"
            v = val if val <= 1.0 else val / 100.0
            return f"{v * 100.0:.1f}%"

        print(f"\n{row['District_Name']} ({row['State']}):")
        print(f"  SEDA Growth Score: {row['SEDA_Growth_Score']:.2f}")
        print(f"  Niche Predicted Score: {row.get('Predicted_Niche_Score', 'N/A')}")
        print(f"  Demographics: White: {fmt_pct(row.get('perwht'))} | Asian: {fmt_pct(row.get('perasn'))} | Hisp: {fmt_pct(row.get('perhsp'))}")
        print(f"  BA+ (Educated Peers): {fmt_pct(row.get('baplusavgall'))}")
        print(f"  Median Income: ${row['Median_Income_Est']:,.0f}")
        print(f"  3BR Home Price: ${row['Current_3BR_Price_Mean']:,.0f}")
        print(f"  Democratic Vote Share: {row.get('Dem_Vote_Share_2020', np.nan):.1f}%")

# ---------------------------------------------------------
# CORRELATION MATRIX
# ---------------------------------------------------------
print("\n--- METRIC CORRELATIONS ---")
corr_cols = [
    'SEDA_Growth_Score', 'Predicted_Niche_Score', 
    'perwht', 'perasn', 'baplusavgall', 'Median_Income_Est', 
    'Current_3BR_Price_Mean', 'Dem_Vote_Share_2020'
]
df_corr = df_master[corr_cols].corr()
print(df_corr.round(2).to_string())

# ---------------------------------------------------------
# OUTLIER DETECTION (High Growth, Affordable)
# ---------------------------------------------------------
print("\n--- HIDDEN GEMS (High Growth, Moderate Price) ---")
# Filter: Growth > 0.1 (Top tier), Price < $800k, BA+ > 40%, Dem > 50%
gems = df_master[
    (df_master['SEDA_Growth_Score'] > 0.08) &
    (df_master['Current_3BR_Price_Mean'] < 850000) &
    (df_master['baplusavgall'] > 0.40) &
    (df_master['Dem_Vote_Share_2020'] > 55.0) &
    (df_master['perasn'] > 0.05)
].sort_values('SEDA_Growth_Score', ascending=False).head(10)

cols_show = ['District_Name', 'SEDA_Growth_Score', 'perasn', 'baplusavgall', 'Current_3BR_Price_Mean', 'Dem_Vote_Share_2020']
for _, row in gems.iterrows():
    v_asn = row.get('perasn', 0)
    v_asn = v_asn * 100.0 if v_asn <= 1.0 else v_asn
    v_ba = row.get('baplusavgall', 0)
    v_ba = v_ba * 100.0 if v_ba <= 1.0 else v_ba
    print(f"{row['District_Name'][:30]:<30} | Grwth: {row['SEDA_Growth_Score']:.2f} | Asn%: {v_asn:4.1f}% | BA+%: {v_ba:4.1f}% | Price: ${row['Current_3BR_Price_Mean']:,.0f} | Dem%: {row['Dem_Vote_Share_2020']:.1f}%")
