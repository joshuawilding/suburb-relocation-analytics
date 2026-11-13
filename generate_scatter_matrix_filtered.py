import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import KMeans
import plotly.express as px

print("Loading Master Dataset...")
df = pd.read_csv('tri_state_master_with_niche.csv')

# 1. Impute Missing Data
df['Family_Proximity_Avg'] = df[['Drive_Mins_To_Old Tappan', 'Drive_Mins_To_Queens', 'Drive_Mins_To_Roslyn']].mean(axis=1)
df['Manhattan_Commute_Used'] = df['Dense_Drive_Mins_To_Manhattan'].fillna(df['Drive_Mins_To_Manhattan'])

cols_to_impute = ['True_Monthly_Carrying_Cost', 'Max_Walkability', 'SEDA_Growth_Score', 'Predicted_Niche_Score']
for col in cols_to_impute:
    df[col] = df.groupby('County')[col].transform(lambda x: x.fillna(x.median()))
    df[col] = df.groupby('State')[col].transform(lambda x: x.fillna(x.median()))
    df[col] = df[col].fillna(df[col].median())

# 2. Apply User Filters!
print(f"Original rows: {len(df)}")
df = df[df['Manhattan_Commute_Used'] <= 90]
df = df[df['Predicted_Niche_Score'] >= 85]
df = df[df['Max_Walkability'] >= 10]
print(f"Rows after filters (Commute <= 90, Prestige >= 85, Walkability >= 10): {len(df)}")

# 3. Pre-processing for Clustering
df_score = pd.DataFrame(index=df.index)
df_score['Prestige'] = df['Predicted_Niche_Score']
df_score['Teaching'] = df['SEDA_Growth_Score']
df_score['Commute_Avg'] = (df['Manhattan_Commute_Used'] + df['Family_Proximity_Avg']) / 2.0
df_score['Walkability'] = df['Max_Walkability']

cost_cap = df['True_Monthly_Carrying_Cost'].quantile(0.95)
df_score['Cost'] = df['True_Monthly_Carrying_Cost'].clip(upper=cost_cap)

df_score['Commute_Avg_Inverted'] = df_score['Commute_Avg'].max() - df_score['Commute_Avg']
df_score['Cost_Inverted'] = df_score['Cost'].max() - df_score['Cost']

# 4. Scale and Cluster
scaler = MinMaxScaler(feature_range=(0, 100))
scaled_data = scaler.fit_transform(df_score[['Prestige', 'Teaching', 'Commute_Avg_Inverted', 'Walkability', 'Cost_Inverted']])
kmeans = KMeans(n_clusters=4, random_state=42, n_init='auto')
df['Cluster_ID'] = kmeans.fit_predict(scaled_data)
df['Archetype'] = "Cluster " + df['Cluster_ID'].astype(str)

# 5. Generate 2D Scatter Matrix
print("Generating Plotly Scatter Matrix...")
plot_df = df.copy()
plot_df['Hover_Name'] = plot_df['District_Name']

# Format tooltip columns nicely
plot_df['% BA+'] = plot_df['BA_Plus_Percentage'] * 100
plot_df['Median Income ($)'] = plot_df['Median_Income_Est']
plot_df['% Asian'] = plot_df['perasn']

fig = px.scatter_matrix(
    plot_df,
    dimensions=['Predicted_Niche_Score', 'SEDA_Growth_Score', 'Manhattan_Commute_Used', 'Max_Walkability', 'True_Monthly_Carrying_Cost'],
    color='Archetype',
    hover_name='Hover_Name',
    hover_data={'% BA+': ':.1f', 'Median Income ($)': ':,.0f', '% Asian': ':.1f'},
    title="5D Scatter Matrix (Filtered: Commute <= 90m, Prestige >= 85, Walkability >= 10)",
    labels={
        'Predicted_Niche_Score': 'Prestige',
        'SEDA_Growth_Score': 'Teaching',
        'Manhattan_Commute_Used': 'Commute (Mins)',
        'Max_Walkability': 'Walkability',
        'True_Monthly_Carrying_Cost': 'Cost ($)'
    },
    height=1000,
    width=1200
)

fig.update_traces(diagonal_visible=False, marker=dict(size=4, opacity=0.7))
fig.write_html("2D_Scatter_Matrix_Filtered.html")
print("Filtered Scatter Matrix generated!")

# 5.5 Generate 3D Scatter Plot
print("Generating 3D Scatter Plot...")
fig_3d = px.scatter_3d(
    plot_df,
    x='Manhattan_Commute_Used',
    y='True_Monthly_Carrying_Cost',
    z='Predicted_Niche_Score',
    color='Archetype',
    hover_name='Hover_Name',
    hover_data={'% BA+': ':.1f', 'Median Income ($)': ':,.0f', '% Asian': ':.1f', 'SEDA_Growth_Score': ':.3f', 'Max_Walkability': ':.1f'},
    title="3D Phase Space (Cost vs. Commute vs. Prestige)",
    labels={
        'Predicted_Niche_Score': 'Prestige',
        'Manhattan_Commute_Used': 'Commute (Mins)',
        'True_Monthly_Carrying_Cost': 'Monthly Cost ($)'
    }
)
fig_3d.update_traces(marker=dict(size=5, opacity=0.8))
fig_3d.write_html("3D_Scatter_Visualization_Filtered.html")
print("3D Scatter Plot generated!")

