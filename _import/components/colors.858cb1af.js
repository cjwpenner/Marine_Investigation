// dashboard/src/components/colors.js
export const SEVERITY_COLORS = {
  "Very Serious": "#dc2626",
  "Serious": "#d97706",
  "Less Serious": "#16a34a",
  "Marine Incident": "#2563eb",
  "Unknown": "#94a3b8",
};

export function severityColor(severity) {
  return SEVERITY_COLORS[severity] ?? "#94a3b8";
}

export const THEME_COLORS = [
  "#1e40af","#2563eb","#3b82f6","#60a5fa",
  "#93c5fd","#1d4ed8","#1e3a8a","#172554"
];

export function themeColor(themeId) {
  if (themeId < 0) return "#94a3b8";
  return THEME_COLORS[themeId % THEME_COLORS.length];
}
