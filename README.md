# Suburb Relocation Analytics

A decision science pipeline and geospatial analysis framework evaluating housing affordability, commute accessibility, and school district performance across the New York Tri-State metropolitan area.

## Highlights
- **Multi-Source Data Integration:** Ingests and harmonizes census-tract and zip-level metrics from the **EPA Smart Location Database** (walkability index, transit frequency, vehicle dependency), **Zillow Home Value Index (ZHVI)** (multi-tier and bedroom time-series), and the **Stanford Education Data Archive (SEDA)**.
- **Decision Science & Feature Modeling:** Generates composite desirability scores balancing travel times to NYC transit hubs against cost-per-square-foot and educational performance benchmarks.
- **Geospatial & Neighborhood Clustering:** Classifies Tri-State submarkets into distinct lifestyle archetypes (e.g., Transit-Oriented Dense, Suburban Family, Car-Dependent Acreage) to support data-driven relocation decisions.

## Tech Stack
- **Languages & Analysis:** Python 3.11+, Pandas, NumPy, Scikit-Learn, Statsmodels
- **Geospatial & Visualization:** GeoPandas, Shapely, Plotly, Matplotlib, Seaborn
- **Data Stores:** Parquet, GeoJSON, SQLite

## Structure
```
suburb_relocation_analytics/
├── data/                       # Ingested and processed datasets
├── append_commute_model.py     # Commute duration and transit frequency scoring
├── append_advanced_zillow.py   # ZHVI time-series transformations & tiers
├── append_lifestyle_label.py   # Unsupervised clustering / lifestyle archetypes
├── evaluate_model.py           # Goodness-of-fit and ranking sensitivity tests
├── generate_scatter_matrix.py  # Dimensionality & correlation diagnostics
├── export_json.py              # Export normalized GeoJSON for web exploration
└── School_District_Analysis.ipynb # SEDA standardized testing and demographic EDA
```

## Quickstart
```bash
git clone https://github.com/joshuawilding/suburb-relocation-analytics.git
cd suburb-relocation-analytics
pip install -r requirements.txt
python run_eda.py
```