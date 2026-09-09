(() => {
    "use strict";

    const storageKey = "lvjiujitsu-theme";
    // O espaco do produto le a chave daqui em vez de redeclara-la.
    window.THEME_STORAGE_KEY = storageKey;
    const root = document.documentElement;
    const media = window.matchMedia("(prefers-color-scheme: dark)");

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

    function syncControls(theme) {
        const nextTheme = theme === "dark" ? "claro" : "escuro";
        document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
            button.setAttribute("aria-pressed", String(theme === "dark"));
            button.setAttribute("aria-label", `Ativar tema ${nextTheme}`);
            button.setAttribute("title", `Ativar tema ${nextTheme}`);
            const label = button.querySelector("[data-theme-label]");
            if (label) label.textContent = `Ativar tema ${nextTheme}`;
        });

        const themeColor = document.querySelector('meta[name="theme-color"]');
        if (themeColor) {
            const surface = getComputedStyle(root)
                .getPropertyValue("--bg")
                .trim();
            if (surface) themeColor.content = surface;
        }
    }

    function applyTheme(theme) {
        root.dataset.theme = theme;
        root.style.colorScheme = theme;
        if (document.readyState !== "loading") syncControls(theme);
    }

    function persistTheme(theme) {
        try {
            window.localStorage.setItem(storageKey, theme);
        } catch (_error) {
        }
    }

    applyTheme(preferredTheme());

    document.addEventListener("DOMContentLoaded", () => {
        syncControls(root.dataset.theme);
        document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
            button.addEventListener("click", () => {
                const theme = root.dataset.theme === "dark" ? "light" : "dark";
                persistTheme(theme);
                applyTheme(theme);
            });
        });
    });

    media.addEventListener("change", () => {
        if (!storedTheme()) applyTheme(preferredTheme());
    });
})();
