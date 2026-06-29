(function () {
  "use strict";

  function bindMartialArtFields() {
    document.querySelectorAll("[data-martial-art-form]").forEach(function (form) {
      var select = form.querySelector("[data-martial-art-presence-select]");
      var fields = form.querySelector("[data-martial-art-fields]");
      if (!select || !fields) {
        return;
      }

      function sync() {
        if (select.value === "yes") {
          fields.removeAttribute("hidden");
        } else {
          fields.setAttribute("hidden", "");
        }
      }

      select.addEventListener("change", sync);
      sync();
    });
  }

  document.addEventListener("DOMContentLoaded", bindMartialArtFields);
}());
