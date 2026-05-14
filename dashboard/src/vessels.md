---
title: Vessels & People
---

```js
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
```

# Vessels & People

```js
{
  const wrapper = document.createElement("div");
  wrapper.style.cssText = "display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:2rem;";

  const cards = [
    {value: casualties.total_affected.toLocaleString(), label: "Total Affected", borderColor: "#1e40af"},
    {value: Math.round(casualties.ppe_deficient_pct*100) + "%", label: "PPE Deficient", borderColor: "#dc2626"},
    {value: Math.round(casualties.on_duty_pct*100) + "%", label: "On Duty", borderColor: "#1e40af"},
    {value: vessels.incidents_with_vessel_loss.toLocaleString(), label: "Vessel Losses", borderColor: "#1e40af"},
  ];

  cards.forEach(c => {
    const card = document.createElement("div");
    card.className = "stat-card";
    card.style.borderLeftColor = c.borderColor;
    const valEl = document.createElement("div");
    valEl.className = "value";
    valEl.textContent = c.value;
    const lblEl = document.createElement("div");
    lblEl.className = "label";
    lblEl.textContent = c.label;
    card.append(valEl, lblEl);
    wrapper.appendChild(card);
  });

  display(wrapper);
}
```

<div style="display:grid;grid-template-columns:2fr 1fr;gap:1.5rem;">

<div>

## By Vessel Type

```js
Plot.plot({
  height: 220, marginLeft: 110,
  x: {label: "Incidents"},
  marks: [Plot.barX(vesselCatData, {x:"count", y:"category", fill:"#1e40af", tip:true, sort:{y:"-x"}})]
})
```

</div><div>

## Casualties by Type

```js
Plot.plot({
  height: 220,
  marks: [Plot.barY(typeData, {x:"type", y:"count", fill:"#3b82f6", tip:true, sort:{x:"-y"}})]
})
```

</div></div>

<div style="display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;margin-top:1.5rem;">

<div>

## Age Distribution

```js
Plot.plot({
  height: 180, marginLeft: 50,
  x: {label: "Age band"},
  y: {label: "Persons"},
  marks: [Plot.barY(ageData, {x:"age", y:"count", fill:"#1e40af", tip:true})]
})
```

</div><div>

## Injury Types

```js
Plot.plot({
  height: 180, marginLeft: 110,
  x: {label: "Count"},
  marks: [Plot.barX(injuryData, {x:"count", y:"type", fill:"#3b82f6", tip:true, sort:{y:"-x"}})]
})
```

</div></div>

## Body Parts Injured

```js
Plot.plot({
  height: 200, marginLeft: 130,
  x: {label: "Count"},
  marks: [Plot.barX(bodyPartData, {x:"count", y:"part", fill:"#60a5fa", tip:true, sort:{y:"-x"}})]
})
```

## Top Flag States

```js
Plot.plot({
  height: 240,
  x: {label: "Flag state"},
  y: {label: "Incidents"},
  marks: [Plot.barY(vessels.by_flag_state.slice(0,15), {x:"flag", y:"count", fill:"#1e40af", tip:true, sort:{x:"-y"}})]
})
```
