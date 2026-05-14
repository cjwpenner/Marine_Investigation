# Marine Safety Observatory — Design Specification

**Date:** 2026-05-14
**Status:** Approved
**Scope:** Improved AI analysis pipeline + interactive web dashboard

---

## 1. Overview

Build an improved marine incident analysis pipeline and a publicly-accessible web dashboard for the Marine Safety Observatory. The project processes ~7,400 open-source European marine incident records, enriches them with AI-extracted structured analysis and objective weather data, clusters them into themes, and presents findings as an interactive site deployable to GitHub Pages.

**Audience:** Layered — accessible entry for general public and journalists, with drill-down detail for marine safety professionals and regulators/policymakers.

**Hosting:** GitHub Pages (static site). No server required.

**Visual style:** Professional Blue — clean card-based layout, blue identity palette, readable at all levels.

---

## 2. Architecture

Three sequential layers, each with a clean interface to the next:

```
Raw CSVs
  ↓ stitch_dataset.py (unchanged)
stitched_marine_data.json
  ↓ marine_async_processor_v2.py  (NEW — Claude Sonnet 4.6 + Open-Meteo)
analyzed_incidents_v2.jsonl
  ↓ marine_theme_generator_v2.py  (NEW — HDBSCAN + Claude Sonnet 4.6)
marine_accident_themes_analysis_v2.md  (comparable to original)
  ↓ export_dashboard_data.py       (NEW — data contract layer)
dashboard/src/data/*.json           (6 pre-aggregated files)
  ↓ Observable Framework build
dist/                               (static site)
  ↓ GitHub Pages
https://<user>.github.io/<repo>/
```

Both `marine_accident_themes_analysis.md` (original) and `marine_accident_themes_analysis_v2.md` (improved) are preserved for direct comparison.

---

## 3. Python Pipeline — Improvements

### 3.1 marine_async_processor_v2.py

Replaces `marine_async_processor.py`. Key changes:

**Model:** Claude Sonnet 4.6 (`claude-sonnet-4-6`) via Anthropic async SDK, replacing GPT-4o.

**Weather enrichment:** Replace Meteostat (land-station only, ~63% coverage) with two Open-Meteo calls per incident:
- **ERA5 Atmospheric API** — `wind_speed_10m`, `wind_gusts_10m`, `temperature_2m`, `precipitation`, `cloud_cover` (global coverage including open ocean)
- **Open-Meteo Marine API** — `wave_height`, `wave_period`, `wave_direction` (covers ocean incidents without land-station gaps)
- Both APIs are free, require no key, and support historical data via the `archive` endpoint.

**Lighting enrichment:** Use the `astral` Python library to compute sunrise/sunset/dusk/dawn times from lat/lon + incident datetime. Produces `natural_light_calculated` to complement `natural_light_reported` from the CSV. Fills nulls; flags disagreements for QA.

**Richer extraction schema** (see Section 3.3).

**Embeddings:** Unchanged — OpenAI `text-embedding-3-small` on `pattern_discovery_summary`. No Anthropic embedding equivalent.

**Short description handling:** Incidents with descriptions <200 chars (currently discarded) are processed with a lighter prompt focused on classification fields only, rather than being dropped. Target: cover >90% of all 7,398 incidents.

**Concurrency:** 15 concurrent Claude requests (same semaphore pattern as current code). Exponential backoff on rate limits.

**Output:** `analyzed_incidents_v2.jsonl`

### 3.2 Weather Enrichment Schema

```json
"weather_enrichment": {
  "natural_light_reported": "Night",
  "natural_light_calculated": "Night",
  "natural_light_source": "both_agree | calculated_only | reported_only | disagree",
  "wind_kph": 42.3,
  "wind_gust_kph": 58.1,
  "wave_height_m": 2.4,
  "wave_period_s": 8.2,
  "wave_direction_deg": 245,
  "precip_mm": 1.1,
  "temp_c": 8.4,
  "cloud_cover_pct": 87,
  "visibility_reported": "Good",
  "sea_state_reported": "Rough",
  "weather_data_source": "open_meteo | none"
}
```

### 3.3 AI Extraction Schema (Claude Sonnet 4.6)

**Classification:**
```json
"incident_category": "navigation | mooring | crew_injury | machinery | fire | flooding | contact | other",
"vessel_activity": "underway | berthing | anchored | cargo_ops | maintenance | other",
"immediate_cause": "string"
```

**Contributing factors** (array):
```json
"contributing_factors": [
  {
    "type": "human | hardware | environmental | procedural",
    "description": "string",
    "confidence": "high | medium | low"
  }
]
```

**Human factor flags** (`true` / `false` / `null` where null = cannot determine):
```json
"fatigue_factor": true | false | null,
"training_factor": true | false | null,
"communication_factor": true | false | null,
"ppe_factor": true | false | null
```

**Environment linkage:**
```json
"weather_was_factor": true | false | null,
"lighting_was_factor": true | false | null
```

**Regulatory:**
```json
"solas_chapters": ["II-1", "V"],
"preventable_by": ["string"]
```

**Pattern (for embedding):**
```json
"pattern_discovery_summary": "string"
```

