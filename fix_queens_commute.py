import pandas as pd
import requests
import time
from geopy.geocoders import Nominatim
import nbformat as nbf

# 1. Fix the Jupyter Notebook text
notebook_path = "School_District_Analysis.ipynb"
with open(notebook_path, 'r') as f:
    nb = nbf.read(f, as_version=4)

for cell in nb.cells:
    if cell.cell_type == 'code' and "Estates Lane, Bayside, NY" in cell.source:
        cell.source = cell.source.replace(
            "'Queens Family': \"Estates Lane, Bayside, NY\"",
            "'Queens Family': \"Bayside, Queens, NY\""
        )
with open(notebook_path, 'w') as f:
    nbf.write(nb, f)

# 2. Fix the CSV data
df_seda = pd.read_csv('../brain/1aa0d3c1-7a3f-4417-9041-18ac4fb2f2a3/tri_state_master_with_niche.csv', dtype={'sedaadmin': str})

geolocator = Nominatim(user_agent="nyc_commute_estimator")
location = geolocator.geocode("Bayside, Queens, NY")
dest = (location.latitude, location.longitude)
print(f"Correct Queens Coords: {dest}")

def get_drive_time_osrm(lat1, lon1, lat2, lon2):
    url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false"
    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        if data['code'] == 'Ok':
            return data['routes'][0]['duration'] / 60.0
    except:
        pass
    return None

print("Re-calculating Queens drive times...")
for idx, row in df_seda.iterrows():
    if pd.isna(row.get('latcod')): continue
    origin = (row['latcod'], row['loncod'])
    mins = get_drive_time_osrm(origin[0], origin[1], dest[0], dest[1])
    df_seda.at[idx, 'Drive_Mins_To_Queens'] = mins
    time.sleep(0.1)

df_seda['Drive_Mins_To_Queens'] = df_seda['Drive_Mins_To_Queens'].round(0)
df_seda.to_csv('../brain/1aa0d3c1-7a3f-4417-9041-18ac4fb2f2a3/tri_state_master_with_niche.csv', index=False)
print("Queens commute fixed!")
