import pandas as pd
import numpy as np
import pgeocode
import requests
import time
import math

print("Loading datasets...")
df_seda = pd.read_csv('tri_state_master_with_niche.csv', dtype={'sedaadmin': str})
df_cross = pd.read_excel('GRF21/grf21_lea_zcta5ce20.xlsx', dtype={'LEAID': str, 'ZCTA5CE20': str})
df_cross['ZCTA5CE20'] = df_cross['ZCTA5CE20'].str.zfill(5)

# Load Zillow Inventory to find the most populated ZIP per district
zillow_inv = "Zip_invt_fs_uc_sfrcondo_sm_month.csv"
df_inv = pd.read_csv(zillow_inv, dtype={'RegionName': str})
df_inv['RegionName'] = df_inv['RegionName'].str.zfill(5)
latest_col = sorted([c for c in df_inv.columns if '-' in c])[-1]
df_inv['Inventory'] = df_inv[latest_col]

# Merge crosswalk with inventory to find the 'Primary' ZIP (highest inventory = most residential homes)
df_zip_inv = df_cross.merge(df_inv[['RegionName', 'Inventory']], left_on='ZCTA5CE20', right_on='RegionName', how='left')
df_zip_inv['Inventory'] = df_zip_inv['Inventory'].fillna(0)

# Sort by LEAID and Inventory descending, then drop duplicates to keep the #1 ZIP per LEAID
primary_zips = df_zip_inv.sort_values(['LEAID', 'Inventory'], ascending=[True, False]).drop_duplicates('LEAID')

print("Geocoding Primary ZIP Codes...")
nom = pgeocode.Nominatim('us')

target_locations = {
    'Manhattan': (40.7118, -73.9856),   # Financial District
    'Old Tappan': (41.0182, -73.9832),  # Old Tappan Hub
    'Queens': (40.7632, -73.7712),      # Estates Lane, Bayside
    'Roslyn': (40.8009, -73.6521)       # Roslyn Hub
}

def get_drive_time(start_lat, start_lon, end_lat, end_lon):
    if pd.isna(start_lat) or pd.isna(start_lon) or pd.isna(end_lat) or pd.isna(end_lon):
        return np.nan
    try:
        url = f"http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}?overview=false"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data['code'] == 'Ok':
                return round(data['routes'][0]['duration'] / 60.0, 1) # minutes
    except:
        pass
    return np.nan

# We only need to run OSRM for the Top 167 districts from earlier to save time and API rate limits,
# or we can run all 514 if we are careful. Let's do all 514 but with a small sleep.
# Wait, 514 * 4 destinations = 2000 requests. At 0.1s sleep, that's 3.5 minutes.
print("Running OSRM API for densest block commutes...")

# Merge Primary ZIPs into df_seda
df_seda = df_seda.merge(primary_zips[['LEAID', 'ZCTA5CE20']], left_on='sedaadmin', right_on='LEAID', how='left').drop(columns=['LEAID'])

# Geocode
zip_coords = nom.query_postal_code(df_seda['ZCTA5CE20'].tolist())
df_seda['Dense_Lat'] = zip_coords.latitude.values
df_seda['Dense_Lon'] = zip_coords.longitude.values

# Apply OSRM
for target_name, coords in target_locations.items():
    col_name = f'Dense_Drive_Mins_To_{target_name}'
    if col_name not in df_seda.columns:
        df_seda[col_name] = np.nan
        
    for idx, row in df_seda.iterrows():
        # Only query if NaN (idempotent)
        if pd.isna(row[col_name]):
            dur = get_drive_time(row['Dense_Lat'], row['Dense_Lon'], coords[0], coords[1])
            df_seda.at[idx, col_name] = dur
            time.sleep(0.1) # Be nice to OSRM API
            
    print(f"Finished routing to {target_name}...")

# Drop the helper lat/lon columns to keep it clean
df_seda.drop(columns=['Dense_Lat', 'Dense_Lon', 'ZCTA5CE20'], inplace=True, errors='ignore')

# Save
df_seda.to_csv('tri_state_master_with_niche.csv', index=False)
print("Densest Block Commutes appended!")
