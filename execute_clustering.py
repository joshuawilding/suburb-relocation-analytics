import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import KMeans
import plotly.express as px
import folium
import pgeocode

print("1. Loading & Pre-Processing Data...")
df = pd.read_csv('tri_state_master_with_niche.csv', dtype={'sedaadmin': str})

# Generate Family Proximity
df['Family_Proximity_Avg'] = df[['Drive_Mins_To_Old Tappan', 'Drive_Mins_To_Queens', 'Drive_Mins_To_Roslyn']].mean(axis=1)

# Define the 6 Core Raw Columns
raw_cols = {
    'Prestige': 'Predicted_Niche_Score',
    'Teaching': 'SEDA_Growth_Score',
    'Manhattan_Commute': 'Drive_Mins_To_Manhattan', # fallback used automatically if dense missing
    'Family_Commute': 'Family_Proximity_Avg',
    'Walkability': 'Max_Walkability',
    'Park_Acres': 'Total_Park_Acres',
    'Carrying_Cost': 'True_Monthly_Carrying_Cost'
}

# Override Manhattan commute with Dense commute if it exists
df['Manhattan_Commute_Used'] = df['Dense_Drive_Mins_To_Manhattan'].fillna(df['Drive_Mins_To_Manhattan'])

# Drop rows missing ANY of the core features to ensure perfect 6D geometry
core_eval_cols = [raw_cols['Prestige'], raw_cols['Teaching'], 'Manhattan_Commute_Used', 
                  raw_cols['Family_Commute'], raw_cols['Walkability'], raw_cols['Park_Acres'], raw_cols['Carrying_Cost']]
df_clean = df.dropna(subset=core_eval_cols).copy()
print(f"Retained {len(df_clean)} fully-mapped districts for the 6D space.")

# Handle Outliers
df_clean['Park_Acres_Log'] = np.log10(df_clean[raw_cols['Park_Acres']] + 1)
cost_cap = df_clean[raw_cols['Carrying_Cost']].quantile(0.95)
df_clean['Cost_Capped'] = df_clean[raw_cols['Carrying_Cost']].clip(upper=cost_cap)

# Build the scoring dataframe
df_score = pd.DataFrame(index=df_clean.index)
df_score['Prestige'] = df_clean[raw_cols['Prestige']]
df_score['Teaching'] = df_clean[raw_cols['Teaching']]
df_score['Commute_Avg'] = (df_clean['Manhattan_Commute_Used'] + df_clean[raw_cols['Family_Commute']]) / 2.0
df_score['Walkability'] = df_clean[raw_cols['Walkability']]
df_score['Nature'] = df_clean['Park_Acres_Log']
df_score['Cost'] = df_clean['Cost_Capped']

# Invert negatives so 100 is always "Best"
df_score['Commute_Avg'] = df_score['Commute_Avg'].max() - df_score['Commute_Avg']
df_score['Cost'] = df_score['Cost'].max() - df_score['Cost']

print("2. Scaling & K-Means Clustering...")
scaler = MinMaxScaler(feature_range=(0, 100))
scaled_data = scaler.fit_transform(df_score)
df_scaled = pd.DataFrame(scaled_data, columns=df_score.columns, index=df_score.index)

# K-Means
kmeans = KMeans(n_clusters=6, random_state=42, n_init='auto')
df_clean['Cluster_ID'] = kmeans.fit_predict(df_scaled)

# Give human-readable names to clusters based on their centroids
cluster_centers = pd.DataFrame(kmeans.cluster_centers_, columns=df_score.columns)
def name_cluster(row):
    # Extremely basic logic to name the archetypes based on their relative highs/lows
    if row['Cost'] < 30 and row['Prestige'] > 70: return "Elite Expensive Estates"
    if row['Walkability'] > 70 and row['Commute_Avg'] > 70: return "Dense Commuter Hubs"
    if row['Teaching'] > 70 and row['Prestige'] < 80: return "Teaching Hidden Gems"
    if row['Nature'] > 70 and row['Walkability'] < 30: return "Rural Nature Sprawl"
    if row['Commute_Avg'] > 70 and row['Cost'] > 60: return "Accessible Value Plays"
    return "Classic Balanced Suburbs"

cluster_names = cluster_centers.apply(name_cluster, axis=1).to_dict()
df_clean['Archetype'] = df_clean['Cluster_ID'].map(cluster_names)
# Deduplicate names if multiple hit the same logic
archetypes = df_clean['Archetype'].unique()
name_counts = {}
final_names = []
for name in df_clean['Archetype']:
    if list(df_clean['Archetype']).count(name) > 1:
        # Just append a number to make them unique if the simplistic logic overlaps too much
        pass 
