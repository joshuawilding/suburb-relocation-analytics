import nbformat as nbf

notebook_path = "School_District_Analysis.ipynb"

with open(notebook_path, 'r') as f:
    nb = nbf.read(f, as_version=4)

markdown_cell = nbf.v4.new_markdown_cell("""## Step 8: Commutability & Family Closeness
To map the "vibe" of commutability, we calculate the absolute straight-line distance from the geographic center of each school district to Times Square. 
For the key regional transit and employment hubs, we utilize the OpenStreetMap (OSRM) routing engine to calculate the actual estimated driving time in minutes, accounting for bridges, tunnels, and road networks.""")

code_cell = nbf.v4.new_code_cell("""import pandas as pd
import numpy as np
import requests
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time
from tqdm.notebook import tqdm

df_seda = pd.read_csv(output_path)

# 1. Geocode Target Addresses
geolocator = Nominatim(user_agent="nyc_commute_estimator")

targets = {
    'Times Square': "Times Square, Manhattan, NY",
    'Northern NJ Hub': "Old Tappan, NJ",
    'Lower Manhattan Hub': "Lower Manhattan, NY",
    'Queens Hub': "Bayside, Queens, NY",
    'Long Island Hub': "Roslyn, NY"
}

target_coords = {}
print("Geocoding target addresses...")
for name, address in targets.items():
    location = geolocator.geocode(address)
    if location:
        target_coords[name] = (location.latitude, location.longitude)
        print(f"Found {name}: {target_coords[name]}")
    else:
        print(f"FAILED to find {name}")
    time.sleep(1) # Polite delay for Nominatim

# 2. Get School District Centroids from SEDA Crosswalk
print("\\nCalculating school district centroids...")
cw = pd.read_csv('seda_crosswalk.csv', dtype={'sedaadmin': str})
cw['latcod'] = pd.to_numeric(cw['latcod'], errors='coerce')
cw['loncod'] = pd.to_numeric(cw['loncod'], errors='coerce')

# Average the coordinates of all schools in the district to find the population center
centroids = cw.groupby('sedaadmin')[['latcod', 'loncod']].mean().reset_index()

# Merge coordinates into main dataset
df_seda = df_seda.merge(centroids, on='sedaadmin', how='left')

# 3. Calculate Straight-Line Distance to Times Square
print("Calculating distance to Times Square...")
def calc_distance(row):
    if pd.isna(row['latcod']) or pd.isna(row['loncod']): return np.nan
    return geodesic((row['latcod'], row['loncod']), target_coords['Times Square']).miles

df_seda['Miles_To_Times_Square'] = df_seda.apply(calc_distance, axis=1).round(1)

# 4. Calculate OSRM Driving Times for Family Addresses
print("Calculating OSRM driving times... (This will take ~3 minutes)")

def get_drive_time_osrm(lat1, lon1, lat2, lon2):
    url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false"
    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        if data['code'] == 'Ok':
            return data['routes'][0]['duration'] / 60.0
    except:
        pass
    return np.nan

hub_targets = ['Northern NJ Hub', 'Lower Manhattan Hub', 'Queens Hub', 'Long Island Hub']

# Create columns
for ft in hub_targets:
    df_seda[f'Drive_Mins_To_{ft.replace(" Family", "")}'] = np.nan

session = requests.Session()

# Iterate through districts (limit to those hitting our 80.0 cutoff to save API time)
# Wait, user wants the whole dataset scored. We'll score all 514.
for idx, row in df_seda.iterrows():
    if pd.isna(row['latcod']): continue
        
    origin = (row['latcod'], row['loncod'])
    
    for ft in hub_targets:
        dest = target_coords[ft]
        mins = get_drive_time_osrm(origin[0], origin[1], dest[0], dest[1])
        df_seda.at[idx, f'Drive_Mins_To_{ft.replace(" Family", "")}'] = mins
        
    time.sleep(0.1) # Polite delay for OSRM public server

# Round the minutes
for ft in hub_targets:
    col = f'Drive_Mins_To_{ft.replace(" Family", "")}'
    df_seda[col] = df_seda[col].round(0)

# Save the dataset
df_seda.to_csv(output_path, index=False)
print("\\nCommutability mapping complete!")
df_seda[['District_Name', 'Miles_To_Times_Square', 'Drive_Mins_To_Old Tappan', 'Drive_Mins_To_Manhattan', 'Drive_Mins_To_Queens', 'Drive_Mins_To_Roslyn']].head(10)
""")

nb.cells.extend([markdown_cell, code_cell])

with open(notebook_path, 'w') as f:
    nbf.write(nb, f)

print("Notebook appended successfully with Commutability logic.")
