# Marine Safety Observatory Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and deploy an Observable Framework dashboard with 5 pages (landing, map, themes, trends, vessels & people) that reads from the 6 JSON files produced by the pipeline plan, deployable to GitHub Pages.

**Architecture:** Observable Framework project in `dashboard/`. Pages are Markdown files with embedded JavaScript. Leaflet.js handles the interactive map with heatmap/pin toggle. Observable Plot handles all charts. A GitHub Actions workflow builds and deploys on every push.

**Tech Stack:** Node.js 18+, Observable Framework, Leaflet.js, Leaflet.heat, Leaflet.markercluster, Observable Plot, GitHub Actions

**Prerequisite:** The 6 JSON files in `dashboard/src/data/` must exist (produced by the pipeline plan). To start development before the full pipeline is ready, see Task 1 Step 3 for generating stub data.

---

## File Map

```
dashboard/
  package.json                    NEW
  observablehq.config.js          NEW
  src/
    index.md                      NEW - landing page
    map.md                        NEW - map page
    themes.md                     NEW - themes page
    trends.md                     NEW - trends page
    vessels.md                    NEW - vessels & people page
    data/                         EXISTS (from pipeline plan)
      incidents_map.json
      themes.json
      time_series.json
      weather_stats.json
      casualties.json
      vessels.json
    components/
      map-component.js            NEW - Leaflet map with toggle
      dom-utils.js                NEW - safe DOM helpers (escapeHtml, setText, etc.)
      colors.js                   NEW - shared severity colour scale
  .github/
    workflows/
      deploy.yml                  NEW - build + deploy to GitHub Pages
```

---

## Task 1: Observable Framework Scaffold

**Files:**
- Create: `dashboard/package.json`
- Create: `dashboard/observablehq.config.js`

- [ ] **Step 1: Initialise the dashboard**

```bash
cd dashboard
npm init -y
npm install --save-dev @observablehq/framework
```

- [ ] **Step 2: Write package.json scripts**

Edit `dashboard/package.json` to add scripts:

```json
{
  "name": "marine-safety-observatory",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "observable preview",
    "build": "observable build",
    "clean": "rm -rf dist"
  },
  "devDependencies": {
    "@observablehq/framework": "latest"
  }
}
```

- [ ] **Step 3: Create stub JSON files for development (if pipeline not yet run)**

If `dashboard/src/data/*.json` files do not yet exist, run:

```bash
mkdir -p dashboard/src/data
node -e "
const fs = require('fs');
fs.writeFileSync('dashboard/src/data/incidents_map.json', JSON.stringify([
  {id:'stub-1',lat:51.5,lon:-0.1,date:'2023-04-12',severity:'Serious',
   theme_id:0,incident_category:'mooring',vessel_activity:'berthing',
   natural_light:'Night',weather_was_factor:true,wave_height_m:2.1,
   wind_kph:35,short_description:'Mooring line parted during night berthing.',
   pattern_summary:'Fatigue and equipment failure during berthing.'}
]));
fs.writeFileSync('dashboard/src/data/themes.json', JSON.stringify([
  {theme_id:0,title:'Mooring Failures',description:'Recurring theme description.',
   incident_count:1,severity_breakdown:{'Serious':1},
   top_contributing_factor_types:{human:0.6,hardware:0.4},
   fatigue_factor_pct:0.4,training_factor_pct:0.1,
   ppe_factor_pct:0.05,communication_factor_pct:0.1,
   weather_factor_pct:0.3,lighting_factor_pct:0.2,
   solas_chapters:['VI'],preventable_by:['Pre-op briefing'],
   representative_cases:[{id:'stub-1',description:'Mooring line parted.',severity:'Serious'}]}
]));
fs.writeFileSync('dashboard/src/data/time_series.json', JSON.stringify([
  {year_month:'2023-04',total:142,very_serious:3,serious:18,less_serious:121,
   night_pct:0.38,weather_factor_pct:0.29,avg_wave_height_m:1.8}
]));
fs.writeFileSync('dashboard/src/data/weather_stats.json', JSON.stringify({
  by_natural_light:{Day:4210,Night:2100,Dusk:620,Dawn:310,Unknown:158},
  by_wave_height_band:{'0-0.5m':890,'0.5-1.5m':1240,'1.5-2.5m':980,'2.5-4m':420,'4m+':90},
  weather_factor_by_month:[{month:1,pct:0.31},{month:2,pct:0.28}]
}));
fs.writeFileSync('dashboard/src/data/casualties.json', JSON.stringify({
  total_affected:2509,
  by_type:{Crew:1455,Passenger:527,Other:527},
  by_gender:{Male:1820,Female:412,Unknown:277},
  by_age_band:{'<25':180,'25-34':420,'35-44':680,'45-54':590,'55-64':390,'65+':249},
  by_injury_type:{Fracture:380,Laceration:290,Contusion:210,Sprain:180},
  by_body_part:{'Lower limb':420,'Back/Spine':310,'Upper limb':290,'Head':210},
  ppe_used_pct:0.41,ppe_deficient_pct:0.18,on_duty_pct:0.73
}));
fs.writeFileSync('dashboard/src/data/vessels.json', JSON.stringify({
  by_category:{Cargo:2072,Passenger:1701,Tanker:1331,Fishing:1183,Other:1111},
  by_flag_state:[{flag:'GB',count:1842},{flag:'NL',count:934},{flag:'NO',count:721}],
  commercial_vs_recreational:{Commercial:6420,Recreational:978},
  incidents_with_vessel_loss:87
}));
console.log('Stub data written.');
"
```

- [ ] **Step 4: Write observablehq.config.js**

```js
// dashboard/observablehq.config.js
export default {
  title: "Marine Safety Observatory",
  pages: [
    {name: "Map", path: "/map"},
    {name: "Themes", path: "/themes"},
    {name: "Trends", path: "/trends"},
    {name: "Vessels & People", path: "/vessels"},
  ],
  style: "style.css",
};
```

- [ ] **Step 5: Create style.css**

