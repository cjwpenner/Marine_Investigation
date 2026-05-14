# export_dashboard_data.py
import json
import os
import csv
from pathlib import Path
from collections import defaultdict
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent

ANALYZED_JSONL = SCRIPT_DIR / "analyzed_incidents_v2.jsonl"
THEMES_JSON = SCRIPT_DIR / "themes_raw.json"
VESSELS_CSV = PROJECT_ROOT / "vessels.csv"
AFFECTED_CSV = PROJECT_ROOT / "affected_persons.csv"
OUTPUT_DIR = SCRIPT_DIR / "dashboard/src/data"


def build_incidents_map(incidents: list) -> list:
    """One record per incident with location. Skips incidents without lat/lon."""
    result = []
    for r in incidents:
        lat = r.get("Latitude")
        lon = r.get("Longitude")
        if lat is None or lon is None:
            continue
        we = r.get("Weather_Enrichment") or {}
        a = r.get("Analysis") or {}
        natural_light = (we.get("natural_light_calculated") or
                         we.get("natural_light_reported") or "Unknown")
        desc = r.get("Original_Description", "")
        result.append({
            "id": r["Occurrence_Id"],
            "lat": lat,
            "lon": lon,
            "date": (r.get("Local_Date_Main_Event") or "")[:10],
            "severity": r.get("Occurrence_Severity", "Unknown"),
            "theme_id": r.get("theme_id", -1),
            "incident_category": a.get("incident_category", "other"),
            "vessel_activity": a.get("vessel_activity", "other"),
            "natural_light": natural_light,
            "weather_was_factor": we.get("weather_was_factor") or a.get("weather_was_factor"),
            "wave_height_m": we.get("wave_height_m"),
            "wind_kph": we.get("wind_kph"),
            "short_description": desc[:200],
            "pattern_summary": a.get("pattern_discovery_summary", ""),
        })
    return result


def build_time_series(incidents: list) -> list:
    """Monthly aggregates."""
    monthly = defaultdict(lambda: {"total": 0, "very_serious": 0, "serious": 0,
                                    "less_serious": 0, "night_count": 0,
                                    "weather_factor_count": 0, "wave_heights": []})
    for r in incidents:
        date_str = (r.get("Local_Date_Main_Event") or "")[:7]
        if not date_str or len(date_str) < 7:
            continue
        m = monthly[date_str]
        m["total"] += 1
        sev = r.get("Occurrence_Severity", "")
        if sev == "Very Serious": m["very_serious"] += 1
        elif sev == "Serious": m["serious"] += 1
        elif sev == "Less Serious": m["less_serious"] += 1
        # else: unknown severity — not counted in named buckets, still in total
        we = r.get("Weather_Enrichment") or {}
        a = r.get("Analysis") or {}
        nl = we.get("natural_light_calculated") or we.get("natural_light_reported", "")
        if nl in ("Night", "Dusk"): m["night_count"] += 1
        if we.get("weather_was_factor") or a.get("weather_was_factor"): m["weather_factor_count"] += 1
        wh = we.get("wave_height_m")
        if wh is not None: m["wave_heights"].append(wh)

    result = []
    for ym in sorted(monthly):
        m = monthly[ym]
        total = max(m["total"], 1)
        result.append({
            "year_month": ym,
            "total": m["total"],
            "very_serious": m["very_serious"],
            "serious": m["serious"],
            "less_serious": m["less_serious"],
            "night_pct": round(m["night_count"] / total, 3),
            "weather_factor_pct": round(m["weather_factor_count"] / total, 3),
            "avg_wave_height_m": round(sum(m["wave_heights"]) / len(m["wave_heights"]), 2)
                                  if m["wave_heights"] else None,
        })
    return result


def kph_to_beaufort(kph: float) -> int:
    """Convert wind speed in km/h to Beaufort force (0-12)."""
    thresholds = [1, 6, 12, 20, 29, 39, 50, 62, 75, 89, 103, 118]
    for force, threshold in enumerate(thresholds):
        if kph < threshold:
            return force
    return 12


