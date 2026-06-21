import pandas as pd
import numpy as np

print("Loading local EPA data to rebuild corrupt GEOIDs...")
filename = "EPA_SmartLocationDatabase_V3_Jan_2021_Final.csv"

# Load with strings for the FIPS components to prevent precision loss
df = pd.read_csv(filename, dtype={'STATEFP': str, 'COUNTYFP': str, 'TRACTCE': str, 'BLKGRPCE': str})

df_tri = df[df['STATEFP'].isin(['34', '36', '09'])].copy()

# Reconstruct 12-digit GEOID string perfectly
df_tri['GEOID20_Fixed'] = (
    df_tri['STATEFP'].str.zfill(2) + 
    df_tri['COUNTYFP'].str.zfill(3) + 
    df_tri['TRACTCE'].str.zfill(6) + 
    df_tri['BLKGRPCE'].str.zfill(1)
)

print(f"Sample of fixed GEOID20s:\n{df_tri['GEOID20_Fixed'].head()}")

df_walk = df_tri[['GEOID20_Fixed', 'NatWalkInd']]

# Load Crosswalk
df_cross = pd.read_excel('GRF21/grf21_lea_blkgrp.xlsx', dtype={'LEAID': str, 'BLKGRP': str})
df_cross['BLKGRP'] = df_cross['BLKGRP'].str.zfill(12)

# Merge on the fixed GEOID
df_merged = df_cross.merge(df_walk, left_on='BLKGRP', right_on='GEOID20_Fixed', how='inner')
print(f"Number of perfectly matched blocks: {len(df_merged)}")

# Aggregate by LEAID
walk_agg = df_merged.groupby('LEAID')['NatWalkInd'].agg(['max', 'mean']).reset_index()
walk_agg.rename(columns={'max': 'Max_Walkability', 'mean': 'Avg_Walkability'}, inplace=True)

# Merge back into main dataset
df_seda = pd.read_csv('../brain/1aa0d3c1-7a3f-4417-9041-18ac4fb2f2a3/tri_state_master_with_niche.csv', dtype={'sedaadmin': str})

# Drop old broken walkability columns if they exist
if 'Max_Walkability' in df_seda.columns:
    df_seda = df_seda.drop(columns=['Max_Walkability', 'Avg_Walkability'])

df_seda = df_seda.merge(walk_agg, left_on='sedaadmin', right_on='LEAID', how='left').drop(columns=['LEAID'], errors='ignore')

# Verify the successful match count on the 514 districts
matched = df_seda['Max_Walkability'].notna().sum()
print(f"Number of School Districts successfully receiving Walkability data: {matched}")

df_seda.to_csv('../brain/1aa0d3c1-7a3f-4417-9041-18ac4fb2f2a3/tri_state_master_with_niche.csv', index=False)
print("Walkability fully repaired and saved!")