Write `dashboard/src/style.css`:

```css
:root {
  --theme-foreground: #1e293b;
  --theme-background: #f8f9fc;
  --theme-foreground-muted: #64748b;
  --theme-background-alt: #ffffff;
  --theme-border: #e2e8f0;
  --accent-blue: #1e40af;
}
.stat-card {
  background: var(--theme-background-alt);
  border: 1px solid var(--theme-border);
  border-radius: 8px;
  padding: 16px;
  border-left: 4px solid var(--accent-blue);
}
.stat-card .value { font-size: 2rem; font-weight: 800; color: var(--theme-foreground); }
.stat-card .label { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--theme-foreground-muted); }
.theme-card {
  background: var(--theme-background-alt);
  border: 1px solid var(--theme-border);
  border-top: 3px solid var(--accent-blue);
  border-radius: 6px;
  padding: 14px;
  cursor: pointer;
  transition: box-shadow 0.15s;
}
.theme-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
```

- [ ] **Step 6: Start dev server and verify it loads**

```bash
cd dashboard && npm run dev
```

Expected: Dev server starts at `http://localhost:3000`. No errors in terminal.

- [ ] **Step 7: Commit**

```bash
cd ..
git add dashboard/
git commit -m "feat: scaffold Observable Framework dashboard"
```

---

## Task 2: Shared Components

**Files:**
- Create: `dashboard/src/components/dom-utils.js`
- Create: `dashboard/src/components/colors.js`
- Create: `dashboard/src/components/map-component.js`

- [ ] **Step 1: Write dom-utils.js**

Safe DOM helpers. All user-facing dynamic text goes through `escapeHtml` before
being placed into markup, preventing XSS from unexpected characters in incident data.

```js
// dashboard/src/components/dom-utils.js

/**
 * Escape a string for safe insertion into HTML markup.
 * Use on all values that originate from external JSON data.
 */
export function escapeHtml(str) {
  if (str == null) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

/** Set element text content safely. */
export function setText(el, value) {
  el.textContent = value == null ? "" : String(value);
}

/** Create an element with optional class and text content. */
export function el(tag, cls, text) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text != null) node.textContent = String(text);
  return node;
}
```

- [ ] **Step 2: Write colors.js**

```js
// dashboard/src/components/colors.js
export const SEVERITY_COLORS = {
  "Very Serious": "#dc2626",
  "Serious": "#d97706",
  "Less Serious": "#16a34a",
  "Marine Incident": "#2563eb",
  "Unknown": "#94a3b8",
};

export function severityColor(severity) {
  return SEVERITY_COLORS[severity] ?? "#94a3b8";
}

export const THEME_COLORS = [
  "#1e40af","#2563eb","#3b82f6","#60a5fa",
  "#93c5fd","#1d4ed8","#1e3a8a","#172554"
];

export function themeColor(themeId) {
  if (themeId < 0) return "#94a3b8";
  return THEME_COLORS[themeId % THEME_COLORS.length];
}
```

- [ ] **Step 3: Write map-component.js**

Note: All incident data values displayed in the panel use `escapeHtml()` before
being placed into markup, and plain text values use `textContent` directly.

