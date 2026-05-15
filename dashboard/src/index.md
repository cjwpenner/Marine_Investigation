---
title: Marine Safety Observatory
---

```js
import * as Plot from "npm:@observablehq/plot";
const escapeHtml = str => str == null ? "" : String(str)
  .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
  .replace(/"/g, "&quot;").replace(/'/g, "&#039;");
const incidents = await FileAttachment("data/incidents_map.json").json();
const themes = await FileAttachment("data/themes.json").json();
const timeSeries = await FileAttachment("data/time_series.json").json();
const weatherStats = await FileAttachment("data/weather_stats.json").json();

const totalIncidents = incidents.length;
const casualties = await FileAttachment("data/casualties.json").json();
const totalCasualties = Number(casualties.total_affected);
const nightPct = Math.round(
  incidents.filter(d => d.natural_light === "Night" || d.natural_light === "Twilight").length
  / totalIncidents * 100
);
const weatherPct = Math.round(
  incidents.filter(d => d.weather_was_factor).length / totalIncidents * 100
);
const themeCount = themes.length;
```

<div style="background:linear-gradient(135deg,#1e3a8a 0%,#1e40af 60%,#2563eb 100%);padding:32px 24px;margin:-1rem -1rem 2rem;color:#fff;">
  <div style="font-size:11px;letter-spacing:2px;text-transform:uppercase;opacity:0.7;margin-bottom:8px;">UK Waters &amp; Beyond · 2010–2025 · MAIB Open Data</div>
  <h1 style="font-size:2rem;font-weight:800;margin:0 0 8px;color:#fff;">Marine Incident Analysis</h1>
  <p style="opacity:0.85;max-width:580px;margin:0 0 24px;line-height:1.6;">AI-assisted analysis of reported marine incidents. Explore where accidents happen, what causes them, and how weather, lighting and human factors contribute.</p>

```js
const labels = ["Incidents","Casualties","Night / Twilight","Weather Factor","Themes"];
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

<div style="display:grid;grid-template-columns:2fr 1fr;gap:1.5rem;margin-bottom:2rem;">

<div>

<p style="font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;color:#64748b;margin:0 0 12px;">Top Incident Themes</p>

```js
const icons = ["⚓","🚨","⚠️","🔧","🗺️","👥","🛟"];
const colors = ["#1e40af","#2563eb","#3b82f6","#60a5fa","#93c5fd","#1d4ed8","#1e3a8a"];
const sortedThemes = [...themes].sort((a,b) => b.incident_count - a.incident_count);
html`<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
  ${sortedThemes.slice(0,4).map((t, i) => html`<a href="./themes" style="text-decoration:none;">
    <div class="theme-card" style="border-top-color:${colors[i % colors.length]};">
      <div style="font-size:1.2rem;margin-bottom:4px;">${icons[i % icons.length]}</div>
      <div style="font-weight:700;color:#1e293b;font-size:12px;margin-bottom:3px;line-height:1.3;">${escapeHtml(t.title)}</div>
      <div style="font-size:11px;color:#64748b;">${escapeHtml(String(t.incident_count.toLocaleString()))} incidents</div>
    </div>
  </a>`)}
</div>`
```

<div style="text-align:center;margin-top:12px;">
  <a href="./themes" style="display:inline-block;background:#1e40af;color:#fff;padding:8px 20px;border-radius:6px;text-decoration:none;font-weight:600;font-size:12px;">View all ${themeCount} themes →</a>
</div>

</div>

<div>

<p style="font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;color:#64748b;margin:0 0 12px;">Lighting at Time of Incident</p>

```js
const LIGHT_COLORS = {
  "Daylight": "#60a5fa",
  "Twilight": "#d97706",
  "Night": "#1e293b",
  "Dawn": "#f59e0b",
};
const lightData = Object.entries(weatherStats.by_natural_light)
  .map(([k,v]) => ({light: k, count: v}))
  .filter(d => d.light !== "Unknown" && d.light !== "Unknown NL" && d.count > 0)
  .sort((a,b) => b.count - a.count);

const totalLight = lightData.reduce((s,d) => s + d.count, 0);

// Donut-style breakdown as a horizontal stacked bar with labels
{
  const container = document.createElement("div");

  // Stacked bar
  const bar = document.createElement("div");
  bar.style.cssText = "display:flex;height:28px;border-radius:6px;overflow:hidden;margin-bottom:14px;";
  lightData.forEach(d => {
    const seg = document.createElement("div");
    const pct = d.count / totalLight * 100;
    seg.style.cssText = `width:${pct}%;background:${LIGHT_COLORS[d.light] ?? "#94a3b8"};`;
    seg.title = `${d.light}: ${d.count.toLocaleString()} (${Math.round(pct)}%)`;
    bar.appendChild(seg);
  });
  container.appendChild(bar);

  // Legend rows
  lightData.forEach(d => {
    const pct = Math.round(d.count / totalLight * 100);
    const row = document.createElement("div");
    row.style.cssText = "display:flex;justify-content:space-between;align-items:center;margin-bottom:7px;font-size:13px;";
    const left = document.createElement("div");
    left.style.cssText = "display:flex;align-items:center;gap:8px;";
    const dot = document.createElement("div");
    dot.style.cssText = `width:11px;height:11px;border-radius:50%;background:${LIGHT_COLORS[d.light] ?? "#94a3b8"};flex-shrink:0;`;
    const lbl = document.createElement("span");
    lbl.style.cssText = "color:#475569;";
    lbl.textContent = d.light;
    left.append(dot, lbl);
    const right = document.createElement("div");
    right.style.cssText = "text-align:right;";
    const cnt = document.createElement("div");
    cnt.style.cssText = "font-weight:700;color:#1e293b;font-size:13px;";
    cnt.textContent = d.count.toLocaleString();
    const pctEl = document.createElement("div");
    pctEl.style.cssText = "font-size:10px;color:#94a3b8;";
    pctEl.textContent = pct + "%";
    right.append(cnt, pctEl);
    row.append(left, right);
    container.appendChild(row);
  });

  display(container);
}
```

</div></div>

<p style="font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;color:#64748b;margin:0 0 12px;">Monthly Incidents by Severity</p>

```js
const stackData = timeSeries.flatMap(d => [
  {year_month: d.year_month, count: d.less_serious,  severity: "Less Serious"},
  {year_month: d.year_month, count: d.serious,        severity: "Serious"},
  {year_month: d.year_month, count: d.very_serious,   severity: "Very Serious"},
]);
Plot.plot({
  height: 220,
  marginLeft: 40,
  x: {label: null},
  y: {label: "Incidents"},
  color: {
    domain: ["Less Serious","Serious","Very Serious"],
    range: ["#bfdbfe","#d97706","#dc2626"],
    legend: true
  },
  marks: [
    Plot.barY(stackData, Plot.stackY({x: "year_month", y: "count", fill: "severity", tip: true,
      order: ["Less Serious","Serious","Very Serious"]})),
    Plot.ruleY([0])
  ]
})
```

<div style="text-align:center;margin-top:1.5rem;">
  <a href="./map" style="display:inline-block;background:#1e40af;color:#fff;padding:10px 24px;border-radius:6px;text-decoration:none;font-weight:600;font-size:13px;margin-right:10px;">🗺️ Explore the Incident Map</a>
  <a href="./trends" style="display:inline-block;background:#fff;color:#1e40af;padding:10px 24px;border-radius:6px;text-decoration:none;font-weight:600;font-size:13px;border:1px solid #1e40af;">📈 View Trends</a>
</div>
