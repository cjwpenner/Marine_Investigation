---
title: Incident Themes
---

```js
import {SEVERITY_COLORS} from "./components/colors.js";
const themes = await FileAttachment("data/themes.json").json();

function severityScore(t) {
  const sb = t.severity_breakdown || {};
  const total = Object.values(sb).reduce((a, b) => a + b, 0) || 1;
  return ((sb["Very Serious"] || 0) * 1.0 + (sb["Serious"] || 0) * 0.5) / total;
}
const severityBand = t =>
  severityScore(t) > 0.2 ? {label: "High", color: SEVERITY_COLORS["Very Serious"]} :
  severityScore(t) > 0.05 ? {label: "Med", color: SEVERITY_COLORS["Serious"]} :
  {label: "Low", color: SEVERITY_COLORS["Less Serious"]};

const sorted = [...themes].sort((a, b) => b.incident_count - a.incident_count);
const top30 = sorted.slice(0, 30);
const maxCount = top30[0]?.incident_count || 1;
```

# Incident Themes

AI-identified clusters of similar incidents — **${themes.length} themes** across **${themes.reduce((s, t) => s + (t.incident_count || 0), 0).toLocaleString()} incidents**. Severity bands reflect each theme's share of Serious and Very Serious outcomes.

## Top 30 Themes by Volume

```js
{
  const table = document.createElement("div");
  table.className = "mio-ranktable";

  const hdr = document.createElement("div");
  hdr.className = "hdr";
  ["#", "Theme", "Incidents", "Severity"].forEach(t => {
    const c = document.createElement("div");
    c.textContent = t;
    hdr.appendChild(c);
  });
  table.appendChild(hdr);

  top30.forEach((d, i) => {
    const sev = severityBand(d);
    const pct = d.incident_count / maxCount;
    const row = document.createElement("div");
    row.className = "row";

    const rank = document.createElement("div");
    rank.className = "rank";
    rank.textContent = i + 1;

    const title = document.createElement("div");
    title.className = "title";
    title.textContent = d.title;

    const barWrap = document.createElement("div");
    barWrap.className = "barwrap";
    const track = document.createElement("div");
    track.className = "bartrack";
    const bar = document.createElement("div");
    bar.className = "bar";
    bar.style.cssText = `background:${sev.color};width:${Math.round(pct * 100)}%;`;
    track.appendChild(bar);
    const cnt = document.createElement("span");
    cnt.className = "count";
    cnt.textContent = d.incident_count.toLocaleString();
    barWrap.append(track, cnt);

    const sevCell = document.createElement("div");
    sevCell.className = "mio-chip";
    const sevDot = document.createElement("span");
    sevDot.className = "dot";
    sevDot.style.background = sev.color;
    const sevLabel = document.createElement("span");
    sevLabel.style.color = sev.color;
    sevLabel.textContent = sev.label;
    sevCell.append(sevDot, sevLabel);

    row.append(rank, title, barWrap, sevCell);
    table.appendChild(row);
  });

  const footer = document.createElement("div");
  footer.style.cssText = "font-size:11px;color:var(--ink-faint);padding:8px;";
  footer.textContent = `Showing top 30 of ${themes.length} themes. Use the search below to find any theme.`;
  table.appendChild(footer);

  display(table);
}
```

---

## Theme Details

```js
// `view()` makes `search` a reactive variable — the card cell below re-runs on change
const search = view(Inputs.search(sorted, {
  placeholder: `Search all ${sorted.length} themes by title or description…`,
  columns: ["title", "description"],
  label: null,
  width: "100%"
}));
```

