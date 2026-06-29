/*
 * crud_modal.js — Controlador genérico de CRUD em modal/dialog para o LV.
 * Portado do padrão consolidado no Visary (clients.js / modal_frame.js).
 *
 * Contrato de marcação:
 *   - Modal:   <dialog data-crud-modal="NAME" data-crud-initial-open="true|false">
 *                ... <iframe data-crud-frame ...></iframe>
 *                ... <button data-crud-close>
 *   - Abrir:   <button data-crud-open="NAME" data-crud-url="/rota/?modal=1">
 *              (sem data-crud-url usa o src inicial do iframe — modais de criação)
 *   - Confirm: <form data-confirm-submit data-confirm-message="...">
 *
 * O iframe sinaliza conclusão via postMessage:
 *   { type: "crud-modal-close", modal: "NAME" }  -> fecha
 *   { type: "crud-complete",    modal: "NAME" }  -> fecha e recarrega a página
 */
(function () {
  "use strict";

  function canUseDialog(modal) {
    return modal && typeof modal.showModal === "function";
  }

  function openDialog(modal, bodyClass) {
    if (canUseDialog(modal)) {
      if (!modal.open) {
        modal.showModal();
      }
    } else {
      modal.setAttribute("open", "");
      modal.classList.add("is-open");
    }
    if (bodyClass) {
      document.body.classList.add(bodyClass);
    }
  }

  function closeDialog(modal, bodyClass) {
    if (canUseDialog(modal) && modal.open) {
      modal.close();
    } else {
      modal.removeAttribute("open");
      modal.classList.remove("is-open");
    }
    if (bodyClass) {
      document.body.classList.remove(bodyClass);
    }
  }

  function resolveUrl(url) {
    try {
      return new URL(url, window.location.href).href;
    } catch (error) {
      return url;
    }
  }

  function bindCrudModal(modal) {
    var name = modal.dataset.crudModal || "";
    var bodyClass = "crud-modal-open--" + name;
    var frame = modal.querySelector("[data-crud-frame]");
    var initialFrameUrl = frame ? frame.getAttribute("src") : "";
    var activeTrigger = null;

    function setFrameUrl(url) {
      if (!frame || !url) {
        return;
      }
      var resolved = resolveUrl(url);
      if (frame.getAttribute("src") !== resolved) {
        frame.setAttribute("src", resolved);
      }
    }

    function open(url, trigger) {
      activeTrigger = trigger || null;
      if (url) {
        setFrameUrl(url);
      } else if (frame && initialFrameUrl && !frame.getAttribute("src")) {
        frame.setAttribute("src", initialFrameUrl);
      }
      openDialog(modal, bodyClass);
      var firstInput = modal.querySelector("input:not([type='hidden']), select, textarea, [data-crud-frame]");
      if (firstInput) {
        window.setTimeout(function () {
          firstInput.focus();
        }, 0);
      }
    }

    function close(options) {
      closeDialog(modal, bodyClass);
      if (options && options.resetFrame && frame) {
        if (initialFrameUrl) {
          frame.setAttribute("src", initialFrameUrl);
        } else {
          frame.removeAttribute("src");
        }
      }
      if (activeTrigger) {
        activeTrigger.focus();
        activeTrigger = null;
      }
    }

    modal.querySelectorAll("[data-crud-close]").forEach(function (button) {
      button.addEventListener("click", function () {
        close();
      });
    });

    modal.addEventListener("click", function (event) {
      if (event.target === modal) {
        close();
      }
    });

    modal.addEventListener("close", function () {
      document.body.classList.remove(bodyClass);
      if (activeTrigger) {
        activeTrigger.focus();
        activeTrigger = null;
      }
    });

    window.addEventListener("message", function (event) {
      if (event.origin !== window.location.origin || !event.data) {
        return;
      }
      if (event.data.modal && event.data.modal !== name) {
        return;
      }
      if (event.data.type === "crud-modal-close") {
        close({ resetFrame: true });
      } else if (event.data.type === "crud-complete") {
        close();
        window.location.reload();
      }
    });

    if (modal.dataset.crudInitialOpen === "true") {
      open(modal.dataset.crudInitialSrc || "");
    }

    return { open: open, close: close, name: name };
  }

  function bindOpeners(registry) {
    document.querySelectorAll("[data-crud-open]").forEach(function (button) {
      button.addEventListener("click", function () {
        var modal = registry[button.dataset.crudOpen];
        if (modal) {
          modal.open(button.dataset.crudUrl || "", button);
        }
      });
    });
  }

  function bindConfirmSubmits() {
    document.querySelectorAll("[data-confirm-submit]").forEach(function (form) {
      form.addEventListener("submit", function (event) {
        var message = form.dataset.confirmMessage || "Confirma esta ação?";
        if (!window.confirm(message)) {
          event.preventDefault();
        }
      });
    });
  }

  function bindGlobalEscape(registry) {
    document.addEventListener("keydown", function (event) {
      if (event.key !== "Escape") {
        return;
      }
      Object.keys(registry).forEach(function (key) {
        var modal = registry[key];
        if (document.body.classList.contains("crud-modal-open--" + modal.name)) {
          modal.close();
        }
      });
    });
  }

  function syncThemeToFrame(frame) {
    if (!frame || !frame.contentWindow) {
      return;
    }
    var theme = document.documentElement.getAttribute("data-theme");
    try {
      frame.contentWindow.postMessage({ type: "theme-change", theme: theme }, window.location.origin);
    } catch (error) {}
  }

  function bindThemeSyncToFrames() {
    var frames = document.querySelectorAll("[data-crud-frame]");
    if (!frames.length) {
      return;
    }
    frames.forEach(function (frame) {
      frame.addEventListener("load", function () {
        syncThemeToFrame(frame);
      });
    });
    if (typeof MutationObserver === "undefined") {
      return;
    }
    var observer = new MutationObserver(function (mutations) {
      mutations.forEach(function (mutation) {
        if (mutation.attributeName !== "data-theme") {
          return;
        }
        frames.forEach(syncThemeToFrame);
      });
    });
    try {
      observer.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    } catch (error) {}
  }

  document.addEventListener("DOMContentLoaded", function () {
    var registry = {};
    document.querySelectorAll("[data-crud-modal]").forEach(function (modal) {
      var controller = bindCrudModal(modal);
      registry[controller.name] = controller;
    });
    bindOpeners(registry);
    bindConfirmSubmits();
    bindGlobalEscape(registry);
    bindThemeSyncToFrames();
    window.LvCrudModal = registry;
  });
}());
