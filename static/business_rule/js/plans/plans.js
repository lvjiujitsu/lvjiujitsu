(function () {
  var toggle = document.getElementById("theme-toggle");
  var sun = document.getElementById("icon-sun");
  var moon = document.getElementById("icon-moon");

  function resolveInitialTheme() {
    var storedTheme = localStorage.getItem(window.THEME_STORAGE_KEY);
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

  if (toggle) {
    applyTheme(resolveInitialTheme());
    toggle.addEventListener("click", function () {
      var nextTheme = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
      localStorage.setItem(window.THEME_STORAGE_KEY, nextTheme);
      applyTheme(nextTheme);
    });
  }

  var pricePreview = document.querySelector("[data-price-preview]");
  if (!pricePreview) {
    return;
  }

  var cycleMonths = {
    monthly: 1,
    quarterly: 3,
    semiannual: 6,
    annual: 12
  };

  function readDecimal(id) {
    var field = document.getElementById(id);
    if (!field || field.value.trim() === "") {
      return null;
    }
    var value = Number(field.value.replace(",", "."));
    return Number.isFinite(value) ? value : null;
  }

  function readString(id) {
    var field = document.getElementById(id);
    return field ? field.value : "";
  }

  function formatCurrency(value) {
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL"
    }).format(value);
  }

  function updatePricePreview() {
    var base = readDecimal("id_base_monthly_net_price");
    if (base === null) {
      pricePreview.textContent = "Preço manual: informe o valor líquido mensal para estimar o cálculo automático.";
      return;
    }

    var months = cycleMonths[readString("id_billing_cycle")] || 1;
    var fixedFee = readDecimal("id_gateway_fixed_fee") || 0;
    var gatewayPercentage = readDecimal("id_gateway_percentage_fee") || 0;
    var discount = readDecimal("id_cycle_discount_percentage") || 0;
    var netTotal = base * months * (1 - discount);
    var gross = gatewayPercentage === 0
      ? netTotal + fixedFee
      : (netTotal + fixedFee) / (1 - gatewayPercentage);

    pricePreview.textContent = "Estimativa calculada: " + formatCurrency(gross) + " no ciclo selecionado.";
  }

  [
    "id_base_monthly_net_price",
    "id_billing_cycle",
    "id_gateway_fixed_fee",
    "id_gateway_percentage_fee",
    "id_cycle_discount_percentage"
  ].forEach(function (id) {
    var field = document.getElementById(id);
    if (field) {
      field.addEventListener("input", updatePricePreview);
      field.addEventListener("change", updatePricePreview);
    }
  });

  updatePricePreview();
})();