> **Note:** `null` means the description does not contain enough information to determine. `false` means explicitly not a factor. This distinction is preserved in dashboard filtering.

### 3.4 marine_theme_generator_v2.py

Replaces `marine_theme_generator.py`. Key changes:

**Clustering algorithm:** Replace K-Means (`k=7`, forced) with **HDBSCAN** (Hierarchical Density-Based Spatial Clustering). HDBSCAN discovers natural cluster count, handles variable cluster sizes, and marks outliers rather than force-fitting them.

**Embedding input:** Richer embedding text combining `pattern_discovery_summary` + `incident_category` + top `contributing_factors` types, rather than summary alone.

**Severity weighting:** Incidents weighted by `Occurrence_Severity` when selecting cluster representatives (Very Serious weighted 4×, Serious 2×, Less Serious 1×).

**Stratification:** HDBSCAN runs on the full combined dataset. Vessel category is included as a feature in the enriched embedding text so the algorithm can discover cross-fleet patterns naturally. A single combined `marine_accident_themes_analysis_v2.md` is generated (directly comparable to the original). Per-category breakdowns are available in `themes.json` but no separate per-category .md reports are generated for this POC.

**Theme synthesis:** Claude Sonnet 4.6 (replacing GPT-4o-mini) with a prompt that references contributing factor type distributions, SOLAS chapters, and severity breakdown per cluster.

**Output:** `marine_accident_themes_analysis_v2.md` (same format as original for direct comparison)

---

## 4. Data Contract — export_dashboard_data.py

New script. Reads `analyzed_incidents_v2.jsonl` + original CSVs. Outputs 6 lightweight JSON files to `dashboard/src/data/`. The dashboard never reads raw CSVs or the full JSONL.

### incidents_map.json
One record per incident with location data. Used by the map page.
```json
[{
  "id": "uuid",
  "lat": 51.23,
  "lon": 1.45,
  "date": "2023-04-12",
  "severity": "Serious",
  "theme_id": 3,
  "incident_category": "mooring",
  "vessel_activity": "berthing",
  "natural_light": "Night",   // calculated value preferred; falls back to reported if calculation unavailable
  "weather_was_factor": true,
  "wave_height_m": 2.4,
  "wind_kph": 42.3,
  "short_description": "string",
  "pattern_summary": "string"
}]
```

### themes.json
One record per theme. Used by the themes page.
```json
[{
  "theme_id": 3,
  "title": "Mooring and Operational Vulnerabilities",
  "description": "string",
  "incident_count": 1161,
  "severity_breakdown": {"Very Serious": 12, "Serious": 89, "Less Serious": 1060},
  "top_contributing_factor_types": {"human": 0.52, "hardware": 0.31, "procedural": 0.17},
  "top_solas_chapters": ["VI", "VII"],
  "fatigue_factor_pct": 0.38,
  "training_factor_pct": 0.22,
  "representative_cases": [{"id": "uuid", "description": "string", "severity": "Serious"}]  // max 10, severity-weighted selection
}]
```

### time_series.json
Monthly aggregates. Used by the trends page.
```json
[{
  "year_month": "2023-04",
  "total": 142,
  "very_serious": 3,
  "serious": 18,
  "less_serious": 121,
  "night_pct": 0.38,
  "weather_factor_pct": 0.29,
  "avg_wave_height_m": 1.8
}]
```

### weather_stats.json
Aggregated weather/lighting distributions. Used by the trends page.
```json
{
  "by_natural_light": {"Day": 4210, "Night": 2100, "Dusk": 620, "Dawn": 310, "Unknown": 158},
  "by_wind_force_beaufort": {"1": 120, "2": 340, ...},
  "by_wave_height_band": {"0-0.5m": 890, "0.5-1.5m": 1240, ...},
  "by_sea_state_reported": {"Calm": 1200, "Slight": 980, ...},
  "weather_factor_by_month": [{"month": 1, "pct": 0.31}, ...]
}
```

### casualties.json
Aggregated casualty data. Used by the vessels & people page.
```json
{
  "total_affected": 2509,
  "by_type": {"Crew": 1455, "Passenger": 527, "Other": 527},
  "by_gender": {"Male": 1820, "Female": 412, "Unknown": 277},
  "by_age_band": {"<25": 180, "25-40": 620, ...},
  "by_injury_type": {"Fracture": 380, "Laceration": 290, ...},
  "by_body_part": {"Back/Spine": 310, "Lower limb": 420, ...},
  "ppe_used_pct": 0.41,
  "ppe_deficient_pct": 0.18,
  "on_duty_pct": 0.73
}
```

### vessels.json
Vessel breakdown. Used by the vessels & people page.
```json
{
  "by_category": {"Cargo": 2072, "Passenger": 1701, ...},
  "by_flag_state": [{"flag": "GB", "count": 1842}, ...],
  "by_gt_band": {"<500GT": 890, "500-3000GT": 1240, ...},
  "commercial_vs_recreational": {"Commercial": 6420, "Recreational": 978},
  "incidents_with_vessel_loss": 87
}
```

---

