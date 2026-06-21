import nbformat as nbf

notebook_path = "School_District_Analysis.ipynb"
with open(notebook_path, 'r') as f:
    nb = nbf.read(f, as_version=4)

for cell in nb.cells:
    if cell.cell_type == 'code' and "Target_Score" in cell.source and "Max_Walkability" in cell.source:
        cell.source = cell.source.replace(
            "'Target_Score', ",
            ""
        ).replace(
            "'Target_Niche_Grade', ",
            ""
        )

with open(notebook_path, 'w') as f:
    nbf.write(nb, f)
print("Notebook column typo fixed.")
