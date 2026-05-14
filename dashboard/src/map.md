---
title: Incident Map
---

# Incident Map

```js
const incidents = await FileAttachment("data/incidents_map.json").json();
```

<div id="map-container" style="height:calc(100vh - 120px);"></div>

```js
// Map will be implemented with Leaflet
display(html`<p style="color:#64748b;font-style:italic;">Interactive map coming soon. ${incidents.length} incidents loaded.</p>`);
```
