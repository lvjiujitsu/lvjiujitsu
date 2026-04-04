(function () {
  const toggles = document.querySelectorAll("[data-password-toggle]");

  toggles.forEach((toggle) => {
    const targetId = toggle.getAttribute("data-target-id");
    const input = targetId ? document.getElementById(targetId) : null;

    if (!input) {
      return;
    }

    toggle.addEventListener("click", () => {
      const shouldShowPassword = input.type === "password";
      input.type = shouldShowPassword ? "text" : "password";
      toggle.textContent = shouldShowPassword ? "Ocultar" : "Mostrar";
      toggle.setAttribute(
        "aria-label",
        shouldShowPassword ? "Ocultar senha" : "Mostrar senha",
      );
    });
  });
})();
