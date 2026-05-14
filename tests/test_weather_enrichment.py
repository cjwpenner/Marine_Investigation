# tests/test_weather_enrichment.py
from unittest.mock import patch, MagicMock
import datetime
import pytest
from weather_enrichment import get_open_meteo_weather, calculate_natural_light, enrich_weather

def test_calculate_natural_light_day():
    # London, noon UTC on a summer day
    result = calculate_natural_light(51.5, -0.1, datetime.datetime(2023, 6, 15, 11, 0))
    assert result == "Day"

def test_calculate_natural_light_night():
    # London, 2am UTC
    result = calculate_natural_light(51.5, -0.1, datetime.datetime(2023, 6, 15, 1, 0))
    assert result == "Night"

def test_calculate_natural_light_missing_coords():
    result = calculate_natural_light(None, None, datetime.datetime(2023, 6, 15, 11, 0))
    assert result is None

def test_get_open_meteo_weather_returns_dict():
    mock_atmo = {
        "hourly": {
            "time": ["2023-04-12T12:00"],
            "wind_speed_10m": [12.5],
            "wind_gusts_10m": [18.2],
            "temperature_2m": [10.1],
            "precipitation": [0.0],
            "cloud_cover": [75]
        }
    }
    mock_marine = {
        "hourly": {
            "time": ["2023-04-12T12:00"],
            "wave_height": [1.8],
            "wave_period": [7.2],
            "wave_direction": [240]
        }
    }
    with patch("weather_enrichment.requests.get") as mock_get:
        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: mock_atmo),
            MagicMock(status_code=200, json=lambda: mock_marine),
        ]
        result = get_open_meteo_weather(51.5, -0.1, "2023-04-12", 12)
    assert result["wind_kph"] == pytest.approx(12.5 * 3.6, rel=0.01)
    assert result["wave_height_m"] == 1.8
    assert result["temp_c"] == 10.1

def test_get_open_meteo_weather_no_location():
    result = get_open_meteo_weather(None, None, "2023-04-12", 12)
    assert result is None

def test_enrich_weather_combines_reported_and_calculated():
    incident = {
        "Latitude": 51.5, "Longitude": -0.1,
        "Local_Date_Main_Event": "2023-04-12T12:00:00",
        "Natural_Light": "Day",
        "Sea_State": "Slight",
        "Visibility": "Good"
    }
    mock_weather = {
        "wind_kph": 25.0, "wind_gust_kph": 35.0, "wave_height_m": 0.8,
        "wave_period_s": 6.0, "wave_direction_deg": 200,
        "precip_mm": 0.0, "temp_c": 12.0, "cloud_cover_pct": 40
    }
    with patch("weather_enrichment.get_open_meteo_weather", return_value=mock_weather):
        result = enrich_weather(incident)
    assert result["natural_light_reported"] == "Day"
    assert result["natural_light_calculated"] == "Day"
    assert result["natural_light_source"] == "both_agree"
    assert result["wind_kph"] == 25.0
    assert result["weather_data_source"] == "open_meteo"


def test_enrich_weather_disagree_source():
    """When reported and calculated natural light differ, source should be 'disagree'."""
    incident = {
        "Latitude": 51.5, "Longitude": -0.1,
        "Local_Date_Main_Event": "2023-04-12T12:00:00",
        "Natural_Light": "Night",  # Reported as Night
    }
    mock_weather = {"wind_kph": 10.0, "wind_gust_kph": 15.0, "wave_height_m": 0.5,
                    "wave_period_s": 5.0, "wave_direction_deg": 180,
                    "precip_mm": 0.0, "temp_c": 15.0, "cloud_cover_pct": 20}
    with patch("weather_enrichment.get_open_meteo_weather", return_value=mock_weather):
        result = enrich_weather(incident)
    # Noon UTC in London is definitely Day — should disagree with reported "Night"
    assert result["natural_light_reported"] == "Night"
    assert result["natural_light_calculated"] == "Day"
    assert result["natural_light_source"] == "disagree"


def test_enrich_weather_calculated_only_source():
    """When no Natural_Light in CSV, source should be 'calculated_only'."""
    incident = {
        "Latitude": 51.5, "Longitude": -0.1,
        "Local_Date_Main_Event": "2023-04-12T12:00:00",
        # No Natural_Light field
    }
    with patch("weather_enrichment.get_open_meteo_weather", return_value=None):
        result = enrich_weather(incident)
    assert result["natural_light_reported"] is None
    assert result["natural_light_calculated"] == "Day"
    assert result["natural_light_source"] == "calculated_only"
