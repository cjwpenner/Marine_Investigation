---
title: Trends
---

```js
import * as Plot from "npm:@observablehq/plot";
const timeSeries = await FileAttachment("data/time_series.json").json();
const weatherStats = await FileAttachment("data/weather_stats.json").json();
const incidentsMap = await FileAttachment("data/incidents_map.json").json();

// Lighting conditions (exclude Unknown)
const lightData = Object.entries(weatherStats.by_natural_light)
  .map(([k,v]) => ({light: k, count: v}))
  .filter(d => d.light !== "Unknown" && d.light !== "Unknown NL")
  .sort((a,b) => b.count - a.count);

// Sea state — sort by Douglas scale order
const SEA_STATE_ORDER = [
  "0 - Calm glassy - (0 m)",
  "1 - Calm rippled - (0 - 0.1 m)",
  "2 - Smooth - (0.1 - 0.5 m)",
  "3 - Slight - (0.5 - 1.25 m)",
  "4 - Moderate - (1.25 - 2.5 m)",
  "5 - Rough - (2.5 - 4 m)",
  "6 - Very rough - (4.0 - 6.0 m)",
  "7 - High - (6.0 - 9.0 m)",
  "8 - Very high - (9.0 - 14.0 m)",
  "9 - Phenomenal - (> 14.0 m)"
];
const seaStateData = Object.entries(weatherStats.by_sea_state ?? {})
  .map(([k,v]) => ({state: k, count: v}))
  .sort((a,b) => SEA_STATE_ORDER.indexOf(a.state) - SEA_STATE_ORDER.indexOf(b.state));

// Wind force — strip long label to just "F0"–"F12"
const windForceData = Object.entries(weatherStats.by_wind_force ?? {})
  .filter(([k]) => k !== "Beaufort scale: Unknown")
  .map(([k,v]) => {
    const match = k.match(/^(\d+)/);
    return {label: match ? "F" + match[1] : k, force: match ? +match[1] : 99, count: v};
  })
  .sort((a,b) => a.force - b.force);

// Weather type (exclude Unknown variants)
const weatherTypeData = Object.entries(weatherStats.by_weather_type ?? {})
  .map(([k,v]) => ({type: k, count: v}))
  .filter(d => !d.type.startsWith("Unknown"))
  .sort((a,b) => b.count - a.count);

// Visibility
const VIS_ORDER = [
  "Calm glassy - (0 m)",
  "Very good - Vis >= 25.0 nm",
  "Good - 5.0 <= Vis < 25.0 nm",
  "Moderate - 2.0 <=Vis < 5.0 nm",
  "Poor - 0.5 <=Vis < 2.0 nm",
  "Very poor - Vis < 0.5 nm"
];
const visibilityData = Object.entries(weatherStats.by_visibility ?? {})
  .map(([k,v]) => ({vis: k, count: v}))
  .filter(d => !d.vis.startsWith("Unknown"))
  .sort((a,b) => VIS_ORDER.indexOf(a.vis) - VIS_ORDER.indexOf(b.vis));

// Night incidents by category (Night + Twilight)
const catNight = {};
const catTotal = {};
for (const inc of incidentsMap) {
  const cat = inc.incident_category ?? "other";
  catTotal[cat] = (catTotal[cat] ?? 0) + 1;
  if (inc.natural_light === "Night" || inc.natural_light === "Twilight") {
    catNight[cat] = (catNight[cat] ?? 0) + 1;
  }
}
const overallNightPct = incidentsMap.filter(d => d.natural_light === "Night" || d.natural_light === "Twilight").length / Math.max(incidentsMap.length, 1);
const nightByCat = Object.entries(catTotal)
  .map(([cat, total]) => ({
    cat,
    total,
    night_pct: (catNight[cat] ?? 0) / total
  }))
  .filter(d => d.total >= 20)
  .sort((a, b) => b.night_pct - a.night_pct);

const years = [...new Set(timeSeries.map(d => d.year_month.slice(0, 4)))].sort();
const minYear = years[0] ?? "2010";
const maxYear = years[years.length - 1] ?? "2024";
```

# Trends

```js
const fromYear = view(Inputs.select(years, {label: "From year", value: minYear}));
const toYear = view(Inputs.select(years, {label: "To year", value: maxYear}));
```

## Incidents per Month

