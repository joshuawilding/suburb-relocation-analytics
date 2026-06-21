import json

# 1. Read the parsed GeoJSON from the previous step
with open('district_boundaries.geojson', 'r') as f:
    geojson_payload = f.read()

# 2. Build the HTML UI template
html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Advanced Tri-State Choropleth Dashboard</title>
    
    <!-- Leaflet CSS & JS -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    
    <!-- D3 for Color Scales -->
    <script src="https://d3js.org/d3.v7.min.js"></script>

    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap" rel="stylesheet">
    
    <style>
        :root {{
            --bg-color: #f8fafc;
            --panel-bg: rgba(255, 255, 255, 0.95);
            --text-main: #0f172a;
            --text-muted: #64748b;
            --accent: #2563eb;
            --border: rgba(0,0,0,0.1);
            --shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -2px rgba(0,0,0,0.1);
        }}
        
        body, html {{
            margin: 0; padding: 0;
            height: 100vh; width: 100vw;
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            overflow: hidden;
        }}

        #app-container {{ display: flex; height: 100vh; width: 100vw; }}

        /* Clean Light Sidebar */
        #sidebar {{
            width: 420px;
            background: var(--panel-bg);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-right: 1px solid var(--border);
            padding: 24px;
            overflow-y: auto;
            z-index: 1000;
            box-shadow: 4px 0 24px rgba(0,0,0,0.05);
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}

        #map-container {{ flex-grow: 1; height: 100vh; position: relative; }}
        #map {{ height: 100%; width: 100%; background: #e2e8f0; }}

        h1 {{ margin: 0; font-size: 24px; font-weight: 800; letter-spacing: -0.5px; color: #0f172a; }}
        h2 {{ margin: 0; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; color: var(--text-muted); padding-bottom: 8px; border-bottom: 1px solid var(--border); }}
        
        .control-group {{ display: flex; flex-direction: column; gap: 8px; margin-top: 12px; }}
        label {{ font-size: 13px; font-weight: 600; display: flex; justify-content: space-between; }}
        .val-display {{ color: var(--accent); }}
        
        input[type="range"] {{ width: 100%; cursor: pointer; accent-color: var(--accent); }}
        select {{ width: 100%; padding: 10px; background: #f1f5f9; border: 1px solid var(--border); color: #0f172a; border-radius: 6px; font-family: 'Inter'; font-size: 13px; outline: none; cursor: pointer; }}
        
        /* Universal Tooltip styling (Light Mode) */
        .leaflet-popup-content-wrapper {{
            background: #ffffff;
            color: #0f172a;
            border: 1px solid rgba(0,0,0,0.1);
            border-radius: 12px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.2);
        }}
        .leaflet-popup-tip {{ background: #ffffff; }}
        .leaflet-popup-content {{ margin: 16px; font-family: 'Inter'; width: 340px !important; }}
        
        .popup-title {{ font-size: 20px; font-weight: 800; margin-bottom: 4px; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px; color: #0f172a; }}
        .popup-subtitle {{ font-size: 13px; color: #64748b; margin-bottom: 12px; font-weight: 600; }}
        
        .tooltip-scroll-container {{
            max-height: 350px;
            overflow-y: auto;
            padding-right: 8px;
        }}
        
        /* Custom Scrollbar for tooltip */
        .tooltip-scroll-container::-webkit-scrollbar {{ width: 6px; }}
        .tooltip-scroll-container::-webkit-scrollbar-track {{ background: #f1f5f9; border-radius: 4px; }}
        .tooltip-scroll-container::-webkit-scrollbar-thumb {{ background: #cbd5e1; border-radius: 4px; }}
        
        .popup-row {{ display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 13px; border-bottom: 1px solid #f1f5f9; padding-bottom: 6px; align-items: center; }}
        .popup-key {{ color: #475569; font-weight: 400; max-width: 65%; }}
        .popup-val {{ font-weight: 700; color: #0f172a; text-align: right; max-width: 35%; }}

        .metric-count {{ font-size: 13px; color: #64748b; margin-top: 6px; font-weight: 600; }}
        
        .legend {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: var(--shadow);
            border: 1px solid var(--border);
            line-height: 1.5;
            color: #0f172a;
            font-size: 12px;
            font-weight: 600;
        }}
        .legend i {{ width: 18px; height: 18px; float: left; margin-right: 8px; opacity: 0.8; border: 1px solid rgba(0,0,0,0.1); border-radius: 3px; }}
    </style>
</head>
<body>

<div id="app-container">
    <div id="sidebar">
        <div>
            <h1>Geographic Explorer</h1>
            <div id="town-count" class="metric-count">Loading districts...</div>
        </div>

        <div>
            <h2>Core Filters</h2>
            <div class="control-group">
                <label>Max Commute <span class="val-display" id="val-commute">90 mins</span></label>
                <input type="range" id="filter-commute" min="30" max="150" value="90" step="5">
            </div>
            <div class="control-group">
                <label>Min Prestige <span class="val-display" id="val-prestige">85</span></label>
                <input type="range" id="filter-prestige" min="70" max="100" value="85" step="1">
            </div>
            <div class="control-group">
                <label>Min Walkability <span class="val-display" id="val-walk">10.0</span></label>
                <input type="range" id="filter-walk" min="0" max="20" value="10" step="0.5">
            </div>
            <div class="control-group">
                <label>Max Monthly Cost <span class="val-display" id="val-cost">$12,000</span></label>
                <input type="range" id="filter-cost" min="3000" max="25000" value="12000" step="500">
            </div>
        </div>

        <div>
            <h2>Dynamic Advanced Filter</h2>
            <div class="control-group">
                <label>Select any variable to filter on:</label>
                <select id="adv-filter-select">
                    <option value="none">-- No Advanced Filter --</option>
                </select>
            </div>
            <div class="control-group" id="adv-filter-container" style="display: none;">
                <label><span id="adv-label">Value</span> <span class="val-display" id="adv-val"></span></label>
                <input type="range" id="adv-slider">
                <select id="adv-operator" style="margin-top: 4px;">
                    <option value=">=">Greater Than or Equal (>=)</option>
                    <option value="<=">Less Than or Equal (<=)</option>
                </select>
            </div>
        </div>

        <div>
            <h2>Choropleth Visual Mapping</h2>
            <div class="control-group">
                <label>Color Scale By:</label>
                <select id="map-color">
                    <!-- Options populated dynamically -->
                </select>
            </div>
        </div>
        
        <div style="flex-grow: 1;"></div>
        <div style="font-size: 11px; color: var(--text-muted); text-align: center;">
            Engineered by Antigravity AI
        </div>
    </div>

    <div id="map-container">
        <div id="map"></div>
    </div>
</div>

<script>
    // 1. Load GeoJSON Payload natively
    const geojsonData = {geojson_payload};
    
    // 2. Initialize Leaflet Map (Light Theme - CartoDB Positron)
    const map = L.map('map', {{ zoomControl: false }}).setView([40.85, -74.00], 9);
    L.control.zoom({{ position: 'topright' }}).addTo(map);

    L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
        attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
        subdomains: 'abcd',
        maxZoom: 19
    }}).addTo(map);

    let geoJsonLayer;
    let legend = L.control({{position: 'bottomright'}});

    // 3. UI Elements
    const elCommute = document.getElementById('filter-commute');
    const elPrestige = document.getElementById('filter-prestige');
    const elWalk = document.getElementById('filter-walk');
    const elCost = document.getElementById('filter-cost');
    const elColor = document.getElementById('map-color');
    const elCount = document.getElementById('town-count');
    
    const advSelect = document.getElementById('adv-filter-select');
    const advContainer = document.getElementById('adv-filter-container');
    const advSlider = document.getElementById('adv-slider');
    const advLabel = document.getElementById('adv-label');
    const advVal = document.getElementById('adv-val');
    const advOperator = document.getElementById('adv-operator');

    const dispCommute = document.getElementById('val-commute');
    const dispPrestige = document.getElementById('val-prestige');
    const dispWalk = document.getElementById('val-walk');
    const dispCost = document.getElementById('val-cost');

    // 4. Dynamically Parse all Numerical Columns from Data for Dropdowns
    const sampleProps = geojsonData.features[0].properties;
    const numericKeys = [];
    
    for (let key in sampleProps) {{
        if (typeof sampleProps[key] === 'number' && key !== 'Lat' && key !== 'Lon' && key !== 'Cluster_ID') {{
            numericKeys.push(key);
        }}
    }}
    numericKeys.sort();

    // Populate Color Dropdown
    numericKeys.forEach(key => {{
        const opt = document.createElement('option');
        opt.value = key;
        opt.innerText = key.replace(/_/g, ' ');
        if (key === 'True_Monthly_Carrying_Cost') opt.selected = true;
        elColor.appendChild(opt);
    }});
    
    // Add Archetype option
    const archOpt = document.createElement('option');
    archOpt.value = 'Archetype';
    archOpt.innerText = 'K-Means Cluster Archetype';
    elColor.prepend(archOpt);

    // Populate Advanced Filter Dropdown
    numericKeys.forEach(key => {{
        const opt = document.createElement('option');
        opt.value = key;
        opt.innerText = key.replace(/_/g, ' ');
        advSelect.appendChild(opt);
    }});

    function formatNumber(num, key) {{
        if (num == null) return "N/A";
        if (key.includes('Cost') || key.includes('Price') || key.includes('Income')) return '$' + Math.round(num).toLocaleString();
        if (key.includes('Percentage') || key.includes('perwht') || key.includes('perasn') || key.includes('perhsp') || key.includes('perblk')) return (num * (num < 1 && key.includes('Percentage') ? 100 : 1)).toFixed(1) + '%';
        if (Math.abs(num) < 10) return num.toFixed(3);
        return Math.round(num).toLocaleString();
    }}

    // Advanced Filter setup logic
    advSelect.addEventListener('change', () => {{
        const key = advSelect.value;
        if (key === 'none') {{
            advContainer.style.display = 'none';
            renderMap();
            return;
        }}
        
        // Find min/max for the selected key
        let min = Infinity, max = -Infinity;
        geojsonData.features.forEach(f => {{
            const val = f.properties[key];
            if (val != null) {{
                if (val < min) min = val;
                if (val > max) max = val;
            }}
        }});

        advSlider.min = min;
        advSlider.max = max;
        advSlider.step = (max - min) / 100;
        advSlider.value = min + (max - min) / 2; // set to middle default
        
        advLabel.innerText = key.replace(/_/g, ' ');
        advContainer.style.display = 'flex';
        
        updateAdvLabel();
        renderMap();
    }});

    function updateAdvLabel() {{
        advVal.innerText = formatNumber(parseFloat(advSlider.value), advSelect.value);
    }}
    advSlider.addEventListener('input', () => {{ updateAdvLabel(); renderMap(); }});
    advOperator.addEventListener('change', renderMap);

    // Main Render Function
    function renderMap() {{
        const maxCommute = parseFloat(elCommute.value);
        const minPrestige = parseFloat(elPrestige.value);
        const minWalk = parseFloat(elWalk.value);
        const maxCost = parseFloat(elCost.value);
        const colorBy = elColor.value;

        // Display updates
        dispCommute.innerText = maxCommute + " mins";
        dispPrestige.innerText = minPrestige;
        dispWalk.innerText = minWalk.toFixed(1);
        dispCost.innerText = formatNumber(maxCost, 'Cost');

        // Advanced Filter
        const advKey = advSelect.value;
        const advOp = advOperator.value;
        const advThreshold = parseFloat(advSlider.value);

        // 1. Filter GeoJSON Features
        const filteredFeatures = geojsonData.features.filter(f => {{
            const d = f.properties;
            let pass = true;
            
            if (d.Manhattan_Commute_Used != null && d.Manhattan_Commute_Used > maxCommute) pass = false;
            if (d.Predicted_Niche_Score != null && d.Predicted_Niche_Score < minPrestige) pass = false;
            if (d.Max_Walkability != null && d.Max_Walkability < minWalk) pass = false;
            if (d.True_Monthly_Carrying_Cost != null && d.True_Monthly_Carrying_Cost > maxCost) pass = false;
            
            if (advKey !== 'none' && d[advKey] != null) {{
                if (advOp === '>=' && d[advKey] < advThreshold) pass = false;
                if (advOp === '<=' && d[advKey] > advThreshold) pass = false;
            }}
            return pass;
        }});

        elCount.innerText = `Showing ${{filteredFeatures.length}} active districts`;

        if (geoJsonLayer) map.removeLayer(geoJsonLayer);

        // 2. Setup Dynamic Color Scale
        let colorScale;
        let domainMin = 0, domainMax = 100;
        
        if (colorBy !== 'Archetype') {{
            // Calculate Min/Max of currently filtered dataset for the chosen color variable
            const vals = filteredFeatures.map(f => f.properties[colorBy]).filter(v => v != null);
            if (vals.length > 0) {{
                // Determine 5th and 95th percentiles to avoid outlier washout
                vals.sort((a,b) => a - b);
                domainMin = vals[Math.floor(vals.length * 0.05)] || vals[0];
                domainMax = vals[Math.floor(vals.length * 0.95)] || vals[vals.length - 1];
            }}
            
            // Choose Interpolator (Cost is Red/Green inverted, Prestige is Red/Green normal, etc.)
            let interpolator = d3.interpolatePlasma; // Default
            if (colorBy.includes('Cost') || colorBy.includes('Price') || colorBy.includes('Commute') || colorBy.includes('Crime')) {{
                // Bad things = Red, Good things = Green
                colorScale = d3.scaleSequential(d3.interpolateRdYlGn).domain([domainMax, domainMin]);
            }} else if (colorBy.includes('Score') || colorBy.includes('Prestige') || colorBy.includes('Walkability')) {{
                // Good things = Green, Bad things = Red
                colorScale = d3.scaleSequential(d3.interpolateRdYlGn).domain([domainMin, domainMax]);
            }} else {{
                // Neutral demographics = Viridis/Plasma
                colorScale = d3.scaleSequential(d3.interpolateViridis).domain([domainMin, domainMax]);
            }}
        }}

        const clusterColors = {{
            'Cluster 0': '#ef4444', 'Cluster 1': '#3b82f6', 
            'Cluster 2': '#10b981', 'Cluster 3': '#8b5cf6', 
            'Cluster 4': '#f59e0b', 'Cluster 5': '#ec4899'
        }};

        function getColor(val, arch) {{
            if (colorBy === 'Archetype') return clusterColors[arch] || '#cbd5e1';
            if (val == null) return '#cbd5e1'; // Grey for missing data
            return colorScale(val);
        }}

        // 3. Draw GeoJSON Polygons!
        geoJsonLayer = L.geoJSON(filteredFeatures, {{
            style: function(feature) {{
                const val = feature.properties[colorBy];
                const color = getColor(val, feature.properties.Archetype);
                return {{
                    fillColor: color,
                    weight: 1.5,
                    opacity: 1,
                    color: '#ffffff', // White borders between districts looks extremely clean in Light Mode
                    fillOpacity: 0.8
                }};
            }},
            onEachFeature: function(feature, layer) {{
                // Hover Effects
                layer.on({{
                    mouseover: function(e) {{
                        var l = e.target;
                        l.setStyle({{ weight: 3, color: '#0f172a', fillOpacity: 1 }});
                        if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {{ l.bringToFront(); }}
                    }},
                    mouseout: function(e) {{ geoJsonLayer.resetStyle(e.target); }}
                }});

                // Universal Tooltip Generation
                const p = feature.properties;
                let rowsHtml = '';
                
                // Group 1: The Core Metrics
                const coreKeys = ['Predicted_Niche_Score', 'True_Monthly_Carrying_Cost', 'Manhattan_Commute_Used', 'Max_Walkability', 'SEDA_Growth_Score'];
                coreKeys.forEach(k => {{
                    rowsHtml += `<div class="popup-row"><span class="popup-key"><b>${{k.replace(/_/g, ' ')}}</b></span> <span class="popup-val">${{formatNumber(p[k], k)}}</span></div>`;
                }});
                
                rowsHtml += '<br><div style="font-weight:800; border-bottom:1px solid #e2e8f0; margin-bottom:4px;">All Raw Data</div>';
                
                // Group 2: Literally Everything Else
                Object.keys(p).sort().forEach(k => {{
                    if (!coreKeys.includes(k) && k !== 'District_Name' && k !== 'County' && k !== 'State' && k !== 'Lat' && k !== 'Lon') {{
                        rowsHtml += `<div class="popup-row"><span class="popup-key">${{k.replace(/_/g, ' ')}}</span> <span class="popup-val">${{formatNumber(p[k], k)}}</span></div>`;
                    }}
                }});

                const popupHtml = `
                    <div class="popup-title">${{p.NAME || p.District_Name}}</div>
                    <div class="popup-subtitle">${{p.County}}, ${{p.State}} | Archetype: ${{p.Archetype || 'None'}}</div>
                    <div class="tooltip-scroll-container">
                        ${{rowsHtml}}
                    </div>
                `;
                layer.bindPopup(popupHtml);
            }}
        }}).addTo(map);

        // 4. Update Legend
        if (map.hasLayer(legend)) {{
            map.removeControl(legend);
        }}
        
        legend.onAdd = function (map) {{
            var div = L.DomUtil.create('div', 'legend');
            div.innerHTML = `<strong>${{colorBy.replace(/_/g, ' ')}}</strong><br>`;
            
            if (colorBy === 'Archetype') {{
                for (let k in clusterColors) {{
                    div.innerHTML += `<i style="background:${{clusterColors[k]}}"></i> ${{k}}<br>`;
                }}
            }} else {{
                // Gradient Legend
                const steps = 5;
                const stepSize = (domainMax - domainMin) / steps;
                for (let i = 0; i <= steps; i++) {{
                    let val = domainMin + (stepSize * i);
                    div.innerHTML += `<i style="background:${{colorScale(val)}}"></i> ${{formatNumber(val, colorBy)}}<br>`;
                }}
            }}
            return div;
        }};
        legend.addTo(map);
    }}

    // Attach Event Listeners
    [elCommute, elPrestige, elWalk, elCost, elColor].forEach(el => {{
        el.addEventListener('input', renderMap);
    }});

    // Initial Render
    renderMap();

</script>
</body>
</html>
"""

with open('../brain/1aa0d3c1-7a3f-4417-9041-18ac4fb2f2a3/Master_Choropleth_Dashboard.html', 'w') as f:
    f.write(html_template)

print("Master Choropleth Dashboard generated successfully!")
