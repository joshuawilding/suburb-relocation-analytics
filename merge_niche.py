import pandas as pd
import re
import difflib

def clean_district_name(name):
    if pd.isna(name): return ""
    name = str(name).lower()
    # Remove common district filler words
    filler_words = [
        r'\bpublic\b', r'\bschools\b', r'\bschool\b', r'\bdistrict\b',
        r'\bregional\b', r'\btownship\b', r'\bborough\b', r'\bof\b', r'\bthe\b',
        r'\bboard\b', r'\beducation\b', r'\bunion\b', r'\bfree\b', r'\bcentral\b',
        r'\bcity\b', r'\bvocational\b', r'\btechnical\b', r'\bhudson county schools of technology\b'
    ]
    for w in filler_words:
        name = re.sub(w, '', name)
    # Remove punctuation and extra spaces
    name = re.sub(r'[^\w\s]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def merge_datasets():
    seda_file = "../brain/1aa0d3c1-7a3f-4417-9041-18ac4fb2f2a3/tri_state_master_districts.csv"
    niche_file = "../brain/1aa0d3c1-7a3f-4417-9041-18ac4fb2f2a3/commutable_districts.csv"
    output_file = "../brain/1aa0d3c1-7a3f-4417-9041-18ac4fb2f2a3/tri_state_master_with_niche.csv"

    print("Loading datasets...")
    df_seda = pd.read_csv(seda_file)
    df_niche = pd.read_csv(niche_file)

    # State mapping
    state_map = {'Connecticut': 'CT', 'New Jersey': 'NJ', 'New York': 'NY'}
    df_niche['State'] = df_niche['State'].map(state_map)
    
    # County mapping
    df_niche['County'] = df_niche['County'] + " County"

    # Clean names
    df_seda['Clean_Name'] = df_seda['District_Name'].apply(clean_district_name)
    df_niche['Clean_Name'] = df_niche['School District Name'].apply(clean_district_name)

    print("Fuzzy matching Niche districts to SEDA master list...")
    # Initialize Niche columns in SEDA df
    df_seda['Niche_Grade'] = None
    df_seda['Niche_Student_Teacher_Ratio'] = None

    matched_count = 0

    for idx, niche_row in df_niche.iterrows():
        state = niche_row['State']
        county = niche_row['County']
        clean_name = niche_row['Clean_Name']
        
        # Isolate SEDA districts in the exact same state and county
        seda_candidates = df_seda[(df_seda['State'] == state) & (df_seda['County'] == county)]
        
        if seda_candidates.empty:
            continue
            
        candidate_names = seda_candidates['Clean_Name'].tolist()
        
        # Fuzzy match
        matches = difflib.get_close_matches(clean_name, candidate_names, n=1, cutoff=0.7)
        
        if matches:
            best_match = matches[0]
            # Find the original row in SEDA
            seda_idx = seda_candidates[seda_candidates['Clean_Name'] == best_match].index[0]
            
            # Map Niche Grade
            df_seda.at[seda_idx, 'Niche_Grade'] = niche_row['Niche Grade']
            # Map Niche S/T Ratio if it exists
            if 'Student-Teacher Ratio' in niche_row:
                df_seda.at[seda_idx, 'Niche_Student_Teacher_Ratio'] = niche_row['Student-Teacher Ratio']
            
            matched_count += 1
        else:
            print(f"Failed to match Niche District: {niche_row['School District Name']} in {county}, {state}")

    print(f"Successfully matched {matched_count} out of {len(df_niche)} Niche districts.")
    
    # Drop temp column
    df_seda = df_seda.drop(columns=['Clean_Name'])
    
    # Sort so Niche A+ districts bubble to the top
    df_seda = df_seda.sort_values(by=['Niche_Grade', 'SEDA_Growth_Score'], ascending=[True, False], na_position='last')

    df_seda.to_csv(output_file, index=False)
    print(f"Saved merged dataset to {output_file}")

if __name__ == "__main__":
    merge_datasets()
