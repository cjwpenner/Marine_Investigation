# patch_weather_fields.py
# Joins Weather, Wind_Force, Visibility back into analyzed_incidents_v2.jsonl
# from the source occurrences.csv — no AI re-run needed.

import csv
import json
from pathlib import Path

CSV_FILE  = Path(__file__).parent.parent.parent / "occurrences.csv"
JSONL_FILE = Path(__file__).parent / "analyzed_incidents_v2.jsonl"

print("Loading source CSV...")
csv_lookup: dict[str, dict] = {}
with open(CSV_FILE, encoding="utf-8-sig", errors="replace") as f:
    reader = csv.DictReader(f, delimiter=";")
    for row in reader:
        oid = row.get("Occurrence_Id")
        if oid:
            csv_lookup[oid] = {
                "weather_type":  row.get("Weather") or None,
                "wind_force":    row.get("Wind_Force") or None,
                "visibility":    row.get("Visibility") or None,
            }
print(f"  {len(csv_lookup)} occurrences loaded from CSV")

print("Patching JSONL...")
lines = JSONL_FILE.read_text(encoding="utf-8").splitlines()
patched = 0
out_lines = []
for line in lines:
    if not line.strip():
        continue
    r = json.loads(line)
    oid = r.get("Occurrence_Id")
    if oid and oid in csv_lookup:
        we = r.get("Weather_Enrichment") or {}
        fields = csv_lookup[oid]
        we["weather_type"]   = fields["weather_type"]
        we["wind_force"]     = fields["wind_force"]
        # visibility already stored as visibility_reported — overwrite with clean value
        we["visibility_reported"] = fields["visibility"]
        r["Weather_Enrichment"] = we
        patched += 1
    out_lines.append(json.dumps(r))

JSONL_FILE.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
print(f"  Patched {patched} records. Written {JSONL_FILE}")
