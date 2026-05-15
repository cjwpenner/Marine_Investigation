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
  // Inject download button into the nav bar after the DOM is ready
  head: `<script>
document.addEventListener("DOMContentLoaded", function () {
  var sidebar = document.getElementById("observablehq-sidebar");
  if (!sidebar) return;
  var li = document.createElement("li");
  li.className = "observablehq-link nav-download";
  var a = document.createElement("a");
  a.href = "/Marine_Investigation/marine_safety_analysis_report_2025.docx";
  a.download = "Marine_Safety_Analysis_Report_2025.docx";
  a.textContent = "⬇ Download Report";
  li.appendChild(a);
  sidebar.appendChild(li);
});
</script>`,
};