```js
// dashboard/src/components/map-component.js
import { escapeHtml } from "./dom-utils.js";
import { severityColor } from "./colors.js";

export function createMap(container, allIncidents) {
  // Leaflet CSS injected at runtime (Leaflet is loaded from CDN in the page)
  const cssLink = document.createElement("link");
  cssLink.rel = "stylesheet";
  cssLink.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
  document.head.appendChild(cssLink);

  const L = window.L;

  // ── State ────────────────────────────────────────────────────────────────
  let mode = "heatmap";
  let filters = { severity: "all", year: "all", nightOnly: false, weatherFactor: false };
  let heatLayer = null;
  let clusterGroup = null;

  // ── Layout ───────────────────────────────────────────────────────────────
  // Build the filter bar using safe DOM methods (no user data here — all static)
  container.style.cssText = "display:flex;flex-direction:column;height:calc(100vh - 60px);";

  const filterBar = document.createElement("div");
  filterBar.style.cssText = "display:flex;gap:8px;padding:8px 12px;background:#1e293b;flex-wrap:wrap;align-items:center;border-bottom:1px solid #334155;";

  // Severity select
  const severitySelect = document.createElement("select");
  severitySelect.style.cssText = "background:#334155;color:#e2e8f0;border:none;padding:4px 8px;border-radius:4px;font-size:12px;";
  [["all","All severities"],["Very Serious","Very Serious"],["Serious","Serious"],["Less Serious","Less Serious"]].forEach(([val,text]) => {
    const opt = document.createElement("option");
    opt.value = val;
    opt.textContent = text;
    severitySelect.appendChild(opt);
  });

  // Year select
  const yearSelect = document.createElement("select");
  yearSelect.style.cssText = "background:#334155;color:#e2e8f0;border:none;padding:4px 8px;border-radius:4px;font-size:12px;";
  const allYearOpt = document.createElement("option");
  allYearOpt.value = "all";
  allYearOpt.textContent = "All years";
  yearSelect.appendChild(allYearOpt);
  const years = [...new Set(allIncidents.map(d => d.date?.slice(0,4)).filter(Boolean))].sort();
  years.forEach(y => {
    const opt = document.createElement("option");
    opt.value = y;
    opt.textContent = y;  // year values are our own data — safe
    yearSelect.appendChild(opt);
  });

  // Night toggle
  const nightLabel = document.createElement("label");
  nightLabel.style.cssText = "color:#94a3b8;font-size:12px;display:flex;align-items:center;gap:4px;cursor:pointer;";
  const nightCheck = document.createElement("input");
  nightCheck.type = "checkbox";
  nightLabel.appendChild(nightCheck);
  nightLabel.appendChild(document.createTextNode(" \uD83C\uDF19 Night only"));

  // Weather toggle
  const weatherLabel = document.createElement("label");
  weatherLabel.style.cssText = "color:#94a3b8;font-size:12px;display:flex;align-items:center;gap:4px;cursor:pointer;";
  const weatherCheck = document.createElement("input");
  weatherCheck.type = "checkbox";
  weatherLabel.appendChild(weatherCheck);
  weatherLabel.appendChild(document.createTextNode(" \uD83C\uDF0A Weather factor"));

  // Mode buttons
  const btnWrap = document.createElement("div");
  btnWrap.style.cssText = "margin-left:auto;display:flex;gap:4px;";
  const btnHeat = document.createElement("button");
  btnHeat.textContent = "Heatmap";
  btnHeat.style.cssText = "background:#1e40af;color:#fff;border:none;padding:4px 10px;border-radius:4px;font-size:11px;cursor:pointer;";
  const btnPins = document.createElement("button");
  btnPins.textContent = "Pins";
  btnPins.style.cssText = "background:#334155;color:#94a3b8;border:none;padding:4px 10px;border-radius:4px;font-size:11px;cursor:pointer;";
  btnWrap.append(btnHeat, btnPins);

  filterBar.append(severitySelect, yearSelect, nightLabel, weatherLabel, btnWrap);

  // Map + panel row
  const row = document.createElement("div");
  row.style.cssText = "display:flex;flex:1;overflow:hidden;";

  const mapDiv = document.createElement("div");
  mapDiv.id = "leaflet-map-" + Math.random().toString(36).slice(2);
  mapDiv.style.cssText = "flex:1;min-height:500px;";

  const panel = document.createElement("div");
  panel.style.cssText = "width:0;overflow:hidden;background:#1e293b;transition:width 0.2s;border-left:1px solid #334155;font-size:12px;color:#e2e8f0;";

  row.append(mapDiv, panel);
  container.append(filterBar, row);

  // ── Leaflet init ─────────────────────────────────────────────────────────
  const map = L.map(mapDiv.id, { center: [54, 5], zoom: 5, maxZoom: 14 });
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "\u00a9 OpenStreetMap contributors"
  }).addTo(map);

  // ── Filtering ────────────────────────────────────────────────────────────
  function getFiltered() {
    return allIncidents.filter(d => {
      if (filters.severity !== "all" && d.severity !== filters.severity) return false;
      if (filters.year !== "all" && d.date?.slice(0,4) !== filters.year) return false;
      if (filters.nightOnly && d.natural_light !== "Night" && d.natural_light !== "Dusk") return false;
      if (filters.weatherFactor && !d.weather_was_factor) return false;
      return true;
    });
  }

  // ── Render heatmap ───────────────────────────────────────────────────────
  function renderHeatmap() {
    if (clusterGroup) { map.removeLayer(clusterGroup); clusterGroup = null; }
    if (heatLayer) map.removeLayer(heatLayer);
    const pts = getFiltered()
      .filter(d => d.lat && d.lon)
      .map(d => {
        const intensity = d.severity === "Very Serious" ? 1.0
                        : d.severity === "Serious" ? 0.6 : 0.3;
        return [d.lat, d.lon, intensity];
      });
    heatLayer = L.heatLayer(pts, {
      radius: 18, blur: 15, maxZoom: 10,
      gradient: { 0.2: "#3b82f6", 0.5: "#f97316", 1.0: "#dc2626" }
    }).addTo(map);
  }

  // ── Render pins ──────────────────────────────────────────────────────────
  function renderPins() {
    if (heatLayer) { map.removeLayer(heatLayer); heatLayer = null; }
    if (clusterGroup) map.removeLayer(clusterGroup);
    clusterGroup = L.markerClusterGroup({
      iconCreateFunction(cluster) {
        const n = cluster.getChildCount();
        const size = n > 100 ? 44 : n > 20 ? 36 : 28;
        // Cluster icon: all values are our own numbers — no user data in the label
        const label = n > 999 ? "1k+" : String(n);
        const div = document.createElement("div");
        div.style.cssText = `width:${size}px;height:${size}px;border-radius:50%;background:#1e40af;border:2px solid #fff;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:${size > 36 ? 12 : 10}px;box-shadow:0 2px 6px rgba(0,0,0,0.3);`;
        div.textContent = label;
        return L.divIcon({ html: div, className: "", iconSize: [size, size] });
      }
    });
    getFiltered().filter(d => d.lat && d.lon).forEach(d => {
      const marker = L.circleMarker([d.lat, d.lon], {
        radius: 5, fillColor: severityColor(d.severity),
        color: "#fff", weight: 1.5, fillOpacity: 0.85
      });
      marker.on("click", () => showPanel(d));
      clusterGroup.addLayer(marker);
    });
    map.addLayer(clusterGroup);
  }

  // ── Incident side panel ──────────────────────────────────────────────────
  // All values from incident JSON are treated as untrusted text.
  // Plain text fields use textContent; no dynamic value is inserted via markup.
  function showPanel(incident) {
    panel.style.width = "280px";

    // Clear and rebuild panel using safe DOM methods
    while (panel.firstChild) panel.removeChild(panel.firstChild);

    const wrap = document.createElement("div");
    wrap.style.cssText = "padding:14px;overflow-y:auto;height:100%;box-sizing:border-box;";

    // Header row: severity badge + close button
    const header = document.createElement("div");
    header.style.cssText = "display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px;";
    const badge = document.createElement("span");
    badge.style.cssText = `background:${severityColor(incident.severity)};color:#fff;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:700;`;
    badge.textContent = incident.severity ?? "Unknown";
    const closeBtn = document.createElement("button");
    closeBtn.textContent = "\u00d7";
    closeBtn.style.cssText = "background:none;border:none;color:#64748b;cursor:pointer;font-size:16px;line-height:1;";
    closeBtn.addEventListener("click", () => { panel.style.width = "0"; });
    header.append(badge, closeBtn);
    wrap.appendChild(header);

    // Date
    const dateEl = document.createElement("div");
    dateEl.style.cssText = "font-size:11px;color:#94a3b8;margin-bottom:6px;";
    dateEl.textContent = incident.date ?? "";
    wrap.appendChild(dateEl);

    // Short description
    const descEl = document.createElement("div");
    descEl.style.cssText = "font-size:12px;line-height:1.5;margin-bottom:10px;color:#e2e8f0;";
    descEl.textContent = incident.short_description ?? "";
    wrap.appendChild(descEl);

    // Weather/lighting context
    const ctx = document.createElement("div");
    ctx.style.cssText = "display:flex;flex-direction:column;gap:5px;font-size:11px;border-top:1px solid #334155;padding-top:8px;";
    const addCtxRow = (icon, label, value) => {
      if (value == null || value === "") return;
      const row = document.createElement("div");
      const labelSpan = document.createElement("span");
      labelSpan.style.color = "#94a3b8";
      labelSpan.textContent = `${icon} ${label}: `;
      const valSpan = document.createElement("span");
      valSpan.textContent = String(value);
      row.append(labelSpan, valSpan);
      ctx.appendChild(row);
    };
    addCtxRow("\uD83C\uDF19", "Light", incident.natural_light);
    addCtxRow("\uD83C\uDF0A", "Wave height", incident.wave_height_m != null ? `${incident.wave_height_m}m` : null);
    addCtxRow("\uD83D\uDCA8", "Wind", incident.wind_kph != null ? `${incident.wind_kph} kph` : null);
    if (incident.weather_was_factor) {
      const warn = document.createElement("div");
      warn.style.color = "#f97316";
      warn.textContent = "\u26a0\ufe0f Weather was a factor";
      ctx.appendChild(warn);
    }
    wrap.appendChild(ctx);

    // AI analysis panel
    if (incident.pattern_summary) {
      const aiBox = document.createElement("div");
      aiBox.style.cssText = "margin-top:10px;padding:8px;background:#0f172a;border-radius:4px;font-size:11px;color:#94a3b8;line-height:1.5;border-left:2px solid #1e40af;";
      const aiLabel = document.createElement("div");
      aiLabel.style.cssText = "color:#60a5fa;font-size:9px;font-weight:700;margin-bottom:3px;";
      aiLabel.textContent = "AI ANALYSIS";
      const aiText = document.createElement("div");
      aiText.textContent = incident.pattern_summary;
      aiBox.append(aiLabel, aiText);
      wrap.appendChild(aiBox);
    }

    panel.appendChild(wrap);
  }

  // ── Mode toggle wiring ───────────────────────────────────────────────────
  function setMode(newMode) {
    mode = newMode;
    if (mode === "heatmap") {
      btnHeat.style.background = "#1e40af"; btnHeat.style.color = "#fff";
      btnPins.style.background = "#334155"; btnPins.style.color = "#94a3b8";
    } else {
      btnPins.style.background = "#1e40af"; btnPins.style.color = "#fff";
      btnHeat.style.background = "#334155"; btnHeat.style.color = "#94a3b8";
    }
    render();
  }

  function render() {
    if (mode === "heatmap") renderHeatmap(); else renderPins();
  }

  btnHeat.addEventListener("click", () => setMode("heatmap"));
  btnPins.addEventListener("click", () => setMode("pins"));
  severitySelect.addEventListener("change", e => { filters.severity = e.target.value; render(); });
  yearSelect.addEventListener("change", e => { filters.year = e.target.value; render(); });
  nightCheck.addEventListener("change", e => { filters.nightOnly = e.target.checked; render(); });
  weatherCheck.addEventListener("change", e => { filters.weatherFactor = e.target.checked; render(); });

  render();
  return map;
}
```

- [ ] **Step 4: Commit**

```bash
git add dashboard/src/components/
git commit -m "feat: add shared components (colors, dom-utils, map)"
```

---

## Task 3: Landing Page

**Files:**
- Create: `dashboard/src/index.md`

- [ ] **Step 1: Write dashboard/src/index.md**

```markdown
---
title: Marine Safety Observatory
---

