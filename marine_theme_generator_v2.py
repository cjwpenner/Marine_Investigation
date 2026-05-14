# marine_theme_generator_v2.py
import json
import os
import re
import numpy as np
import anthropic
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from clustering import cluster_embeddings, select_representatives, build_cluster_text

load_dotenv(find_dotenv())

INPUT_FILE = Path(__file__).parent / "analyzed_incidents_v2.jsonl"
OUTPUT_MD = Path(__file__).parent / "marine_accident_themes_analysis_v2.md"
OUTPUT_THEMES_JSON = Path(__file__).parent / "themes_raw.json"

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SEVERITY_WEIGHTS = {"Very Serious": 4, "Serious": 2, "Less Serious": 1, "Marine Incident": 1}


def synthesise_theme(cluster_text: str, representatives: list) -> dict:
    """Ask Claude Sonnet 4.6 to name and describe a theme from cluster evidence."""
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
4. Three specific, actionable measures that would prevent incidents in this theme ("preventable_by")

Return ONLY valid JSON:
{{
  "title": "string",
  "description": "two paragraph string",
  "solas_chapters": ["string"],
  "preventable_by": ["actionable measure 1", "actionable measure 2", "actionable measure 3"]
}}"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )
    text = message.content[0].text
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        return json.loads(match.group(0)) if match else {
            "title": "Unknown Theme", "description": text,
            "solas_chapters": [], "preventable_by": []
        }
    except Exception:
        return {"title": "Unknown Theme", "description": text,
                "solas_chapters": [], "preventable_by": []}


def compute_cluster_stats(records: list) -> dict:
    """Compute aggregate stats for a cluster."""
    factor_counts = {"human": 0, "hardware": 0, "environmental": 0, "procedural": 0}
    fatigue = training = ppe = comms = weather = lighting = 0
    total = len(records)

    for r in records:
        a = r.get("Analysis") or {}
        for f in a.get("contributing_factors", []):
            ft = f.get("type", "")
            if ft in factor_counts:
                factor_counts[ft] += 1
        if a.get("fatigue_factor") is True: fatigue += 1
        if a.get("training_factor") is True: training += 1
        if a.get("ppe_factor") is True: ppe += 1
        if a.get("communication_factor") is True: comms += 1
        if a.get("weather_was_factor") is True: weather += 1
        if a.get("lighting_was_factor") is True: lighting += 1

    sev = {"Very Serious": 0, "Serious": 0, "Less Serious": 0, "Marine Incident": 0, "Other": 0}
    for r in records:
        s = r.get("Occurrence_Severity", "Other")
        sev[s] = sev.get(s, 0) + 1

    total_factors = max(sum(factor_counts.values()), 1)
    t = max(total, 1)
    return {
        "incident_count": total,
        "severity_breakdown": sev,
        "top_contributing_factor_types": {k: round(v/total_factors, 3) for k, v in factor_counts.items()},
        "fatigue_factor_pct": round(fatigue/t, 3),
        "training_factor_pct": round(training/t, 3),
        "ppe_factor_pct": round(ppe/t, 3),
        "communication_factor_pct": round(comms/t, 3),
        "weather_factor_pct": round(weather/t, 3),
        "lighting_factor_pct": round(lighting/t, 3),
    }


def main():
    print(f"Loading {INPUT_FILE}...")
    if not INPUT_FILE.exists():
        print(f"ERROR: {INPUT_FILE} not found. Run marine_async_processor_v2.py first.")
        return

    records = [json.loads(l) for l in open(INPUT_FILE, encoding="utf-8") if l.strip()]
    valid = [r for r in records if r.get("Embedding") and r.get("Analysis")]
    print(f"{len(records)} total records, {len(valid)} with embeddings for clustering.")

    if not valid:
        print("No records with embeddings — cannot cluster. Check OpenAI quota.")
        return

    embeddings = np.array([r["Embedding"] for r in valid])
    print("Running HDBSCAN...")
    labels = cluster_embeddings(embeddings)

    unique_labels = sorted(set(labels) - {-1})
    noise_count = sum(1 for l in labels if l == -1)
    print(f"Found {len(unique_labels)} clusters, {noise_count} outliers.")

    themes = []
    md_sections = [
        "# Marine Accident Thematic Analysis Report V2\n\n"
        "This report uses HDBSCAN clustering on Claude Sonnet 4.6 embeddings "
        "with severity-weighted representative selection.\n\n"
    ]

    for label in unique_labels:
        cluster_records = [r for r, l in zip(valid, labels) if l == label]
        reps = select_representatives(cluster_records, n=10)
        cluster_text = build_cluster_text(cluster_records)

        print(f"  Synthesising theme for cluster {label} ({len(cluster_records)} incidents)...")
        synthesis = synthesise_theme(cluster_text, reps)
        stats = compute_cluster_stats(cluster_records)

        theme = {
            "theme_id": label,
            "title": synthesis["title"],
            "description": synthesis["description"],
            "solas_chapters": synthesis.get("solas_chapters", []),
            "preventable_by": synthesis.get("preventable_by", []),
            **stats,
            "representative_cases": [
                {
                    "id": r.get("Occurrence_Id"),
                    "description": r.get("Original_Description", "")[:400],
                    "severity": r.get("Occurrence_Severity")
                }
                for r in reps[:10]
            ]
        }
        themes.append(theme)

        md_sections.append(
            f"### {synthesis['title']} *(Exhibited in {len(cluster_records)} incidents)*\n\n"
            f"{synthesis['description']}\n\n"
            f"**Representative Cases:**\n"
        )
        for rep in reps[:3]:
            md_sections.append(
                f"- **Occurrence {rep.get('Occurrence_Id')}**: "
                f"{rep.get('Original_Description','')[:200]}\n"
            )
        md_sections.append("\n---\n\n")

    themes.sort(key=lambda t: t["incident_count"], reverse=True)

    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("".join(md_sections))
    print(f"Written {OUTPUT_MD}")

    with open(OUTPUT_THEMES_JSON, "w", encoding="utf-8") as f:
        json.dump(themes, f, indent=2)
    print(f"Written {OUTPUT_THEMES_JSON}")

    # Write theme_id back into the JSONL
    print("Writing theme IDs back to JSONL...")
    id_to_theme = {
        r["Occurrence_Id"]: labels[i]
        for i, r in enumerate(valid)
        if r.get("Occurrence_Id") is not None
    }
    updated_lines = []
    for line in open(INPUT_FILE, encoding="utf-8"):
        r = json.loads(line)
        oid = r.get("Occurrence_Id")
        r["theme_id"] = id_to_theme.get(oid, -1) if oid is not None else -1
        updated_lines.append(json.dumps(r))
    with open(INPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(updated_lines) + "\n")
    print("Theme IDs written.")


if __name__ == "__main__":
    main()
