(function () {
  "use strict";

  var root = document.documentElement;
  var themeKey = "lv-theme";
  var themeToggle = document.querySelector("[data-theme-toggle]");
  var passwordToggles = document.querySelectorAll("[data-password-toggle]");
  var identifierInput = document.getElementById("id_identifier");
  var passwordInput = document.getElementById("id_password");
  var authForms = document.querySelectorAll("[data-auth-form]");

  function preferredTheme() {
    var savedTheme = window.localStorage.getItem(themeKey);
    if (savedTheme === "light" || savedTheme === "dark") {
      return savedTheme;
    }
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  function applyTheme(theme) {
    root.setAttribute("data-theme", theme);
    if (!themeToggle) {
      return;
    }
    var isDark = theme === "dark";
    themeToggle.setAttribute("aria-pressed", String(isDark));
    themeToggle.setAttribute("title", isDark ? "Usar tema claro" : "Usar tema escuro");
  }

  function applyPasswordVisibility(toggle, isVisible) {
    var inputId = toggle.getAttribute("aria-controls");
    var input = inputId ? document.getElementById(inputId) : null;
    if (!input) {
      return;
    }
    input.type = isVisible ? "text" : "password";
    toggle.dataset.passwordVisible = String(isVisible);
    toggle.setAttribute("aria-label", isVisible ? "Ocultar senha" : "Mostrar senha");
  }

  if (identifierInput) {
    identifierInput.setAttribute("placeholder", "Digite seu CPF ou acesso técnico");
    identifierInput.setAttribute("autocomplete", "username");
  }

  if (passwordInput) {
    passwordInput.setAttribute("placeholder", "Digite sua senha");
    passwordInput.setAttribute("autocomplete", "current-password");
  }

  applyTheme(preferredTheme());
  passwordToggles.forEach(function (toggle) {
    applyPasswordVisibility(toggle, false);
  });

  if (themeToggle) {
    themeToggle.addEventListener("click", function () {
      var currentTheme = root.getAttribute("data-theme") === "dark" ? "dark" : "light";
      var nextTheme = currentTheme === "dark" ? "light" : "dark";
      window.localStorage.setItem(themeKey, nextTheme);
      applyTheme(nextTheme);
    });
  }

  passwordToggles.forEach(function (toggle) {
    toggle.addEventListener("click", function () {
      var inputId = toggle.getAttribute("aria-controls");
      var input = inputId ? document.getElementById(inputId) : null;
      var isVisible = input && input.type === "text";
      applyPasswordVisibility(toggle, !isVisible);
      if (input) {
        input.focus();
      }
    });
  });

  authForms.forEach(function (form) {
    var submit = form.querySelector("[data-auth-submit]");
    if (!submit) {
      return;
    }
    form.addEventListener("submit", function () {
      submit.disabled = true;
      submit.dataset.state = "submitting";
      submit.textContent = submit.dataset.loadingLabel || "Enviando...";
    });
  });
}());