def build_weather_stats(incidents: list) -> dict:
    """Aggregated weather and lighting distributions."""
    natural_light = defaultdict(int)
    wave_bands = defaultdict(int)
    beaufort_counts = defaultdict(int)
    sea_state_counts = defaultdict(int)
    monthly_weather = defaultdict(lambda: {"count": 0, "factor": 0})

    def wave_band(h):
        if h is None: return None
        if h < 0.5: return "0-0.5m"
        if h < 1.5: return "0.5-1.5m"
        if h < 2.5: return "1.5-2.5m"
        if h < 4.0: return "2.5-4m"
        return "4m+"

    for r in incidents:
        we = r.get("Weather_Enrichment") or {}
        a = r.get("Analysis") or {}
        nl = we.get("natural_light_calculated") or we.get("natural_light_reported") or "Unknown"
        natural_light[nl] += 1
        band = wave_band(we.get("wave_height_m"))
        if band: wave_bands[band] += 1
        wind_kph = we.get("wind_kph")
        if wind_kph is not None:
            beaufort_counts[str(kph_to_beaufort(wind_kph))] += 1
        sea_state = we.get("sea_state_reported")
        if sea_state:
            sea_state_counts[sea_state] += 1
        month_str = (r.get("Local_Date_Main_Event") or "")[:7]
        if len(month_str) == 7:
            month = int(month_str[5:7])
            monthly_weather[month]["count"] += 1
            if we.get("weather_was_factor") or a.get("weather_was_factor"):
                monthly_weather[month]["factor"] += 1

    weather_by_month = [
        {"month": m, "pct": round(monthly_weather[m]["factor"] /
                                   max(monthly_weather[m]["count"], 1), 3)}
        for m in sorted(monthly_weather)
    ]

    return {
        "by_natural_light": dict(natural_light),
        "by_wave_height_band": dict(wave_bands),
        "by_wind_force_beaufort": dict(sorted(beaufort_counts.items(), key=lambda x: int(x[0]))),
        "by_sea_state_reported": dict(sea_state_counts),
        "weather_factor_by_month": weather_by_month,
    }


def build_themes_json(themes: list) -> list:
    """Pass-through with minor cleanup for dashboard consumption."""
    return themes


