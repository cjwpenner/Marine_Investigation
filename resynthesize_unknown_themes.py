# resynthesize_unknown_themes.py
# Re-runs Claude synthesis only for the 94 "Unknown Theme" clusters,
# then patches themes_raw.json and the dashboard themes.json in-place.

import json
import os
import re
import time
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
import anthropic
from clustering import select_representatives, build_cluster_text

load_dotenv(find_dotenv())

JSONL_FILE   = Path(__file__).parent / "analyzed_incidents_v2.jsonl"
RAW_JSON     = Path(__file__).parent / "themes_raw.json"
DASH_JSON    = Path(__file__).parent / "dashboard/src/data/themes.json"

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def extract_json(text: str) -> dict | None:
    """Extract the outermost JSON object from text by brace-balancing."""
    depth = 0
    start = None
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                try:
                    return json.loads(text[start:i+1])
                except json.JSONDecodeError:
                    start = None
    return None


def synthesise_theme(cluster_text: str, representatives: list) -> dict:
    rep_descriptions = "\n".join(
        f"- [{r.get('Occurrence_Severity','?')}] {r.get('Original_Description', '')[:300]}"
        for r in representatives[:5]
    )
    prompt = f"""You are a Senior Marine Safety Investigator writing a formal thematic analysis report.

I have clustered similar marine incidents by their latent causes. Here is a summary of one cluster:

{cluster_text}

Representative incidents:
{rep_descriptions}

Provide:
1. A short professional Theme Title (max 8 words)
2. Two paragraphs (professional, formal tone) explaining:
   - What characterises this theme and why these incidents keep occurring
   - The role of latent hardware/software issues, human factors, and environmental conditions
3. The top 2-3 SOLAS chapters most relevant to this theme
4. Three specific, actionable measures that would prevent incidents in this theme

Return ONLY valid JSON with no preamble:
{{
  "title": "string",
  "description": "two paragraph string",
  "solas_chapters": ["string"],
  "preventable_by": ["measure 1", "measure 2", "measure 3"]
}}"""

    # Prefill forces Claude to start outputting JSON immediately
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
        system="You are a marine safety expert. Always respond with valid JSON only, no markdown fences, no preamble.",
    )
    text = message.content[0].text.strip()
    result = extract_json(text)
    if result and "title" in result:
        return result
    # Fallback: still failed, keep as Unknown so we can see the raw text
    print(f"    WARNING: JSON parse failed. Raw response:\n{text[:300]}")
    return {"title": "Unknown Theme", "description": text, "solas_chapters": [], "preventable_by": []}


def main():
    print("Loading analyzed incidents...")
    records_by_theme: dict[int, list] = {}
    with open(JSONL_FILE, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            tid = r.get("theme_id", -1)
            records_by_theme.setdefault(tid, []).append(r)

    print("Loading current themes_raw.json...")
    raw_themes: list = json.load(open(RAW_JSON, encoding="utf-8"))

    unknown_themes = [t for t in raw_themes if t["title"] == "Unknown Theme"]
    print(f"Re-synthesising {len(unknown_themes)} unknown themes...")

    theme_index = {t["theme_id"]: i for i, t in enumerate(raw_themes)}

    for n, theme in enumerate(unknown_themes, 1):
        tid = theme["theme_id"]
        cluster_records = records_by_theme.get(tid, [])
        if not cluster_records:
            print(f"  [{n}/{len(unknown_themes)}] theme_id={tid}: no records found, skipping")
            continue

        reps = select_representatives(cluster_records, n=10)
        cluster_text = build_cluster_text(cluster_records)

        print(f"  [{n}/{len(unknown_themes)}] theme_id={tid} ({len(cluster_records)} incidents)...", end=" ", flush=True)
        synthesis = synthesise_theme(cluster_text, reps)
        print(synthesis["title"])

        # Patch in place
        idx = theme_index[tid]
        raw_themes[idx]["title"] = synthesis["title"]
        raw_themes[idx]["description"] = synthesis["description"]
        raw_themes[idx]["solas_chapters"] = synthesis.get("solas_chapters", [])
        raw_themes[idx]["preventable_by"] = synthesis.get("preventable_by", [])

        # Gentle rate-limit: 1 req/s is well within Sonnet limits
        time.sleep(0.5)

    # Write back
    with open(RAW_JSON, "w", encoding="utf-8") as f:
        json.dump(raw_themes, f, indent=2)
    print(f"\nWritten {RAW_JSON}")

    with open(DASH_JSON, "w", encoding="utf-8") as f:
        json.dump(raw_themes, f, indent=2)
    print(f"Written {DASH_JSON}")

    still_unknown = sum(1 for t in raw_themes if t["title"] == "Unknown Theme")
    print(f"\nDone. Remaining 'Unknown Theme' entries: {still_unknown}")


if __name__ == "__main__":
    main()
