import pandas as pd
import numpy as np

# Load the master dataset
df = pd.read_csv('tri_state_master_with_niche.csv')

# --- USER PREFERENCES / FILTERS ---
MIN_NICHE_SCORE = 85.0
MAX_PRICE = 1300000        # Max $1.3M for a 3BR home
MAX_COMMUTE_NYC = 60       # Max 60 mins to Manhattan
MIN_MAX_WALKABILITY = 13.0 # Must have at least a decent walkable town center

print(f"Applying Filters:")
print(f"- Niche Score >= {MIN_NICHE_SCORE}")
print(f"- Max 3BR Price <= ${MAX_PRICE:,.0f}")
print(f"- Drive to NYC <= {MAX_COMMUTE_NYC} mins")
print(f"- Walkability (Downtown) >= {MIN_MAX_WALKABILITY}")

# Apply Filters
df_filtered = df[
    (df['Predicted_Niche_Score'] >= MIN_NICHE_SCORE) &
    (df['Current_3BR_Price_Mean'] <= MAX_PRICE) &
    (df['Drive_Mins_To_Manhattan'] <= MAX_COMMUTE_NYC) &
    (df['Max_Walkability'] >= MIN_MAX_WALKABILITY)
].copy()

print(f"\nFound {len(df_filtered)} districts matching all strict criteria!\n")

# Calculate a "Regional Connectivity Score" (Average drive time to the 3 outer regional hubs)
df_filtered['Regional_Commute_Avg'] = df_filtered[['Drive_Mins_To_Old Tappan', 'Drive_Mins_To_Queens', 'Drive_Mins_To_Roslyn']].mean(axis=1).round(1)

# Sort by a combination of Best Schools, Best Walkability, and Best Regional Transit Access
# We'll prioritize Walkability and Schools
df_sorted = df_filtered.sort_values(by=['Max_Walkability', 'Predicted_Niche_Score', 'Regional_Commute_Avg'], ascending=[False, False, True])

cols_to_display = [
    'State', 'District_Name', 
    'Predicted_Niche_Score', 
    'Max_Walkability', 
    'Current_3BR_Price_Mean', 
    'Drive_Mins_To_Manhattan',
    'Regional_Commute_Avg'
]

print("TOP 15 BEST TOWNS FOR YOUR EXACT LIFESTYLE:")
print("-" * 120)
print(df_sorted[cols_to_display].head(15).to_string(index=False))

# Save the shortlist
df_sorted.to_csv('top_lifestyle_recommendations.csv', index=False)
