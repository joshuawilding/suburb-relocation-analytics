import urllib.request
import zipfile
import os
import shapefile
import json
import pandas as pd

fips_codes = ['34', '36', '09'] # NJ, NY, CT
types = ['unsd', 'elsd', 'scsd']
base_url = "https://www2.census.gov/geo/tiger/TIGER2022/{TYPE}/tl_2022_{fips}_{type}.zip"

os.makedirs("tiger_data", exist_ok=True)

# 1. Download and Extract
for fips in fips_codes:
    for t in types:
        TYPE = t.upper()
        url = base_url.format(TYPE=TYPE, fips=fips, type=t)
        zip_path = f"tiger_data/tl_2022_{fips}_{t}.zip"
        extract_dir = f"tiger_data/tl_2022_{fips}_{t}"
        
        try:
            if not os.path.exists(zip_path):
                print(f"Downloading {url}...")
                urllib.request.urlretrieve(url, zip_path)
            
            if not os.path.exists(extract_dir):
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
        except Exception as e:
            print(f"Skipping {fips}-{t}: {e}")

# 2. Load Master Data
df_master = pd.read_csv('../brain/1aa0d3c1-7a3f-4417-9041-18ac4fb2f2a3/tri_state_master_with_niche.csv')
df_master['sedaadmin'] = df_master['sedaadmin'].astype(str).str.zfill(7)
master_dict = df_master.set_index('sedaadmin').to_dict('index')

geojson = {
    "type": "FeatureCollection",
    "features": []
}

found_ids = set()

# 3. Read Shapefiles using pyshp
print("Parsing shapefiles...")
for fips in fips_codes:
    for t in types:
        extract_dir = f"tiger_data/tl_2022_{fips}_{t}"
        shp_path = f"{extract_dir}/tl_2022_{fips}_{t}.shp"
        
        if os.path.exists(shp_path):
            with shapefile.Reader(shp_path) as shp:
                fields = [f[0] for f in shp.fields[1:]]
                for sr in shp.shapeRecords():
                    record = dict(zip(fields, sr.record))
                    geoid = str(record.get('GEOID', '')).zfill(7)
                    
                    if geoid in master_dict and geoid not in found_ids:
                        found_ids.add(geoid)
                        
                        # Build the Feature
                        geom = sr.shape.__geo_interface__
                        
                        # Create properties by combining shapefile record with master data
                        props = master_dict[geoid].copy()
                        props['sedaadmin'] = geoid
                        props['NAME'] = record.get('NAME', 'Unknown')
                        
                        # Clean NaNs for JSON serialization
                        for k, v in props.items():
                            if pd.isna(v):
                                props[k] = None
                        
                        feature = {
                            "type": "Feature",
                            "geometry": geom,
                            "properties": props
                        }
                        geojson["features"].append(feature)

print(f"Found polygons for {len(found_ids)} out of {len(df_master)} districts.")

# 4. Export GeoJSON
with open("district_boundaries.geojson", "w") as f:
    json.dump(geojson, f)
print("Saved to district_boundaries.geojson")
