# marine_async_processor_v2.py
import asyncio
import json
import os
import time
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
import openai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from weather_enrichment import enrich_weather
from ai_extraction import extract_incident_analysis

load_dotenv(find_dotenv())

INPUT_FILE = Path(__file__).parent.parent.parent / "stitched_marine_data.json"
OUTPUT_FILE = Path(__file__).parent / "analyzed_incidents_v2.jsonl"
CONCURRENCY = 15

openai_client = None
write_lock = None
semaphore = None


def get_openai_client():
    global openai_client
    if openai_client is None:
        openai_client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return openai_client


def load_processed_ids() -> set:
    processed = set()
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            for line in f:
                try:
                    processed.add(json.loads(line)["Occurrence_Id"])
                except (json.JSONDecodeError, KeyError):
                    pass
    return processed


@retry(stop=stop_after_attempt(5),
       wait=wait_exponential(multiplier=1, min=4, max=60),
       retry=retry_if_exception_type(Exception))
async def generate_embedding(text: str) -> list | None:
    if not text:
        return None
    response = await get_openai_client().embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


async def safe_generate_embedding(text: str) -> list | None:
    """Wrapper that returns None on quota/billing errors instead of crashing."""
    try:
        return await generate_embedding(text)
    except Exception as e:
        # Unwrap tenacity RetryError to check underlying cause
        cause = getattr(e, '__cause__', e)
        err_str = str(cause).lower()
        if "quota" in err_str or "billing" in err_str or "insufficient_quota" in err_str or "429" in err_str:
            return None
        raise


async def process_incident(incident: dict) -> dict | None:
    occ_id = incident.get("Occurrence_Id")
    description = incident.get("Description", "")
    if not description or not occ_id:
        return None

    async with semaphore:
        # Step 1: Weather enrichment (sync call in thread pool)
        loop = asyncio.get_event_loop()
        weather = await loop.run_in_executor(None, enrich_weather, incident)

        # Step 2: AI extraction
        analysis = await extract_incident_analysis(description, weather)
        if not analysis:
            return None

        # Step 3: Embedding on pattern summary
        summary = analysis.get("pattern_discovery_summary", "")
        embedding = await safe_generate_embedding(summary)

        return {
            "Occurrence_Id": occ_id,
            "Original_Description": description,
            "Local_Date_Main_Event": incident.get("Local_Date_Main_Event"),
            "Latitude": incident.get("Latitude"),
            "Longitude": incident.get("Longitude"),
            "Occurrence_Severity": incident.get("Occurrence_Severity"),
            "Main_Event_L1": incident.get("Main_Event_L1"),
            "National_Location_L1": incident.get("National_Location_L1"),
            "Weather_Enrichment": weather,
            "Analysis": analysis,
            "Embedding": embedding,
        }


async def write_result(result: dict):
    async with write_lock:
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(result) + "\n")


async def main():
    global write_lock, semaphore
    write_lock = asyncio.Lock()
    semaphore = asyncio.Semaphore(CONCURRENCY)

    print(f"Loading {INPUT_FILE}...")
    if not INPUT_FILE.exists():
        # Try relative path (for when running from parent directory)
        alt = Path("stitched_marine_data.json")
        if alt.exists():
            INPUT_FILE_PATH = alt
        else:
            print(f"ERROR: Cannot find stitched_marine_data.json at {INPUT_FILE} or {alt}")
            return
    else:
        INPUT_FILE_PATH = INPUT_FILE

    with open(INPUT_FILE_PATH, encoding="utf-8") as f:
        records = json.load(f)
    print(f"Loaded {len(records)} records.")

    processed_ids = load_processed_ids()
    print(f"Already processed: {len(processed_ids)}. Remaining: {len(records) - len(processed_ids)}")

    to_process = [r for r in records if r.get("Occurrence_Id") not in processed_ids]

    if not to_process:
        print("Nothing to process.")
        return

    completed = 0
    start = time.time()
    tasks = []

    for incident in to_process:
        async def handle(inc=incident):
            nonlocal completed
            try:
                result = await process_incident(inc)
                if result:
                    await write_result(result)
            except Exception as e:
                print(f"  WARN: skipping {inc.get('Occurrence_Id')} due to error: {e}")
            finally:
                completed += 1
                if completed % 100 == 0:
                    elapsed = time.time() - start
                    rate = completed / max(elapsed, 0.001)
                    remaining = (len(to_process) - completed) / max(rate, 0.001)
                    print(f"  {completed}/{len(to_process)} processed "
                          f"({rate:.1f}/s, ~{remaining/60:.0f}min remaining)")
        tasks.append(handle())

    await asyncio.gather(*tasks)
    print(f"\nDone. {OUTPUT_FILE} written with {completed} records attempted.")


if __name__ == "__main__":
    asyncio.run(main())
