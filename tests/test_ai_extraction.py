# tests/test_ai_extraction.py
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from ai_extraction import build_extraction_prompt, parse_extraction_response, extract_incident_analysis

SAMPLE_DESCRIPTION = (
    "The vessel was approaching the berth in darkness when the mooring line parted. "
    "The crew had been on watch for 14 hours. The bow thruster failed to respond. "
    "No safety briefing had been conducted prior to the operation."
)

SAMPLE_WEATHER = {
    "natural_light_calculated": "Night",
    "wind_kph": 38.0,
    "wave_height_m": 1.5,
    "sea_state_reported": "Moderate"
}

VALID_RESPONSE = {
    "incident_category": "mooring",
    "vessel_activity": "berthing",
    "immediate_cause": "Mooring line failure during berthing approach",
    "contributing_factors": [
        {"type": "human", "description": "Crew fatigue after 14-hour watch", "confidence": "high"},
        {"type": "hardware", "description": "Bow thruster failure", "confidence": "high"},
        {"type": "procedural", "description": "No pre-operation safety briefing", "confidence": "high"}
    ],
    "fatigue_factor": True,
    "training_factor": False,
    "communication_factor": None,
    "ppe_factor": False,
    "weather_was_factor": True,
    "lighting_was_factor": True,
    "solas_chapters": ["VI"],
    "preventable_by": ["Pre-operation safety briefing", "Fatigue management policy"],
    "pattern_discovery_summary": "Mooring line failure during night berthing compounded by crew fatigue and bow thruster malfunction, with no pre-operation safety process in place."
}

def test_build_extraction_prompt_contains_description():
    prompt = build_extraction_prompt(SAMPLE_DESCRIPTION, SAMPLE_WEATHER)
    assert SAMPLE_DESCRIPTION in prompt
    assert "Night" in prompt
    assert "38.0" in prompt

def test_parse_extraction_response_valid():
    result = parse_extraction_response(json.dumps(VALID_RESPONSE))
    assert result["incident_category"] == "mooring"
    assert result["fatigue_factor"] is True
    assert len(result["contributing_factors"]) == 3

def test_parse_extraction_response_extracts_from_markdown():
    wrapped = f"Here is my analysis:\n```json\n{json.dumps(VALID_RESPONSE)}\n```"
    result = parse_extraction_response(wrapped)
    assert result["incident_category"] == "mooring"

def test_parse_extraction_response_invalid_returns_none():
    result = parse_extraction_response("not json at all")
    assert result is None

@pytest.mark.asyncio
async def test_extract_incident_analysis_calls_claude():
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=json.dumps(VALID_RESPONSE))]
    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_message)
    with patch("ai_extraction.get_client", return_value=mock_client):
        result = await extract_incident_analysis(SAMPLE_DESCRIPTION, SAMPLE_WEATHER)
    assert result["incident_category"] == "mooring"
    assert result["pattern_discovery_summary"] is not None
