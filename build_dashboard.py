import json
import pandas as pd

# 1. Load the data
with open('master_data.json', 'r') as f:
    raw_data = json.load(f)

# Clean up any NaN or missing values that break JSON parsing in JS
for row in raw_data:
    for key, value in row.items():
        if pd.isna(value):
            row[key] = None

json_payload = json.dumps(raw_data)

# 2. Build the HTML template
html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tri-State Suburb Explorer</title>
    
    <!-- Leaflet CSS & JS -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    
    <!-- D3 for Color Scales -->
    <script src="https://d3js.org/d3.v7.min.js"></script>

    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap" rel="stylesheet">
    
    <style>
        :root {{
            --bg-color: #0f172a;
            --panel-bg: rgba(30, 41, 59, 0.75);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent: #3b82f6;
            --border: rgba(255,255,255,0.1);
        }}
        
        body, html {{
            margin: 0; padding: 0;
            height: 100vh; width: 100vw;
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            overflow: hidden;
        }}

        #app-container {{
            display: flex;
            height: 100vh;
            width: 100vw;
        }}

        /* Glassmorphic Sidebar */
        #sidebar {{
            width: 400px;
            background: var(--panel-bg);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border-right: 1px solid var(--border);
            padding: 24px;
            overflow-y: auto;
            z-index: 1000;
            box-shadow: 4px 0 24px rgba(0,0,0,0.5);
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}

        #map-container {{
            flex-grow: 1;
            height: 100vh;
            position: relative;
        }}
        
        #map {{
            height: 100%;
            width: 100%;
            background: #1e1e1e; /* Dark fallback */
        }}

        h1 {{ margin: 0; font-size: 24px; font-weight: 800; letter-spacing: -0.5px; background: linear-gradient(to right, #60a5fa, #c084fc); -webkit-background-clip: text; color: transparent; }}
        h2 {{ margin: 0; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; color: var(--text-muted); padding-bottom: 8px; border-bottom: 1px solid var(--border); }}
        
        .control-group {{ display: flex; flex-direction: column; gap: 8px; }}
        label {{ font-size: 13px; font-weight: 600; display: flex; justify-content: space-between; }}
        .val-display {{ color: var(--accent); }}
        
        input[type="range"] {{ width: 100%; cursor: pointer; accent-color: var(--accent); }}
        select {{ width: 100%; padding: 8px; background: rgba(0,0,0,0.5); border: 1px solid var(--border); color: white; border-radius: 6px; font-family: 'Inter'; outline: none; }}
        
        .stat-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px; }}
        .stat-box {{ background: rgba(0,0,0,0.3); padding: 10px; border-radius: 8px; border: 1px solid var(--border); text-align: center; }}
        .stat-value {{ font-size: 18px; font-weight: 800; color: #fff; }}
        .stat-label {{ font-size: 10px; color: var(--text-muted); text-transform: uppercase; }}

        /* Tooltip styling */
        .leaflet-popup-content-wrapper {{
            background: rgba(15, 23, 42, 0.95);
            backdrop-filter: blur(10px);
            color: #fff;
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.8);
        }}
        .leaflet-popup-tip {{ background: rgba(15, 23, 42, 0.95); }}
        .leaflet-popup-content {{ margin: 16px; font-family: 'Inter'; width: 280px !important; }}
        .popup-title {{ font-size: 18px; font-weight: 800; margin-bottom: 4px; border-bottom: 1px solid rgba(255,255,255,0.2); padding-bottom: 8px; }}
        .popup-subtitle {{ font-size: 12px; color: #94a3b8; margin-bottom: 12px; }}
        .popup-row {{ display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 13px; border-bottom: 1px dashed rgba(255,255,255,0.1); padding-bottom: 4px; }}
        .popup-val {{ font-weight: 600; color: #60a5fa; }}

        .metric-count {{ font-size: 12px; color: #94a3b8; margin-top: 10px; text-align: center; }}
    </style>
</head>
<body>

<div id="app-container">
    <div id="sidebar">
        <div>
            <h1>Tri-State Explorer</h1>
            <div id="town-count" class="metric-count">Loading data...</div>
        </div>

        <div>
            <h2>Core Filters</h2>
            
            <div class="control-group" style="margin-top: 12px;">
                <label>Max Commute <span class="val-display" id="val-commute">90 mins</span></label>
                <input type="range" id="filter-commute" min="30" max="150" value="90" step="5">
            </div>

            <div class="control-group" style="margin-top: 12px;">
                <label>Min Prestige <span class="val-display" id="val-prestige">85</span></label>
                <input type="range" id="filter-prestige" min="70" max="100" value="85" step="1">
            </div>

            <div class="control-group" style="margin-top: 12px;">
                <label>Min Walkability <span class="val-display" id="val-walk">10.0</span></label>
                <input type="range" id="filter-walk" min="0" max="20" value="10" step="0.5">
            </div>
            
            <div class="control-group" style="margin-top: 12px;">
                <label>Max Monthly Cost <span class="val-display" id="val-cost">$12,000</span></label>
                <input type="range" id="filter-cost" min="3000" max="25000" value="12000" step="500">
            </div>
        </div>

        <div>
            <h2>Visual Mapping</h2>
            <div class="control-group" style="margin-top: 12px;">
                <label>Color By</label>
                <select id="map-color">
                    <option value="Archetype">K-Means Cluster Archetype</option>
                    <option value="True_Monthly_Carrying_Cost">Monthly Cost (Green to Red)</option>
                    <option value="Predicted_Niche_Score">Prestige (Red to Green)</option>
                    <option value="SEDA_Growth_Score">Teaching Growth (Red to Green)</option>
                    <option value="BA_Plus_Percentage">College Attainment (Red to Blue)</option>
                </select>
            </div>

            <div class="control-group" style="margin-top: 12px;">
                <label>Size By</label>
                <select id="map-size">
                    <option value="Constant">Constant Size</option>
                    <option value="Predicted_Niche_Score">Prestige (Larger = Better)</option>
                    <option value="True_Monthly_Carrying_Cost">Cost (Larger = More Expensive)</option>
                    <option value="Max_Walkability">Walkability (Larger = More Walkable)</option>
                </select>
            </div>
        </div>
        
        <div style="flex-grow: 1;"></div>
        <div style="font-size: 11px; color: var(--text-muted); text-align: center;">
            Built by Antigravity AI
        </div>
    </div>

    <div id="map-container">
        <div id="map"></div>
    </div>
</div>

<script>
    // 1. Load Data Payload
    const masterData = {json_payload};
    
    // 2. Initialize Leaflet Map (Dark Mode Theme)
    const map = L.map('map', {{ zoomControl: false }}).setView([40.85, -74.00], 9);
    L.control.zoom({{ position: 'topright' }}).addTo(map);

    // Add CartoDB Dark Matter tiles
    L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
        attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
        subdomains: 'abcd',
        maxZoom: 19
    }}).addTo(map);

    let markersLayer = L.layerGroup().addTo(map);

    // 3. UI Elements
    const elCommute = document.getElementById('filter-commute');
    const elPrestige = document.getElementById('filter-prestige');
    const elWalk = document.getElementById('filter-walk');
    const elCost = document.getElementById('filter-cost');
    const elColor = document.getElementById('map-color');
    const elSize = document.getElementById('map-size');
    const elCount = document.getElementById('town-count');

    // Display elements
    const dispCommute = document.getElementById('val-commute');
    const dispPrestige = document.getElementById('val-prestige');
    const dispWalk = document.getElementById('val-walk');
    const dispCost = document.getElementById('val-cost');

    // Cluster Colors
    const clusterColors = {{
        'Cluster 0': '#ef4444', // Red
        'Cluster 1': '#3b82f6', // Blue
        'Cluster 2': '#10b981', // Green
        'Cluster 3': '#8b5cf6', // Purple
        'Cluster 4': '#f59e0b', // Orange
        'Cluster 5': '#ec4899'  // Pink
    }};

    // D3 Scales for Dynamic Coloring
    const scaleCost = d3.scaleSequential(d3.interpolateRdYlGn).domain([10000, 3000]); // Red high, Green low
    const scalePrestige = d3.scaleSequential(d3.interpolateRdYlGn).domain([80, 100]); // Red low, Green high
    const scaleTeaching = d3.scaleSequential(d3.interpolateRdYlGn).domain([-0.05, 0.05]); 
    const scaleBA = d3.scaleSequential(d3.interpolateBlues).domain([0.2, 0.9]);

    function formatMoney(num) {{
        return '$' + Math.round(num).toLocaleString();
    }}

    // Main Render Function
    function renderMap() {{
        // Get filter values
        const maxCommute = parseFloat(elCommute.value);
        const minPrestige = parseFloat(elPrestige.value);
        const minWalk = parseFloat(elWalk.value);
        const maxCost = parseFloat(elCost.value);

        // Update display labels
        dispCommute.innerText = maxCommute + " mins";
        dispPrestige.innerText = minPrestige;
        dispWalk.innerText = minWalk.toFixed(1);
        dispCost.innerText = formatMoney(maxCost);

        // Filter Data
        const filteredData = masterData.filter(d => 
            (d.Manhattan_Commute_Used <= maxCommute || d.Manhattan_Commute_Used == null) &&
            (d.Predicted_Niche_Score >= minPrestige || d.Predicted_Niche_Score == null) &&
            (d.Max_Walkability >= minWalk || d.Max_Walkability == null) &&
            (d.True_Monthly_Carrying_Cost <= maxCost || d.True_Monthly_Carrying_Cost == null)
        );

        elCount.innerText = `Showing ${{filteredData.length}} matching districts`;

        // Clear existing markers
        markersLayer.clearLayers();

        // Get Mapping Settings
        const colorBy = elColor.value;
        const sizeBy = elSize.value;

        // Render Markers
        filteredData.forEach(d => {{
            if (!d.Lat || !d.Lon) return;

            // Determine Radius
            let radius = 6;
            if (sizeBy === 'Predicted_Niche_Score') radius = Math.max(3, (d.Predicted_Niche_Score - 70) / 2);
            if (sizeBy === 'True_Monthly_Carrying_Cost') radius = Math.max(3, (d.True_Monthly_Carrying_Cost) / 1000);
            if (sizeBy === 'Max_Walkability') radius = Math.max(3, d.Max_Walkability);

            // Determine Color
            let fillColor = '#ffffff';
            if (colorBy === 'Archetype' && d.Archetype) fillColor = clusterColors[d.Archetype] || '#ffffff';
            else if (colorBy === 'True_Monthly_Carrying_Cost') fillColor = scaleCost(d.True_Monthly_Carrying_Cost);
            else if (colorBy === 'Predicted_Niche_Score') fillColor = scalePrestige(d.Predicted_Niche_Score);
            else if (colorBy === 'SEDA_Growth_Score') fillColor = scaleTeaching(d.SEDA_Growth_Score);
            else if (colorBy === 'BA_Plus_Percentage') fillColor = scaleBA(d.BA_Plus_Percentage);

            // Create Tooltip HTML
            const baPercent = d.BA_Plus_Percentage ? (d.BA_Plus_Percentage * 100).toFixed(1) + '%' : 'N/A';
            const asianPercent = d.perasn ? d.perasn.toFixed(1) + '%' : 'N/A';
            const medInc = d.Median_Income_Est ? formatMoney(d.Median_Income_Est) : 'N/A';
            const cost = d.True_Monthly_Carrying_Cost ? formatMoney(d.True_Monthly_Carrying_Cost) : 'N/A';
            const teach = d.SEDA_Growth_Score ? d.SEDA_Growth_Score.toFixed(3) : 'N/A';
            const walk = d.Max_Walkability ? d.Max_Walkability.toFixed(1) : 'N/A';
            const cluster = d.Archetype ? d.Archetype : 'Unclustered';

            const popupHtml = `
                <div class="popup-title">${{d.District_Name}}</div>
                <div class="popup-subtitle">${{d.County}}, ${{d.State}} | ${{cluster}}</div>
                
                <div class="popup-row"><span>Prestige Score</span> <span class="popup-val">${{d.Predicted_Niche_Score}}</span></div>
                <div class="popup-row"><span>Manhattan Commute</span> <span class="popup-val">${{d.Manhattan_Commute_Used}} mins</span></div>
                <div class="popup-row"><span>Monthly Cost</span> <span class="popup-val">${{cost}}</span></div>
                <div class="popup-row"><span>Walkability</span> <span class="popup-val">${{walk}}</span></div>
                <div class="popup-row"><span>Teaching Growth</span> <span class="popup-val">${{teach}}</span></div>
                <br>
                <div class="popup-row"><span>College Attainment</span> <span class="popup-val">${{baPercent}}</span></div>
                <div class="popup-row"><span>Median Income</span> <span class="popup-val">${{medInc}}</span></div>
                <div class="popup-row"><span>Asian Population</span> <span class="popup-val">${{asianPercent}}</span></div>
            `;

            L.circleMarker([d.Lat, d.Lon], {{
                radius: radius,
                fillColor: fillColor,
                color: '#1e293b',
                weight: 1.5,
                opacity: 1,
                fillOpacity: 0.8
            }}).bindPopup(popupHtml).addTo(markersLayer);
        }});
    }}

    // Attach Event Listeners
    [elCommute, elPrestige, elWalk, elCost, elColor, elSize].forEach(el => {{
        el.addEventListener('input', renderMap);
    }});

    // Initial Render
    renderMap();

</script>
</body>
</html>
"""

with open('../brain/1aa0d3c1-7a3f-4417-9041-18ac4fb2f2a3/Master_Interactive_Dashboard.html', 'w') as f:
    f.write(html_template)

print("Master Interactive Dashboard generated successfully!")
