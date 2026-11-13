import pandas as pd
import pgeocode

df = pd.read_csv('tri_state_master_with_niche.csv')
df_cross = pd.read_excel('GRF21/grf21_lea_zcta5ce20.xlsx', dtype={'LEAID': str, 'ZCTA5CE20': str})
df_cross['ZCTA5CE20'] = df_cross['ZCTA5CE20'].str.zfill(5)
df_zip = df_cross.drop_duplicates('LEAID')

df['sedaadmin'] = df['sedaadmin'].astype(str)
df = df.merge(df_zip[['LEAID', 'ZCTA5CE20']], left_on='sedaadmin', right_on='LEAID', how='left')

nom = pgeocode.Nominatim('us')
zip_coords = nom.query_postal_code(df['ZCTA5CE20'].tolist())
df['Lat'] = zip_coords.latitude.values
df['Lon'] = zip_coords.longitude.values

df = df.dropna(subset=['Lat', 'Lon'])
df.to_json('master_data.json', orient='records')
print("Exported master_data.json with", len(df), "records.")
