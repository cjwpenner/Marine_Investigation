---
title: Trends
---

```js
import * as Plot from "npm:@observablehq/plot";
import {SEVERITY_COLORS, SEVERITY_ORDER, LIGHT_COLORS, BAR_COLOR, BAR_COLOR_DARK} from "./components/colors.js";

const timeSeries = await FileAttachment("data/time_series.json").json();
const weatherStats = await FileAttachment("data/weather_stats.json").json();
const summary = await FileAttachment("data/summary.json").json();

const isUnknown = s => /^unknown/i.test(s ?? "");

// Lighting conditions (exclude Unknown)
const lightData = Object.entries(weatherStats.by_natural_light)
  .map(([k, v]) => ({light: k, count: v}))
  .filter(d => !isUnknown(d.light) && d.light !== "Unknown NL")
  .sort((a, b) => b.count - a.count);

// Sea state — Douglas scale order, short labels, Unknown excluded
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
const shortSeaState = s => {
  const m = s.match(/^(\d+) - ([^-]+?) - \((.+)\)$/);
  return m ? `${m[1]} ${m[2].trim()} (${m[3].trim()})` : s;
};
const seaStateData = SEA_STATE_ORDER
  .filter(k => (weatherStats.by_sea_state ?? {})[k] > 0)
  .map(k => ({state: shortSeaState(k), count: weatherStats.by_sea_state[k]}));

// Wind force — "F0"–"F12", numeric order
const windForceData = Object.entries(weatherStats.by_wind_force ?? {})
  .filter(([k]) => !/unknown/i.test(k))
  .map(([k, v]) => {
    const match = k.match(/^(\d+)/);
    return {label: match ? "F" + match[1] : k, force: match ? +match[1] : 99, count: v};
  })
  .sort((a, b) => a.force - b.force);
const windDomain = windForceData.map(d => d.label);

// Weather type (exclude Unknown variants)
const weatherTypeData = Object.entries(weatherStats.by_weather_type ?? {})
  .map(([k, v]) => ({type: k, count: v}))
  .filter(d => !isUnknown(d.type))
  .sort((a, b) => b.count - a.count);

// Visibility — short labels, best → worst
const VIS_ORDER = [
  "Very good - Vis >= 25.0 nm",
  "Good - 5.0 <= Vis < 25.0 nm",
  "Moderate - 2.0 <=Vis < 5.0 nm",
  "Poor - 0.5 <=Vis < 2.0 nm",
  "Very poor - Vis < 0.5 nm"
];
const shortVis = s => s.split(" - ")[0];
const visibilityData = VIS_ORDER
  .filter(k => (weatherStats.by_visibility ?? {})[k] > 0)
  .map(k => ({vis: shortVis(k), count: weatherStats.by_visibility[k]}));
const visDomain = visibilityData.map(d => d.vis);

// Night incidents by category (Night + Twilight), pre-aggregated at export time
const overallNightPct = summary.overall_night_pct;
const prettyCat = c => (c[0].toUpperCase() + c.slice(1)).replace(/_/g, " ");
const nightByCat = summary.night_by_category
  .filter(d => d.total >= 20)
  .map(d => ({...d, cat: prettyCat(d.cat)}))
  .sort((a, b) => b.night_pct - a.night_pct);

// time series with real dates
const monthly = timeSeries.map(d => ({...d, date: new Date(d.year_month + "-01T00:00:00Z")}));
const years = [...new Set(timeSeries.map(d => d.year_month.slice(0, 4)))].sort();
const minYear = years[0] ?? "2010";
const maxYear = years[years.length - 1] ?? "2024";
```

# Trends

How incident volume, severity, lighting and weather conditions have shifted across fifteen years of MAIB reports.

<div style="display:flex;gap:1.2rem;flex-wrap:wrap;align-items:center;margin:1rem 0 0.4rem;">

```js
const fromYear = view(Inputs.select(years, {label: "From year", value: minYear}));
```

```js
const toYear = view(Inputs.select(years, {label: "To year", value: maxYear}));
```

</div>

## Incidents per Month

```js
const stackData = monthly
  .filter(d => d.year_month >= fromYear && d.year_month <= toYear + "-99")
  .flatMap(d => [
    {date: d.date, count: d.less_serious, severity: "Less Serious"},
    {date: d.date, count: d.serious, severity: "Serious"},
    {date: d.date, count: d.very_serious, severity: "Very Serious"},
  ]);
```

```js
resize((width) => Plot.plot({
  width,
  height: 260,
  marginLeft: 40,
  x: {label: null},
  y: {label: "Incidents"},
  color: {domain: SEVERITY_ORDER, range: SEVERITY_ORDER.map(s => SEVERITY_COLORS[s]), legend: true},
  marks: [
    Plot.rectY(stackData, {x: "date", y: "count", fill: "severity", interval: "month", tip: true, order: SEVERITY_ORDER}),
    Plot.ruleY([0])
  ]
}))
```

