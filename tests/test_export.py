# tests/test_export.py
import json, pytest
from pathlib import Path

SAMPLE_INCIDENTS = [
    {
        "Occurrence_Id": "abc-001",
        "Latitude": 51.5, "Longitude": -0.1,
        "Local_Date_Main_Event": "2023-04-12T12:00:00",
        "Occurrence_Severity": "Serious",
        "Original_Description": "Mooring line parted during berthing.",
        "Weather_Enrichment": {
            "natural_light_calculated": "Day", "natural_light_reported": "Day",
            "wind_kph": 25.0, "wave_height_m": 0.8, "weather_was_factor": False,
        },
        "Analysis": {
            "incident_category": "mooring",
            "vessel_activity": "berthing",
            "fatigue_factor": True,
            "weather_was_factor": False,
            "pattern_discovery_summary": "Mooring failure due to steep approach angle.",
        },
        "theme_id": 0,
    }
]

SAMPLE_THEMES = [
    {"theme_id": 0, "title": "Mooring Failures", "description": "desc",
     "incident_count": 1, "severity_breakdown": {"Serious": 1},
     "top_contributing_factor_types": {"human": 1.0},
     "fatigue_factor_pct": 1.0, "training_factor_pct": 0.0,
     "ppe_factor_pct": 0.0, "communication_factor_pct": 0.0,
     "weather_factor_pct": 0.0, "lighting_factor_pct": 0.0,
     "solas_chapters": ["VI"], "preventable_by": ["Safety brief"],
     "representative_cases": [{"id": "abc-001", "description": "test", "severity": "Serious"}]}
]

def test_incidents_map_json_shape():
    from export_dashboard_data import build_incidents_map
    result = build_incidents_map(SAMPLE_INCIDENTS)
    assert len(result) == 1
    item = result[0]
    assert item["id"] == "abc-001"
    assert item["lat"] == 51.5
    assert item["severity"] == "Serious"
    assert item["natural_light"] == "Day"
    assert "short_description" in item

def test_incidents_map_skips_no_location():
    from export_dashboard_data import build_incidents_map
    no_loc = [{**SAMPLE_INCIDENTS[0], "Latitude": None, "Longitude": None}]
    result = build_incidents_map(no_loc)
    assert len(result) == 0

def test_time_series_json_shape():
    from export_dashboard_data import build_time_series
    result = build_time_series(SAMPLE_INCIDENTS)
    assert len(result) == 1
    assert result[0]["year_month"] == "2023-04"
    assert result[0]["total"] == 1

def test_themes_json_preserves_all_themes():
    from export_dashboard_data import build_themes_json
    result = build_themes_json(SAMPLE_THEMES)
    assert len(result) == 1
    assert result[0]["theme_id"] == 0

def test_weather_stats_includes_beaufort_and_sea_state():
    from export_dashboard_data import build_weather_stats
    incidents = [
        {**SAMPLE_INCIDENTS[0], "Weather_Enrichment": {
            "natural_light_calculated": "Day",
            "wind_kph": 25.0,   # Beaufort 5 (20-28 kph)
            "wave_height_m": 0.8,
            "sea_state_reported": "Slight",
            "weather_was_factor": False,
        }},
    ]
    result = build_weather_stats(incidents)
    assert "by_wind_force_beaufort" in result
    assert "by_sea_state_reported" in result
    assert result["by_wind_force_beaufort"]["4"] == 1   # 25 kph = Beaufort 4
    assert result["by_sea_state_reported"]["Slight"] == 1

def test_kph_to_beaufort_boundaries():
    from export_dashboard_data import kph_to_beaufort
    assert kph_to_beaufort(0) == 0
    assert kph_to_beaufort(5) == 1
    assert kph_to_beaufort(11) == 2
    assert kph_to_beaufort(50) == 7   # 50-61 kph = Force 7
    assert kph_to_beaufort(200) == 12


def test_time_series_unknown_severity_not_in_less_serious():
    from export_dashboard_data import build_time_series
    incidents = [
        {**SAMPLE_INCIDENTS[0], "Occurrence_Severity": "Less Serious"},
        {**SAMPLE_INCIDENTS[0], "Occurrence_Severity": ""},          # unknown
        {**SAMPLE_INCIDENTS[0], "Occurrence_Severity": "Unknown"},   # unknown
    ]
    result = build_time_series(incidents)
    assert result[0]["total"] == 3
    assert result[0]["less_serious"] == 1   # only the explicit "Less Serious"
    assert result[0]["serious"] == 0
    assert result[0]["very_serious"] == 0


def test_casualties_ppe_uses_populated_rows_as_denominator(tmp_path):
    import csv as csv_module
    from export_dashboard_data import build_casualties_json
    # 3 rows: 2 with PPE_Used populated (1 yes, 1 no), 1 with blank PPE_Used
    rows = [
        {"Affected_Person_Type": "Crew", "Gender": "Male", "Age": "35",
         "Injury_Type_L1": "", "Parts_of_Body_Injured": "",
         "PPE_Used": "yes", "PPE_Deficient": "no", "On_Duty": "yes"},
        {"Affected_Person_Type": "Crew", "Gender": "Male", "Age": "40",
         "Injury_Type_L1": "", "Parts_of_Body_Injured": "",
         "PPE_Used": "no", "PPE_Deficient": "no", "On_Duty": ""},
        {"Affected_Person_Type": "Passenger", "Gender": "Female", "Age": "28",
         "Injury_Type_L1": "", "Parts_of_Body_Injured": "",
         "PPE_Used": "", "PPE_Deficient": "", "On_Duty": ""},
    ]
    csv_path = tmp_path / "affected.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv_module.DictWriter(f, fieldnames=rows[0].keys(), delimiter=";")
        writer.writeheader()
        writer.writerows(rows)
    result = build_casualties_json(str(csv_path))
    assert result["total_affected"] == 3
    # ppe_used: 1 yes out of 2 populated rows → 0.5, NOT 1/3
    assert result["ppe_used_pct"] == 0.5
    # on_duty: 1 yes out of 1 populated row → 1.0
    assert result["on_duty_pct"] == 1.0


def test_vessels_blank_commercial_field_not_counted_as_recreational(tmp_path):
    import csv as csv_module
    from export_dashboard_data import build_vessels_json
    rows = [
        {"Vessel_Category_L1": "Cargo", "Flag_State": "GB",
         "Is_Commercial_Vessel": "yes", "GT_Gross_Tonnage": "5000",
         "Loss_Of_Vessel_Damage": ""},
        {"Vessel_Category_L1": "Fishing", "Flag_State": "IE",
         "Is_Commercial_Vessel": "no", "GT_Gross_Tonnage": "200",
         "Loss_Of_Vessel_Damage": ""},
        {"Vessel_Category_L1": "Other", "Flag_State": "",
         "Is_Commercial_Vessel": "", "GT_Gross_Tonnage": "",
         "Loss_Of_Vessel_Damage": ""},
    ]
    csv_path = tmp_path / "vessels.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv_module.DictWriter(f, fieldnames=rows[0].keys(), delimiter=";")
        writer.writeheader()
        writer.writerows(rows)
    result = build_vessels_json(str(csv_path))
    cr = result["commercial_vs_recreational"]
    assert cr["Commercial"] == 1
    assert cr["Recreational"] == 1
    assert cr["Unknown"] == 1   # blank should NOT inflate recreational
