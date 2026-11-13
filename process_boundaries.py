import geopandas as gpd
import pandas as pd
import urllib.request
import zipfile
import os
import json

fips_codes = ['34', '36', '09'] # NJ, NY, CT
types = ['unsd', 'elsd', 'scsd']
base_url = "https://www2.census.gov/geo/tiger/TIGER2022/{TYPE}/tl_2022_{fips}_{type}.zip"

os.makedirs("tiger_data", exist_ok=True)
gdfs = []

# 1. Download and load all shapefiles
print("Downloading TIGER Shapefiles...")
for fips in fips_codes:
    for t in types:
        TYPE = t.upper()
        url = base_url.format(TYPE=TYPE, fips=fips, type=t)
        zip_path = f"tiger_data/tl_{fips}_{t}.zip"
        
        # Try to download. Some states don't have ELSD/SCSD (like CT), so it might 404
        try:
            if not os.path.exists(zip_path):
                print(f"Downloading {url}...")
                urllib.request.urlretrieve(url, zip_path)
            
            # Read shapefile directly from zip using geopandas
            print(f"Reading {zip_path}...")
            gdf = gpd.read_file(f"zip://{zip_path}")
            gdfs.append(gdf)
        except Exception as e:
            print(f"Skipping {fips}-{t} (Likely doesn't exist): {e}")

# 2. Merge all geometries
if not gdfs:
    raise Exception("No shapefiles loaded!")

print("Merging geometries...")
master_gdf = pd.concat(gdfs, ignore_index=True)

# 3. Load our 514-district master dataset to filter down the polygons
print("Filtering to our 514 districts...")
df_master = pd.read_csv('tri_state_master_with_niche.csv')
df_master['sedaadmin'] = df_master['sedaadmin'].astype(str).str.zfill(7)

# Ensure GEOID matches the 7-digit sedaadmin
master_gdf['GEOID'] = master_gdf['GEOID'].astype(str).str.zfill(7)

# Keep only the polygons for the districts we care about
filtered_gdf = master_gdf[master_gdf['GEOID'].isin(df_master['sedaadmin'])]
print(f"Found polygons for {len(filtered_gdf)} out of {len(df_master)} districts.")

# 4. Merge ALL 50 columns into the GeoJSON properties!
print("Merging dataset properties into GeoJSON...")
final_gdf = filtered_gdf.merge(df_master, left_on='GEOID', right_on='sedaadmin', how='inner')

# Simplify geometry slightly to reduce file size for the browser (tolerance in degrees)
# 0.001 is roughly 100 meters, which is perfect for state-level viewing
final_gdf['geometry'] = final_gdf.geometry.simplify(tolerance=0.0005, preserve_topology=True)

# 5. Export to GeoJSON
output_path = 'district_boundaries.geojson'
print("Exporting to GeoJSON...")
final_gdf.to_file(output_path, driver='GeoJSON')
print(f"Success! GeoJSON saved to {output_path}")

# Fix NaN values in GeoJSON properties (Geopandas sometimes leaves them as null which breaks JS)
with open(output_path, 'r') as f:
    geojson_data = json.load(f)

for feature in geojson_data['features']:
    for key, val in feature['properties'].items():
        if pd.isna(val):
            feature['properties'][key] = None

with open(output_path, 'w') as f:
    json.dump(geojson_data, f)
print("GeoJSON NaNs cleaned.")