# A safer way: just use the Cluster ID + basic name
df_clean['Archetype'] = "Cluster " + df_clean['Cluster_ID'].astype(str) + ": " + df_clean['Archetype']


print("3. Pareto Frontier Analysis...")
scores_array = df_scaled.values
is_pareto = np.ones(scores_array.shape[0], dtype=bool)
for i, c in enumerate(scores_array):
    if is_pareto[i]:
        # A town is strictly better if it is >= in ALL dimensions and > in AT LEAST ONE
        # So we kill 'i' if any other town 'j' dominates it
        is_strictly_worse = np.all(scores_array >= c, axis=1) & np.any(scores_array > c, axis=1)
        if np.any(is_strictly_worse):
            is_pareto[i] = False

df_clean['Is_Pareto_Optimal'] = is_pareto
print(f"Found {is_pareto.sum()} Pareto-Optimal Local Maxima.")

# Save master clustered dataset
df_clean.to_csv('clustered_master_dataset.csv', index=False)

print("4. Generating Plotly 3D Visualization...")
# Add hover string
df_clean['Hover_Text'] = df_clean.apply(lambda row: f"<b>{row['District_Name']}</b><br>Prestige: {row[raw_cols['Prestige']]}<br>Teaching: {row[raw_cols['Teaching']]:.2f}<br>Manhattan Mins: {row['Manhattan_Commute_Used']:.1f}<br>Cost: ${row[raw_cols['Carrying_Cost']]:,.0f}<br>Pareto Optimal: {row['Is_Pareto_Optimal']}", axis=1)

fig = px.scatter_3d(
    df_clean, 
    x='Manhattan_Commute_Used', 
    y=raw_cols['Carrying_Cost'], 
    z=raw_cols['Prestige'],
    color='Archetype',
    symbol='Is_Pareto_Optimal',
    size='Max_Walkability',
    hover_name='District_Name',
    hover_data={raw_cols['Teaching']: True, 'Total_Park_Acres': True, 'Manhattan_Commute_Used': False, raw_cols['Carrying_Cost']: False, raw_cols['Prestige']: False, 'Archetype': False, 'Is_Pareto_Optimal': False},
    title="6D Phase Space: Tri-State Suburbs",
    labels={'Manhattan_Commute_Used': 'Commute to Manhattan (Mins)', raw_cols['Carrying_Cost']: 'Monthly Cost ($)', raw_cols['Prestige']: 'Academic Prestige (Niche)'}
)
fig.write_html("6D_Scatter_Visualization.html")

print("5. Generating Folium Geographic Overlay...")
# Need Lat/Lon. Merge with ZIP crosswalk and geocode
df_cross = pd.read_excel('GRF21/grf21_lea_zcta5ce20.xlsx', dtype={'LEAID': str, 'ZCTA5CE20': str})
df_cross['ZCTA5CE20'] = df_cross['ZCTA5CE20'].str.zfill(5)
df_zip = df_cross.drop_duplicates('LEAID')
df_map = df_clean.merge(df_zip[['LEAID', 'ZCTA5CE20']], left_on='sedaadmin', right_on='LEAID', how='inner')

nom = pgeocode.Nominatim('us')
zip_coords = nom.query_postal_code(df_map['ZCTA5CE20'].tolist())
df_map['Lat'] = zip_coords.latitude.values
df_map['Lon'] = zip_coords.longitude.values
df_map = df_map.dropna(subset=['Lat', 'Lon'])

m = folium.Map(location=[40.7128, -74.0060], zoom_start=9) # Center on NYC
colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred']
color_map = {arch: colors[i % len(colors)] for i, arch in enumerate(df_map['Archetype'].unique())}

for idx, row in df_map.iterrows():
    color = color_map[row['Archetype']]
    icon_type = 'star' if row['Is_Pareto_Optimal'] else 'info-sign'
    
    popup_html = f"<h4>{row['District_Name']}</h4>"
    popup_html += f"<b>Cluster:</b> {row['Archetype']}<br>"
    if row['Is_Pareto_Optimal']: popup_html += "<b>🏆 PARETO OPTIMAL</b><br>"
    popup_html += f"<b>Prestige:</b> {row[raw_cols['Prestige']]}<br>"
    popup_html += f"<b>Commute:</b> {row['Manhattan_Commute_Used']} mins<br>"
    popup_html += f"<b>Cost:</b> ${row[raw_cols['Carrying_Cost']]:,.0f}/mo<br>"
    
    folium.CircleMarker(
        location=[row['Lat'], row['Lon']],
        radius=8 if row['Is_Pareto_Optimal'] else 5,
        popup=folium.Popup(popup_html, max_width=300),
        tooltip=f"{row['District_Name']} (Click for stats)",
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.7
    ).add_to(m)

m.save("Interactive_Map_Overlay.html")

print("Pipeline Complete! Visualizations generated.")
