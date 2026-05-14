# weather_enrichment.py
import requests
import datetime
from typing import Optional
from astral import LocationInfo
from astral.sun import sun

OPEN_METEO_ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"
OPEN_METEO_MARINE = "https://marine-api.open-meteo.com/v1/marine"


def calculate_natural_light(lat: Optional[float], lon: Optional[float],
                             dt: datetime.datetime) -> Optional[str]:
    """Return Day/Night/Dusk/Dawn based on sun position at lat/lon/datetime."""
    if lat is None or lon is None:
        return None
    try:
        location = LocationInfo(latitude=lat, longitude=lon)
        s = sun(location.observer, date=dt.date())
        if s["dawn"] <= dt.replace(tzinfo=s["dawn"].tzinfo) < s["sunrise"]:
            return "Dawn"
        elif s["sunrise"] <= dt.replace(tzinfo=s["sunrise"].tzinfo) < s["sunset"]:
            return "Day"
        elif s["sunset"] <= dt.replace(tzinfo=s["sunset"].tzinfo) < s["dusk"]:
            return "Dusk"
        else:
            return "Night"
    except Exception:
        return None


def get_open_meteo_weather(lat: Optional[float], lon: Optional[float],
                            date_str: str, hour: int) -> Optional[dict]:
    """Fetch ERA5 atmospheric and marine weather for a specific lat/lon/date/hour."""
    if lat is None or lon is None:
        return None
    params = {
        "latitude": lat, "longitude": lon,
        "start_date": date_str, "end_date": date_str,
        "hourly": "wind_speed_10m,wind_gusts_10m,temperature_2m,precipitation,cloud_cover",
        "wind_speed_unit": "ms",  # m/s — we convert to kph
    }
    try:
        atmo_resp = requests.get(OPEN_METEO_ARCHIVE, params=params, timeout=10)
        marine_resp = requests.get(OPEN_METEO_MARINE, params={
            "latitude": lat, "longitude": lon,
            "start_date": date_str, "end_date": date_str,
            "hourly": "wave_height,wave_period,wave_direction",
        }, timeout=10)
        if atmo_resp.status_code != 200 or marine_resp.status_code != 200:
            return None
        atmo = atmo_resp.json()["hourly"]
        marine = marine_resp.json()["hourly"]
        # Pick the closest hour index (hourly data, 24 values)
        idx = min(hour, len(atmo["wind_speed_10m"]) - 1)
        m_idx = min(hour, len(marine["wave_height"]) - 1)
        return {
            "wind_kph": round((atmo["wind_speed_10m"][idx] or 0) * 3.6, 1),
            "wind_gust_kph": round((atmo["wind_gusts_10m"][idx] or 0) * 3.6, 1),
            "temp_c": atmo["temperature_2m"][idx],
            "precip_mm": atmo["precipitation"][idx] or 0.0,
            "cloud_cover_pct": atmo["cloud_cover"][idx],
            "wave_height_m": marine["wave_height"][m_idx],
            "wave_period_s": marine["wave_period"][m_idx],
            "wave_direction_deg": marine["wave_direction"][m_idx],
        }
    except Exception:
        return None


def enrich_weather(incident: dict) -> dict:
    """
    Build weather_enrichment dict from an incident record.
    Combines Open-Meteo objective data with CSV-reported fields.
    """
    lat = incident.get("Latitude")
    lon = incident.get("Longitude")
    dt_str = incident.get("Local_Date_Main_Event", "")

    # Parse datetime
    dt = None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.datetime.strptime(dt_str[:19], fmt)
            break
        except (ValueError, TypeError):
            continue

    natural_light_reported = incident.get("Natural_Light") or None
    natural_light_calculated = calculate_natural_light(lat, lon, dt) if dt else None

    if natural_light_reported and natural_light_calculated:
        source = "both_agree" if natural_light_reported == natural_light_calculated else "disagree"
    elif natural_light_calculated:
        source = "calculated_only"
    elif natural_light_reported:
        source = "reported_only"
    else:
        source = "unknown"

    # Fetch objective weather
    date_str = dt.strftime("%Y-%m-%d") if dt else None
    hour = dt.hour if dt else 12
    weather = get_open_meteo_weather(lat, lon, date_str, hour) if date_str else None

    result = {
        "natural_light_reported": natural_light_reported,
        "natural_light_calculated": natural_light_calculated,
        "natural_light_source": source,
        "visibility_reported": incident.get("Visibility"),
        "sea_state_reported": incident.get("Sea_State"),
        "weather_data_source": "open_meteo" if weather else "none",
    }
    if weather:
        result.update(weather)
    return result
