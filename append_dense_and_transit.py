import pandas as pd
import numpy as np
import pgeocode
import requests
import time
from haversine import haversine, Unit

print("Loading Master Dataset...")
df_seda = pd.read_csv('tri_state_master_with_niche.csv', dtype={'sedaadmin': str})
df_cross = pd.read_excel('GRF21/grf21_lea_zcta5ce20.xlsx', dtype={'LEAID': str, 'ZCTA5CE20': str})
df_cross['ZCTA5CE20'] = df_cross['ZCTA5CE20'].str.zfill(5)

# Primary ZIP Logic
df_zip = df_cross.drop_duplicates('LEAID')
df_seda = df_seda.merge(df_zip[['LEAID', 'ZCTA5CE20']], left_on='sedaadmin', right_on='LEAID', how='left').drop(columns=['LEAID'])

print("Geocoding Primary ZIP Codes...")
nom = pgeocode.Nominatim('us')
zip_coords = nom.query_postal_code(df_seda['ZCTA5CE20'].tolist())
df_seda['Dense_Lat'] = zip_coords.latitude.values
df_seda['Dense_Lon'] = zip_coords.longitude.values

target_locations = {
    'Manhattan': (40.7118, -73.9856),
    'Old Tappan': (41.0182, -73.9832),
    'Queens': (40.7632, -73.7712),
    'Roslyn': (40.8009, -73.6521)
}

def get_drive_time(start_lat, start_lon, end_lat, end_lon):
    if pd.isna(start_lat) or pd.isna(start_lon): return np.nan
    try:
        url = f"http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}?overview=false"
        r = requests.get(url, timeout=3)
        if r.status_code == 200:
            return round(r.json()['routes'][0]['duration'] / 60.0, 1)
    except: pass
    return np.nan

# Only filter and route the Top Candidates to save API time
mask_top = (
    (df_seda['Predicted_Niche_Score'] >= 80.0) & 
    (df_seda['Current_3BR_Price_Mean'] <= 1500000) &
    (df_seda['Drive_Mins_To_Manhattan'] <= 70)
)
top_indices = df_seda[mask_top].index
print(f"Running OSRM for {len(top_indices)} highly-qualified districts...")

for target_name, coords in target_locations.items():
    col_name = f'Dense_Drive_Mins_To_{target_name}'
    if col_name not in df_seda.columns: df_seda[col_name] = np.nan
    
    for idx in top_indices:
        if pd.isna(df_seda.at[idx, col_name]):
            dur = get_drive_time(df_seda.at[idx, 'Dense_Lat'], df_seda.at[idx, 'Dense_Lon'], coords[0], coords[1])
            df_seda.at[idx, col_name] = dur
            time.sleep(0.1)
            
print("Calculating Express Train Access...")
hubs = {
    'Secaucus': (40.7615, -74.0743), 'Newark': (40.7342, -74.1643),
    'Jamaica': (40.6996, -73.8087), 'Mineola': (40.7405, -73.6409),
    'Stamford': (41.0406, -73.5416), 'White_Plains': (41.0347, -73.7712)
}
def get_hub_dist(lat, lon):
    if pd.isna(lat) or pd.isna(lon): return np.nan
    return round(min([haversine((lat, lon), h, unit=Unit.MILES) for h in hubs.values()]), 1)

df_seda['Miles_To_Express_Train'] = df_seda.apply(lambda r: get_hub_dist(r['Dense_Lat'], r['Dense_Lon']), axis=1)

df_seda.to_csv('tri_state_master_with_niche.csv', index=False)
print("Dense Commutes & Transit Access Appended!")
