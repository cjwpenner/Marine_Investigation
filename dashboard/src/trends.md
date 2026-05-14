---
title: Trends
---

```js
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
```

# Trends

## Incidents per Month

```js
Plot.plot({
  height: 240, marginLeft: 40,
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

<div style="display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;margin-top:2rem;">

<div>

## Lighting Conditions

```js
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

</div>

</div>

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
