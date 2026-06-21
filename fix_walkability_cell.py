import nbformat as nbf

notebook_path = "School_District_Analysis.ipynb"
with open(notebook_path, 'r') as f:
    nb = nbf.read(f, as_version=4)

# Keep cells up to Step 8
new_cells = []
for cell in nb.cells:
    if cell.cell_type == 'markdown' and 'Step 9: Walkability' in cell.source:
        break
    new_cells.append(cell)

markdown_cell = nbf.v4.new_markdown_cell("""## Step 9: Walkability (EPA Smart Location Database)
We integrate the federal EPA Smart Location Database. To maintain absolute precision without dropping any rows, we use the NCES Geographic Relationship Files to crosswalk the 12-digit Census Block Group of every neighborhood in America directly into your overlying School District polygons. 
This exposes the neighborhood-level variance within each town: `Max_Walkability` proves if the town has a true dense downtown core, while `Avg_Walkability` proves if the rest of the town is suburban sprawl.""")

code_cell = nbf.v4.new_code_cell("""import pandas as pd

print("Loading Walkability and Crosswalk Data...")
df_walk = pd.read_csv('tristate_walkability.csv', dtype={'GEOID20': str})
df_cross = pd.read_excel('GRF21/grf21_lea_blkgrp.xlsx', dtype={'LEAID': str, 'BLKGRP': str})

# Ensure BLKGRP has 12 digits
df_cross['BLKGRP'] = df_cross['BLKGRP'].str.zfill(12)
df_walk['GEOID20'] = df_walk['GEOID20'].str.zfill(12)

# Merge
df_merged = df_cross.merge(df_walk, left_on='BLKGRP', right_on='GEOID20', how='inner')

# Aggregate by School District (LEAID)
walk_agg = df_merged.groupby('LEAID')['NatWalkInd'].agg(['max', 'mean']).reset_index()
walk_agg.rename(columns={'max': 'Max_Walkability', 'mean': 'Avg_Walkability'}, inplace=True)
walk_agg['Max_Walkability'] = walk_agg['Max_Walkability'].round(1)
walk_agg['Avg_Walkability'] = walk_agg['Avg_Walkability'].round(1)

# Merge with main dataset
df_seda = df_seda.merge(walk_agg, left_on='sedaadmin', right_on='LEAID', how='left').drop(columns=['LEAID', 'latcod', 'loncod'], errors='ignore')

# Save Final
df_seda.to_csv(output_path, index=False)

print("\\nTop 15 Most Walkable Downtowns in the Tri-State Area (by Max Walkability):")
cols = ['State', 'District_Name', 'Max_Walkability', 'Avg_Walkability', 'Drive_Mins_To_Manhattan', 'Target_Score', 'Predicted_Niche_Score']

df_walkable = df_seda.sort_values(by=['Max_Walkability', 'Avg_Walkability'], ascending=False)
df_walkable[cols].head(15)
""")

nb.cells = new_cells + [markdown_cell, code_cell]

with open(notebook_path, 'w') as f:
    nbf.write(nb, f)

print("Notebook updated!")
