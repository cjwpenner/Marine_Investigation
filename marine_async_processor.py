import os
import json
import asyncio
from datetime import datetime
import numpy
# Patch for numpy 2.0 compatibility with older libraries
numpy.NaN = numpy.nan

import pandas as pd
from dotenv import load_dotenv
from openai import AsyncOpenAI
import aiohttp
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
import openai
import meteostat
from meteostat import Point, daily as Daily

# Disable caching for async concurrency safety
meteostat.config.cache_enable = False
# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("Error: OPENAI_API_KEY not found in .env file.")

client = AsyncOpenAI(api_key=api_key)

# Concurrency control
SEMAPHORE = asyncio.Semaphore(15)

def fetch_weather(lat, lon, date_str):
    """
    Synchronous fetching of meteostat data, to be run in a thread.
    Returns a dict of weather data or empty if unavailable.
    """
    try:
        # Expected format varies, try YYYY-MM-DD
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        point = Point(lat, lon)
        data = Daily(point, dt, dt).fetch()
        
        if not data.empty:
            row = data.iloc[0]
            # wspd = wind speed km/h, wspg = wind gust, tavg = temp C
            return {
                "wind_kph": row.get('wspd'),
                "wind_gust_kph": row.get('wspd'),
                "temp_c": row.get('tavg'),
                "precip_mm": row.get('prcp')
            }
        return {}
    except Exception as e:
        return {}


# Retry on rate limits to act gracefully
@retry(
    retry=retry_if_exception_type((openai.RateLimitError, openai.APIConnectionError)), 
    wait=wait_exponential(multiplier=1, min=4, max=30), 
    stop=stop_after_attempt(5)
)
async def extract_latent_factors(payload):
    prompt = f"""
    You are an expert marine accident investigator and data scientist identifying hidden patterns in maritime occurrences.
    I will provide an incident report including weather metrics. 
    Look beyond surface causes to infer underlying technical, systemic, fatigue, or process failures.
    
    Incident JSON:
    {json.dumps(payload, indent=2)}
    
    Provide your analysis strictly in the following JSON format without markdown blocks:
    {{
       "explicit_cause_reported": "Main cause stated",
       "latent_hardware_software_issues": ["..."],
       "latent_human_environmental_factors": ["..."],
       "pattern_discovery_summary": "1-2 sentence theory."
    }}
    """
    response = await client.chat.completions.create(
        model="gpt-4o",
        temperature=0.2,
        messages=[{"role": "user", "content": prompt}]
    )
    res_text = response.choices[0].message.content.strip()
    # clean up markdown if accidentally supplied
    if res_text.startswith("```json"):
        res_text = res_text[7:]
    if res_text.endswith("```"):
        res_text = res_text[:-3]
    return json.loads(res_text.strip())

@retry(
    retry=retry_if_exception_type((openai.RateLimitError, openai.APIConnectionError)),
    wait=wait_exponential(multiplier=1, min=2, max=20),
    stop=stop_after_attempt(5)
)
async def generate_embedding(text):
    response = await client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding


async def process_incident(incident, output_queue):
    async with SEMAPHORE:
        occ_id = incident.get("Occurrence_Id")
        desc = incident.get("Description", "")
        short_desc = incident.get("Short_Description", "")
        date_str = incident.get("Local_Date_Main_Event")
        lat = incident.get("Latitude")
        lon = incident.get("Longitude")

        # 1. Weather
        weather = {}
        if date_str and lat and pd.notna(lat) and lon and pd.notna(lon):
             # Run sync method in executor
             weather = await asyncio.to_thread(fetch_weather, float(lat), float(lon), str(date_str))

        # Build payload
        payload = {
            "Description": desc,
            "Short_Description": short_desc,
            "Crew_Reported_Weather": incident.get("Weather", ""),
            "Meteostat_Objective_Weather": weather,
            "Vessels": [{"Type": v.get("Ship_Craft_Type_L1"), "Damage": v.get("Damage_Description")} for v in incident.get("Vessels", [])]
        }

        try:
            # 2. LLM Analysis
            analysis = await extract_latent_factors(payload)
            
            # 3. Embeddings on the summary
            summary = analysis.get("pattern_discovery_summary", "")
            embedding = None
            if summary:
                embedding = await generate_embedding(summary)
            
            result = {
                "Occurrence_Id": occ_id,
                "Original_Description": desc,
                "Meteostat_Weather": weather,
                "Analysis": analysis,
                "Embedding": embedding
            }
            await output_queue.put(result)
            return True
            
        except Exception as e:
            print(f"Failed to process {occ_id} - Error: {e}")
            return False

async def writer_worker(output_file, queue):
    with open(output_file, 'a', encoding='utf-8') as f:
        while True:
            result = await queue.get()
            if result is None: # Sentinel value
                break
            f.write(json.dumps(result, ensure_ascii=False) + '\n')
            queue.task_done()

async def main():
    print("Loading dataset...")
    # Load fully stitched nested dataset
    with open('stitched_marine_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    # Check already processed items from the log
    output_filename = "analyzed_incidents.jsonl"
    processed_ids = set()
    if os.path.exists(output_filename):
        with open(output_filename, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    processed_ids.add(obj.get("Occurrence_Id"))
                except:
                    pass
    
    print(f"Found {len(processed_ids)} already processed incidents.")
    
    # Filter substantial descriptions and skip processed.
    to_process = []
    for d in data:
        occ_id = d.get("Occurrence_Id")
        if occ_id in processed_ids:
            continue
            
        desc = d.get("Description") or ""
        short_desc = d.get("Short_Description") or ""
        if len(desc) > 200 or len(short_desc) > 200:
            to_process.append(d)
    
    print(f"Incidents queued for processing: {len(to_process)}")
    
    if len(to_process) == 0:
        return

    # To keep cost strictly constrained to avoid a massive overrun if limit kicks late,
    # let's process them. We will process ALL of them, but we let it fail gracefully if limit hit.
    
    queue = asyncio.Queue()
    writer_task = asyncio.create_task(writer_worker(output_filename, queue))
    
    tasks = [process_incident(inc, queue) for inc in to_process]
    
    print(f"Starting async batch analysis for {len(tasks)} requests...")
    
    # We will await them with gather. If we hit hard quotas out of retries, it raises.
    # The queue means we successfully saved everything up to the crash!
    try:
         completed = await asyncio.gather(*tasks, return_exceptions=True)
         
         successes = sum(1 for c in completed if c is True)
         failures = len(completed) - successes
         print(f"Batch completed: {successes} successful, {failures} failed or exceeded limits.")
         
    finally:
        await queue.put(None)
        await writer_task
        print("Data safely flushed to output.")

if __name__ == "__main__":
    asyncio.run(main())
