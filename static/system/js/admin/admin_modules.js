(function () {
  var toggle = document.getElementById("theme-toggle");
  var sun = document.getElementById("icon-sun");
  var moon = document.getElementById("icon-moon");

  function resolveInitialTheme() {
    var storedTheme = localStorage.getItem("lv-theme");
    if (storedTheme === "dark" || storedTheme === "light") {
      return storedTheme;
    }
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    if (!sun || !moon) {
      return;
    }
    if (theme === "dark") {
      sun.removeAttribute("hidden");
      moon.setAttribute("hidden", "");
    } else {
      moon.removeAttribute("hidden");
      sun.setAttribute("hidden", "");
    }
  }

  if (!toggle) {
    return;
  }

  applyTheme(resolveInitialTheme());
  toggle.addEventListener("click", function () {
    var currentTheme = document.documentElement.getAttribute("data-theme");
    var nextTheme = currentTheme === "dark" ? "light" : "dark";
    localStorage.setItem("lv-theme", nextTheme);
    applyTheme(nextTheme);
  });
})();