<div class="mio-grid mio-grid-2" style="margin-top:2rem;">
<div class="mio-panel">

## Lighting Conditions

```js
resize((width) => Plot.plot({
  width,
  height: 96,
  marginLeft: 10,
  x: {label: "Incidents"},
  color: {
    domain: ["Daylight", "Twilight", "Night"],
    range: [LIGHT_COLORS.Daylight, LIGHT_COLORS.Twilight, LIGHT_COLORS.Night],
    legend: true
  },
  marks: [
    Plot.barX(lightData, Plot.stackX({x: "count", fill: "light", tip: true,
      order: ["Daylight", "Twilight", "Night"], insetRight: 2}))
  ]
}))
```

</div>
<div class="mio-panel">

## Sea State at Incident

```js
resize((width) => Plot.plot({
  width,
  height: 230,
  marginLeft: 150,
  x: {label: "Incidents"},
  y: {label: null},
  marks: [
    Plot.barX(seaStateData, {x: "count", y: "state", fill: BAR_COLOR, tip: true, sort: {y: null}})
  ]
}))
```

</div>
</div>

<div class="mio-grid mio-grid-2">
<div class="mio-panel">

## Wind Force (Beaufort)

```js
resize((width) => Plot.plot({
  width,
  height: 210,
  marginLeft: 40,
  x: {label: "Beaufort force", domain: windDomain},
  y: {label: "Incidents"},
  marks: [
    Plot.barY(windForceData, {x: "label", y: "count", fill: BAR_COLOR, tip: true})
  ]
}))
```

</div>
<div class="mio-panel">

## Weather Conditions

```js
resize((width) => Plot.plot({
  width,
  height: 210,
  marginLeft: 70,
  x: {label: "Incidents"},
  y: {label: null},
  marks: [
    Plot.barX(weatherTypeData, {x: "count", y: "type", fill: BAR_COLOR, tip: true, sort: {y: "-x"}})
  ]
}))
```

</div>
</div>

<div class="mio-grid mio-grid-2">
<div class="mio-panel">

## Visibility at Incident

```js
resize((width) => Plot.plot({
  width,
  height: 190,
  marginLeft: 74,
  x: {label: "Incidents"},
  y: {label: null, domain: visDomain},
  marks: [
    Plot.barX(visibilityData, {x: "count", y: "vis", fill: BAR_COLOR, tip: true})
  ]
}))
```

</div>
<div class="mio-panel">

## Weather Factor by Month

```js
resize((width) => Plot.plot({
  width,
  height: 190,
  marginLeft: 40,
  x: {label: null, tickFormat: d => ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][d], ticks: 12},
  y: {label: "% with weather factor", percent: true},
  marks: [
    Plot.areaY(weatherStats.weather_factor_by_month, {x: "month", y: "pct", fill: BAR_COLOR, fillOpacity: 0.14}),
    Plot.lineY(weatherStats.weather_factor_by_month, {x: "month", y: "pct", stroke: BAR_COLOR_DARK, strokeWidth: 2}),
    Plot.dot(weatherStats.weather_factor_by_month, {x: "month", y: "pct", fill: BAR_COLOR_DARK, r: 3, tip: true})
  ]
}))
```

</div>
</div>

## Night Incident % over Time

```js
resize((width) => Plot.plot({
  width,
  height: 200,
  marginLeft: 40,
  x: {label: null},
  y: {label: "Night / twilight %", percent: true},
  marks: [
    Plot.ruleY([overallNightPct], {stroke: "#8d99a6", strokeDasharray: "4,3"}),
    Plot.lineY(monthly, {x: "date", y: "night_pct", stroke: BAR_COLOR_DARK, strokeWidth: 1.6, curve: "monotone-x", tip: true})
  ]
}))
```

## Night Incidents by Category

Categories whose bar crosses the dashed line see more night-time incidents than the overall average (${Math.round(overallNightPct * 100)}%).

```js
resize((width) => Plot.plot({
  width,
  height: 260,
  marginLeft: 90,
  x: {label: "Night / twilight %", percent: true},
  y: {label: null},
  marks: [
    Plot.barX(nightByCat, {
      x: "night_pct", y: "cat",
      fill: d => d.night_pct > overallNightPct ? "#4b56a8" : "#3e6fb0",
      fillOpacity: d => d.night_pct > overallNightPct ? 1 : 0.55,
      tip: true, sort: {y: "-x"}
    }),
    Plot.ruleX([overallNightPct], {stroke: "#bb1e2d", strokeDasharray: "4,3"})
  ]
}))
```