\`\`\`js
import * as Plot from "npm:@observablehq/plot";
const incidents = await FileAttachment("data/incidents_map.json").json();
const themes = await FileAttachment("data/themes.json").json();
const timeSeries = await FileAttachment("data/time_series.json").json();
const weatherStats = await FileAttachment("data/weather_stats.json").json();

const totalIncidents = incidents.length;
const casualties = await FileAttachment("data/casualties.json").json();
const totalCasualties = casualties.total_affected;
const nightPct = Math.round(
  incidents.filter(d => d.natural_light === "Night" || d.natural_light === "Dusk").length
  / totalIncidents * 100
);
const weatherPct = Math.round(
  incidents.filter(d => d.weather_was_factor).length / totalIncidents * 100
);
const themeCount = themes.length;
\`\`\`

<div style="background:linear-gradient(135deg,#1e3a8a 0%,#1e40af 60%,#2563eb 100%);padding:32px 24px;margin:-1rem -1rem 2rem;color:#fff;">
  <div style="font-size:11px;letter-spacing:2px;text-transform:uppercase;opacity:0.7;margin-bottom:8px;">European Waters · 2021–2025 · Open Data Analysis</div>
  <h1 style="font-size:2rem;font-weight:800;margin:0 0 8px;color:#fff;">Marine Incident Analysis</h1>
  <p style="opacity:0.85;max-width:580px;margin:0 0 24px;line-height:1.6;">AI-assisted analysis of reported marine incidents. Explore where accidents happen, what causes them, and how weather, lighting and human factors contribute.</p>
  \`\`\`js
  // Stat cards built with safe DOM via html template tag (Observable's built-in safe templating)
  const labels = ["Incidents","Casualties","Night / Dusk","Weather Factor","Themes"];
  const values = [
    totalIncidents.toLocaleString(),
    totalCasualties.toLocaleString(),
    nightPct + "%",
    weatherPct + "%",
    String(themeCount)
  ];
  html\`<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:10px;max-width:700px;">
    ${labels.map((label, i) => html\`<div style="background:rgba(255,255,255,0.12);border-radius:8px;padding:12px;text-align:center;border:1px solid rgba(255,255,255,0.15);">
      <div style="font-size:1.6rem;font-weight:800;">${values[i]}</div>
      <div style="font-size:9px;text-transform:uppercase;letter-spacing:0.5px;opacity:0.65;margin-top:2px;">${label}</div>
    </div>\`)}
  </div>\`
  \`\`\`
</div>

## Incident Themes

\`\`\`js
const icons = ["⚓","🚨","⚠️","🔧","🗺️","👥","🛟"];
const colors = ["#1e40af","#2563eb","#3b82f6","#60a5fa","#93c5fd","#1d4ed8","#1e3a8a"];
html\`<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:2rem;">
  ${themes.slice(0,4).map((t, i) => html\`<a href="./themes" style="text-decoration:none;">
    <div class="theme-card" style="border-top-color:${colors[i % colors.length]};">
      <div style="font-size:1.4rem;margin-bottom:6px;">${icons[i % icons.length]}</div>
      <div style="font-weight:700;color:#1e293b;font-size:13px;margin-bottom:4px;">${t.title}</div>
      <div style="font-size:11px;color:#64748b;">${t.incident_count.toLocaleString()} incidents</div>
    </div>
  </a>\`)}
</div>\`
\`\`\`

<div style="text-align:center;margin-bottom:2rem;">
  <a href="./map" style="display:inline-block;background:#1e40af;color:#fff;padding:10px 24px;border-radius:6px;text-decoration:none;font-weight:600;font-size:13px;">🗺️ Explore the Incident Map</a>
</div>

## Monthly Trend

\`\`\`js
Plot.plot({
  height: 220,
  marginLeft: 40,
  x: {label: null},
  y: {label: "Incidents"},
  marks: [
    Plot.barY(timeSeries, {x: "year_month", y: "less_serious", fill: "#bfdbfe", tip: true}),
    Plot.barY(timeSeries, {x: "year_month", y: "serious", fill: "#d97706", tip: true}),
    Plot.barY(timeSeries, {x: "year_month", y: "very_serious", fill: "#dc2626", tip: true}),
    Plot.ruleY([0])
  ]
})
\`\`\`

## Lighting Conditions

\`\`\`js
const lightData = Object.entries(weatherStats.by_natural_light)
  .map(([k,v]) => ({light: k, count: v}))
  .filter(d => d.light !== "Unknown")
  .sort((a,b) => b.count - a.count);

Plot.plot({
  height: 160,
  marginLeft: 80,
  x: {label: "Incidents"},
  marks: [
    Plot.barX(lightData, {
      x: "count", y: "light",
      fill: d => ({"Day":"#60a5fa","Night":"#1e293b","Dusk":"#d97706","Dawn":"#f59e0b"})[d.light] ?? "#94a3b8",
      tip: true, sort: {y: "-x"}
    })
  ]
})
\`\`\`
```

