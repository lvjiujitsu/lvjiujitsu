(function () {
  "use strict";

  function bindSectionCollapse() {
    document.querySelectorAll("[data-section-toggle]").forEach(function (button) {
      var bodyId = button.getAttribute("aria-controls");
      var body = bodyId ? document.getElementById(bodyId) : null;
      if (!body) {
        return;
      }

      button.addEventListener("click", function () {
        var expanded = button.getAttribute("aria-expanded") === "true";
        var next = !expanded;
        button.setAttribute("aria-expanded", String(next));
        body.hidden = !next;
      });
    });
  }

  document.addEventListener("DOMContentLoaded", bindSectionCollapse);
}());
