import nbformat as nbf
import re

notebook_path = "School_District_Analysis.ipynb"

with open(notebook_path, 'r') as f:
    nb = nbf.read(f, as_version=4)

# Keep only cells before Step 6
new_cells = []
for cell in nb.cells:
    if cell.cell_type == 'markdown' and 'Step 6: Predictive Modeling' in cell.source:
        break
    new_cells.append(cell)

# New Step 6
markdown_6 = nbf.v4.new_markdown_cell("""## Step 6: Continuous Predictive Modeling (Random Forest Regressor)
We will train a **Random Forest Regressor** to predict a continuous Niche Score on a scale of 1-100. This allows us to achieve high recall by applying a flexible minimum cutoff threshold later.""")

code_6 = nbf.v4.new_code_cell("""import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score
import pandas as pd

df_seda = pd.read_csv(output_path)

# 1. Define Features and unify Target Variable
features = ['SEDA_Absolute_Score', 'SEDA_Growth_Score', 'SES_Index', 'BA_Plus_Percentage', 'Free_Reduced_Lunch_Percentage', 'Total_Enrollment']
df_valid = df_seda.dropna(subset=features).copy()

df_valid['Target_Niche_Grade'] = df_valid['Niche_HS_Grade'].combine_first(df_valid['Niche_K8_Grade'])

# Map Letter Grades to a 1-100 Scale
grade_map = {
    'A+': 98, 'A': 95, 'A-': 90,
    'B+': 88, 'B': 85, 'B-': 80,
    'C+': 78, 'C': 75, 'C-': 70,
    'D+': 68, 'D': 65, 'D-': 60,
    'F': 50
}

# Only keep rows where the target grade is valid for training
df_valid['Target_Score'] = df_valid['Target_Niche_Grade'].map(grade_map)

# Split into Training (known grades) and Inference (unknown grades)
df_train = df_valid.dropna(subset=['Target_Score']).copy()
df_infer = df_valid[df_valid['Target_Score'].isna()].copy()

X_train = df_train[features]
y_train = df_train['Target_Score']

print(f"Training on {len(df_train)} labeled districts. Predicting on {len(df_infer)} unknown districts.")

# 2. Train Random Forest Regressor & Validate
rf = RandomForestRegressor(n_estimators=100, random_state=42)

# Use Negative Mean Absolute Error for validation
cv_scores = cross_val_score(rf, X_train, y_train, cv=5, scoring='neg_mean_absolute_error')
mae_scores = -cv_scores
print(f"\\n5-Fold CV Mean Absolute Error (MAE): {np.mean(mae_scores):.2f} points (Scores: {mae_scores})")

rf.fit(X_train, y_train)

print("\\nFeature Importances (What drives the 1-100 score?):")
for f, imp in sorted(zip(features, rf.feature_importances_), key=lambda x: x[1], reverse=True):
    print(f"  {f}: {imp:.3f}")

# 3. Inference
X_infer = df_infer[features]
df_infer['Predicted_Niche_Score'] = rf.predict(X_infer).round(1)

# Apply known scores to the training data so everything has a score
df_train['Predicted_Niche_Score'] = df_train['Target_Score']

# Combine back
df_all_scored = pd.concat([df_train, df_infer])

# Map predictions back to the main dataframe
if 'Predicted_Niche_Score' in df_seda.columns:
    df_seda = df_seda.drop(columns=['Predicted_Niche_Score'])

df_seda = df_seda.merge(df_all_scored[['sedaadmin', 'Predicted_Niche_Score']], on='sedaadmin', how='left')
df_seda.to_csv(output_path, index=False)
""")

# New Step 7
markdown_7 = nbf.v4.new_markdown_cell("""## Step 7: Apply High-Recall Cutoff
To optimize for high recall and ensure no great district is missed, we set a lower cutoff bound on our continuous 1-100 score. 
For instance, setting the cutoff to `80.0` ensures any district predicted to be at least a B- is kept in our shortlist. We then sort this high-recall list by Stanford's True Growth Score.""")

code_7 = nbf.v4.new_code_cell("""# Apply High-Recall Cutoff
MIN_ACCEPTABLE_SCORE = 80.0

# Filter for districts hitting the threshold
df_shortlist = df_seda[df_seda['Predicted_Niche_Score'] >= MIN_ACCEPTABLE_SCORE]

# Sort by Stanford Growth Score (Value-Add)
df_shortlist = df_shortlist.sort_values(by='SEDA_Growth_Score', ascending=False)

print(f"Total districts matching the >={MIN_ACCEPTABLE_SCORE} cutoff: {len(df_shortlist)}")

# Display top 15 hidden gems
cols_to_show = ['State', 'County', 'District_Name', 'Target_Niche_Grade', 'Predicted_Niche_Score', 'SEDA_Growth_Score', 'SES_Index']

# We need to map Target_Niche_Grade back into df_seda just for this display view
df_seda_view = pd.merge(df_shortlist, df_valid[['sedaadmin', 'Target_Niche_Grade']], on='sedaadmin', how='left')
df_seda_view[cols_to_show].head(15)
""")

nb.cells = new_cells + [markdown_6, code_6, markdown_7, code_7]

with open(notebook_path, 'w') as f:
    nbf.write(nb, f)

print("Notebook updated with continuous ML logic.")
