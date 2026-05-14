# ai_extraction.py
import json
import re
import os
import anthropic
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

VALID_CATEGORIES = {"navigation", "mooring", "crew_injury", "machinery", "fire", "flooding", "contact", "other"}
VALID_ACTIVITIES = {"underway", "berthing", "anchored", "cargo_ops", "maintenance", "other"}
VALID_FACTOR_TYPES = {"human", "hardware", "environmental", "procedural"}
VALID_CONFIDENCE = {"high", "medium", "low"}

SHORT_DESCRIPTION_THRESHOLD = 200


@lru_cache(maxsize=1)
def get_client() -> anthropic.AsyncAnthropic:
    return anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def build_extraction_prompt(description: str, weather: dict, short: bool = False) -> str:
    weather_ctx = ""
    if weather:
        parts = []
        if weather.get("natural_light_calculated"):
            parts.append(f"Lighting: {weather['natural_light_calculated']}")
        if weather.get("wind_kph") is not None:
            parts.append(f"Wind: {weather['wind_kph']} kph")
        if weather.get("wave_height_m") is not None:
            parts.append(f"Wave height: {weather['wave_height_m']}m")
        if weather.get("sea_state_reported"):
            parts.append(f"Sea state (reported): {weather['sea_state_reported']}")
        weather_ctx = "Weather context: " + ", ".join(parts)

    if short:
        return f"""You are a marine safety analyst. Classify this brief marine incident report.

Incident: {description}
{weather_ctx}

Return ONLY valid JSON with these fields (use null if cannot determine):
{{
  "incident_category": one of navigation/mooring/crew_injury/machinery/fire/flooding/contact/other,
  "vessel_activity": one of underway/berthing/anchored/cargo_ops/maintenance/other,
  "immediate_cause": string,
  "contributing_factors": [],
  "fatigue_factor": true/false/null,
  "training_factor": true/false/null,
  "communication_factor": true/false/null,
  "ppe_factor": true/false/null,
  "weather_was_factor": true/false/null,
  "lighting_was_factor": true/false/null,
  "solas_chapters": [],
  "preventable_by": [],
  "pattern_discovery_summary": string
}}"""

    return f"""You are a senior marine accident investigator and safety analyst. Analyse this incident report and extract structured information.

INCIDENT DESCRIPTION:
{description}

{weather_ctx}

Extract the following. Use null (not false) when the description provides insufficient information to determine a value. Use false only when the description explicitly indicates a factor was NOT present.

Return ONLY valid JSON:
{{
  "incident_category": one of: navigation, mooring, crew_injury, machinery, fire, flooding, contact, other,
  "vessel_activity": one of: underway, berthing, anchored, cargo_ops, maintenance, other,
  "immediate_cause": "direct triggering event in one sentence",
  "contributing_factors": [
    {{"type": "human|hardware|environmental|procedural", "description": "specific factor", "confidence": "high|medium|low"}}
  ],
  "fatigue_factor": true if fatigue/overwork/long hours evident, false if explicitly absent, null if unknown,
  "training_factor": true if inadequate training/experience evident, false if explicitly absent, null if unknown,
  "communication_factor": true if communication breakdown evident, false if explicitly absent, null if unknown,
  "ppe_factor": true if PPE absence/deficiency was relevant, false if explicitly absent, null if unknown,
  "weather_was_factor": true if weather/sea state contributed, false if explicitly absent, null if unknown,
  "lighting_was_factor": true if lighting conditions contributed, false if explicitly absent, null if unknown,
  "solas_chapters": ["chapter identifiers like II-1, V, VI etc. — only include if clearly relevant"],
  "preventable_by": ["specific actionable measures that would have prevented this"],
  "pattern_discovery_summary": "1-2 sentence theory of root cause linking immediate cause to latent factors"
}}"""


def parse_extraction_response(text: str) -> dict | None:
    """Extract JSON from Claude's response, handling markdown code blocks."""
    # Try direct parse first
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    # Try extracting from markdown code block
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    # Try finding first { ... } block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return None


async def extract_incident_analysis(description: str, weather: dict) -> dict | None:
    """Call Claude Sonnet 4.6 to extract structured analysis from an incident description."""
    is_short = len(description) < SHORT_DESCRIPTION_THRESHOLD
    prompt = build_extraction_prompt(description, weather, short=is_short)
    client = get_client()
    try:
        message = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        return parse_extraction_response(message.content[0].text)
    except Exception:
        return None
