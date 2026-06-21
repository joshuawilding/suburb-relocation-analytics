import nbformat as nbf

notebook_path = "School_District_Analysis.ipynb"

with open(notebook_path, 'r') as f:
    nb = nbf.read(f, as_version=4)

markdown_cell = nbf.v4.new_markdown_cell("""## Step 6: Predictive Modeling (Random Forest)
Now that we have scraped a diverse dataset of both "A-tier" and "B/C/D-tier" Niche districts, we can train a Machine Learning model. 
We will use a **Random Forest Classifier** to learn how Niche evaluates school districts based on Stanford's underlying educational and demographic covariates. We will then apply this trained model to the 400+ unranked districts to predict what their Niche Grade would be.""")

code_cell = nbf.v4.new_code_cell("""import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score
import pandas as pd

df_seda = pd.read_csv(output_path)

# 1. Define Features and unify Target Variable
features = ['SEDA_Absolute_Score', 'SEDA_Growth_Score', 'SES_Index', 'BA_Plus_Percentage', 'Free_Reduced_Lunch_Percentage', 'Total_Enrollment']
df_valid = df_seda.dropna(subset=features).copy()

# The Target Grade is the High School Grade if it exists, otherwise the K-8 Grade
df_valid['Target_Niche_Grade'] = df_valid['Niche_HS_Grade'].combine_first(df_valid['Niche_K8_Grade'])

# Split into Training (known grades) and Inference (unknown grades)
df_train = df_valid.dropna(subset=['Target_Niche_Grade']).copy()
df_infer = df_valid[df_valid['Target_Niche_Grade'].isna()].copy()

X_train = df_train[features]
y_train = df_train['Target_Niche_Grade']

print(f"Training on {len(df_train)} labeled districts. Predicting on {len(df_infer)} unknown districts.")

# 2. Train Random Forest & Validate
rf = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
cv_scores = cross_val_score(rf, X_train, y_train, cv=3)
print(f"\\n3-Fold CV Accuracy: {np.mean(cv_scores):.2f} (Scores: {cv_scores})")

rf.fit(X_train, y_train)

print("\\nFeature Importances (What drives Niche's algorithm?):")
for f, imp in sorted(zip(features, rf.feature_importances_), key=lambda x: x[1], reverse=True):
    print(f"  {f}: {imp:.3f}")

# 3. Inference
X_infer = df_infer[features]
df_infer['Predicted_Niche_Grade'] = rf.predict(X_infer)

# Map predictions back to the main dataframe
df_seda = df_seda.merge(df_infer[['sedaadmin', 'Predicted_Niche_Grade']], on='sedaadmin', how='left')
df_seda.to_csv(output_path, index=False)
""")

markdown_cell_2 = nbf.v4.new_markdown_cell("""## Step 7: View Top Predicted "A" Districts
Let's filter our dataset to exclusively show districts that our Machine Learning model has flagged as likely "A-" or higher, and then sort them by Stanford's True Growth Score to find our hidden gems.""")

code_cell_2 = nbf.v4.new_code_cell("""# Filter for Top Predicted Grades
top_grades = ['A+', 'A', 'A-']
df_hidden_gems = df_seda[df_seda['Predicted_Niche_Grade'].isin(top_grades)]

# Sort by Stanford Growth Score
df_hidden_gems = df_hidden_gems.sort_values(by='SEDA_Growth_Score', ascending=False)

# Display top 15 hidden gems
df_hidden_gems[['State', 'County', 'District_Name', 'Predicted_Niche_Grade', 'SEDA_Growth_Score', 'SES_Index']].head(15)
""")

nb.cells.extend([markdown_cell, code_cell, markdown_cell_2, code_cell_2])

with open(notebook_path, 'w') as f:
    nbf.write(nb, f)

print("Notebook appended successfully with ML logic.")
