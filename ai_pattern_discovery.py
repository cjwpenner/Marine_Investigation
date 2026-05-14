import os
import json
import random
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables (API keys)
load_dotenv()

# Ensure we have the API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Error: OPENAI_API_KEY not found in .env file.")
    exit(1)

client = OpenAI(api_key=api_key)

def load_dataset(filepath, min_description_length=200):
    """
    Loads the stitched json dataset and filters for records with substantial descriptions.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Filter out incidents without a meaningful description
    filtered = []
    for d in data:
        desc = d.get("Description") or ""
        short_desc = d.get("Short_Description") or ""
        if len(desc) > min_description_length or len(short_desc) > min_description_length:
            filtered.append(d)
            
    return filtered

def analyze_incident(incident):
    """
    Passes the incident text to OpenAI's GPT-4o model to extract hidden patterns.
    """
    occurrence_id = incident.get("Occurrence_Id")
    desc = incident.get("Description", "")
    short_desc = incident.get("Short_Description", "")
    
    # We build a concise payload for the LLM to avoid overwhelming it with empty columns
    payload = {
        "Description": desc,
        "Short_Description": short_desc,
        "Weather": incident.get("Weather", ""),
        "Sea_State": incident.get("Sea_State", ""),
        "Wind_Force": incident.get("Wind_Force", ""),
        "Vessels": [{"Type": v.get("Ship_Craft_Type_L1"), "Damage": v.get("Damage_Description")} for v in incident.get("Vessels", [])]
    }
    
    prompt = f"""
    You are an expert marine accident investigator and data scientist identifying hidden patterns in maritime occurrences.
    
    I will provide you with a JSON object representing a marine accident report. 
    Often, surface-level causes (like 'human error' or 'lost control') hide underlying systemic or hardware failures (like 'GPS failure', 'autopilot UI bugs', 'fatigue', or 'sensor degradation').
    
    Read the following incident report carefully.
    
    Incident JSON:
    {json.dumps(payload, indent=2)}
    
    Please provide your analysis strictly in the following JSON format:
    {{
       "explicit_cause_reported": "The main cause as stated by the text",
       "latent_hardware_software_issues": ["List possible hidden equipment, software, sensor or UI failures that could have contributed"],
       "latent_human_environmental_factors": ["List fatigue, miscommunication, micro-weather, or process failures"],
       "pattern_discovery_summary": "A 1-2 sentence theory on what really went wrong logically beneath the surface description."
    }}
    
    Do not include any other markdown or conversational text, only return the JSON block.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            temperature=0.2,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    print("Loading stitched marine dataset...")
    reports = load_dataset('stitched_marine_data.json')
    print(f"Found {len(reports)} records with substantial descriptions.")
    
    if len(reports) == 0:
        print("No suitable records found.")
        exit(0)
        
    # Pick a random sample of 3 interesting records for POC
    random.seed(42) # For reproducible POC
    sample_reports = random.sample(reports, min(3, len(reports)))
    
    results = []
    for idx, report in enumerate(sample_reports):
        occ_id = report.get('Occurrence_Id')
        print(f"\n--- Analyzing Incident {idx+1}: {occ_id} ---")
        print(f"REPORT TEXT:\n{report.get('Description')[:500]}...\n")
        
        analysis_json = analyze_incident(report)
        print("AI ANALYSIS:")
        print(analysis_json)
        
        results.append({
            "Occurrence_Id": occ_id,
            "Original_Description": report.get("Description"),
            "AI_Analysis": analysis_json
        })
        
    with open('poc_ai_insights.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    print("\nPOC Analysis complete. Saved results to poc_ai_insights.json")
