import nbformat as nbf

notebook_path = "School_District_Analysis.ipynb"
with open(notebook_path, 'r') as f:
    nb = nbf.read(f, as_version=4)

for cell in nb.cells:
    if cell.cell_type == 'code' and "df_seda = pd.read_csv(output_path)" in cell.source and "Nominatim" in cell.source:
        cell.source = cell.source.replace(
            "df_seda = pd.read_csv(output_path)",
            "df_seda = pd.read_csv(output_path, dtype={'sedaadmin': str})"
        )

with open(notebook_path, 'w') as f:
    nbf.write(nb, f)
print("Notebook fixed.")