- [ ] **Step 2: Verify landing page**

Open `http://localhost:3000`. Expected: Hero with stats, 4 theme cards, monthly trend chart, lighting chart.

- [ ] **Step 3: Commit**

```bash
git add dashboard/src/index.md
git commit -m "feat: add landing page"
```

---

## Task 4: Map Page

**Files:**
- Create: `dashboard/src/map.md`

- [ ] **Step 1: Write dashboard/src/map.md**

```markdown
---
title: Incident Map
---

\`\`\`js
import {createMap} from "./components/map-component.js";
const incidents = await FileAttachment("data/incidents_map.json").json();
\`\`\`

<style>
#map-host {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 60px);
  margin: -1rem -1rem 0;
}
</style>

<div id="map-host"></div>

\`\`\`js
// Load Leaflet and plugins from CDN before initialising the component
async function loadScript(src) {
  if (document.querySelector(\`script[src="${src}"]\`)) return;
  await new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.src = src; s.onload = resolve; s.onerror = reject;
    document.head.appendChild(s);
  });
}
await loadScript("https://unpkg.com/leaflet@1.9.4/dist/leaflet.js");
await loadScript("https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js");

const mcCss = document.createElement("link");
mcCss.rel = "stylesheet";
mcCss.href = "https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css";
document.head.appendChild(mcCss);
await loadScript("https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js");

const host = document.getElementById("map-host");
createMap(host, incidents);
\`\`\`
```

- [ ] **Step 2: Verify map page**

Open `http://localhost:3000/map`. Expected: Full-height dark map, filter bar, heatmap visible. Toggle to Pins shows clusters. Clicking a pin opens the side panel with safe text content (no raw HTML from incident data).

- [ ] **Step 3: Commit**

```bash
git add dashboard/src/map.md
git commit -m "feat: add map page"
```

---

## Task 5: Themes Page

**Files:**
- Create: `dashboard/src/themes.md`

- [ ] **Step 1: Write dashboard/src/themes.md**

