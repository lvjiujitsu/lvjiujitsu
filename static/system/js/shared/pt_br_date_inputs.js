(function () {
  "use strict";

  var PT_BR_DATE_HINT = "dd/mm/aaaa";

  function formatIsoToPtBr(iso) {
    if (!iso) {
      return "";
    }

    var parts = String(iso).split("-");
    if (parts.length !== 3) {
      return "";
    }

    return parts[2] + "/" + parts[1] + "/" + parts[0];
  }

  function bindLegacyMaskedDateInputs(root) {
    if (!root) {
      return;
    }

    root.querySelectorAll('[data-date-input="pt-br"]').forEach(function (input) {
      if (input.dataset.ptBrDateBound === "true") {
        return;
      }

      input.dataset.ptBrDateBound = "true";
      input.addEventListener("input", function () {
        var digits = input.value.replace(/\D/g, "").slice(0, 8);
        var formatted = "";

        if (digits.length > 0) {
          formatted = digits.slice(0, 2);
        }
        if (digits.length > 2) {
          formatted += "/" + digits.slice(2, 4);
        }
        if (digits.length > 4) {
          formatted += "/" + digits.slice(4, 8);
        }

        input.value = formatted;
      });
    });
  }

  function syncNativeDateWrapState(wrap, input) {
    var hasValue = !!input.value;
    var isFocused = document.activeElement === input;
    wrap.classList.toggle("pt-br-date-wrap--filled", hasValue);
    wrap.classList.toggle("pt-br-date-wrap--focused", isFocused);

    var valueEl = wrap.querySelector(".pt-br-date-wrap__value");
    if (valueEl) {
      valueEl.textContent = hasValue ? formatIsoToPtBr(input.value) : "";
    }
  }

  function wrapNativePtBrDateInput(input) {
    if (!input || input.closest(".pt-br-date-wrap")) {
      return;
    }

    var wrap = document.createElement("div");
    wrap.className = "pt-br-date-wrap";
    input.parentNode.insertBefore(wrap, input);
    wrap.appendChild(input);

    var hint = document.createElement("span");
    hint.className = "pt-br-date-wrap__hint";
    hint.textContent = PT_BR_DATE_HINT;
    hint.setAttribute("aria-hidden", "true");
    wrap.appendChild(hint);

    var value = document.createElement("span");
    value.className = "pt-br-date-wrap__value";
    value.setAttribute("aria-hidden", "true");
    wrap.appendChild(value);

    function syncState() {
      syncNativeDateWrapState(wrap, input);
    }

    input.addEventListener("focus", syncState);
    input.addEventListener("blur", syncState);
    input.addEventListener("change", syncState);
    input.addEventListener("input", syncState);
    syncState();
  }

  function refreshNativePtBrDateInput(input) {
    if (!input) {
      return;
    }

    var wrap = input.closest(".pt-br-date-wrap");
    if (wrap) {
      syncNativeDateWrapState(wrap, input);
      return;
    }

    if (input.dataset.ptBrNativeDateBound !== "true") {
      input.dataset.ptBrNativeDateBound = "true";
      input.lang = "pt-BR";
      wrapNativePtBrDateInput(input);
    }
  }

  function bindNativePtBrDateInputs(root) {
    if (!root) {
      return;
    }

    root.querySelectorAll('input[type="date"][data-pt-br-native-date="true"]').forEach(function (input) {
      refreshNativePtBrDateInput(input);
    });
  }

  function bindPtBrDateInputs(root) {
    bindLegacyMaskedDateInputs(root);
    bindNativePtBrDateInputs(root);
  }

  document.addEventListener("DOMContentLoaded", function () {
    bindPtBrDateInputs(document);
  });

  window.LvPtBrDateInputs = {
    bind: bindPtBrDateInputs,
    refresh: refreshNativePtBrDateInput,
    formatIsoToPtBr: formatIsoToPtBr,
  };
}());