# 6. Generate Folium Geographic Overlay
print("Generating Folium Map Overlay...")
import folium
import pgeocode

df_cross = pd.read_excel('GRF21/grf21_lea_zcta5ce20.xlsx', dtype={'LEAID': str, 'ZCTA5CE20': str})
df_cross['ZCTA5CE20'] = df_cross['ZCTA5CE20'].str.zfill(5)
df_zip = df_cross.drop_duplicates('LEAID')
df['sedaadmin'] = df['sedaadmin'].astype(str)
df_map = df.merge(df_zip[['LEAID', 'ZCTA5CE20']], left_on='sedaadmin', right_on='LEAID', how='inner')

nom = pgeocode.Nominatim('us')
zip_coords = nom.query_postal_code(df_map['ZCTA5CE20'].tolist())
df_map['Lat'] = zip_coords.latitude.values
df_map['Lon'] = zip_coords.longitude.values
df_map = df_map.dropna(subset=['Lat', 'Lon'])

m = folium.Map(location=[40.7128, -74.0060], zoom_start=9)
colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred']
color_map = {arch: colors[i % len(colors)] for i, arch in enumerate(df_map['Archetype'].unique())}

for idx, row in df_map.iterrows():
    color = color_map[row['Archetype']]
    
    popup_html = f"<h4>{row['District_Name']}</h4>"
    popup_html += f"<b>Cluster:</b> {row['Archetype']}<br>"
    popup_html += f"<b>Prestige:</b> {row['Predicted_Niche_Score']}<br>"
    popup_html += f"<b>Teaching:</b> {row['SEDA_Growth_Score']:.3f}<br>"
    popup_html += f"<b>Commute:</b> {row['Manhattan_Commute_Used']} mins<br>"
    popup_html += f"<b>Cost:</b> ${row['True_Monthly_Carrying_Cost']:,.0f}/mo<br><hr>"
    popup_html += f"<b>% BA+:</b> {(row['BA_Plus_Percentage'] * 100):.1f}%<br>"
    popup_html += f"<b>Median Income:</b> ${row['Median_Income_Est']:,.0f}<br>"
    popup_html += f"<b>% Asian:</b> {row['perasn']:.1f}%<br>"
    
    folium.CircleMarker(
        location=[row['Lat'], row['Lon']],
        radius=6,
        popup=folium.Popup(popup_html, max_width=300),
        tooltip=f"{row['District_Name']}",
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.7
    ).add_to(m)

m.save("Interactive_Map_Overlay.html")
print("Folium Map updated!")

# 7. Generate Geographic Heatmap (Cost = Color, Prestige = Size)
print("Generating Geographic Heatmap...")
import branca.colormap as cm

m2 = folium.Map(location=[40.7128, -74.0060], zoom_start=9)

# Create a Red (High Cost) to Green (Low Cost) colormap
min_cost = df_map['True_Monthly_Carrying_Cost'].min()
max_cost = df_map['True_Monthly_Carrying_Cost'].quantile(0.95) # Cap at 95th so outliers don't ruin the gradient
colormap = cm.LinearColormap(colors=['green', 'yellow', 'red'], vmin=min_cost, vmax=max_cost)
colormap.caption = 'Monthly Carrying Cost ($)'
m2.add_child(colormap)

for idx, row in df_map.iterrows():
    # Size based on Prestige (Scores are 85-100, so subtract 80 and multiply to scale properly)
    radius = (row['Predicted_Niche_Score'] - 80) / 1.5 
    
    # Color based on Cost
    cost = min(row['True_Monthly_Carrying_Cost'], max_cost) # Cap the visual color at the 95th percentile
    color = colormap(cost)
    
    popup_html = f"<h4>{row['District_Name']}</h4>"
    popup_html += f"<b>Prestige:</b> {row['Predicted_Niche_Score']}<br>"
    popup_html += f"<b>Cost:</b> ${row['True_Monthly_Carrying_Cost']:,.0f}/mo<br><hr>"
    popup_html += f"<b>% BA+:</b> {(row['BA_Plus_Percentage'] * 100):.1f}%<br>"
    popup_html += f"<b>Median Income:</b> ${row['Median_Income_Est']:,.0f}<br>"
    popup_html += f"<b>% Asian:</b> {row['perasn']:.1f}%<br>"
    
    folium.CircleMarker(
        location=[row['Lat'], row['Lon']],
        radius=radius,
        popup=folium.Popup(popup_html, max_width=300),
        tooltip=f"{row['District_Name']} (Cost: ${row['True_Monthly_Carrying_Cost']:,.0f})",
        color='black', # Add a thin black border so bubbles pop
        weight=1,
        fill=True,
        fill_color=color,
        fill_opacity=0.8
    ).add_to(m2)

m2.save("Geographic_Cost_Heatmap.html")
print("Geographic Heatmap generated!")