```js
// This cell re-runs reactively whenever search changes
{
  let expandedId = null;
  const container = document.createElement("div");
  container.style.marginTop = "12px";

  function renderCards(themesToShow) {
    while (container.firstChild) container.removeChild(container.firstChild);

    if (themesToShow.length === 0) {
      const empty = document.createElement("p");
      empty.style.cssText = "color:var(--ink-faint);font-size:13px;padding:20px 0;";
      empty.textContent = "No themes match your search.";
      container.appendChild(empty);
      return;
    }

    themesToShow.forEach(t => {
      const sev = severityBand(t);
      const card = document.createElement("div");
      card.className = "mio-acc-card";

      // Header
      const hdr = document.createElement("div");
      hdr.className = "mio-acc-hdr";
      hdr.style.borderLeftColor = sev.color;
      hdr.addEventListener("click", () => {
        expandedId = expandedId === t.theme_id ? null : t.theme_id;
        renderCards(themesToShow);
      });

      const titleWrap = document.createElement("div");
      const titleEl = document.createElement("div");
      titleEl.className = "mio-acc-title";
      titleEl.textContent = t.title;
      const metaEl = document.createElement("div");
      metaEl.className = "mio-acc-meta";
      const countSpan = document.createElement("span");
      countSpan.textContent = (t.incident_count ?? 0).toLocaleString() + " incidents";
      metaEl.appendChild(countSpan);
      const vs = (t.severity_breakdown || {})["Very Serious"] || 0;
      if (vs > 0) {
        const sevSpan = document.createElement("span");
        sevSpan.className = "very-serious";
        sevSpan.textContent = vs + " very serious";
        metaEl.appendChild(sevSpan);
      }
      titleWrap.append(titleEl, metaEl);
      const chevron = document.createElement("span");
      chevron.className = "mio-acc-chevron";
      chevron.textContent = expandedId === t.theme_id ? "▲" : "▼";
      hdr.append(titleWrap, chevron);
      card.appendChild(hdr);

      // Expanded body
      if (expandedId === t.theme_id) {
        const body = document.createElement("div");
        body.className = "mio-acc-body";

        const descEl = document.createElement("p");
        descEl.className = "mio-acc-desc";
        descEl.textContent = t.description;
        body.appendChild(descEl);

        // Factor grid
        const grid = document.createElement("div");
        grid.className = "mio-factor-grid";

        const factorCol = document.createElement("div");
        const factorLabel = document.createElement("div");
        factorLabel.className = "mio-subhead";
        factorLabel.textContent = "Contributing Factor Types";
        factorCol.appendChild(factorLabel);
        Object.entries(t.top_contributing_factor_types || {}).sort((a, b) => b[1] - a[1]).forEach(([type, pct]) => {
          const row = document.createElement("div");
          row.className = "mio-factor-row";
          const rowLabel = document.createElement("div");
          rowLabel.className = "lbl";
          const ts = document.createElement("span"); ts.className = "name"; ts.textContent = type;
          const ps = document.createElement("span"); ps.className = "val"; ps.textContent = Math.round(pct * 100) + "%";
          rowLabel.append(ts, ps);
          const track = document.createElement("div"); track.className = "track";
          const fill = document.createElement("div"); fill.className = "fill"; fill.style.width = Math.round(pct * 100) + "%";
          track.appendChild(fill);
          row.append(rowLabel, track);
          factorCol.appendChild(row);
        });

        const flagCol = document.createElement("div");
        const flagLabel = document.createElement("div");
        flagLabel.className = "mio-subhead";
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
          row.className = "mio-flag-row";
          const lbl = document.createElement("span"); lbl.className = "name"; lbl.textContent = f.label;
          const val = document.createElement("span");
          val.className = "val";
          const p = f.pct ?? 0;
          val.style.color = p > 0.3 ? SEVERITY_COLORS["Very Serious"] : p > 0.15 ? SEVERITY_COLORS["Serious"] : "var(--ink)";
          val.textContent = Math.round(p * 100) + "%";
          row.append(lbl, val);
          flagCol.appendChild(row);
        });

        grid.append(factorCol, flagCol);
        body.appendChild(grid);

        if (t.solas_chapters?.length) {
          const solasBox = document.createElement("div");
          solasBox.className = "mio-callout solas";
          const sl = document.createElement("span"); sl.className = "head"; sl.textContent = "SOLAS:";
          solasBox.appendChild(sl);
          solasBox.appendChild(document.createTextNode(t.solas_chapters.join(" · ")));
          body.appendChild(solasBox);
        }

        if (t.preventable_by?.length) {
          const prevBox = document.createElement("div");
          prevBox.className = "mio-callout prevent";
          const pl = document.createElement("div"); pl.className = "head"; pl.textContent = "Preventable by";
          const pul = document.createElement("ul");
          t.preventable_by.forEach(p => { const li = document.createElement("li"); li.textContent = p; pul.appendChild(li); });
          prevBox.append(pl, pul);
          body.appendChild(prevBox);
        }

        if ((t.representative_cases ?? []).length > 0) {
          const cl = document.createElement("div"); cl.className = "mio-subhead"; cl.textContent = "Representative Cases";
          body.appendChild(cl);
          t.representative_cases.slice(0, 5).forEach(c => {
            const cb = document.createElement("div"); cb.className = "mio-case";
            const cm = document.createElement("div"); cm.className = "meta";
            cm.textContent = (c.severity ?? "Unknown") + " · " + (c.id ?? "").slice(0, 8);
            const cd = document.createElement("div"); cd.className = "desc";
            cd.textContent = (c.description ?? "").slice(0, 300);
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
