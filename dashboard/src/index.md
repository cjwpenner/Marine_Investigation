---
title: Marine Safety Observatory
---

```js
import * as Plot from "npm:@observablehq/plot";
import {SEVERITY_COLORS, SEVERITY_ORDER, LIGHT_COLORS, severityColor} from "./components/colors.js";

const summary = await FileAttachment("data/summary.json").json();
const themes = await FileAttachment("data/themes.json").json();
const timeSeries = await FileAttachment("data/time_series.json").json();
const weatherStats = await FileAttachment("data/weather_stats.json").json();
const casualties = await FileAttachment("data/casualties.json").json();

const totalIncidents = summary.total_incidents;
const totalCasualties = Number(casualties.total_affected);
const nightPct = Math.round(summary.night_twilight_count / totalIncidents * 100);
const weatherPct = Math.round(summary.weather_factor_count / totalIncidents * 100);
const themeCount = themes.length;
const sortedThemes = [...themes].sort((a, b) => b.incident_count - a.incident_count);

const yearRange = summary.year_min ? `${summary.year_min}–${summary.year_max}` : "";

function themeSeverity(t) {
  const sb = t.severity_breakdown || {};
  const total = Object.values(sb).reduce((a, b) => a + b, 0) || 1;
  const score = ((sb["Very Serious"] || 0) + (sb["Serious"] || 0) * 0.5) / total;
  return score > 0.2 ? {label: "High severity", color: SEVERITY_COLORS["Very Serious"]}
       : score > 0.05 ? {label: "Med severity", color: SEVERITY_COLORS["Serious"]}
       : {label: "Low severity", color: SEVERITY_COLORS["Less Serious"]};
}

// monthly stacked severity series, with real dates for a proper time axis
const stackData = timeSeries.flatMap(d => {
  const date = new Date(d.year_month + "-01T00:00:00Z");
  return [
    {date, count: d.less_serious, severity: "Less Serious"},
    {date, count: d.serious, severity: "Serious"},
    {date, count: d.very_serious, severity: "Very Serious"},
  ];
});
```

<div class="mio-hero">
  <p class="mio-hero-kicker">UK Waters &amp; Beyond · ${yearRange} · MAIB Open Data</p>
  <h1>Marine Incident Analysis</h1>
  <p>AI-assisted analysis of reported marine incidents. Explore where accidents happen, what causes them, and how weather, lighting and human factors contribute.</p>
  <div class="mio-kpis">
    <div class="mio-kpi"><div class="value">${totalIncidents.toLocaleString()}</div><div class="label">Incidents</div></div>
    <div class="mio-kpi"><div class="value">${totalCasualties.toLocaleString()}</div><div class="label">Casualties</div></div>
    <div class="mio-kpi"><div class="value">${nightPct}%</div><div class="label">Night / Twilight</div></div>
    <div class="mio-kpi"><div class="value">${weatherPct}%</div><div class="label">Weather Factor</div></div>
    <div class="mio-kpi"><div class="value">${themeCount}</div><div class="label">Themes</div></div>
  </div>
</div>

<div class="mio-grid mio-grid-2-1">
<div>

<p class="mio-kicker">Top Incident Themes</p>

```js
html`<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
  ${sortedThemes.slice(0, 4).map((t, i) => {
    const sev = themeSeverity(t);
    return html`<a href="./themes" style="text-decoration:none;">
      <div class="mio-theme-card">
        <div class="rank">${i + 1}</div>
        <div>
          <div class="title">${t.title}</div>
          <div class="meta">${(t.incident_count ?? 0).toLocaleString()} incidents ·
            <span class="mio-chip"><span class="dot" style="background:${sev.color}"></span>${sev.label}</span>
          </div>
        </div>
      </div>
    </a>`;
  })}
</div>`
```

<div style="text-align:center;margin-top:14px;">
  <a href="./themes" class="mio-btn">View all ${themeCount} themes →</a>
</div>

</div>
<div>

<p class="mio-kicker">Lighting at Time of Incident</p>

```js
{
  const lightData = Object.entries(weatherStats.by_natural_light)
    .map(([k, v]) => ({light: k, count: v}))
    .filter(d => d.light !== "Unknown" && d.light !== "Unknown NL" && d.count > 0)
    .sort((a, b) => b.count - a.count);
  const totalLight = lightData.reduce((s, d) => s + d.count, 0);

  const container = document.createElement("div");

  const bar = document.createElement("div");
  bar.className = "mio-distbar";
  lightData.forEach(d => {
    const seg = document.createElement("div");
    const pct = d.count / totalLight * 100;
    seg.style.cssText = `width:${pct}%;background:${LIGHT_COLORS[d.light] ?? "#8d99a6"};`;
    seg.title = `${d.light}: ${d.count.toLocaleString()} (${Math.round(pct)}%)`;
    bar.appendChild(seg);
  });
  container.appendChild(bar);

  lightData.forEach(d => {
    const pct = Math.round(d.count / totalLight * 100);
    const row = document.createElement("div");
    row.className = "mio-legend-row";
    const left = document.createElement("div");
    left.style.cssText = "display:flex;align-items:center;gap:8px;";
    const dot = document.createElement("div");
    dot.className = "swatch";
    dot.style.background = LIGHT_COLORS[d.light] ?? "#8d99a6";
    const lbl = document.createElement("span");
    lbl.className = "name";
    lbl.textContent = d.light;
    left.append(dot, lbl);
    const right = document.createElement("div");
    const cnt = document.createElement("span");
    cnt.className = "count";
    cnt.textContent = d.count.toLocaleString();
    const pctEl = document.createElement("span");
    pctEl.className = "pct";
    pctEl.textContent = pct + "%";
    right.append(cnt, pctEl);
    row.append(left, right);
    container.appendChild(row);
  });

  display(container);
}
```

</div>
</div>

<p class="mio-kicker">Monthly Incidents by Severity</p>

```js
resize((width) => Plot.plot({
  width,
  height: 240,
  marginLeft: 40,
  x: {label: null},
  y: {label: "Incidents"},
  color: {
    domain: SEVERITY_ORDER,
    range: SEVERITY_ORDER.map(s => SEVERITY_COLORS[s]),
    legend: true
  },
  marks: [
    Plot.rectY(stackData, {
      x: "date", y: "count", fill: "severity", interval: "month", tip: true,
      order: SEVERITY_ORDER
    }),
    Plot.ruleY([0])
  ]
}))
```

<div style="text-align:center;margin-top:1.6rem;">
  <a href="./map" class="mio-btn">Explore the Incident Map</a>
  <a href="./trends" class="mio-btn secondary" style="margin-left:10px;">View Trends</a>
</div>
