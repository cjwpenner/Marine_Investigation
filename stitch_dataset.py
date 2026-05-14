import pandas as pd
import json
import ast

def load_data():
    # Read files handling standard bad lines just in case
    # using low_memory=False due to mixed types in columns
    o_df = pd.read_csv('occurrences.csv', sep=';', on_bad_lines='skip', low_memory=False)
    v_df = pd.read_csv('vessels.csv', sep=';', on_bad_lines='skip', low_memory=False)
    p_df = pd.read_csv('affected_persons.csv', sep=';', on_bad_lines='skip', low_memory=False)
    return o_df, v_df, p_df

def stitch_data(o_df, v_df, p_df):
    # Fill NA with None to ensure valid JSON output instead of NaN
    o_df = o_df.where(pd.notnull(o_df), None)
    v_df = v_df.where(pd.notnull(v_df), None)
    p_df = p_df.where(pd.notnull(p_df), None)

    print(f"Structuring {len(p_df)} affected persons...")
    # Group persons by Vessel_Profile_Id
    p_grouped = {}
    for record in p_df.to_dict(orient='records'):
        v_id = record.get('Vessel_Profile_Id')
        if v_id not in p_grouped:
            p_grouped[v_id] = []
        p_grouped[v_id].append(record)
    
    print(f"Structuring {len(v_df)} vessels...")
    # Group vessels by Occurrence_Id
    v_grouped = {}
    for record in v_df.to_dict(orient='records'):
        occ_id = record.get('Occurrence_Id')
        v_id = record.get('Vessel_Profile_Id')
        
        # Attach any persons mapping to this vessel
        record['Affected_Persons'] = p_grouped.get(v_id, [])
        
        if occ_id not in v_grouped:
            v_grouped[occ_id] = []
        v_grouped[occ_id].append(record)

    print(f"Structuring {len(o_df)} occurrences...")
    # Build the master occurrences list
    results = []
    for record in o_df.to_dict(orient='records'):
        occ_id = record.get('Occurrence_Id')
        # Attach any vessels mapping to this occurrence
        record['Vessels'] = v_grouped.get(occ_id, [])
        results.append(record)

    return results

if __name__ == "__main__":
    print("Loading CSV files...")
    o_df, v_df, p_df = load_data()
    
    print("Stitching datasets...")
    stitched = stitch_data(o_df, v_df, p_df)
    
    print("Saving to JSON format...")
    with open('stitched_marine_data.json', 'w', encoding='utf-8') as f:
        json.dump(stitched, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully processed and saved {len(stitched)} nested occurrences to stitched_marine_data.json")