```markdown
---
title: Incident Themes
---

\`\`\`js
import * as Plot from "npm:@observablehq/plot";
const themes = await FileAttachment("data/themes.json").json();
const selected = Mutable(null);
\`\`\`

# Incident Themes

AI-identified clusters of incidents with shared latent causes. Click any theme to expand.

\`\`\`js
Plot.plot({
  height: 280,
  marks: [
    Plot.treemap(themes, {
      value: "incident_count",
      fill: (d, i) => ["#1e40af","#2563eb","#3b82f6","#60a5fa","#93c5fd","#bfdbfe","#1d4ed8"][i % 7],
      title: d => d.title + "\n" + d.incident_count.toLocaleString() + " incidents",
      tip: true,
    })
  ]
})
\`\`\`

\`\`\`js
// Theme cards — text content only, no raw HTML from data
themes.map(t => {
  const isSelected = t.theme_id === selected;
  const factorData = Object.entries(t.top_contributing_factor_types)
    .map(([k,v]) => ({type: k, pct: v}))
    .sort((a,b) => b.pct - a.pct);

  const card = document.createElement("div");
  card.style.cssText = "background:#fff;border:1px solid #e2e8f0;border-radius:8px;margin-bottom:12px;overflow:hidden;";

  // Header
  const hdr = document.createElement("div");
  hdr.style.cssText = "padding:14px 16px;cursor:pointer;display:flex;justify-content:space-between;align-items:center;border-top:3px solid #1e40af;";
  hdr.addEventListener("click", () => { selected.value = isSelected ? null : t.theme_id; });

  const titleWrap = document.createElement("div");
  const titleEl = document.createElement("div");
  titleEl.style.cssText = "font-weight:700;font-size:14px;color:#1e293b;";
  titleEl.textContent = t.title;
  const countEl = document.createElement("div");
  countEl.style.cssText = "font-size:11px;color:#64748b;margin-top:2px;";
  countEl.textContent = t.incident_count.toLocaleString() + " incidents";
  titleWrap.append(titleEl, countEl);

  const chevron = document.createElement("span");
  chevron.style.color = "#94a3b8";
  chevron.textContent = isSelected ? "\u25b2" : "\u25bc";
  hdr.append(titleWrap, chevron);
  card.appendChild(hdr);

  if (isSelected) {
    const body = document.createElement("div");
    body.style.cssText = "padding:14px 16px;border-top:1px solid #f1f5f9;background:#fafafa;";

    const descEl = document.createElement("p");
    descEl.style.cssText = "color:#475569;font-size:13px;line-height:1.6;margin-bottom:14px;";
    descEl.textContent = t.description;
    body.appendChild(descEl);

    // Factor bars
    const factorsGrid = document.createElement("div");
    factorsGrid.style.cssText = "display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:14px;";

    const factorCol = document.createElement("div");
    const factorLabel = document.createElement("div");
    factorLabel.style.cssText = "font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px;";
    factorLabel.textContent = "Contributing Factor Types";
    factorCol.appendChild(factorLabel);
    factorData.forEach(f => {
      const row = document.createElement("div");
      row.style.marginBottom = "5px";
      const rowLabel = document.createElement("div");
      rowLabel.style.cssText = "display:flex;justify-content:space-between;font-size:11px;margin-bottom:2px;";
      const typeSpan = document.createElement("span");
      typeSpan.style.cssText = "color:#475569;text-transform:capitalize;";
      typeSpan.textContent = f.type;
      const pctSpan = document.createElement("span");
      pctSpan.style.cssText = "font-weight:600;color:#1e293b;";
      pctSpan.textContent = Math.round(f.pct * 100) + "%";
      rowLabel.append(typeSpan, pctSpan);
      const barWrap = document.createElement("div");
      barWrap.style.cssText = "height:4px;background:#f1f5f9;border-radius:2px;";
      const bar = document.createElement("div");
      bar.style.cssText = "height:100%;background:#1e40af;border-radius:2px;";
      bar.style.width = Math.round(f.pct * 100) + "%";
      barWrap.appendChild(bar);
      row.append(rowLabel, barWrap);
      factorCol.appendChild(row);
    });

    const flagCol = document.createElement("div");
    const flagLabel = document.createElement("div");
    flagLabel.style.cssText = "font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px;";
    flagLabel.textContent = "Human Factor Flags";
    flagCol.appendChild(flagLabel);
    [
      {label: "Fatigue", pct: t.fatigue_factor_pct},
      {label: "Training gap", pct: t.training_factor_pct},
      {label: "PPE issue", pct: t.ppe_factor_pct},
      {label: "Communication", pct: t.communication_factor_pct},
    ].forEach(f => {
      const row = document.createElement("div");
      row.style.cssText = "display:flex;justify-content:space-between;font-size:11px;margin-bottom:5px;";
      const lbl = document.createElement("span");
      lbl.style.color = "#475569";
      lbl.textContent = f.label;
      const val = document.createElement("span");
      val.style.cssText = "font-weight:600;color:" + (f.pct > 0.3 ? "#dc2626" : "#1e293b") + ";";
      val.textContent = Math.round((f.pct ?? 0) * 100) + "%";
      row.append(lbl, val);
      flagCol.appendChild(row);
    });
    if (t.solas_chapters?.length) {
      const solasEl = document.createElement("div");
      solasEl.style.cssText = "margin-top:10px;font-size:11px;color:#64748b;";
      const solasStrong = document.createElement("strong");
      solasStrong.textContent = "SOLAS: ";
      solasEl.appendChild(solasStrong);
      solasEl.appendChild(document.createTextNode(t.solas_chapters.join(", ")));
      flagCol.appendChild(solasEl);
    }

    factorsGrid.append(factorCol, flagCol);
    body.appendChild(factorsGrid);

    // Preventable by
    if (t.preventable_by?.length) {
      const prevBox = document.createElement("div");
      prevBox.style.cssText = "background:#f0fdf4;border-radius:4px;padding:10px;margin-bottom:12px;";
      const prevLabel = document.createElement("div");
      prevLabel.style.cssText = "font-size:10px;font-weight:700;color:#166534;text-transform:uppercase;margin-bottom:4px;";
      prevLabel.textContent = "Preventable by";
      const prevList = document.createElement("ul");
      prevList.style.cssText = "margin:0;padding-left:16px;font-size:11px;color:#475569;";
      t.preventable_by.forEach(p => {
        const li = document.createElement("li");
        li.textContent = p;
        prevList.appendChild(li);
      });
      prevBox.append(prevLabel, prevList);
      body.appendChild(prevBox);
    }

    // Representative cases
    const caseLabel = document.createElement("div");
    caseLabel.style.cssText = "font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px;";
    caseLabel.textContent = "Representative Cases";
    body.appendChild(caseLabel);
    (t.representative_cases ?? []).slice(0, 5).forEach(c => {
      const caseBox = document.createElement("div");
      caseBox.style.cssText = "border:1px solid #e2e8f0;border-radius:4px;padding:8px;margin-bottom:6px;background:#fff;";
      const caseMeta = document.createElement("div");
      caseMeta.style.cssText = "font-size:10px;color:#94a3b8;margin-bottom:3px;";
      caseMeta.textContent = (c.severity ?? "") + " \u00b7 " + (c.id ?? "").slice(0, 8) + "...";
      const caseDesc = document.createElement("div");
      caseDesc.style.cssText = "font-size:11px;color:#475569;line-height:1.4;";
      caseDesc.textContent = (c.description ?? "").slice(0, 250);
      caseBox.append(caseMeta, caseDesc);
      body.appendChild(caseBox);
    });

    card.appendChild(body);
  }

  return card;
})
\`\`\`
```