## 5. Dashboard — Observable Framework

### Tech Stack
- **Framework:** Observable Framework (static site generator for data apps)
- **Maps:** Leaflet.js with OpenStreetMap tiles + Leaflet.heat plugin (heatmap) + Leaflet.markercluster (clustered pins)
- **Charts:** Observable Plot (built into Observable Framework)
- **Deployment:** `npm run build` → `dist/` → GitHub Pages via GitHub Actions

### Site Structure

```
dashboard/
  src/
    index.md          ← Landing page
    map.md            ← Map page
    themes.md         ← Themes page
    trends.md         ← Trends page
    vessels.md        ← Vessels & People page
    data/             ← 6 JSON files from export script
    components/       ← Shared JS components
      map.js          ← Leaflet map with toggle
      filters.js      ← Filter bar state
  .github/
    workflows/
      deploy.yml      ← Build + deploy to GitHub Pages
```

### Navigation
Blue top navigation bar (anchored): Logo | Map | Themes | Trends | Vessels & People

### Landing Page
- Blue hero banner with 5 headline stats: total incidents, casualties, night/dusk %, weather factor %, theme count
- Map preview strip (static heatmap image linking to map page)
- Theme cards grid (top 4 themes, sized by count, linking to themes page)
- Two summary charts: monthly incident trend + contributing factor breakdown

### Map Page
- Full-width Leaflet map (fills viewport below nav)
- Filter bar above map: Severity, Vessel type, Year, Night-only toggle, Weather-factor toggle
- **Toggle switch:** Heatmap mode (default) ↔ Clustered pins mode
  - Heatmap: Leaflet.heat layer, intensity = incident count, colour = severity-weighted
  - Pins: Leaflet.markercluster, cluster bubbles sized by count and coloured by max severity in cluster
- **Click a pin → side panel** slides in from right: short description, date, severity badge, vessel type, lighting condition, wave height/wind, AI pattern summary, link to full incident detail
- All filters update both map modes in real time

### Themes Page
- **Treemap** (Observable Plot) sized by incident count, coloured by severity distribution
- Click a theme → expanded panel below:
  - AI-generated theme description
  - Contributing factor type bar (human / hardware / environmental / procedural)
  - Human factor flags summary (% fatigue, training, communication, PPE)
  - Top SOLAS chapters referenced
  - Preventability recommendations
  - Searchable representative case list

### Trends Page
- **Monthly timeline** (line chart, stacked by severity) with year range selector
- **Lighting condition breakdown** — stacked bar: Day / Night / Dusk / Dawn
- **Wind force distribution** — bar chart (Beaufort scale)
- **Wave height distribution** — bar chart (height bands)
- **Weather factor % by month** — area chart showing seasonality
- **Night incidents by category** — which incident types are most over-represented at night

### Vessels & People Page
- **Incidents by vessel type** — horizontal bar chart
- **Flag state breakdown** — ranked list with counts
- **Casualty donut** — crew vs passenger vs other
- **Age distribution** — histogram of affected persons
- **Injury type breakdown** — bar chart
- **Body part frequency** — SVG body diagram with hover counts (or bar chart fallback)
- **PPE usage rate** — stat cards: used %, deficient %

---

## 6. Deployment

GitHub Actions workflow (`deploy.yml`):
1. `cd dashboard && npm install`
2. `npm run build` → outputs to `dist/`
3. Deploy `dist/` to `gh-pages` branch via `peaceiris/actions-gh-pages`

One-time setup: enable GitHub Pages on the repo pointing to `gh-pages` branch.

Re-running the pipeline (when new data arrives):
1. Run `marine_async_processor_v2.py`
2. Run `marine_theme_generator_v2.py`
3. Run `export_dashboard_data.py`
4. Commit updated JSON files in `dashboard/src/data/`
5. Push → GitHub Actions auto-deploys

---

## 7. New Python Dependencies

```
anthropic          # Claude Sonnet 4.6 async client
astral             # Sunrise/sunset calculation for lighting enrichment
hdbscan            # Density-based clustering
openai             # Embeddings only (text-embedding-3-small)
pandas, numpy      # Unchanged
scikit-learn       # Unchanged (UMAP/preprocessing utilities)
tenacity           # Retry logic (unchanged)
python-dotenv      # Unchanged
requests           # Open-Meteo API calls (replaces meteostat)
```

No API key needed for Open-Meteo. Anthropic key already in `.env`.

---

## 8. Files Created / Modified

| File | Status | Notes |
|---|---|---|
| `stitch_dataset.py` | Unchanged | |
| `marine_async_processor_v2.py` | New | Replaces v1 for improved run |
| `marine_theme_generator_v2.py` | New | Replaces v1 for improved run |
| `export_dashboard_data.py` | New | Data contract layer |
| `analyzed_incidents_v2.jsonl` | New output | From v2 processor |
| `marine_accident_themes_analysis_v2.md` | New output | Comparable to original |
| `marine_accident_themes_analysis.md` | Preserved | Original for comparison |
| `dashboard/` | New directory | Observable Framework project |
| `requirements.txt` | New | Python dependencies |
