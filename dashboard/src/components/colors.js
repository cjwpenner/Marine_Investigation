// dashboard/src/components/colors.js
// Validated palette (dataviz six-checks, light surface #f7f4ee).
export const SEVERITY_COLORS = {
  "Very Serious": "#bb1e2d",
  "Serious": "#b45309",
  "Less Serious": "#3e6fb0",
  "Marine Incident": "#64748b",
  "Unknown": "#8d99a6",
};

export const SEVERITY_ORDER = ["Less Serious", "Serious", "Very Serious"];

export function severityColor(severity) {
  return SEVERITY_COLORS[severity] ?? "#8d99a6";
}

export const LIGHT_COLORS = {
  "Daylight": "#3d7fc1",
  "Twilight": "#c26100",
  "Dawn": "#c26100",
  "Night": "#4b56a8",
};

export function lightColor(light) {
  return LIGHT_COLORS[light] ?? "#8d99a6";
}

// single-hue navy for magnitude bars
export const BAR_COLOR = "#3e6fb0";
export const BAR_COLOR_DARK = "#1c3b63";