def build_casualties_json(affected_csv_path: str) -> dict:
    """Aggregate affected persons data from CSV."""
    by_type = defaultdict(int)
    by_gender = defaultdict(int)
    by_age_band = defaultdict(int)
    by_injury = defaultdict(int)
    by_body_part = defaultdict(int)
    ppe_used = ppe_deficient = on_duty = total = 0
    ppe_denominator = ppe_deficient_denominator = on_duty_denominator = 0

    def age_band(age_str):
        try:
            age = int(float(age_str))
            if age < 25: return "<25"
            if age < 35: return "25-34"
            if age < 45: return "35-44"
            if age < 55: return "45-54"
            if age < 65: return "55-64"
            return "65+"
        except (ValueError, TypeError):
            return "Unknown"

    with open(affected_csv_path, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            total += 1
            by_type[row.get("Affected_Person_Type", "Unknown")] += 1
            by_gender[row.get("Gender", "Unknown")] += 1
            by_age_band[age_band(row.get("Age"))] += 1
            inj = row.get("Injury_Type_L1", "")
            if inj: by_injury[inj] += 1
            body = row.get("Parts_of_Body_Injured", "")
            if body: by_body_part[body] += 1
            ppe_used_val = row.get("PPE_Used", "").lower()
            if ppe_used_val in ("yes", "no"):
                ppe_denominator += 1
                if ppe_used_val == "yes": ppe_used += 1
            ppe_def_val = row.get("PPE_Deficient", "").lower()
            if ppe_def_val in ("yes", "no"):
                ppe_deficient_denominator += 1
                if ppe_def_val == "yes": ppe_deficient += 1
            on_duty_val = row.get("On_Duty", "").lower()
            if on_duty_val in ("yes", "no"):
                on_duty_denominator += 1
                if on_duty_val == "yes": on_duty += 1

    return {
        "total_affected": total,
        "by_type": dict(by_type),
        "by_gender": dict(by_gender),
        "by_age_band": dict(by_age_band),
        "by_injury_type": dict(sorted(by_injury.items(), key=lambda x: -x[1])[:20]),
        "by_body_part": dict(sorted(by_body_part.items(), key=lambda x: -x[1])[:20]),
        "ppe_used_pct": round(ppe_used / max(ppe_denominator, 1), 3),
        "ppe_deficient_pct": round(ppe_deficient / max(ppe_deficient_denominator, 1), 3),
        "on_duty_pct": round(on_duty / max(on_duty_denominator, 1), 3),
    }


def gt_band(gt_str: str) -> str:
    """Bucket gross tonnage string into a band label."""
    try:
        gt = float(gt_str)
        if gt < 500: return "<500GT"
        if gt < 3000: return "500-3000GT"
        if gt < 10000: return "3000-10000GT"
        if gt < 50000: return "10000-50000GT"
        return "50000GT+"
    except (ValueError, TypeError):
        return "Unknown"


def build_vessels_json(vessels_csv_path: str) -> dict:
    """Aggregate vessel data from CSV."""
    by_category = defaultdict(int)
    by_flag = defaultdict(int)
    by_gt = defaultdict(int)
    commercial = recreational = vessel_loss = 0
    commercial_unknown = 0

    GT_BAND_ORDER = ["<500GT", "500-3000GT", "3000-10000GT", "10000-50000GT", "50000GT+", "Unknown"]

    with open(vessels_csv_path, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            cat = row.get("Vessel_Category_L1", "Unknown")
            by_category[cat] += 1
            flag = row.get("Flag_State", "Unknown")
            if flag: by_flag[flag] += 1
            by_gt[gt_band(row.get("GT_Gross_Tonnage", ""))] += 1
            is_comm = row.get("Is_Commercial_Vessel", "").lower()
            if is_comm == "yes": commercial += 1
            elif is_comm == "no": recreational += 1
            else: commercial_unknown += 1
            if row.get("Loss_Of_Vessel_Damage", "").lower() in ("total loss", "constructive total loss"):
                vessel_loss += 1

    return {
        "by_category": dict(sorted(by_category.items(), key=lambda x: -x[1])),
        "by_flag_state": [{"flag": k, "count": v}
                          for k, v in sorted(by_flag.items(), key=lambda x: -x[1])[:30]],
        "by_gt_band": {b: by_gt[b] for b in GT_BAND_ORDER if b in by_gt},
        "commercial_vs_recreational": {"Commercial": commercial, "Recreational": recreational, "Unknown": commercial_unknown},
        "incidents_with_vessel_loss": vessel_loss,
    }


def assign_theme_ids(incidents: list, themes: list) -> list:
    """
    Incidents should already have theme_id from the theme generator's JSONL update.
    This is a fallback for any that don't.
    """
    id_to_theme = {}
    for t in themes:
        for case in t.get("representative_cases", []):
            id_to_theme[case["id"]] = t["theme_id"]
    for r in incidents:
        if "theme_id" not in r:
            r["theme_id"] = id_to_theme.get(r["Occurrence_Id"], -1)
    return incidents


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading analyzed incidents...")
    if not ANALYZED_JSONL.exists():
        print(f"ERROR: {ANALYZED_JSONL} not found. Run marine_async_processor_v2.py first.")
        return

    incidents = [json.loads(l) for l in open(ANALYZED_JSONL, encoding="utf-8") if l.strip()]
    print(f"Loaded {len(incidents)} incidents.")

    print("Loading themes...")
    if not THEMES_JSON.exists():
        print(f"ERROR: {THEMES_JSON} not found. Run marine_theme_generator_v2.py first.")
        return
    themes = json.load(open(THEMES_JSON, encoding="utf-8"))
    print(f"Loaded {len(themes)} themes.")

    print("Assigning theme IDs to incidents without them...")
    incidents = assign_theme_ids(incidents, themes)

    outputs = {
        "incidents_map.json": build_incidents_map(incidents),
        "themes.json": build_themes_json(themes),
        "time_series.json": build_time_series(incidents),
        "weather_stats.json": build_weather_stats(incidents),
        "casualties.json": build_casualties_json(str(AFFECTED_CSV)),
        "vessels.json": build_vessels_json(str(VESSELS_CSV)),
    }

    for filename, data in outputs.items():
        path = OUTPUT_DIR / filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        size_kb = path.stat().st_size // 1024
        print(f"  Written {path} ({size_kb} KB)")

    print("Done.")


if __name__ == "__main__":
    main()
