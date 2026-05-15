---
title: Incident Themes
---

```js
import * as Plot from "npm:@observablehq/plot";
const themes = await FileAttachment("data/themes.json").json();

function severityScore(t) {
  const sb = t.severity_breakdown || {};
  const total = Object.values(sb).reduce((a,b) => a+b, 0) || 1;
  return ((sb["Very Serious"] || 0) * 1.0 + (sb["Serious"] || 0) * 0.5) / total;
}

const sorted = [...themes].sort((a,b) => b.incident_count - a.incident_count);
const top30 = sorted.slice(0, 30).map(d => ({
  ...d,
  label: d.title.length > 48 ? d.title.slice(0, 48) + "…" : d.title
}));
```

# Incident Themes

AI-identified clusters of similar incidents. **${themes.length} themes** across **${themes.reduce((s,t) => s + (t.incident_count||0), 0).toLocaleString()} incidents**.

## Top 30 Themes by Volume

```js
Plot.plot({
  height: Math.max(200, top30.length * 28),
  marginLeft: 330,
  marginRight: 50,
  x: {label: "Incidents"},
  marks: [
    Plot.barX(top30, {
      x: "incident_count",
      y: "label",
      fill: d => severityScore(d) > 0.2 ? "#dc2626" : severityScore(d) > 0.05 ? "#d97706" : "#1e40af",
      title: d => d.title,
      tip: true,
      sort: {y: "-x"}
    }),
    Plot.text(top30, {
      x: "incident_count",
      y: "label",
      text: d => d.incident_count.toLocaleString(),
      dx: 5, fontSize: 10, fill: "#64748b",
      sort: {y: "-x"}
    })
  ]
})
```

<div style="font-size:11px;color:#94a3b8;margin-top:4px;">
  Colour: <span style="color:#dc2626;">■</span> High severity &nbsp;
  <span style="color:#d97706;">■</span> Medium &nbsp;
  <span style="color:#1e40af;">■</span> Low &nbsp;·&nbsp;
  Showing top 30 of ${themes.length} themes. Use search below to find any theme.
</div>

---

## Theme Details

```js
// `view()` makes `search` a reactive variable — the card cell below re-runs on change
const search = view(Inputs.search(sorted, {
  placeholder: "Search all ${themes.length} themes by title or description…",
  columns: ["title", "description"],
  label: null,
  width: "100%"
}));
```

