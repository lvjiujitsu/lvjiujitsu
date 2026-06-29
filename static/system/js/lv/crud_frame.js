/*
 * crud_frame.js — Lado-iframe do CRUD em modal (LV, do zero).
 * Sincroniza tema com o pai, mascara datas pt-BR e sinaliza conclusão.
 *
 * <body data-crud-frame-modal="NAME"
 *       [data-crud-frame-complete="true"] | [data-crud-frame-close="true"]>
 * Botão: [data-crud-frame-cancel] fecha o modal pai.
 */
(function () {
  "use strict";

  function syncThemeFromParent() {
    if (!window.parent || window.parent === window) { return; }
    try {
      var t = window.parent.document.documentElement.getAttribute("data-theme");
      if (t) { document.documentElement.setAttribute("data-theme", t); }
    } catch (e) {}
  }

  function post(type) {
    if (!window.parent || window.parent === window) { return; }
    var modal = document.body ? (document.body.dataset.crudFrameModal || "") : "";
    window.parent.postMessage({ type: type, modal: modal }, window.location.origin);
  }

  function bindDateMasks() {
    document.querySelectorAll('input[data-date-mask]').forEach(function (input) {
      input.addEventListener("input", function () {
        var d = input.value.replace(/\D/g, "").slice(0, 8);
        var v = "";
        if (d.length > 0) { v = d.slice(0, 2); }
        if (d.length > 2) { v += "/" + d.slice(2, 4); }
        if (d.length > 4) { v += "/" + d.slice(4, 8); }
        input.value = v;
      });
    });
  }

  window.addEventListener("message", function (e) {
    if (!e.data || e.data.type !== "theme-change") { return; }
    if (e.data.theme) { document.documentElement.setAttribute("data-theme", e.data.theme); }
  });

  document.addEventListener("DOMContentLoaded", function () {
    syncThemeFromParent();
    if (!document.body) { return; }

    bindDateMasks();

    document.querySelectorAll("[data-crud-frame-cancel]").forEach(function (b) {
      b.addEventListener("click", function (e) { e.preventDefault(); post("crud-modal-close"); });
    });

    if (document.body.dataset.crudFrameComplete === "true") { post("crud-complete"); }
    else if (document.body.dataset.crudFrameClose === "true") { post("crud-modal-close"); }
  });
}());
