# weather_enrichment.py
# Extracts weather context directly from the source incident record.
# Open-Meteo was removed: all incidents are date-only (no time), making
# ERA5 hourly data unreliable (always defaulted to midnight hour=0).
# The MAIB source CSV fields are the authoritative weather record.


def enrich_weather(incident: dict) -> dict:
    """
    Build weather context from source CSV fields already on the incident record.
    All fields are as-reported by the investigating authority.
    """
    return {
        "natural_light_reported": incident.get("Natural_Light") or None,
        "sea_state_reported":     incident.get("Sea_State") or None,
        "visibility_reported":    incident.get("Visibility") or None,
        "weather_type":           incident.get("Weather") or None,
        "wind_force":             incident.get("Wind_Force") or None,
        "weather_was_factor":     None,  # set by AI analysis
        "weather_data_source":    "source_csv",
    }
