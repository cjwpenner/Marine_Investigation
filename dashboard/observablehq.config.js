// dashboard/observablehq.config.js
export default {
  title: "Marine Safety Observatory",
  root: "src",
  base: "/Marine_Investigation",
  pages: [
    {name: "Incident Map", path: "/map"},
    {name: "Themes", path: "/themes"},
    {name: "Trends", path: "/trends"},
    {name: "Vessels & People", path: "/vessels"},
  ],
  style: "style.css",
  head: `
<link rel="icon" href='data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y="0.9em" font-size="90">⚓</text></svg>'>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Public+Sans:wght@400;500;600;700&display=swap">
<script>
// Inject the report download link into the nav bar after the DOM is ready
document.addEventListener("DOMContentLoaded", function () {
  var sidebar = document.getElementById("observablehq-sidebar");
  if (!sidebar) return;
  var base = location.pathname.indexOf("/Marine_Investigation") === 0 ? "/Marine_Investigation" : "";
  var li = document.createElement("li");
  li.className = "observablehq-link nav-download";
  var a = document.createElement("a");
  a.href = base + "/marine_safety_analysis_report_2025.docx";
  a.download = "Marine_Safety_Analysis_Report_2025.docx";
  a.textContent = "Download Report";
  li.appendChild(a);
  sidebar.appendChild(li);
});
</script>`,
};
