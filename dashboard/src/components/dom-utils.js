// dashboard/src/components/dom-utils.js

/**
 * Escape a string for safe insertion into HTML markup.
 * Use on all values that originate from external JSON data.
 */
export function escapeHtml(str) {
  if (str == null) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

/** Set element text content safely. */
export function setText(el, value) {
  el.textContent = value == null ? "" : String(value);
}

/** Create an element with optional class and text content. */
export function el(tag, cls, text) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text != null) node.textContent = String(text);
  return node;
}
