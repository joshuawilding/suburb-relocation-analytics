import pandas as pd
import numpy as np
from haversine import haversine, Unit

print("Loading Master Dataset...")
df_seda = pd.read_csv('../brain/1aa0d3c1-7a3f-4417-9041-18ac4fb2f2a3/tri_state_master_with_niche.csv')

# Major Express Train Hubs
# These hubs guarantee frequent, direct trains into Manhattan (Penn Station or Grand Central)
hubs = {
    'Secaucus_Junction_NJ': (40.7615, -74.0743),
    'Newark_Penn_NJ': (40.7342, -74.1643),
    'Jamaica_LIRR_NY': (40.6996, -73.8087),
    'Mineola_LIRR_NY': (40.7405, -73.6409),
    'Stamford_MN_CT': (41.0406, -73.5416),
    'White_Plains_MN_NY': (41.0347, -73.7712)
}

def get_nearest_hub_distance(lat, lon):
    if pd.isna(lat) or pd.isna(lon):
        return np.nan
    distances = [haversine((lat, lon), coords, unit=Unit.MILES) for coords in hubs.values()]
    return round(min(distances), 1)

df_seda['Miles_To_Express_Train_Hub'] = df_seda.apply(lambda row: get_nearest_hub_distance(row['Latitude'], row['Longitude']), axis=1)

df_seda.to_csv('../brain/1aa0d3c1-7a3f-4417-9041-18ac4fb2f2a3/tri_state_master_with_niche.csv', index=False)
print("Express Train Access Appended!")
