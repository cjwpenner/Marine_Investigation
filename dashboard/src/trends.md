---
title: Trends
---

```js
import * as Plot from "npm:@observablehq/plot";
const timeSeries = await FileAttachment("data/time_series.json").json();
const weatherStats = await FileAttachment("data/weather_stats.json").json();
const incidentsMap = await FileAttachment("data/incidents_map.json").json();

const lightData = Object.entries(weatherStats.by_natural_light)
  .map(([k,v]) => ({light: k, count: v}))
  .filter(d => d.light !== "Unknown")
  .sort((a,b) => b.count - a.count);

const waveData = Object.entries(weatherStats.by_wave_height_band)
  .map(([k,v]) => ({band: k, count: v}));
const WAVE_ORDER = ["0-0.5m","0.5-1.5m","1.5-2.5m","2.5-4m","4m+"];
waveData.sort((a,b) => WAVE_ORDER.indexOf(a.band) - WAVE_ORDER.indexOf(b.band));

const beaufortData = Object.entries(weatherStats.by_wind_force_beaufort ?? {})
  .map(([k, v]) => ({force: "F" + k, n: k, count: v}))
  .sort((a, b) => +a.n - +b.n);

// Night incidents by category
const catNight = {};
const catTotal = {};
for (const inc of incidentsMap) {
  const cat = inc.incident_category ?? "other";
  catTotal[cat] = (catTotal[cat] ?? 0) + 1;
  if (inc.natural_light === "Night" || inc.natural_light === "Dusk") {
    catNight[cat] = (catNight[cat] ?? 0) + 1;
  }
}
const overallNightPct = incidentsMap.filter(d => d.natural_light === "Night" || d.natural_light === "Dusk").length / Math.max(incidentsMap.length, 1);
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
Plot.plot({
  height: 240, marginLeft: 40,
  x: {label: null},
  y: {label: "Incidents"},
  marks: [
    Plot.barY(filtered, {x: "year_month", y: "less_serious", fill: "#bfdbfe", tip: true}),
    Plot.barY(filtered, {x: "year_month", y: "serious", fill: "#d97706", tip: true}),
    Plot.barY(filtered, {x: "year_month", y: "very_serious", fill: "#dc2626", tip: true}),
    Plot.ruleY([0])
  ]
})
```

<div style="display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;margin-top:2rem;">

<div>

## Lighting Conditions

```js
const LIGHT_COLORS = {Day: "#60a5fa", Night: "#1e293b", Dusk: "#d97706", Dawn: "#f59e0b"};
Plot.plot({
  height: 80, marginLeft: 10,
  x: {label: "Incidents", percent: false},
  color: {domain: ["Day","Night","Dusk","Dawn"], range: ["#60a5fa","#1e293b","#d97706","#f59e0b"], legend: true},
  marks: [
    Plot.barX(lightData, Plot.stackX({x: "count", fill: "light", tip: true,
      order: ["Day","Dusk","Dawn","Night"]}))
  ]
})
```

</div>

<div>

## Wave Height at Incident

```js
Plot.plot({
  height: 200, marginLeft: 80,
  x: {label: "Incidents"},
  marks: [
    Plot.barX(waveData, {x: "count", y: "band", fill: "#1e40af", tip: true})
  ]
})
```

</div></div>

## Wind Force Distribution (Beaufort)

```js
Plot.plot({
  height: 200, marginLeft: 40,
  x: {label: "Beaufort force"},
  y: {label: "Incidents"},
  marks: [
    Plot.barY(beaufortData, {x: "force", y: "count", fill: "#1e40af", tip: true})
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
    Plot.dot(timeSeries, {x: "year_month", y: "night_pct", fill: "#1e293b", tip: true})
  ]
})
```

## Night Incidents by Category

```js
Plot.plot({
  height: 250, marginLeft: 120,
  x: {label: "Night / dusk %", percent: true},
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
