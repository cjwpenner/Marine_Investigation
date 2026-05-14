---
title: Trends
---

# Trends

```js
import * as Plot from "npm:@observablehq/plot";
const timeSeries = await FileAttachment("data/time_series.json").json();
```

## Monthly Incident Counts

```js
Plot.plot({
  height: 300,
  marginLeft: 50,
  x: {label: null},
  y: {label: "Incidents"},
  marks: [
    Plot.barY(timeSeries, {x: "year_month", y: "total", fill: "#3b82f6", tip: true}),
    Plot.ruleY([0])
  ]
})
```
