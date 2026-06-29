(function () {
  var storedTheme = localStorage.getItem("lv-theme");
  var prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  var theme = storedTheme === "dark" || storedTheme === "light"
    ? storedTheme
    : (prefersDark ? "dark" : "light");

  document.documentElement.setAttribute("data-theme", theme);
}());
