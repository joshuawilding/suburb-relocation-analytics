import pandas as pd
import requests
import io

print("Downloading EPA Smart Location Database...")
url = "https://edg.epa.gov/EPADataCommons/public/OA/EPA_SmartLocationDatabase_V3_Jan_2021_Final.csv"
df = pd.read_csv(url, dtype={'GEOID20': str, 'GEOID10': str, 'STATEFP': str})

# Filter for NJ (34), NY (36), CT (09)
df_tri = df[df['STATEFP'].isin(['34', '36', '09'])].copy()

# Keep only necessary columns: GEOID20, NatWalkInd (National Walkability Index)
df_tri = df_tri[['GEOID20', 'NatWalkInd']]
df_tri.to_csv('tristate_walkability.csv', index=False)
print(f"Saved {len(df_tri)} block groups to tristate_walkability.csv")
