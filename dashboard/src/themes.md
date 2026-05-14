---
title: Incident Themes
---

# Incident Themes

```js
const themes = await FileAttachment("data/themes.json").json();
```

```js
html`<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;">
  ${themes.map(t => html`<div class="theme-card">
    <div style="font-weight:700;font-size:15px;margin-bottom:6px;">${t.title}</div>
    <div style="font-size:12px;color:#64748b;margin-bottom:8px;">${t.description}</div>
    <div style="font-weight:600;color:#1e40af;">${t.incident_count.toLocaleString()} incidents</div>
  </div>`)}
</div>`
```
