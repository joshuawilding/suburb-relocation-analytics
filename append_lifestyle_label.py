import pandas as pd

print("Loading Master Dataset...")
df_seda = pd.read_csv('../brain/1aa0d3c1-7a3f-4417-9041-18ac4fb2f2a3/tri_state_master_with_niche.csv')

def categorize_lifestyle(max_walk, avg_walk):
    if pd.isna(max_walk) or pd.isna(avg_walk):
        return "Unknown"
        
    if avg_walk >= 15.0:
        return "Urban Core"
    elif max_walk >= 14.0 and avg_walk >= 12.0:
        return "Dense Suburb"
    elif max_walk >= 12.0:
        return "Classic Suburb"
    else:
        return "Rural Sprawl"

df_seda['Density_Lifestyle'] = df_seda.apply(lambda row: categorize_lifestyle(row['Max_Walkability'], row['Avg_Walkability']), axis=1)

df_seda.to_csv('../brain/1aa0d3c1-7a3f-4417-9041-18ac4fb2f2a3/tri_state_master_with_niche.csv', index=False)
print("Lifestyle Labels Appended!")