```js
// This cell re-runs reactively whenever search changes
{
  const COLORS = ["#1e40af","#2563eb","#3b82f6","#1d4ed8","#0284c7","#0369a1","#1e3a8a"];
  let expandedId = null;
  const container = document.createElement("div");
  container.style.marginTop = "12px";

  function renderCards(themesToShow) {
    while (container.firstChild) container.removeChild(container.firstChild);

    if (themesToShow.length === 0) {
      const empty = document.createElement("p");
      empty.style.cssText = "color:#94a3b8;font-size:13px;padding:20px 0;";
      empty.textContent = "No themes match your search.";
      container.appendChild(empty);
      return;
    }

    themesToShow.forEach(t => {
      const color = COLORS[Math.abs(t.theme_id ?? 0) % COLORS.length];
      const card = document.createElement("div");
      card.style.cssText = "background:#fff;border:1px solid #e2e8f0;border-radius:8px;margin-bottom:10px;overflow:hidden;";

      // Header
      const hdr = document.createElement("div");
      hdr.style.cssText = `padding:12px 16px;cursor:pointer;display:flex;justify-content:space-between;align-items:center;border-left:4px solid ${color};`;
      hdr.addEventListener("click", () => {
        expandedId = expandedId === t.theme_id ? null : t.theme_id;
        renderCards(themesToShow);
      });

      const titleWrap = document.createElement("div");
      const titleEl = document.createElement("div");
      titleEl.style.cssText = "font-weight:600;font-size:14px;color:#1e293b;";
      titleEl.textContent = t.title;
      const metaEl = document.createElement("div");
      metaEl.style.cssText = "font-size:11px;color:#64748b;margin-top:3px;display:flex;gap:12px;";
      const countSpan = document.createElement("span");
      countSpan.textContent = (t.incident_count ?? 0).toLocaleString() + " incidents";
      metaEl.appendChild(countSpan);
      const vs = (t.severity_breakdown || {})["Very Serious"] || 0;
      if (vs > 0) {
        const sevSpan = document.createElement("span");
        sevSpan.style.color = "#dc2626";
        sevSpan.textContent = vs + " very serious";
        metaEl.appendChild(sevSpan);
      }
      titleWrap.append(titleEl, metaEl);
      const chevron = document.createElement("span");
      chevron.style.cssText = "color:#94a3b8;font-size:12px;margin-left:12px;flex-shrink:0;";
      chevron.textContent = expandedId === t.theme_id ? "▲" : "▼";
      hdr.append(titleWrap, chevron);
      card.appendChild(hdr);

      // Expanded body
      if (expandedId === t.theme_id) {
        const body = document.createElement("div");
        body.style.cssText = "padding:16px;border-top:1px solid #f1f5f9;background:#fafafa;";

        // Description
        const descEl = document.createElement("p");
        descEl.style.cssText = "color:#475569;font-size:13px;line-height:1.65;margin:0 0 16px;";
        descEl.textContent = t.description;
        body.appendChild(descEl);

        // Factor grid
        const grid = document.createElement("div");
        grid.style.cssText = "display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:14px;";

        const factorCol = document.createElement("div");
        const factorLabel = document.createElement("div");
        factorLabel.style.cssText = "font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px;";
        factorLabel.textContent = "Contributing Factor Types";
        factorCol.appendChild(factorLabel);
        Object.entries(t.top_contributing_factor_types || {}).sort((a,b) => b[1]-a[1]).forEach(([type, pct]) => {
          const row = document.createElement("div");
          row.style.marginBottom = "6px";
          const rowLabel = document.createElement("div");
          rowLabel.style.cssText = "display:flex;justify-content:space-between;font-size:11px;margin-bottom:2px;";
          const ts = document.createElement("span"); ts.style.cssText = "color:#475569;text-transform:capitalize;"; ts.textContent = type;
          const ps = document.createElement("span"); ps.style.cssText = "font-weight:600;color:#1e293b;"; ps.textContent = Math.round(pct*100)+"%";
          rowLabel.append(ts, ps);
          const bw = document.createElement("div"); bw.style.cssText = "height:4px;background:#f1f5f9;border-radius:2px;";
          const b = document.createElement("div"); b.style.cssText = `height:100%;background:${color};border-radius:2px;width:${Math.round(pct*100)}%;`;
          bw.appendChild(b);
          row.append(rowLabel, bw);
          factorCol.appendChild(row);
        });

        const flagCol = document.createElement("div");
        const flagLabel = document.createElement("div");
        flagLabel.style.cssText = "font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px;";
        flagLabel.textContent = "Human Factor Flags";
        flagCol.appendChild(flagLabel);
        [
          {label: "Fatigue",        pct: t.fatigue_factor_pct},
          {label: "Training gap",   pct: t.training_factor_pct},
          {label: "PPE issue",      pct: t.ppe_factor_pct},
          {label: "Communication",  pct: t.communication_factor_pct},
          {label: "Weather factor", pct: t.weather_factor_pct},
          {label: "Night lighting", pct: t.lighting_factor_pct},
        ].filter(f => (f.pct ?? 0) > 0).forEach(f => {
          const row = document.createElement("div");
          row.style.cssText = "display:flex;justify-content:space-between;font-size:11px;margin-bottom:5px;";
          const lbl = document.createElement("span"); lbl.style.color = "#475569"; lbl.textContent = f.label;
          const val = document.createElement("span");
          const p = f.pct ?? 0;
          val.style.cssText = "font-weight:600;color:" + (p > 0.3 ? "#dc2626" : p > 0.15 ? "#d97706" : "#1e293b") + ";";
          val.textContent = Math.round(p * 100) + "%";
          row.append(lbl, val);
          flagCol.appendChild(row);
        });

        grid.append(factorCol, flagCol);
        body.appendChild(grid);

        if (t.solas_chapters?.length) {
          const solasBox = document.createElement("div");
          solasBox.style.cssText = "background:#eff6ff;border-radius:4px;padding:10px 12px;margin-bottom:12px;font-size:11px;color:#1e40af;line-height:1.5;";
          const sl = document.createElement("span"); sl.style.cssText = "font-weight:700;text-transform:uppercase;font-size:10px;letter-spacing:0.5px;margin-right:6px;"; sl.textContent = "SOLAS:";
          solasBox.appendChild(sl);
          solasBox.appendChild(document.createTextNode(t.solas_chapters.join(" · ")));
          body.appendChild(solasBox);
        }

        if (t.preventable_by?.length) {
          const prevBox = document.createElement("div");
          prevBox.style.cssText = "background:#f0fdf4;border-radius:4px;padding:10px 12px;margin-bottom:12px;";
          const pl = document.createElement("div"); pl.style.cssText = "font-size:10px;font-weight:700;color:#166534;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;"; pl.textContent = "Preventable by";
          const pul = document.createElement("ul"); pul.style.cssText = "margin:0;padding-left:16px;font-size:12px;color:#475569;line-height:1.6;";
          t.preventable_by.forEach(p => { const li = document.createElement("li"); li.textContent = p; pul.appendChild(li); });
          prevBox.append(pl, pul);
          body.appendChild(prevBox);
        }

        if ((t.representative_cases ?? []).length > 0) {
          const cl = document.createElement("div"); cl.style.cssText = "font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px;"; cl.textContent = "Representative Cases";
          body.appendChild(cl);
          t.representative_cases.slice(0,5).forEach(c => {
            const cb = document.createElement("div"); cb.style.cssText = "border:1px solid #e2e8f0;border-radius:4px;padding:8px 10px;margin-bottom:6px;background:#fff;";
            const cm = document.createElement("div"); cm.style.cssText = "font-size:10px;color:#94a3b8;margin-bottom:3px;"; cm.textContent = (c.severity ?? "Unknown") + " · " + (c.id ?? "").slice(0,8);
            const cd = document.createElement("div"); cd.style.cssText = "font-size:11px;color:#475569;line-height:1.5;"; cd.textContent = (c.description ?? "").slice(0,300);
            cb.append(cm, cd);
            body.appendChild(cb);
          });
        }

        card.appendChild(body);
      }
      container.appendChild(card);
    });
  }

  renderCards(search);
  display(container);
}
```
