---
title: Vessels & People
---

```js
import * as Plot from "npm:@observablehq/plot";
const vessels = await FileAttachment("data/vessels.json").json();
const casualties = await FileAttachment("data/casualties.json").json();

const truncate = (s, n=38) => s.length > n ? s.slice(0, n) + "…" : s;

const vesselCatData = Object.entries(vessels.by_category)
  .map(([k,v]) => ({category: truncate(k, 35), count:v}))
  .sort((a,b) => b.count - a.count);

const injuryData = Object.entries(casualties.by_injury_type)
  .map(([k,v]) => ({type: truncate(k), count:v}))
  .sort((a,b) => b.count - a.count).slice(0,12);

const bodyPartData = Object.entries(casualties.by_body_part)
  .map(([k,v]) => ({part: truncate(k), count:v}))
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
  wrapper.style.cssText = "display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:2rem;";

  const cards = [
    {value: (casualties.total_affected ?? 0).toLocaleString(), label: "Total Affected", borderColor: "#1e40af"},
    {value: Math.round((casualties.ppe_deficient_pct ?? 0)*100) + "%", label: "PPE Deficient", borderColor: "#dc2626"},
    {value: Math.round((casualties.ppe_used_pct ?? 0)*100) + "%", label: "PPE Used", borderColor: "#16a34a"},
    {value: Math.round((casualties.on_duty_pct ?? 0)*100) + "%", label: "On Duty", borderColor: "#1e40af"},
    {value: (vessels.incidents_with_vessel_loss ?? 0).toLocaleString(), label: "Vessel Losses", borderColor: "#1e40af"},
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
  height: 220, marginLeft: 220,
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
  height: 220, marginLeft: 260,
  x: {label: "Count"},
  marks: [Plot.barX(injuryData, {x:"count", y:"type", fill:"#3b82f6", tip:true, sort:{y:"-x"}})]
})
```

</div></div>

## Body Parts Injured

```js
Plot.plot({
  height: 200, marginLeft: 260,
  x: {label: "Count"},
  marks: [Plot.barX(bodyPartData, {x:"count", y:"part", fill:"#60a5fa", tip:true, sort:{y:"-x"}})]
})
```

## Top Flag States

```js
{
  const list = document.createElement("div");
  list.style.cssText = "font-size:12px;";
  const header = document.createElement("div");
  header.style.cssText = "display:flex;justify-content:space-between;font-size:10px;font-weight:700;color:#94a3b8;text-transform:uppercase;padding-bottom:4px;border-bottom:1px solid #e2e8f0;margin-bottom:4px;";
  const hFlag = document.createElement("span"); hFlag.textContent = "Flag State";
  const hCount = document.createElement("span"); hCount.textContent = "Incidents";
  header.append(hFlag, hCount);
  list.appendChild(header);
  vessels.by_flag_state.slice(0, 15).forEach((item, i) => {
    const row = document.createElement("div");
    row.style.cssText = "display:flex;justify-content:space-between;align-items:center;padding:4px 0;border-bottom:1px solid #f8fafc;";
    const rank = document.createElement("span");
    rank.style.cssText = "color:#94a3b8;font-size:10px;min-width:18px;";
    rank.textContent = (i + 1) + ".";
    const flag = document.createElement("span");
    flag.style.cssText = "flex:1;padding-left:4px;color:#1e293b;";
    flag.textContent = item.flag;
    const count = document.createElement("span");
    count.style.cssText = "font-weight:600;color:#1e40af;min-width:40px;text-align:right;";
    count.textContent = (item.count ?? 0).toLocaleString();
    row.append(rank, flag, count);
    list.appendChild(row);
  });
  display(list);
}
```
