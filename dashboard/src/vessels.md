---
title: Vessels & People
---

# Vessels & People

```js
import * as Plot from "npm:@observablehq/plot";
const vessels = await FileAttachment("data/vessels.json").json();
const casualties = await FileAttachment("data/casualties.json").json();
```

## Vessel Categories

```js
const vesselData = Object.entries(vessels.by_category)
  .map(([category, count]) => ({category, count}))
  .sort((a,b) => b.count - a.count);

Plot.plot({
  height: 250,
  marginLeft: 80,
  x: {label: "Incidents"},
  marks: [
    Plot.barX(vesselData, {x: "count", y: "category", fill: "#1e40af", tip: true, sort: {y: "-x"}})
  ]
})
```

## People Affected

```js
html`<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;">
  <div class="stat-card"><div class="value">${casualties.total_affected.toLocaleString()}</div><div class="label">Total Affected</div></div>
  <div class="stat-card"><div class="value">${Math.round(casualties.ppe_used_pct * 100)}%</div><div class="label">PPE Used</div></div>
  <div class="stat-card"><div class="value">${Math.round(casualties.on_duty_pct * 100)}%</div><div class="label">On Duty</div></div>
</div>`
```
