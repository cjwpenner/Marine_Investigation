---
title: Marine Safety Observatory
---

```js
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
```

<div style="background:linear-gradient(135deg,#1e3a8a 0%,#1e40af 60%,#2563eb 100%);padding:32px 24px;margin:-1rem -1rem 2rem;color:#fff;">
  <div style="font-size:11px;letter-spacing:2px;text-transform:uppercase;opacity:0.7;margin-bottom:8px;">European Waters · 2021–2025 · Open Data Analysis</div>
  <h1 style="font-size:2rem;font-weight:800;margin:0 0 8px;color:#fff;">Marine Incident Analysis</h1>
  <p style="opacity:0.85;max-width:580px;margin:0 0 24px;line-height:1.6;">AI-assisted analysis of reported marine incidents. Explore where accidents happen, what causes them, and how weather, lighting and human factors contribute.</p>

```js
const labels = ["Incidents","Casualties","Night / Dusk","Weather Factor","Themes"];
const values = [
  totalIncidents.toLocaleString(),
  totalCasualties.toLocaleString(),
  nightPct + "%",
  weatherPct + "%",
  String(themeCount)
];
html`<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:10px;max-width:700px;">
  ${labels.map((label, i) => html`<div style="background:rgba(255,255,255,0.12);border-radius:8px;padding:12px;text-align:center;border:1px solid rgba(255,255,255,0.15);">
    <div style="font-size:1.6rem;font-weight:800;">${values[i]}</div>
    <div style="font-size:9px;text-transform:uppercase;letter-spacing:0.5px;opacity:0.65;margin-top:2px;">${label}</div>
  </div>`)}
</div>`
```

</div>

## Incident Themes

```js
const icons = ["⚓","🚨","⚠️","🔧","🗺️","👥","🛟"];
const colors = ["#1e40af","#2563eb","#3b82f6","#60a5fa","#93c5fd","#1d4ed8","#1e3a8a"];
html`<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:2rem;">
  ${themes.slice(0,4).map((t, i) => html`<a href="./themes" style="text-decoration:none;">
    <div class="theme-card" style="border-top-color:${colors[i % colors.length]};">
      <div style="font-size:1.4rem;margin-bottom:6px;">${icons[i % icons.length]}</div>
      <div style="font-weight:700;color:#1e293b;font-size:13px;margin-bottom:4px;">${t.title}</div>
      <div style="font-size:11px;color:#64748b;">${t.incident_count.toLocaleString()} incidents</div>
    </div>
  </a>`)}
</div>`
```

<div style="text-align:center;margin-bottom:2rem;">
  <a href="./map" style="display:inline-block;background:#1e40af;color:#fff;padding:10px 24px;border-radius:6px;text-decoration:none;font-weight:600;font-size:13px;">🗺️ Explore the Incident Map</a>
</div>

## Monthly Trend

```js
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
```

## Lighting Conditions

```js
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
```
