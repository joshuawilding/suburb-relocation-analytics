import nbformat as nbf

nb = nbf.v4.new_notebook()

nb.cells = [
    nbf.v4.new_markdown_cell("""# NYC-Commutable School District Analysis
This notebook contains the complete data engineering and Exploratory Data Analysis (EDA) pipeline used to build a mathematically exhaustive database of all school districts in the 14 NYC-commutable counties.

It merges two primary datasets:
1. **Stanford SEDA (V6.0)**: Provides exhaustive geographic coverage, student enrollment, absolute test scores, and academic growth metrics.
2. **Niche**: Provides commercial letter grades (A+, A, etc.) which we fuzzy-matched onto the Stanford data."""),

    nbf.v4.new_code_cell("""import pandas as pd
import requests
import os
import difflib
import re

# Suppress DtypeWarnings
import warnings
warnings.filterwarnings('ignore')"""),

    nbf.v4.new_markdown_cell("""## Step 1: Download Stanford (SEDA) Datasets
We download the District-Level covariate pool, the test score pool, and the geographic crosswalk."""),

    nbf.v4.new_code_cell("""def download_file(url, local_filename):
    if not os.path.exists(local_filename):
        print(f"Downloading {url}...")
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): 
                    f.write(chunk)
    else:
        print(f"File {local_filename} already exists.")
    return local_filename

cov_url = "https://stacks.stanford.edu/file/xh833nn4025/seda_cov_admindist_pool_6.0.csv"
score_url = "https://stacks.stanford.edu/file/xh833nn4025/seda_admindist_pool_cs_6.0.csv"
crosswalk_url = "https://stacks.stanford.edu/file/xh833nn4025/seda_crosswalk_6.0.csv"

cov_file = "seda_cov.csv"
score_file = "seda_score.csv"
crosswalk_file = "seda_crosswalk.csv"

download_file(cov_url, cov_file)
download_file(score_url, score_file)
download_file(crosswalk_url, crosswalk_file)"""),

    nbf.v4.new_markdown_cell("""## Step 2: Ingest and Filter SEDA Data
Filter the data precisely to the 14 NYC commutable counties using the Stanford geographic crosswalk."""),

    nbf.v4.new_code_cell("""print("Loading data into Pandas...")
df_cov = pd.read_csv(cov_file, dtype={'sedaadmin': str, 'fips': str})
df_score = pd.read_csv(score_file, dtype={'sedaadmin': str, 'fips': str})
df_crosswalk = pd.read_csv(crosswalk_file, dtype={'sedaadmin': str})

target_counties_nj = ['Bergen County', 'Hudson County', 'Essex County', 'Union County', 
                      'Morris County', 'Passaic County', 'Somerset County', 'Middlesex County', 
                      'Monmouth County']
target_counties_ny = ['Nassau County', 'Suffolk County', 'Westchester County', 'Rockland County']
target_counties_ct = ['Fairfield County']

# Merge on all common geographic columns
df_merged = pd.merge(df_cov, df_score, on=['sedaadmin', 'sedaadminname', 'fips', 'stateabb'], how='inner')

# Get unique county mappings from crosswalk and merge
df_cw_unique = df_crosswalk[['sedaadmin', 'countyname']].drop_duplicates()
df_merged = pd.merge(df_merged, df_cw_unique, on='sedaadmin', how='left')

# Apply exact state/county masks to prevent pulling "Union County, AR"
mask_nj = (df_merged['stateabb'] == 'NJ') & (df_merged['countyname'].isin(target_counties_nj))
mask_ny = (df_merged['stateabb'] == 'NY') & (df_merged['countyname'].isin(target_counties_ny))
mask_ct = (df_merged['stateabb'] == 'CT') & (df_merged['countyname'].isin(target_counties_ct))

df_seda = df_merged[mask_nj | mask_ny | mask_ct].drop_duplicates(subset=['sedaadmin']).copy()
print(f"Total commutable districts found: {len(df_seda)}")

# Clean up columns
cols_to_keep = [
    'stateabb', 'countyname', 'sedaadminname', 'sedaadmin', 'totenrl', 
    'cs_mn_avg_ol', 'cs_mn_lrn_ol', 'sesavgall', 'baplusavgall', 'perfrl'
]
df_seda = df_seda[cols_to_keep].rename(columns={
    'stateabb': 'State',
    'countyname': 'County',
    'sedaadminname': 'District_Name',
    'totenrl': 'Total_Enrollment',
    'cs_mn_avg_ol': 'SEDA_Absolute_Score',
    'cs_mn_lrn_ol': 'SEDA_Growth_Score',
    'sesavgall': 'SES_Index',
    'baplusavgall': 'BA_Plus_Percentage',
    'perfrl': 'Free_Reduced_Lunch_Percentage'
})"""),

    nbf.v4.new_markdown_cell("""## Step 3: Fuzzy Merge Niche Grades
Load the Niche scrape and fuzzy-match the district names onto the Stanford dataset."""),

    nbf.v4.new_code_cell("""def clean_district_name(name):
    if pd.isna(name): return ""
    name = str(name).lower()
    filler_words = [
        r'\\bpublic\\b', r'\\bschools\\b', r'\\bschool\\b', r'\\bdistrict\\b',
        r'\\bregional\\b', r'\\btownship\\b', r'\\bborough\\b', r'\\bof\\b', r'\\bthe\\b',
        r'\\bboard\\b', r'\\beducation\\b', r'\\bunion\\b', r'\\bfree\\b', r'\\bcentral\\b',
        r'\\bcity\\b', r'\\bvocational\\b', r'\\btechnical\\b', r'\\bhudson county schools of technology\\b'
    ]
    for w in filler_words:
        name = re.sub(w, '', name)
    name = re.sub(r'[^\\w\\s]', '', name)
    return re.sub(r'\\s+', ' ', name).strip()

niche_file = "../brain/1aa0d3c1-7a3f-4417-9041-18ac4fb2f2a3/commutable_districts.csv"
if os.path.exists(niche_file):
    df_niche = pd.read_csv(niche_file)
    df_niche['State'] = df_niche['State'].map({'Connecticut': 'CT', 'New Jersey': 'NJ', 'New York': 'NY'})
    df_niche['County'] = df_niche['County'] + " County"

    df_seda['Clean_Name'] = df_seda['District_Name'].apply(clean_district_name)
    df_niche['Clean_Name'] = df_niche['School District Name'].apply(clean_district_name)

    df_seda['Niche_Grade'] = None
    matched_count = 0

    for idx, niche_row in df_niche.iterrows():
        seda_cands = df_seda[(df_seda['State'] == niche_row['State']) & (df_seda['County'] == niche_row['County'])]
        matches = difflib.get_close_matches(niche_row['Clean_Name'], seda_cands['Clean_Name'].tolist(), n=1, cutoff=0.7)
        if matches:
            seda_idx = seda_cands[seda_cands['Clean_Name'] == matches[0]].index[0]
            df_seda.at[seda_idx, 'Niche_Grade'] = niche_row['Niche Grade']
            matched_count += 1

    print(f"Matched {matched_count} out of {len(df_niche)} Niche districts.")
    df_seda = df_seda.drop(columns=['Clean_Name'])
else:
    print("Niche file not found.")"""),

    nbf.v4.new_markdown_cell("""## Step 4: Final Output & EDA Preview
Sort the dataset so the most premium districts bubble to the top, and display the first 10 rows."""),

    nbf.v4.new_code_cell("""# Sort by Niche Grade then Stanford Growth Score
df_seda = df_seda.sort_values(by=['Niche_Grade', 'SEDA_Growth_Score'], ascending=[True, False], na_position='last')

# Save the final master file
output_path = "../brain/1aa0d3c1-7a3f-4417-9041-18ac4fb2f2a3/tri_state_master_with_niche.csv"
df_seda.to_csv(output_path, index=False)
print(f"Saved to {output_path}")

# Display the top 10 results
df_seda.head(10)""")
]

with open('School_District_Analysis.ipynb', 'w') as f:
    nbf.write(nb, f)
print("Notebook generated.")
