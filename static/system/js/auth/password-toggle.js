(function () {
  function resolveTargetInput(toggle) {
    const targetId = toggle.getAttribute("data-target-id");
    if (targetId) {
      return document.getElementById(targetId);
    }

    const wrapper = toggle.closest(".password-input-wrapper");
    return wrapper ? wrapper.querySelector('input[type="password"], input[type="text"]') : null;
  }

  document.addEventListener("click", function (event) {
    const toggle = event.target.closest("[data-password-toggle]");
    if (!toggle) {
      return;
    }

    const input = resolveTargetInput(toggle);
    if (!input) {
      return;
    }

    const shouldShowPassword = input.type === "password";
    input.type = shouldShowPassword ? "text" : "password";
    toggle.textContent = shouldShowPassword ? "Ocultar" : "Mostrar";
    toggle.setAttribute("aria-label", shouldShowPassword ? "Ocultar senha" : "Mostrar senha");
  });
})();
