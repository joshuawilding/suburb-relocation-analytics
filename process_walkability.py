import urllib.request
import zipfile
import io
import pandas as pd
import glob

print("Downloading NCES GRF21 (Block Group to School District Crosswalk)...")
url = "https://nces.ed.gov/programs/edge/data/GRF21.zip"
r = urllib.request.urlopen(url)
z = zipfile.ZipFile(io.BytesIO(r.read()))
z.extractall("grf21")

# Find the unified school district to block group file
csv_file = glob.glob("grf21/*LEA_BG*.csv")
if not csv_file:
    # Try txt
    csv_file = glob.glob("grf21/*LEA_BG*.txt")

if csv_file:
    print(f"Loading {csv_file[0]}...")
    # GRF files are often tab or pipe delimited if they are .txt
    try:
        df_grf = pd.read_csv(csv_file[0], dtype=str)
    except:
        df_grf = pd.read_csv(csv_file[0], dtype=str, sep='\t')
    
    # We need: LEAID (7 digits) and BG (12 digits)
    # The columns are usually 'LEAID' and 'BG' or 'TRACT'
    print(df_grf.columns.tolist())
    print(df_grf.head())
else:
    print("Could not find LEA to BG crosswalk file.")

