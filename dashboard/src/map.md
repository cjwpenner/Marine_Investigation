---
title: Incident Map
---

```js
import {createMap} from "./components/map-component.js";
const incidents = await FileAttachment("data/incidents_map.json").json();
```

<style>
#map-host {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 60px);
  margin: -1rem -1rem 0;
}
</style>

<div id="map-host"></div>

```js
// Load Leaflet and plugins from CDN before initialising the component
async function loadScript(src) {
  if (document.querySelector(`script[src="${src}"]`)) return;
  await new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.src = src; s.onload = resolve; s.onerror = reject;
    document.head.appendChild(s);
  });
}
await loadScript("https://unpkg.com/leaflet@1.9.4/dist/leaflet.js");
await loadScript("https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js");

const mcCss = document.createElement("link");
mcCss.rel = "stylesheet";
mcCss.href = "https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css";
document.head.appendChild(mcCss);
await loadScript("https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js");

const host = document.getElementById("map-host");
createMap(host, incidents);
```
