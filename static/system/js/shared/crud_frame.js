/*
 * crud_frame.js — Lado-iframe do CRUD em modal do LV.
 * Portado de modal_frame.js (Visary). Sincroniza tema com o pai e,
 * ao concluir, sinaliza o controlador para fechar/recarregar.
 *
 * Marcação no <body> da página renderizada dentro do iframe:
 *   data-crud-frame-modal="NAME"        -> nome do modal pai
 *   data-crud-frame-complete="true"     -> ao carregar, fecha e recarrega o pai
 *   data-crud-frame-close="true"        -> ao carregar, apenas fecha o pai
 */
(function () {
  "use strict";

  function syncThemeFromParent() {
    if (!window.parent || window.parent === window) {
      return;
    }
    try {
      var parentTheme = window.parent.document.documentElement.getAttribute("data-theme");
      if (parentTheme) {
        document.documentElement.setAttribute("data-theme", parentTheme);
      }
    } catch (error) {}
  }

  function post(type) {
    if (!window.parent || window.parent === window) {
      return;
    }
    var modal = document.body ? document.body.dataset.crudFrameModal || "" : "";
    window.parent.postMessage({ type: type, modal: modal }, window.location.origin);
  }

  window.addEventListener("message", function (event) {
    if (!event.data || event.data.type !== "theme-change") {
      return;
    }
    if (event.data.theme) {
      document.documentElement.setAttribute("data-theme", event.data.theme);
    }
  });

  function bindCancelButtons() {
    document.querySelectorAll("[data-crud-frame-cancel]").forEach(function (button) {
      button.addEventListener("click", function (event) {
        event.preventDefault();
        post("crud-modal-close");
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    syncThemeFromParent();

    if (!document.body) {
      return;
    }

    bindCancelButtons();

    if (document.body.dataset.crudFrameComplete === "true") {
      post("crud-complete");
    } else if (document.body.dataset.crudFrameClose === "true") {
      post("crud-modal-close");
    }
  });
}());
