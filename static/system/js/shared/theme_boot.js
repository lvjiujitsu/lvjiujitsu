(() => {
    "use strict";

    const root = document.documentElement;
    const storageKey = root.dataset.themeStorageKey || "app-theme";
    window.THEME_STORAGE_KEY = storageKey;
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const TOGGLE_SELECTOR = "[data-theme-toggle], #theme-toggle";

    function toggles() {
        return Array.prototype.slice.call(document.querySelectorAll(TOGGLE_SELECTOR));
    }

    function storedTheme() {
        try {
            const value = window.localStorage.getItem(storageKey);
            return value === "light" || value === "dark" ? value : null;
        } catch (_error) {
            return null;
        }
    }

    function preferredTheme() {
        return storedTheme() || (media.matches ? "dark" : "light");
    }

    function currentTheme() {
        return root.dataset.theme === "dark" ? "dark" : "light";
    }

    function syncControls(theme) {
        const nextTheme = theme === "dark" ? "claro" : "escuro";
        toggles().forEach((button) => {
            button.setAttribute("aria-pressed", String(theme === "dark"));
            button.setAttribute("aria-label", `Ativar tema ${nextTheme}`);
            button.setAttribute("title", `Ativar tema ${nextTheme}`);
            const label = button.querySelector("[data-theme-label]");
            if (label) label.textContent = `Ativar tema ${nextTheme}`;
        });

        const sun = document.getElementById("icon-sun");
        const moon = document.getElementById("icon-moon");
        if (sun) sun.hidden = theme === "dark";
        if (moon) moon.hidden = theme !== "dark";

        const themeColor = document.querySelector('meta[name="theme-color"]');
        if (themeColor) {
            const surface = getComputedStyle(root)
                .getPropertyValue("--bg")
                .trim();
            if (surface) themeColor.content = surface;
        }
    }

    function applyTheme(theme) {
        const next = theme === "dark" ? "dark" : "light";
        root.dataset.theme = next;
        root.style.colorScheme = next;
        if (document.readyState !== "loading") syncControls(next);
        return next;
    }

    function persistTheme(theme) {
        try {
            window.localStorage.setItem(storageKey, theme);
        } catch (_error) {
        }
    }

    function setTheme(theme) {
        const next = theme === "dark" ? "dark" : "light";
        persistTheme(next);
        return applyTheme(next);
    }

    function bindToggles() {
        toggles().forEach((button) => {
            if (button.dataset.themeToggleBound === "true") return;
            button.dataset.themeToggleBound = "true";
            button.addEventListener("click", () => {
                setTheme(currentTheme() === "dark" ? "light" : "dark");
            });
        });
    }

    applyTheme(preferredTheme());

    document.addEventListener("DOMContentLoaded", () => {
        syncControls(currentTheme());
        bindToggles();
    });

    media.addEventListener("change", () => {
        if (!storedTheme()) applyTheme(preferredTheme());
    });

    window.APP = window.APP || {};
    window.APP.Theme = {
        get: currentTheme,
        set: setTheme,
        apply: applyTheme,
        bindToggles: bindToggles,
        storageKey: storageKey,
    };
})();
