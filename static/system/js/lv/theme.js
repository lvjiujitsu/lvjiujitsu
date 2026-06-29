(function () {
  "use strict";

  function current() {
    return document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
  }

  function apply(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    var sun = document.getElementById("icon-sun");
    var moon = document.getElementById("icon-moon");
    var toggle = document.getElementById("theme-toggle");
    var isDark = theme === "dark";

    if (sun && moon) {
      sun.hidden = isDark;
      moon.hidden = !isDark;
    }
    if (toggle) {
      toggle.setAttribute("aria-pressed", String(isDark));
      toggle.setAttribute("aria-label", isDark ? "Mudar para tema claro" : "Mudar para tema escuro");
      toggle.setAttribute("title", isDark ? "Tema claro" : "Tema escuro");
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    apply(current());
    var toggle = document.getElementById("theme-toggle");
    if (!toggle) { return; }
    toggle.addEventListener("click", function () {
      var next = current() === "dark" ? "light" : "dark";
      try { localStorage.setItem("lv-theme", next); } catch (e) {}
      apply(next);
    });
  });
}());
