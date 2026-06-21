import pandas as pd
import argparse
import os

def build_pipeline(nces_path, seda_path, output_path):
    print(f"Loading datasets from {nces_path} and {seda_path}...")
    
    try:
        # Load NCES. Enforce string typing on ID columns to prevent leading zero loss
        df_nces = pd.read_csv(nces_path, dtype={'Agency ID - NCES Assigned [District] Latest available year': str, 'LEAID': str})
    except FileNotFoundError:
        print(f"Error: Could not find NCES data at {nces_path}")
        print("Please download the CSV from the NCES ELSi portal and ensure the path is correct.")
        return

    try:
        # Load SEDA. 
        df_seda = pd.read_csv(seda_path, dtype={'sedalea': str, 'leaid': str})
    except FileNotFoundError:
        print(f"Error: Could not find SEDA data at {seda_path}")
        return

    print("Standardizing primary keys (LEAID)...")
    # NCES ELSi column naming can be extremely verbose. We look for 'LEAID' or the verbose equivalent.
    nces_id_col = 'LEAID' if 'LEAID' in df_nces.columns else 'Agency ID - NCES Assigned [District] Latest available year'
    if nces_id_col in df_nces.columns:
        df_nces['LEAID_CLEAN'] = df_nces[nces_id_col].astype(str).str.zfill(7)
    else:
        print("Error: Could not locate the NCES Agency ID column. Check your CSV headers.")
        return

    # SEDA's district ID is usually 'sedalea' or 'leaid'
    seda_id_col = 'sedalea' if 'sedalea' in df_seda.columns else 'leaid'
    if seda_id_col in df_seda.columns:
        df_seda['LEAID_CLEAN'] = df_seda[seda_id_col].astype(str).str.zfill(7)
    else:
        print("Error: Could not locate the SEDA District ID column.")
        return

    # 1. Geographic Filtering
    target_counties = [
        'Bergen County', 'Hudson County', 'Essex County', 'Union County', 
        'Morris County', 'Passaic County', 'Somerset County', 'Middlesex County', 
        'Monmouth County', 'Nassau County', 'Suffolk County', 'Westchester County', 
        'Rockland County', 'Fairfield County'
    ]
    
    print("Filtering for Tri-State Commutable Counties...")
    county_col = 'County Name [District] Latest available year' if 'County Name [District] Latest available year' in df_nces.columns else 'County Name'
    if county_col in df_nces.columns:
        df_nces = df_nces[df_nces[county_col].isin(target_counties)]
    else:
        print("Warning: 'County Name' column not found in NCES. Skipping geographic filter.")

    # 2. Merging Data
    print("Merging NCES and SEDA datasets on LEAID_CLEAN...")
    df_merged = pd.merge(df_nces, df_seda, on='LEAID_CLEAN', how='left')

    # 3. Clean up the dataframe
    print(f"Pipeline complete. Total districts matching filter: {len(df_merged)}")
    
    # Check for un-matched SEDA rows
    matched_ratio = df_merged[seda_id_col].notna().mean() * 100
    print(f"Match Rate: {matched_ratio:.1f}% of NCES districts successfully matched with SEDA data.")

    # Export
    df_merged.to_csv(output_path, index=False)
    print(f"Saved unified dataset to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge NCES and SEDA datasets to build a master school district dataframe.")
    parser.add_argument("--nces", default="nces_districts.csv", help="Path to NCES CSV download")
    parser.add_argument("--seda", default="seda_districts.csv", help="Path to SEDA CSV download")
    parser.add_argument("--output", default="tri_state_master_districts.csv", help="Path for output CSV")
    
    args = parser.parse_args()
    build_pipeline(args.nces, args.seda, args.output)
