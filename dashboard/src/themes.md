---
title: Incident Themes
---

```js
import * as Plot from "npm:@observablehq/plot";
const themes = await FileAttachment("data/themes.json").json();

// escapeHtml for safely rendering external data in html templates
const escapeHtml = str => str == null ? "" : String(str)
  .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
  .replace(/"/g, "&quot;").replace(/'/g, "&#039;");
```

# Incident Themes

AI-identified clusters of incidents with shared latent causes. Click any theme to expand.

## Theme Overview

```js
// Theme sizes as horizontal bar chart (safe fallback for treemap)
Plot.plot({
  height: Math.max(200, themes.length * 36),
  marginLeft: 220,
  x: {label: "Incidents"},
  marks: [
    Plot.barX(themes, {
      x: "incident_count",
      y: "title",
      fill: (d, i) => ["#1e40af","#2563eb","#3b82f6","#60a5fa","#93c5fd","#bfdbfe","#1d4ed8"][i % 7],
      tip: true,
      sort: {y: "-x"}
    })
  ]
})
```

## Theme Details

```js
// expandable theme cards — all dynamic data via textContent
const container = document.createElement("div");
let expandedId = null;

function renderCards() {
  while (container.firstChild) container.removeChild(container.firstChild);
  themes.forEach(t => {
    const card = document.createElement("div");
    card.style.cssText = "background:#fff;border:1px solid #e2e8f0;border-radius:8px;margin-bottom:12px;overflow:hidden;";

    const COLORS = ["#1e40af","#2563eb","#3b82f6","#60a5fa","#93c5fd","#bfdbfe","#1d4ed8"];
    const color = COLORS[t.theme_id % COLORS.length] ?? "#1e40af";

    // Header
    const hdr = document.createElement("div");
    hdr.style.cssText = `padding:14px 16px;cursor:pointer;display:flex;justify-content:space-between;align-items:center;border-top:3px solid ${color};`;
    hdr.addEventListener("click", () => {
      expandedId = expandedId === t.theme_id ? null : t.theme_id;
      renderCards();
    });

    const titleWrap = document.createElement("div");
    const titleEl = document.createElement("div");
    titleEl.style.cssText = "font-weight:700;font-size:14px;color:#1e293b;";
    titleEl.textContent = t.title;
    const countEl = document.createElement("div");
    countEl.style.cssText = "font-size:11px;color:#64748b;margin-top:2px;";
    countEl.textContent = t.incident_count.toLocaleString() + " incidents";
    titleWrap.append(titleEl, countEl);

    const chevron = document.createElement("span");
    chevron.style.color = "#94a3b8";
    chevron.textContent = expandedId === t.theme_id ? "▲" : "▼";
    hdr.append(titleWrap, chevron);
    card.appendChild(hdr);

    if (expandedId === t.theme_id) {
      const body = document.createElement("div");
      body.style.cssText = "padding:14px 16px;border-top:1px solid #f1f5f9;background:#fafafa;";

      // Description
      const descEl = document.createElement("p");
      descEl.style.cssText = "color:#475569;font-size:13px;line-height:1.6;margin-bottom:14px;";
      descEl.textContent = t.description;
      body.appendChild(descEl);

      // Factor grid
      const grid = document.createElement("div");
      grid.style.cssText = "display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:14px;";

      // Contributing factor types
      const factorCol = document.createElement("div");
      const factorLabel = document.createElement("div");
      factorLabel.style.cssText = "font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px;";
      factorLabel.textContent = "Contributing Factor Types";
      factorCol.appendChild(factorLabel);
      Object.entries(t.top_contributing_factor_types || {})
        .sort((a,b) => b[1]-a[1])
        .forEach(([type, pct]) => {
          const row = document.createElement("div");
          row.style.marginBottom = "5px";
          const rowLabel = document.createElement("div");
          rowLabel.style.cssText = "display:flex;justify-content:space-between;font-size:11px;margin-bottom:2px;";
          const typeSpan = document.createElement("span");
          typeSpan.style.cssText = "color:#475569;text-transform:capitalize;";
          typeSpan.textContent = type;
          const pctSpan = document.createElement("span");
          pctSpan.style.cssText = "font-weight:600;color:#1e293b;";
          pctSpan.textContent = Math.round(pct * 100) + "%";
          rowLabel.append(typeSpan, pctSpan);
          const barWrap = document.createElement("div");
          barWrap.style.cssText = "height:4px;background:#f1f5f9;border-radius:2px;";
          const bar = document.createElement("div");
          bar.style.cssText = `height:100%;background:${color};border-radius:2px;width:${Math.round(pct * 100)}%;`;
          barWrap.appendChild(bar);
          row.append(rowLabel, barWrap);
          factorCol.appendChild(row);
        });

      // Human factor flags
      const flagCol = document.createElement("div");
      const flagLabel = document.createElement("div");
      flagLabel.style.cssText = "font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px;";
      flagLabel.textContent = "Human Factor Flags";
      flagCol.appendChild(flagLabel);
      [
        {label: "Fatigue", pct: t.fatigue_factor_pct},
        {label: "Training gap", pct: t.training_factor_pct},
        {label: "PPE issue", pct: t.ppe_factor_pct},
        {label: "Communication", pct: t.communication_factor_pct},
      ].forEach(f => {
        const row = document.createElement("div");
        row.style.cssText = "display:flex;justify-content:space-between;font-size:11px;margin-bottom:5px;";
        const lbl = document.createElement("span");
        lbl.style.color = "#475569";
        lbl.textContent = f.label;
        const val = document.createElement("span");
        val.style.cssText = "font-weight:600;color:" + ((f.pct ?? 0) > 0.3 ? "#dc2626" : "#1e293b") + ";";
        val.textContent = Math.round((f.pct ?? 0) * 100) + "%";
        row.append(lbl, val);
        flagCol.appendChild(row);
      });

      // SOLAS
      if (t.solas_chapters?.length) {
        const solasEl = document.createElement("div");
        solasEl.style.cssText = "margin-top:10px;font-size:11px;color:#64748b;";
        const solasStrong = document.createElement("strong");
        solasStrong.textContent = "SOLAS: ";
        solasEl.appendChild(solasStrong);
        solasEl.appendChild(document.createTextNode(t.solas_chapters.join(", ")));
        flagCol.appendChild(solasEl);
      }

      grid.append(factorCol, flagCol);
      body.appendChild(grid);

      // Preventable by
      if (t.preventable_by?.length) {
        const prevBox = document.createElement("div");
        prevBox.style.cssText = "background:#f0fdf4;border-radius:4px;padding:10px;margin-bottom:12px;";
        const prevLabel = document.createElement("div");
        prevLabel.style.cssText = "font-size:10px;font-weight:700;color:#166534;text-transform:uppercase;margin-bottom:4px;";
        prevLabel.textContent = "Preventable by";
        const prevList = document.createElement("ul");
        prevList.style.cssText = "margin:0;padding-left:16px;font-size:11px;color:#475569;";
        t.preventable_by.forEach(p => {
          const li = document.createElement("li");
          li.textContent = p;
          prevList.appendChild(li);
        });
        prevBox.append(prevLabel, prevList);
        body.appendChild(prevBox);
      }

      // Representative cases
      const caseLabel = document.createElement("div");
      caseLabel.style.cssText = "font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px;";
      caseLabel.textContent = "Representative Cases";
      body.appendChild(caseLabel);
      (t.representative_cases ?? []).slice(0, 5).forEach(c => {
        const caseBox = document.createElement("div");
        caseBox.style.cssText = "border:1px solid #e2e8f0;border-radius:4px;padding:8px;margin-bottom:6px;background:#fff;";
        const caseMeta = document.createElement("div");
        caseMeta.style.cssText = "font-size:10px;color:#94a3b8;margin-bottom:3px;";
        caseMeta.textContent = (c.severity ?? "") + " · " + (c.id ?? "").slice(0, 8) + "...";
        const caseDesc = document.createElement("div");
        caseDesc.style.cssText = "font-size:11px;color:#475569;line-height:1.4;";
        caseDesc.textContent = (c.description ?? "").slice(0, 250);
        caseBox.append(caseMeta, caseDesc);
        body.appendChild(caseBox);
      });

      card.appendChild(body);
    }
    container.appendChild(card);
  });
  return container;
}

renderCards()
```
