import pandas as pd
import numpy as np
from sklearn.metrics import r2_score, mean_absolute_error

df = pd.read_csv('tri_state_master_with_niche.csv')

# Mapping dict (same as Phase 1)
grade_map = {
    'A+': 98.0, 'A': 94.0, 'A-': 90.0,
    'B+': 88.0, 'B': 85.0, 'B-': 82.0,
    'C+': 78.0, 'C': 75.0, 'C-': 72.0,
    'D+': 68.0, 'D': 65.0, 'D-': 62.0,
    'F': 50.0
}

# Reconstruct the actual numerical Niche score
# Prefer HS grade, fallback to K8 grade
df['Actual_Niche_Score'] = df['Niche_HS_Grade'].map(grade_map).fillna(df['Niche_K8_Grade'].map(grade_map))

# Filter rows that have BOTH actual and predicted
eval_df = df.dropna(subset=['Actual_Niche_Score', 'Predicted_Niche_Score'])

if not eval_df.empty:
    r2 = r2_score(eval_df['Actual_Niche_Score'], eval_df['Predicted_Niche_Score'])
    mae = mean_absolute_error(eval_df['Actual_Niche_Score'], eval_df['Predicted_Niche_Score'])
    
    print(f"Model Evaluation Metrics (n={len(eval_df)} districts with actual Niche grades):")
    print(f"R-squared (R2): {r2:.3f}")
    print(f"Mean Absolute Error (MAE): {mae:.2f} points (on a 1-100 scale)")
    
    # Calculate how many predictions were within exactly 1 letter grade (approx 4 points)
    eval_df['Error'] = abs(eval_df['Actual_Niche_Score'] - eval_df['Predicted_Niche_Score'])
    within_1_grade = len(eval_df[eval_df['Error'] <= 4.0]) / len(eval_df) * 100
    print(f"Predictions within +/- 1 Letter Grade: {within_1_grade:.1f}%")
else:
    print("Could not evaluate, missing data.")