```js
const filtered = timeSeries.filter(d => d.year_month >= fromYear && d.year_month <= toYear + "-99");
const stackData = filtered.flatMap(d => [
  {year_month: d.year_month, count: d.less_serious,  severity: "Less Serious"},
  {year_month: d.year_month, count: d.serious,        severity: "Serious"},
  {year_month: d.year_month, count: d.very_serious,   severity: "Very Serious"},
]);
Plot.plot({
  height: 240, marginLeft: 40,
  x: {label: null},
  y: {label: "Incidents"},
  color: {domain: ["Less Serious","Serious","Very Serious"], range: ["#bfdbfe","#d97706","#dc2626"]},
  marks: [
    Plot.barY(stackData, Plot.stackY({x: "year_month", y: "count", fill: "severity", tip: true})),
    Plot.ruleY([0])
  ]
})
```

<div style="display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;margin-top:2rem;">

<div>

## Lighting Conditions

```js
Plot.plot({
  height: 80, marginLeft: 10,
  x: {label: "Incidents"},
  color: {domain: ["Daylight","Night","Twilight"], range: ["#60a5fa","#1e293b","#d97706"], legend: true},
  marks: [
    Plot.barX(lightData, Plot.stackX({x: "count", fill: "light", tip: true,
      order: ["Daylight","Twilight","Night"]}))
  ]
})
```

</div>

<div>

## Sea State at Incident

```js
Plot.plot({
  height: 220, marginLeft: 200,
  x: {label: "Incidents"},
  marks: [
    Plot.barX(seaStateData, {x: "count", y: "state", fill: "#1e40af", tip: true,
      sort: {y: null}})
  ]
})
```

</div></div>

<div style="display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;margin-top:2rem;">

<div>

## Wind Force (Beaufort)

```js
Plot.plot({
  height: 200, marginLeft: 40,
  x: {label: "Beaufort force"},
  y: {label: "Incidents"},
  marks: [
    Plot.barY(windForceData, {x: "label", y: "count", fill: "#1e40af", tip: true})
  ]
})
```

</div>

<div>

## Weather Conditions

```js
Plot.plot({
  height: 200, marginLeft: 80,
  x: {label: "Incidents"},
  marks: [
    Plot.barX(weatherTypeData, {x: "count", y: "type", fill: "#1e40af", tip: true,
      sort: {y: "-x"}})
  ]
})
```

</div></div>

## Visibility at Incident

```js
Plot.plot({
  height: 180, marginLeft: 220,
  x: {label: "Incidents"},
  marks: [
    Plot.barX(visibilityData, {x: "count", y: "vis", fill: "#1e40af", tip: true,
      sort: {y: null}})
  ]
})
```

## Weather Factor by Month

```js
Plot.plot({
  height: 180, marginLeft: 40,
  x: {label: "Month", tickFormat: d => ["","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][d]},
  y: {label: "% incidents with weather factor", percent: true},
  marks: [
    Plot.areaY(weatherStats.weather_factor_by_month, {x: "month", y: "pct", fill: "#bfdbfe", fillOpacity: 0.5}),
    Plot.lineY(weatherStats.weather_factor_by_month, {x: "month", y: "pct", stroke: "#1e40af", strokeWidth: 2}),
    Plot.dot(weatherStats.weather_factor_by_month, {x: "month", y: "pct", fill: "#1e40af", tip: true})
  ]
})
```

## Night Incident % by Month

```js
Plot.plot({
  height: 180, marginLeft: 40,
  x: {label: null},
  y: {label: "Night %", percent: true},
  marks: [
    Plot.lineY(timeSeries, {x: "year_month", y: "night_pct", stroke: "#1e293b", strokeWidth: 2}),
    Plot.dot(timeSeries, {x: "year_month", y: "night_pct", fill: "#1e293b", r: 2, tip: true})
  ]
})
```

## Night Incidents by Category

```js
Plot.plot({
  height: 250, marginLeft: 120,
  x: {label: "Night / twilight %", percent: true},
  marks: [
    Plot.barX(nightByCat, {
      x: "night_pct", y: "cat", fill: d => d.night_pct > overallNightPct ? "#1e293b" : "#60a5fa",
      tip: true, sort: {y: "-x"}
    }),
    Plot.ruleX([overallNightPct], {stroke: "#dc2626", strokeDasharray: "4,3",
      title: "Overall average"})
  ]
})
```
