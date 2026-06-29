/*
 * crud_modal.js — Controlador de CRUD em modal/dialog (lado-pai). LV, do zero.
 *
 * Marcação:
 *   <dialog data-crud-modal="NAME"> ... <iframe data-crud-frame [src]></iframe>
 *           ... <button data-crud-close>
 *   <button data-crud-open="NAME" data-crud-url="/rota/?modal=1">
 *   <form data-confirm-submit data-confirm-message="...">
 *
 * O iframe sinaliza por postMessage:
 *   { type: "crud-modal-close", modal } -> fecha
 *   { type: "crud-complete",    modal } -> fecha e recarrega
 */
(function () {
  "use strict";

  function nativeDialog(modal) { return modal && typeof modal.showModal === "function"; }

  function open(modal, bodyClass) {
    if (nativeDialog(modal)) { if (!modal.open) { modal.showModal(); } }
    else { modal.setAttribute("open", ""); modal.classList.add("is-open"); }
    document.body.classList.add(bodyClass);
  }

  function close(modal, bodyClass) {
    if (nativeDialog(modal) && modal.open) { modal.close(); }
    else { modal.removeAttribute("open"); modal.classList.remove("is-open"); }
    document.body.classList.remove(bodyClass);
  }

  function resolve(url) {
    try { return new URL(url, window.location.href).href; } catch (e) { return url; }
  }

  function bind(modal) {
    var name = modal.dataset.crudModal || "";
    var bodyClass = "crud-modal-open--" + name;
    var frame = modal.querySelector("[data-crud-frame]");
    var initialSrc = frame ? frame.getAttribute("src") : "";
    var trigger = null;

    function openWith(url, btn) {
      trigger = btn || null;
      if (url && frame) {
        var r = resolve(url);
        if (frame.getAttribute("src") !== r) { frame.setAttribute("src", r); }
      } else if (frame && initialSrc && !frame.getAttribute("src")) {
        frame.setAttribute("src", initialSrc);
      }
      open(modal, bodyClass);
    }

    function closeMe(reset) {
      close(modal, bodyClass);
      if (reset && frame) {
        if (initialSrc) { frame.setAttribute("src", initialSrc); }
        else { frame.removeAttribute("src"); }
      }
      if (trigger) { trigger.focus(); trigger = null; }
    }

    modal.querySelectorAll("[data-crud-close]").forEach(function (b) {
      b.addEventListener("click", function () { closeMe(false); });
    });
    modal.addEventListener("click", function (e) { if (e.target === modal) { closeMe(false); } });
    modal.addEventListener("close", function () { document.body.classList.remove(bodyClass); if (trigger) { trigger.focus(); trigger = null; } });

    window.addEventListener("message", function (e) {
      if (e.origin !== window.location.origin || !e.data) { return; }
      if (e.data.modal && e.data.modal !== name) { return; }
      if (e.data.type === "crud-modal-close") { closeMe(true); }
      else if (e.data.type === "crud-complete") { closeMe(false); window.location.reload(); }
    });

    return { name: name, open: openWith, close: closeMe };
  }

  function syncTheme(frame) {
    if (!frame || !frame.contentWindow) { return; }
    var theme = document.documentElement.getAttribute("data-theme");
    try { frame.contentWindow.postMessage({ type: "theme-change", theme: theme }, window.location.origin); } catch (e) {}
  }

  document.addEventListener("DOMContentLoaded", function () {
    var registry = {};
    document.querySelectorAll("[data-crud-modal]").forEach(function (m) {
      var c = bind(m);
      registry[c.name] = c;
    });

    document.querySelectorAll("[data-crud-open]").forEach(function (b) {
      b.addEventListener("click", function () {
        var c = registry[b.dataset.crudOpen];
        if (c) { c.open(b.dataset.crudUrl || "", b); }
      });
    });

    document.querySelectorAll("[data-confirm-submit]").forEach(function (form) {
      form.addEventListener("submit", function (e) {
        if (!window.confirm(form.dataset.confirmMessage || "Confirma esta ação?")) { e.preventDefault(); }
      });
    });

    document.addEventListener("keydown", function (e) {
      if (e.key !== "Escape") { return; }
      Object.keys(registry).forEach(function (k) {
        if (document.body.classList.contains("crud-modal-open--" + registry[k].name)) { registry[k].close(false); }
      });
    });

    var frames = document.querySelectorAll("[data-crud-frame]");
    frames.forEach(function (f) { f.addEventListener("load", function () { syncTheme(f); }); });
    if (typeof MutationObserver !== "undefined") {
      var obs = new MutationObserver(function (muts) {
        muts.forEach(function (m) { if (m.attributeName === "data-theme") { frames.forEach(syncTheme); } });
      });
      try { obs.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] }); } catch (e) {}
    }
  });
}());
