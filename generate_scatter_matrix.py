import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import KMeans
import plotly.express as px

print("Loading Master Dataset...")
df = pd.read_csv('../brain/1aa0d3c1-7a3f-4417-9041-18ac4fb2f2a3/tri_state_master_with_niche.csv')

# 1. Impute Missing Data to keep all 514 districts
print("Imputing missing values to preserve all 514 districts...")
df['Family_Proximity_Avg'] = df[['Drive_Mins_To_Old Tappan', 'Drive_Mins_To_Queens', 'Drive_Mins_To_Roslyn']].mean(axis=1)

# For Commute, if Dense is missing, we already know we fall back to Centroid
df['Manhattan_Commute_Used'] = df['Dense_Drive_Mins_To_Manhattan'].fillna(df['Drive_Mins_To_Manhattan'])

# For Cost, Walkability, and SEDA Growth, we will impute using the County Median first, then State Median
cols_to_impute = ['True_Monthly_Carrying_Cost', 'Max_Walkability', 'SEDA_Growth_Score', 'Predicted_Niche_Score']

for col in cols_to_impute:
    # Fill with County Median
    df[col] = df.groupby('County')[col].transform(lambda x: x.fillna(x.median()))
    # If still missing (e.g. whole county missing), fill with State Median
    df[col] = df.groupby('State')[col].transform(lambda x: x.fillna(x.median()))
    # Fallback to overall median just in case
    df[col] = df[col].fillna(df[col].median())

# 2. Pre-processing for Clustering
df_score = pd.DataFrame(index=df.index)
df_score['Prestige'] = df['Predicted_Niche_Score']
df_score['Teaching'] = df['SEDA_Growth_Score']
df_score['Commute_Avg'] = (df['Manhattan_Commute_Used'] + df['Family_Proximity_Avg']) / 2.0
df_score['Walkability'] = df['Max_Walkability']
df_score['Nature'] = np.log10(df['Total_Park_Acres'] + 1)

# Cap cost at 95th percentile
cost_cap = df['True_Monthly_Carrying_Cost'].quantile(0.95)
df_score['Cost'] = df['True_Monthly_Carrying_Cost'].clip(upper=cost_cap)

# Invert negatives so 100 is always "Best" for the clustering math
df_score['Commute_Avg_Inverted'] = df_score['Commute_Avg'].max() - df_score['Commute_Avg']
df_score['Cost_Inverted'] = df_score['Cost'].max() - df_score['Cost']

# 3. Scale and Cluster
scaler = MinMaxScaler(feature_range=(0, 100))
scaled_data = scaler.fit_transform(df_score[['Prestige', 'Teaching', 'Commute_Avg_Inverted', 'Walkability', 'Nature', 'Cost_Inverted']])
kmeans = KMeans(n_clusters=6, random_state=42, n_init='auto')
df['Cluster_ID'] = kmeans.fit_predict(scaled_data)

# Name Clusters basic
df['Archetype'] = "Cluster " + df['Cluster_ID'].astype(str)

# 4. Generate 2D Scatter Matrix
print("Generating Plotly Scatter Matrix...")
# We want to plot the ACTUAL values, not the inverted/scaled ones, for human readability
plot_df = df.copy()
plot_df['Park_Acres_Log'] = df_score['Nature'] # Use Log for parks so the chart is readable
plot_df['Hover_Name'] = plot_df['District_Name']

fig = px.scatter_matrix(
    plot_df,
    dimensions=['Predicted_Niche_Score', 'SEDA_Growth_Score', 'Manhattan_Commute_Used', 'Max_Walkability', 'Park_Acres_Log', 'True_Monthly_Carrying_Cost'],
    color='Archetype',
    hover_name='Hover_Name',
    title="6D Scatter Matrix (All 514 Districts)",
    labels={
        'Predicted_Niche_Score': 'Prestige',
        'SEDA_Growth_Score': 'Teaching',
        'Manhattan_Commute_Used': 'Commute (Mins)',
        'Max_Walkability': 'Walkability',
        'Park_Acres_Log': 'Parks (Log)',
        'True_Monthly_Carrying_Cost': 'Cost ($)'
    },
    height=1200, # Make it tall enough to read
    width=1400
)

# Update layout for better readability
fig.update_traces(diagonal_visible=False, marker=dict(size=4, opacity=0.7))

fig.write_html("../brain/1aa0d3c1-7a3f-4417-9041-18ac4fb2f2a3/2D_Scatter_Matrix.html")
print("Scatter Matrix generated!")
