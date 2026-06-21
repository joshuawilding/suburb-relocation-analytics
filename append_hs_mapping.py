import nbformat as nbf
import pandas as pd

notebook_path = "School_District_Analysis.ipynb"

with open(notebook_path, 'r') as f:
    nb = nbf.read(f, as_version=4)

markdown_cell = nbf.v4.new_markdown_cell("""## Step 5: Regional High School Mapping
Some New Jersey districts operate as K-8 elementary districts that funnel into shared "Regional High Schools". Niche ranks the Regional High Schools separately, while SEDA tracks the component K-8 towns. 

Since the official federal Secondary District crosswalk doesn't perfectly map these in NJ, we manually map the Niche Grade of the 4 missed Regional High Schools directly to their constituent towns as a new feature: `Niche_HS_Grade`. This allows us to see the K-8 Niche grade and the High School Niche grade side-by-side without duplicating rows.""")

code_cell = nbf.v4.new_code_cell("""# 1. Load the merged dataset
df_seda = pd.read_csv(output_path)

# 2. Rename the original Niche Grade column for clarity
df_seda = df_seda.rename(columns={'Niche_Grade': 'Niche_K8_Grade'})
df_seda['Niche_HS_Grade'] = None

# 3. Define the Regional High School to Component Town Mapping
# We map the town names (or partial names) that feed into each specific Regional HS
regional_mappings = {
    # Northern Valley Regional (Niche: A+)
    'A+': {
        'Northern Valley': ['Closter', 'Demarest', 'Harrington Park', 'Haworth', 'Northvale', 'Norwood', 'Old Tappan'],
        'Pascack Valley': ['Hillsdale', 'Montvale', 'River Vale', 'Woodcliff Lake'],
        'West Morris': ['Chester', 'Mendham', 'Washington Township'], # Note: Washington Twp in Morris
        'West Essex': ['Essex Fells', 'Fairfield', 'North Caldwell', 'Roseland']
    }
}

# 4. Apply the mappings
for hs_grade, hs_dict in regional_mappings.items():
    for hs_name, towns in hs_dict.items():
        for town in towns:
            # We use string matching to find the SEDA district row
            mask = df_seda['District_Name'].str.contains(town, case=False, na=False)
            
            # Special case for Washington Township to ensure it's the one in Morris County
            if town == 'Washington Township':
                mask = mask & (df_seda['County'] == 'Morris County')
            
            df_seda.loc[mask, 'Niche_HS_Grade'] = hs_grade

# 5. Rearrange columns so the grades are next to each other
cols = df_seda.columns.tolist()
k8_idx = cols.index('Niche_K8_Grade')
cols.insert(k8_idx + 1, cols.pop(cols.index('Niche_HS_Grade')))
df_seda = df_seda[cols]

# 6. Save and Preview
df_seda.to_csv(output_path, index=False)

# Preview the towns that received a mapped High School grade
df_seda[df_seda['Niche_HS_Grade'].notna()][['District_Name', 'Niche_K8_Grade', 'Niche_HS_Grade', 'SEDA_Growth_Score']].head(10)""")

nb.cells.extend([markdown_cell, code_cell])

with open(notebook_path, 'w') as f:
    nbf.write(nb, f)

print("Notebook appended successfully.")
