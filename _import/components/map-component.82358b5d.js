// dashboard/src/components/map-component.js
import { escapeHtml } from "./dom-utils.2ca39570.js";
import { severityColor } from "./colors.858cb1af.js";

export function createMap(container, allIncidents) {
  // Leaflet CSS injected at runtime (Leaflet is loaded from CDN in the page)
  const cssLink = document.createElement("link");
  cssLink.rel = "stylesheet";
  cssLink.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
  document.head.appendChild(cssLink);

  const L = window.L;

  // ── State ────────────────────────────────────────────────────────────────
  let mode = "heatmap";
  let filters = { severity: "all", year: "all", nightOnly: false, weatherFactor: false };
  let heatLayer = null;
  let clusterGroup = null;

  // ── Layout ───────────────────────────────────────────────────────────────
  container.style.cssText = "display:flex;flex-direction:column;height:calc(100vh - 60px);";

  const filterBar = document.createElement("div");
  filterBar.style.cssText = "display:flex;gap:8px;padding:8px 12px;background:#1e293b;flex-wrap:wrap;align-items:center;border-bottom:1px solid #334155;";

  // Severity select
  const severitySelect = document.createElement("select");
  severitySelect.style.cssText = "background:#334155;color:#e2e8f0;border:none;padding:4px 8px;border-radius:4px;font-size:12px;";
  [["all","All severities"],["Very Serious","Very Serious"],["Serious","Serious"],["Less Serious","Less Serious"]].forEach(([val,text]) => {
    const opt = document.createElement("option");
    opt.value = val;
    opt.textContent = text;
    severitySelect.appendChild(opt);
  });

  // Year select
  const yearSelect = document.createElement("select");
  yearSelect.style.cssText = "background:#334155;color:#e2e8f0;border:none;padding:4px 8px;border-radius:4px;font-size:12px;";
  const allYearOpt = document.createElement("option");
  allYearOpt.value = "all";
  allYearOpt.textContent = "All years";
  yearSelect.appendChild(allYearOpt);
  const years = [...new Set(allIncidents.map(d => d.date?.slice(0,4)).filter(Boolean))].sort();
  years.forEach(y => {
    const opt = document.createElement("option");
    opt.value = y;
    opt.textContent = y;
    yearSelect.appendChild(opt);
  });

  // Night toggle
  const nightLabel = document.createElement("label");
  nightLabel.style.cssText = "color:#94a3b8;font-size:12px;display:flex;align-items:center;gap:4px;cursor:pointer;";
  const nightCheck = document.createElement("input");
  nightCheck.type = "checkbox";
  nightLabel.appendChild(nightCheck);
  nightLabel.appendChild(document.createTextNode(" \uD83C\uDF19 Night only"));

  // Weather toggle
  const weatherLabel = document.createElement("label");
  weatherLabel.style.cssText = "color:#94a3b8;font-size:12px;display:flex;align-items:center;gap:4px;cursor:pointer;";
  const weatherCheck = document.createElement("input");
  weatherCheck.type = "checkbox";
  weatherLabel.appendChild(weatherCheck);
  weatherLabel.appendChild(document.createTextNode(" \uD83C\uDF0A Weather factor"));

  // Mode buttons
  const btnWrap = document.createElement("div");
  btnWrap.style.cssText = "margin-left:auto;display:flex;gap:4px;";
  const btnHeat = document.createElement("button");
  btnHeat.textContent = "Heatmap";
  btnHeat.style.cssText = "background:#1e40af;color:#fff;border:none;padding:4px 10px;border-radius:4px;font-size:11px;cursor:pointer;";
  const btnPins = document.createElement("button");
  btnPins.textContent = "Pins";
  btnPins.style.cssText = "background:#334155;color:#94a3b8;border:none;padding:4px 10px;border-radius:4px;font-size:11px;cursor:pointer;";
  btnWrap.append(btnHeat, btnPins);

  filterBar.append(severitySelect, yearSelect, nightLabel, weatherLabel, btnWrap);

  // Map + panel row
  const row = document.createElement("div");
  row.style.cssText = "display:flex;flex:1;overflow:hidden;";

  const mapDiv = document.createElement("div");
  mapDiv.id = "leaflet-map-" + Math.random().toString(36).slice(2);
  mapDiv.style.cssText = "flex:1;min-height:500px;";

  const panel = document.createElement("div");
  panel.style.cssText = "width:0;overflow:hidden;background:#1e293b;transition:width 0.2s;border-left:1px solid #334155;font-size:12px;color:#e2e8f0;";

  row.append(mapDiv, panel);
  container.append(filterBar, row);

  // ── Leaflet init ─────────────────────────────────────────────────────────
  const map = L.map(mapDiv.id, { center: [54, 5], zoom: 5, maxZoom: 14 });
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "\u00a9 OpenStreetMap contributors"
  }).addTo(map);

  // ── Filtering ────────────────────────────────────────────────────────────
  function getFiltered() {
    return allIncidents.filter(d => {
      if (filters.severity !== "all" && d.severity !== filters.severity) return false;
      if (filters.year !== "all" && d.date?.slice(0,4) !== filters.year) return false;
      if (filters.nightOnly && d.natural_light !== "Night" && d.natural_light !== "Dusk") return false;
      if (filters.weatherFactor && !d.weather_was_factor) return false;
      return true;
    });
  }

  // ── Render heatmap ───────────────────────────────────────────────────────
  function renderHeatmap() {
    if (clusterGroup) { map.removeLayer(clusterGroup); clusterGroup = null; }
    if (heatLayer) map.removeLayer(heatLayer);
    const pts = getFiltered()
      .filter(d => d.lat && d.lon)
      .map(d => {
        const intensity = d.severity === "Very Serious" ? 1.0
                        : d.severity === "Serious" ? 0.6 : 0.3;
        return [d.lat, d.lon, intensity];
      });
    heatLayer = L.heatLayer(pts, {
      radius: 18, blur: 15, maxZoom: 10,
      gradient: { 0.2: "#3b82f6", 0.5: "#f97316", 1.0: "#dc2626" }
    }).addTo(map);
  }

  // ── Render pins ──────────────────────────────────────────────────────────
  function renderPins() {
    if (heatLayer) { map.removeLayer(heatLayer); heatLayer = null; }
    if (clusterGroup) map.removeLayer(clusterGroup);
    clusterGroup = L.markerClusterGroup({
      iconCreateFunction(cluster) {
        const n = cluster.getChildCount();
        const size = n > 100 ? 44 : n > 20 ? 36 : 28;
        const label = n > 999 ? "1k+" : String(n);
        const div = document.createElement("div");
        div.style.cssText = `width:${size}px;height:${size}px;border-radius:50%;background:#1e40af;border:2px solid #fff;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:${size > 36 ? 12 : 10}px;box-shadow:0 2px 6px rgba(0,0,0,0.3);`;
        div.textContent = label;
        return L.divIcon({ html: div, className: "", iconSize: [size, size] });
      }
    });
    getFiltered().filter(d => d.lat && d.lon).forEach(d => {
      const marker = L.circleMarker([d.lat, d.lon], {
        radius: 5, fillColor: severityColor(d.severity),
        color: "#fff", weight: 1.5, fillOpacity: 0.85
      });
      marker.on("click", () => showPanel(d));
      clusterGroup.addLayer(marker);
    });
    map.addLayer(clusterGroup);
  }

  // ── Incident side panel ──────────────────────────────────────────────────
  // All values from incident JSON are treated as untrusted text.
  // Plain text fields use textContent; no dynamic value is inserted via innerHTML.
  function showPanel(incident) {
    panel.style.width = "280px";

    while (panel.firstChild) panel.removeChild(panel.firstChild);

    const wrap = document.createElement("div");
    wrap.style.cssText = "padding:14px;overflow-y:auto;height:100%;box-sizing:border-box;";

    // Header row: severity badge + close button
    const header = document.createElement("div");
    header.style.cssText = "display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px;";
    const badge = document.createElement("span");
    badge.style.cssText = `background:${severityColor(incident.severity)};color:#fff;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:700;`;
    badge.textContent = incident.severity ?? "Unknown";
    const closeBtn = document.createElement("button");
    closeBtn.textContent = "\u00d7";
    closeBtn.style.cssText = "background:none;border:none;color:#64748b;cursor:pointer;font-size:16px;line-height:1;";
    closeBtn.addEventListener("click", () => { panel.style.width = "0"; });
    header.append(badge, closeBtn);
    wrap.appendChild(header);

    // Date
    const dateEl = document.createElement("div");
    dateEl.style.cssText = "font-size:11px;color:#94a3b8;margin-bottom:6px;";
    dateEl.textContent = incident.date ?? "";
    wrap.appendChild(dateEl);

    // Short description
    const descEl = document.createElement("div");
    descEl.style.cssText = "font-size:12px;line-height:1.5;margin-bottom:10px;color:#e2e8f0;";
    descEl.textContent = incident.short_description ?? "";
    wrap.appendChild(descEl);

    // Weather/lighting context
    const ctx = document.createElement("div");
    ctx.style.cssText = "display:flex;flex-direction:column;gap:5px;font-size:11px;border-top:1px solid #334155;padding-top:8px;";
    const addCtxRow = (icon, label, value) => {
      if (value == null || value === "") return;
      const rowEl = document.createElement("div");
      const labelSpan = document.createElement("span");
      labelSpan.style.color = "#94a3b8";
      labelSpan.textContent = `${icon} ${label}: `;
      const valSpan = document.createElement("span");
      valSpan.textContent = String(value);
      rowEl.append(labelSpan, valSpan);
      ctx.appendChild(rowEl);
    };
    addCtxRow("\uD83C\uDF19", "Light", incident.natural_light);
    addCtxRow("\uD83C\uDF0A", "Wave height", incident.wave_height_m != null ? `${incident.wave_height_m}m` : null);
    addCtxRow("\uD83D\uDCA8", "Wind", incident.wind_kph != null ? `${incident.wind_kph} kph` : null);
    if (incident.weather_was_factor) {
      const warn = document.createElement("div");
      warn.style.color = "#f97316";
      warn.textContent = "\u26a0\ufe0f Weather was a factor";
      ctx.appendChild(warn);
    }
    wrap.appendChild(ctx);

    // AI analysis panel
    if (incident.pattern_summary) {
      const aiBox = document.createElement("div");
      aiBox.style.cssText = "margin-top:10px;padding:8px;background:#0f172a;border-radius:4px;font-size:11px;color:#94a3b8;line-height:1.5;border-left:2px solid #1e40af;";
      const aiLabel = document.createElement("div");
      aiLabel.style.cssText = "color:#60a5fa;font-size:9px;font-weight:700;margin-bottom:3px;";
      aiLabel.textContent = "AI ANALYSIS";
      const aiText = document.createElement("div");
      aiText.textContent = incident.pattern_summary;
      aiBox.append(aiLabel, aiText);
      wrap.appendChild(aiBox);
    }

    panel.appendChild(wrap);
  }

  // ── Mode toggle wiring ───────────────────────────────────────────────────
  function setMode(newMode) {
    mode = newMode;
    if (mode === "heatmap") {
      btnHeat.style.background = "#1e40af"; btnHeat.style.color = "#fff";
      btnPins.style.background = "#334155"; btnPins.style.color = "#94a3b8";
    } else {
      btnPins.style.background = "#1e40af"; btnPins.style.color = "#fff";
      btnHeat.style.background = "#334155"; btnHeat.style.color = "#94a3b8";
    }
    render();
  }

  function render() {
    if (mode === "heatmap") renderHeatmap(); else renderPins();
  }

  btnHeat.addEventListener("click", () => setMode("heatmap"));
  btnPins.addEventListener("click", () => setMode("pins"));
  severitySelect.addEventListener("change", e => { filters.severity = e.target.value; render(); });
  yearSelect.addEventListener("change", e => { filters.year = e.target.value; render(); });
  nightCheck.addEventListener("change", e => { filters.nightOnly = e.target.checked; render(); });
  weatherCheck.addEventListener("change", e => { filters.weatherFactor = e.target.checked; render(); });

  render();
  return map;
}
