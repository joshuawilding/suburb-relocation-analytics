import pandas as pd
import numpy as np

print("Loading EPA SLD for Nature Index...")
filename = "EPA_SmartLocationDatabase_V3_Jan_2021_Final.csv"
df_epa = pd.read_csv(filename, dtype={'STATEFP': str, 'COUNTYFP': str, 'TRACTCE': str, 'BLKGRPCE': str})

# Filter Tri-State
df_tri = df_epa[df_epa['STATEFP'].isin(['34', '36', '09'])].copy()

# Reconstruct GEOID20
df_tri['GEOID20_Fixed'] = (
    df_tri['STATEFP'].str.zfill(2) + 
    df_tri['COUNTYFP'].str.zfill(3) + 
    df_tri['TRACTCE'].str.zfill(6) + 
    df_tri['BLKGRPCE'].str.zfill(1)
)

# Calculate Protected Park Acres
df_tri['Ac_Protected_Parks'] = df_tri['Ac_Land'] - df_tri['Ac_Unpr']

# Load Crosswalk
df_cross = pd.read_excel('GRF21/grf21_lea_blkgrp.xlsx', dtype={'LEAID': str, 'BLKGRP': str})
df_cross['BLKGRP'] = df_cross['BLKGRP'].str.zfill(12)

# Merge
df_merged = df_cross.merge(df_tri[['GEOID20_Fixed', 'Ac_Protected_Parks']], left_on='BLKGRP', right_on='GEOID20_Fixed', how='inner')

# Aggregate to School District (Sum of all park acres in the district)
park_agg = df_merged.groupby('LEAID')['Ac_Protected_Parks'].sum().reset_index()
park_agg.rename(columns={'Ac_Protected_Parks': 'Total_Park_Acres'}, inplace=True)

# Round
park_agg['Total_Park_Acres'] = park_agg['Total_Park_Acres'].round(1)

print("Merging into Master Dataset...")
df_seda = pd.read_csv('../brain/1aa0d3c1-7a3f-4417-9041-18ac4fb2f2a3/tri_state_master_with_niche.csv', dtype={'sedaadmin': str})

# Idempotency
if 'Total_Park_Acres' in df_seda.columns:
    df_seda.drop(columns=['Total_Park_Acres'], inplace=True)

df_seda = df_seda.merge(park_agg, left_on='sedaadmin', right_on='LEAID', how='left').drop(columns=['LEAID'], errors='ignore')

# Identify massive state parks
df_seda['Total_Park_Acres'] = df_seda['Total_Park_Acres'].fillna(0)

df_seda.to_csv('../brain/1aa0d3c1-7a3f-4417-9041-18ac4fb2f2a3/tri_state_master_with_niche.csv', index=False)
print("Nature Index (Park Acres) Appended!")