- [ ] **Step 2: Verify themes page**

Open `http://localhost:3000/themes`. Expected: Treemap visible, theme cards listed below. Clicking expands with factor bars, SOLAS chapters, preventability list, representative cases. All text uses textContent (no raw HTML injection).

- [ ] **Step 3: Commit**

```bash
git add dashboard/src/themes.md
git commit -m "feat: add themes page"
```

---

## Task 6: Trends Page

**Files:**
- Create: `dashboard/src/trends.md`

- [ ] **Step 1: Write dashboard/src/trends.md**

```markdown
---
title: Trends
---

\`\`\`js
import * as Plot from "npm:@observablehq/plot";
const timeSeries = await FileAttachment("data/time_series.json").json();
const weatherStats = await FileAttachment("data/weather_stats.json").json();

const lightData = Object.entries(weatherStats.by_natural_light)
  .map(([k,v]) => ({light: k, count: v}))
  .filter(d => d.light !== "Unknown")
  .sort((a,b) => b.count - a.count);

const waveData = Object.entries(weatherStats.by_wave_height_band)
  .map(([k,v]) => ({band: k, count: v}));
const WAVE_ORDER = ["0-0.5m","0.5-1.5m","1.5-2.5m","2.5-4m","4m+"];
waveData.sort((a,b) => WAVE_ORDER.indexOf(a.band) - WAVE_ORDER.indexOf(b.band));
\`\`\`

# Trends

## Incidents per Month

\`\`\`js
Plot.plot({
  height: 240, marginLeft: 40,
  x: {label: null},
  y: {label: "Incidents"},
  marks: [
    Plot.barY(timeSeries, Plot.stackY({x:"year_month", y:"less_serious", fill:"#bfdbfe", tip:true})),
    Plot.barY(timeSeries, Plot.stackY({x:"year_month", y:"serious", fill:"#d97706", tip:true})),
    Plot.barY(timeSeries, Plot.stackY({x:"year_month", y:"very_serious", fill:"#dc2626", tip:true})),
    Plot.ruleY([0])
  ]
})
\`\`\`

<div style="display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;margin-top:2rem;">

<div>

## Lighting Conditions

\`\`\`js
Plot.plot({
  height: 200, marginLeft: 90,
  x: {label: "Incidents"},
  marks: [
    Plot.barX(lightData, {
      x: "count", y: "light", tip: true, sort: {y: "-x"},
      fill: d => ({"Day":"#60a5fa","Night":"#1e293b","Dusk":"#d97706","Dawn":"#f59e0b"})[d.light] ?? "#94a3b8"
    })
  ]
})
\`\`\`

</div>

<div>

## Wave Height at Incident

\`\`\`js
Plot.plot({
  height: 200, marginLeft: 80,
  x: {label: "Incidents"},
  marks: [
    Plot.barX(waveData, {x: "count", y: "band", fill: "#1e40af", tip: true})
  ]
})
\`\`\`

</div>

</div>

## Weather Factor by Month

\`\`\`js
Plot.plot({
  height: 180, marginLeft: 40,
  x: {label: "Month", tickFormat: d => ["","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][d]},
  y: {label: "% incidents with weather factor", percent: true},
  marks: [
    Plot.areaY(weatherStats.weather_factor_by_month, {x:"month", y:"pct", fill:"#bfdbfe", fillOpacity:0.5}),
    Plot.lineY(weatherStats.weather_factor_by_month, {x:"month", y:"pct", stroke:"#1e40af", strokeWidth:2}),
    Plot.dot(weatherStats.weather_factor_by_month, {x:"month", y:"pct", fill:"#1e40af", tip:true})
  ]
})
\`\`\`

## Night Incident % by Month

\`\`\`js
Plot.plot({
  height: 180, marginLeft: 40,
  x: {label: null},
  y: {label: "Night %", percent: true},
  marks: [
    Plot.lineY(timeSeries, {x:"year_month", y:"night_pct", stroke:"#1e293b", strokeWidth:2}),
    Plot.dot(timeSeries, {x:"year_month", y:"night_pct", fill:"#1e293b", tip:true})
  ]
})
\`\`\`
```

- [ ] **Step 2: Verify trends page**

Open `http://localhost:3000/trends`. Expected: All 5 charts render. Monthly chart is stacked. Lighting and wave charts are horizontal bars. Weather and night charts are line/area.

- [ ] **Step 3: Commit**

```bash
git add dashboard/src/trends.md
git commit -m "feat: add trends page"
```

---

## Task 7: Vessels & People Page

**Files:**
- Create: `dashboard/src/vessels.md`

- [ ] **Step 1: Write dashboard/src/vessels.md**

