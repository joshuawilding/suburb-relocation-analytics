import pandas as pd
import numpy as np

# Load Data
df = pd.read_csv('../brain/1aa0d3c1-7a3f-4417-9041-18ac4fb2f2a3/tri_state_master_with_niche.csv')

# Select relevant numerical columns for our model
features = [
    'Predicted_Niche_Score', 'SEDA_Growth_Score', 'BA_Plus_Percentage', 
    'Drive_Mins_To_Manhattan', 'Miles_To_Express_Train', 'Drive_Mins_To_Old Tappan',
    'Drive_Mins_To_Queens', 'Drive_Mins_To_Roslyn',
    'Max_Walkability', 'Total_Park_Acres', 
    'True_Monthly_Carrying_Cost', 'Growth_3yr_Mean', 'Active_Inventory_Mean',
    'Median_Income_Est', 'Overall_Home_Price_Mean'
]

# Ensure they exist in df
features = [f for f in features if f in df.columns]
df_feat = df[features].copy()

out_md = "# Feature Analysis: Outliers & Correlations\n\n"
out_md += "This report analyzes the core features proposed for the ranking model to identify redundancies, outliers, and overly common values.\n\n"

# 1. Low Variance & Overly Common Values
out_md += "## 1. Low Variance & Common Values\n"
out_md += "Checking if any features lack meaningful variance (i.e., almost all towns have the same value):\n\n"
out_md += "| Feature | Most Common Value | % of Rows with Common Value | Std Dev |\n"
out_md += "| :--- | :--- | :--- | :--- |\n"
for col in features:
    val_counts = df_feat[col].value_counts(normalize=True)
    if not val_counts.empty:
        top_val = val_counts.index[0]
        top_pct = val_counts.iloc[0] * 100
        std_dev = df_feat[col].std()
        out_md += f"| `{col}` | {top_val:.2f} | {top_pct:.1f}% | {std_dev:.2f} |\n"

# 2. Outliers Analysis (using IQR)
out_md += "\n## 2. Outlier Analysis (IQR Method)\n"
out_md += "Identifying severe outliers that might skew the Min-Max scaling of our final model.\n\n"
out_md += "| Feature | Lower Bound | Upper Bound | # of Outliers | Example Extreme Outliers |\n"
out_md += "| :--- | :--- | :--- | :--- | :--- |\n"

for col in features:
    Q1 = df_feat[col].quantile(0.25)
    Q3 = df_feat[col].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    
    outliers = df_feat[(df_feat[col] < lower_bound) | (df_feat[col] > upper_bound)][col]
    num_outliers = len(outliers)
    
    if num_outliers > 0:
        # Get the top 3 most extreme values
        extremes = outliers.sort_values(ascending=False).head(3).tolist()
        extremes_str = ", ".join([f"{x:.1f}" for x in extremes])
    else:
        extremes_str = "None"
        
    out_md += f"| `{col}` | {lower_bound:.1f} | {upper_bound:.1f} | **{num_outliers}** | {extremes_str} |\n"

# 3. Correlation Matrix
out_md += "\n## 3. Highly Correlated Features (Redundancies)\n"
out_md += "Finding features that measure the exact same thing (Pearson correlation > 0.70 or < -0.70).\n\n"
out_md += "| Feature A | Feature B | Correlation | Recommendation |\n"
out_md += "| :--- | :--- | :--- | :--- |\n"

corr_matrix = df_feat.corr(numeric_only=True)
high_corr_pairs = []

for i in range(len(corr_matrix.columns)):
    for j in range(i):
        val = corr_matrix.iloc[i, j]
        if abs(val) >= 0.70:
            col_a = corr_matrix.columns[i]
            col_b = corr_matrix.columns[j]
            high_corr_pairs.append((col_a, col_b, val))

for col_a, col_b, val in sorted(high_corr_pairs, key=lambda x: abs(x[2]), reverse=True):
    strength = "Very Strong" if abs(val) > 0.85 else "Strong"
    color = "Positive" if val > 0 else "Negative"
    out_md += f"| `{col_a}` | `{col_b}` | **{val:.2f}** ({strength} {color}) | Consider dropping one |\n"

with open('../brain/1aa0d3c1-7a3f-4417-9041-18ac4fb2f2a3/feature_analysis.md', 'w') as f:
    f.write(out_md)

print("Feature analysis generated at feature_analysis.md")
