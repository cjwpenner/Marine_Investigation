---
title: Vessels & People
---

```js
import * as Plot from "npm:@observablehq/plot";
import {BAR_COLOR, BAR_COLOR_DARK} from "./components/colors.js";

const vessels = await FileAttachment("data/vessels.json").json();
const casualties = await FileAttachment("data/casualties.json").json();

const truncate = (s, n = 38) => s.length > n ? s.slice(0, n) + "…" : s;

const vesselCatData = Object.entries(vessels.by_category)
  .map(([k, v]) => ({category: truncate(k, 35), count: v}))
  .sort((a, b) => b.count - a.count);

const injuryData = Object.entries(casualties.by_injury_type)
  .map(([k, v]) => ({type: truncate(k), count: v}))
  .sort((a, b) => b.count - a.count).slice(0, 12);

const bodyPartData = Object.entries(casualties.by_body_part)
  .map(([k, v]) => ({part: truncate(k.replace(/^.*-> /, ""), 34), count: v}))
  .sort((a, b) => b.count - a.count).slice(0, 12);

const AGE_ORDER = ["<25", "25-34", "35-44", "45-54", "55-64", "65+"];
const ageData = Object.entries(casualties.by_age_band)
  .map(([k, v]) => ({age: k, count: v}))
  .filter(d => d.age !== "Unknown");

const typeData = Object.entries(casualties.by_type)
  .map(([k, v]) => ({type: k, count: v}));

// PPE fields are sparsely recorded in the source data — present counts, not
// percentages of the whole population, to stay honest about coverage.
const ppeWorn = casualties.ppe_recorded_worn ?? null;
const ppeDeficient = casualties.ppe_deficiency_noted ?? null;
const onDutyPct = Math.round((casualties.on_duty_pct ?? 0) * 100);
```

# Vessels &amp; People

Who was involved: the vessels that had incidents, and the people injured aboard them.

<div class="mio-stats">
  <div class="stat-card">
    <div class="value">${(casualties.total_affected ?? 0).toLocaleString()}</div>
    <div class="label">People Affected</div>
  </div>
  <div class="stat-card" style="border-top-color:var(--sev-very);">
    <div class="value">${ppeDeficient == null ? "—" : ppeDeficient.toLocaleString()}</div>
    <div class="label">PPE Deficiency Noted</div>
    <div class="caveat">where investigators recorded PPE detail</div>
  </div>
  <div class="stat-card" style="border-top-color:#3a6c4a;">
    <div class="value">${ppeWorn == null ? "—" : ppeWorn.toLocaleString()}</div>
    <div class="label">PPE Recorded Worn</div>
    <div class="caveat">where investigators recorded PPE detail</div>
  </div>
  <div class="stat-card">
    <div class="value">${onDutyPct}%</div>
    <div class="label">On Duty</div>
    <div class="caveat">of records where duty status is known</div>
  </div>
  <div class="stat-card" style="border-top-color:var(--sev-serious);">
    <div class="value">${(vessels.incidents_with_vessel_loss ?? 0).toLocaleString()}</div>
    <div class="label">Vessel Losses</div>
  </div>
</div>

<div class="mio-grid mio-grid-2">
<div class="mio-panel">

## By Vessel Type

```js
resize((width) => Plot.plot({
  width,
  height: 220,
  marginLeft: 190,
  x: {label: "Incidents"},
  y: {label: null},
  marks: [Plot.barX(vesselCatData, {x: "count", y: "category", fill: BAR_COLOR, tip: true, sort: {y: "-x"}})]
}))
```

</div>
<div class="mio-panel">

## Casualties by Type

```js
resize((width) => Plot.plot({
  width,
  height: 220,
  x: {label: null},
  y: {label: "Persons"},
  marks: [Plot.barY(typeData, {x: "type", y: "count", fill: BAR_COLOR, tip: true, sort: {x: "-y"}})]
}))
```

</div>
</div>

<div class="mio-grid mio-grid-2">
<div class="mio-panel">

## Age Distribution

```js
resize((width) => Plot.plot({
  width,
  height: 200,
  marginLeft: 45,
  x: {label: "Age band", domain: AGE_ORDER},
  y: {label: "Persons"},
  marks: [Plot.barY(ageData, {x: "age", y: "count", fill: BAR_COLOR, tip: true})]
}))
```

</div>
<div class="mio-panel">

## Injury Types

```js
resize((width) => Plot.plot({
  width,
  height: 240,
  marginLeft: 210,
  x: {label: "Persons"},
  y: {label: null},
  marks: [Plot.barX(injuryData, {x: "count", y: "type", fill: BAR_COLOR, tip: true, sort: {y: "-x"}})]
}))
```

</div>
</div>

<div class="mio-grid mio-grid-2">
<div class="mio-panel">

## Body Parts Injured

```js
resize((width) => Plot.plot({
  width,
  height: 240,
  marginLeft: 190,
  x: {label: "Persons"},
  y: {label: null},
  marks: [Plot.barX(bodyPartData, {x: "count", y: "part", fill: BAR_COLOR, tip: true, sort: {y: "-x"}})]
}))
```

</div>
<div class="mio-panel">

## Top Flag States

```js
{
  const list = document.createElement("div");
  list.className = "mio-flagtable";
  const header = document.createElement("div");
  header.className = "hdr";
  ["#", "Flag State", "Incidents"].forEach(t => {
    const c = document.createElement("span");
    c.textContent = t;
    header.appendChild(c);
  });
  list.appendChild(header);
  vessels.by_flag_state.slice(0, 12).forEach((item, i) => {
    const row = document.createElement("div");
    row.className = "row";
    const rank = document.createElement("span");
    rank.className = "rank";
    rank.textContent = (i + 1) + ".";
    const flag = document.createElement("span");
    flag.className = "name";
    flag.textContent = item.flag;
    const count = document.createElement("span");
    count.className = "count";
    count.textContent = (item.count ?? 0).toLocaleString();
    row.append(rank, flag, count);
    list.appendChild(row);
  });
  display(list);
}
```

</div>
</div>