```markdown
---
title: Vessels & People
---

\`\`\`js
import * as Plot from "npm:@observablehq/plot";
const vessels = await FileAttachment("data/vessels.json").json();
const casualties = await FileAttachment("data/casualties.json").json();

const vesselCatData = Object.entries(vessels.by_category)
  .map(([k,v]) => ({category:k, count:v}))
  .sort((a,b) => b.count - a.count);

const injuryData = Object.entries(casualties.by_injury_type)
  .map(([k,v]) => ({type:k, count:v}))
  .sort((a,b) => b.count - a.count).slice(0,12);

const bodyPartData = Object.entries(casualties.by_body_part)
  .map(([k,v]) => ({part:k, count:v}))
  .sort((a,b) => b.count - a.count).slice(0,12);

const AGE_ORDER = ["<25","25-34","35-44","45-54","55-64","65+"];
const ageData = Object.entries(casualties.by_age_band)
  .map(([k,v]) => ({age:k, count:v}))
  .filter(d => d.age !== "Unknown")
  .sort((a,b) => AGE_ORDER.indexOf(a.age) - AGE_ORDER.indexOf(b.age));

const typeData = Object.entries(casualties.by_type)
  .map(([k,v]) => ({type:k, count:v}));
\`\`\`

# Vessels & People

\`\`\`js
html\`<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:2rem;">
  <div class="stat-card"><div class="value">${casualties.total_affected.toLocaleString()}</div><div class="label">Total Affected</div></div>
  <div class="stat-card" style="border-left-color:#dc2626;"><div class="value">${Math.round(casualties.ppe_deficient_pct*100)}%</div><div class="label">PPE Deficient</div></div>
  <div class="stat-card"><div class="value">${Math.round(casualties.on_duty_pct*100)}%</div><div class="label">On Duty</div></div>
  <div class="stat-card"><div class="value">${vessels.incidents_with_vessel_loss.toLocaleString()}</div><div class="label">Vessel Losses</div></div>
</div>\`
\`\`\`

<div style="display:grid;grid-template-columns:2fr 1fr;gap:1.5rem;">

<div>

## By Vessel Type

\`\`\`js
Plot.plot({
  height: 220, marginLeft: 110,
  x: {label: "Incidents"},
  marks: [Plot.barX(vesselCatData, {x:"count", y:"category", fill:"#1e40af", tip:true, sort:{y:"-x"}})]
})
\`\`\`

</div><div>

## Casualties by Type

\`\`\`js
Plot.plot({
  height: 220,
  marks: [Plot.arc(typeData, {
    value: "count",
    fill: d => ({"Crew":"#1e40af","Passenger":"#3b82f6","Other":"#93c5fd"})[d.type] ?? "#94a3b8",
    innerRadius: 60, tip: true,
    title: d => d.type + ": " + d.count.toLocaleString()
  })]
})
\`\`\`

</div></div>

<div style="display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;margin-top:1.5rem;">

<div>

## Age Distribution

\`\`\`js
Plot.plot({
  height: 180, marginLeft: 50,
  x: {label: "Age band"},
  y: {label: "Persons"},
  marks: [Plot.barY(ageData, {x:"age", y:"count", fill:"#1e40af", tip:true})]
})
\`\`\`

</div><div>

## Injury Types

\`\`\`js
Plot.plot({
  height: 180, marginLeft: 110,
  x: {label: "Count"},
  marks: [Plot.barX(injuryData, {x:"count", y:"type", fill:"#3b82f6", tip:true, sort:{y:"-x"}})]
})
\`\`\`

</div></div>

## Body Parts Injured

\`\`\`js
Plot.plot({
  height: 200, marginLeft: 130,
  x: {label: "Count"},
  marks: [Plot.barX(bodyPartData, {x:"count", y:"part", fill:"#60a5fa", tip:true, sort:{y:"-x"}})]
})
\`\`\`

## Top Flag States

\`\`\`js
Plot.plot({
  height: 240,
  x: {label: "Flag state"},
  y: {label: "Incidents"},
  marks: [Plot.barY(vessels.by_flag_state.slice(0,15), {x:"flag", y:"count", fill:"#1e40af", tip:true, sort:{x:"-y"}})]
})
\`\`\`
```

- [ ] **Step 2: Verify vessels page**

Open `http://localhost:3000/vessels`. Expected: 4 stat cards, all charts render.

- [ ] **Step 3: Commit**

```bash
git add dashboard/src/vessels.md
git commit -m "feat: add vessels and people page"
```

---

## Task 8: GitHub Actions Deployment

**Files:**
- Create: `.github/workflows/deploy.yml`

- [ ] **Step 1: Create GitHub Actions workflow**

```bash
mkdir -p .github/workflows
```

Write `.github/workflows/deploy.yml`:

```yaml
name: Build and Deploy Dashboard

on:
  push:
    branches: [main]
    paths:
      - "dashboard/**"

permissions:
  contents: write

jobs:
  build-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
          cache-dependency-path: dashboard/package-lock.json

      - name: Install dependencies
        run: cd dashboard && npm ci

      - name: Build
        run: cd dashboard && npm run build

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: dashboard/dist
          publish_branch: gh-pages
```

- [ ] **Step 2: Initialise git repo and push to GitHub**

If no git repo yet:
```bash
cd C:/Users/Chris/MarineInvestigation
git init
git add .
git commit -m "initial commit"
gh repo create marine-safety-observatory --public
git remote add origin https://github.com/YOUR_USERNAME/marine-safety-observatory.git
git push -u origin main
```

- [ ] **Step 3: Enable GitHub Pages**

In the GitHub repo: Settings → Pages → Source: Deploy from branch `gh-pages`. GitHub Actions will create this branch on first successful deploy.

- [ ] **Step 4: Generate lock file and commit**

```bash
cd dashboard && npm install
cd ..
git add .github/workflows/deploy.yml dashboard/package-lock.json
git commit -m "feat: add GitHub Actions deployment"
git push
```

- [ ] **Step 5: Verify deployment**

GitHub → Actions tab: workflow should succeed. Then open `https://YOUR_USERNAME.github.io/marine-safety-observatory/`. Expected: Landing page loads, all navigation links work.

---

## Final Verification

- [ ] **Local build passes**

```bash
cd dashboard && npm run build
```

Expected: `dist/` created, no errors.

- [ ] **All pages accessible**

```bash
npm run dev
```

Verify each page loads without console errors:
- `http://localhost:3000/` — Landing
- `http://localhost:3000/map` — Map with toggle
- `http://localhost:3000/themes` — Treemap + expand
- `http://localhost:3000/trends` — All charts
- `http://localhost:3000/vessels` — All charts

- [ ] **Replace stub data with real data**

Once pipeline plan is complete, the JSON files are already in `dashboard/src/data/`. Restart dev server and verify real data renders correctly. Then push to trigger re-deployment.

- [ ] **Final commit**

```bash
git add .
git commit -m "chore: dashboard complete"
git push
```
