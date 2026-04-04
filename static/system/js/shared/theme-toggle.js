(function () {
  const root = document.documentElement;
  const storageKey = "lv-theme";
  const toggles = document.querySelectorAll("[data-theme-toggle]");

  function getPreferredTheme() {
    const savedTheme = window.localStorage.getItem(storageKey);
    if (savedTheme === "light" || savedTheme === "dark") {
      return savedTheme;
    }

    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  function applyTheme(theme) {
    root.setAttribute("data-theme", theme);
    window.localStorage.setItem(storageKey, theme);
    toggles.forEach((toggle) => {
      toggle.setAttribute("aria-label", theme === "dark" ? "Ativar tema claro" : "Ativar tema escuro");
      toggle.setAttribute("title", theme === "dark" ? "Ativar tema claro" : "Ativar tema escuro");
    });
  }

  const initialTheme = getPreferredTheme();
  applyTheme(initialTheme);

  toggles.forEach((toggle) => {
    toggle.addEventListener("click", () => {
      const currentTheme = root.getAttribute("data-theme") === "dark" ? "dark" : "light";
      applyTheme(currentTheme === "dark" ? "light" : "dark");
    });
  });
})();
