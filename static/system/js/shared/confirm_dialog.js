(function () {
  "use strict";

  var GRANTED = "confirmGranted";
  var dialog = null;
  var titleEl = null;
  var messageEl = null;
  var confirmButton = null;
  var cancelButton = null;
  var pending = null;

  function build() {
    if (dialog) {
      return dialog;
    }
    dialog = document.createElement("dialog");
    dialog.className = "app-confirm";
    dialog.setAttribute("aria-modal", "true");
    dialog.innerHTML =
      '<div class="app-confirm__panel">' +
      '<h2 class="app-confirm__title"></h2>' +
      '<p class="app-confirm__message"></p>' +
      '<div class="app-confirm__actions">' +
      '<button type="button" class="app-confirm__button app-confirm__button--cancel"></button>' +
      '<button type="button" class="app-confirm__button app-confirm__button--confirm"></button>' +
      "</div>" +
      "</div>";

    titleEl = dialog.querySelector(".app-confirm__title");
    messageEl = dialog.querySelector(".app-confirm__message");
    cancelButton = dialog.querySelector(".app-confirm__button--cancel");
    confirmButton = dialog.querySelector(".app-confirm__button--confirm");

    cancelButton.addEventListener("click", function () {
      settle(false);
    });
    confirmButton.addEventListener("click", function () {
      settle(true);
    });
    dialog.addEventListener("cancel", function (event) {
      event.preventDefault();
      settle(false);
    });
    dialog.addEventListener("keydown", function (event) {
      if (event.key !== "Escape") {
        return;
      }
      event.preventDefault();
      event.stopPropagation();
      settle(false);
    });
    dialog.addEventListener("close", function () {
      settle(false);
    });

    document.body.appendChild(dialog);
    return dialog;
  }

  function open() {
    if (typeof dialog.showModal === "function" && !dialog.open) {
      dialog.showModal();
    } else if (typeof dialog.show === "function" && !dialog.open) {
      dialog.show();
    }
    dialog.classList.add("is-open");
  }

  function settle(result) {
    var resolver = pending;
    pending = null;
    dialog.classList.remove("is-open");
    if (dialog.open) {
      dialog.close();
    }
    if (resolver) {
      resolver(result);
    }
  }

  function request(options) {
    var opts = options || {};
    var isNotify = opts.mode === "notify";
    build();
    if (pending) {
      settle(false);
    }
    titleEl.textContent = opts.title || (isNotify ? "Aviso" : "Confirmar ação");
    messageEl.textContent = opts.message || "Confirma esta ação?";
    confirmButton.textContent = opts.confirmLabel || (isNotify ? "Entendi" : "Confirmar");
    cancelButton.textContent = opts.cancelLabel || "Cancelar";
    cancelButton.hidden = isNotify;
    dialog.classList.toggle("app-confirm--danger", opts.tone === "danger");

    return new Promise(function (resolve) {
      pending = resolve;
      open();
      var initial = isNotify ? confirmButton : cancelButton;
      initial.focus({ preventScroll: true });
    });
  }

  function notify(message, options) {
    var opts = options || {};
    opts.mode = "notify";
    opts.message = message;
    return request(opts);
  }

  function messageFor(element) {
    return (
      element.dataset.confirmMessage ||
      element.dataset.confirm ||
      "Confirma esta ação?"
    );
  }

  function wasGranted(element) {
    if (element.dataset[GRANTED] !== "1") {
      return false;
    }
    delete element.dataset[GRANTED];
    return true;
  }

  function grant(element, replay) {
    element.dataset[GRANTED] = "1";
    replay();
  }

  function bindForms() {
    document.addEventListener(
      "submit",
      function (event) {
        var form = event.target.closest("form[data-confirm-submit], form[data-confirm]");
        if (!form || wasGranted(form)) {
          return;
        }
        event.preventDefault();
        event.stopPropagation();
        var submitter = event.submitter;
        request({ message: messageFor(form), tone: form.dataset.confirmTone }).then(
          function (accepted) {
            if (!accepted) {
              return;
            }
            grant(form, function () {
              if (typeof form.requestSubmit === "function") {
                form.requestSubmit(submitter || undefined);
              } else {
                form.submit();
              }
            });
          }
        );
      },
      true
    );
  }

  function bindControls() {
    document.addEventListener(
      "click",
      function (event) {
        var control = event.target.closest("[data-confirm]:not(form)");
        if (!control || wasGranted(control)) {
          return;
        }
        event.preventDefault();
        event.stopPropagation();
        request({ message: messageFor(control), tone: control.dataset.confirmTone }).then(
          function (accepted) {
            if (!accepted) {
              return;
            }
            grant(control, function () {
              control.click();
            });
          }
        );
      },
      true
    );
  }

  var promptDialog = null;
  var promptNodes = null;

  function buildPrompt() {
    if (promptDialog) {
      return promptDialog;
    }
    promptDialog = document.createElement("dialog");
    promptDialog.className = "app-prompt";
    promptDialog.setAttribute("aria-modal", "true");
    promptDialog.innerHTML =
      '<form method="dialog" class="app-prompt__panel">' +
      '<h2 class="app-prompt__title"></h2>' +
      '<p class="app-prompt__message"></p>' +
      '<label class="app-prompt__field">' +
      '<span class="app-prompt__label"></span>' +
      '<input type="text" class="app-prompt__input">' +
      "</label>" +
      '<p class="app-prompt__error" hidden></p>' +
      '<div class="app-prompt__actions">' +
      '<button type="button" class="app-prompt__button app-prompt__button--cancel"></button>' +
      '<button type="button" class="app-prompt__button app-prompt__button--confirm"></button>' +
      "</div>" +
      "</form>";

    promptNodes = {
      title: promptDialog.querySelector(".app-prompt__title"),
      message: promptDialog.querySelector(".app-prompt__message"),
      field: promptDialog.querySelector(".app-prompt__field"),
      label: promptDialog.querySelector(".app-prompt__label"),
      input: promptDialog.querySelector(".app-prompt__input"),
      error: promptDialog.querySelector(".app-prompt__error"),
      cancel: promptDialog.querySelector(".app-prompt__button--cancel"),
      confirm: promptDialog.querySelector(".app-prompt__button--confirm")
    };

    document.body.appendChild(promptDialog);
    return promptDialog;
  }

  function prompt(options) {
    var opts = options || {};
    if (!document.body) {
      return Promise.resolve(null);
    }
    buildPrompt();
    var nodes = promptNodes;
    var wantsText = Boolean(opts.fieldLabel);

    nodes.title.textContent = opts.title || "Confirmar";
    nodes.message.textContent = opts.message || "";
    nodes.message.hidden = !opts.message;
    nodes.error.hidden = true;
    nodes.error.textContent = "";
    nodes.confirm.textContent = opts.confirmLabel || "Confirmar";
    nodes.cancel.textContent = opts.cancelLabel || "Cancelar";
    nodes.confirm.classList.toggle("app-prompt__button--danger", Boolean(opts.tone === "danger" || opts.danger));
    nodes.field.hidden = !wantsText;
    if (wantsText) {
      nodes.label.textContent = opts.fieldLabel;
      nodes.input.value = opts.value || "";
      nodes.input.maxLength = opts.maxLength || 120;
    }

    return new Promise(function (resolve) {
      function finish(value) {
        nodes.cancel.removeEventListener("click", onCancel);
        nodes.confirm.removeEventListener("click", onConfirm);
        nodes.input.removeEventListener("keydown", onKeydown);
        promptDialog.removeEventListener("cancel", onCancel);
        if (promptDialog.open && typeof promptDialog.close === "function") {
          promptDialog.close();
        } else {
          promptDialog.removeAttribute("open");
        }
        resolve(value);
      }

      function onCancel(event) {
        if (event) event.preventDefault();
        finish(null);
      }

      function onConfirm() {
        if (!wantsText) {
          finish(true);
          return;
        }
        var value = nodes.input.value.trim();
        if (!value) {
          nodes.error.textContent = opts.requiredMessage || "Preencha este campo.";
          nodes.error.hidden = false;
          nodes.input.focus();
          return;
        }
        finish(value);
      }

      function onKeydown(event) {
        if (event.key === "Enter") {
          event.preventDefault();
          onConfirm();
        }
      }

      nodes.cancel.addEventListener("click", onCancel);
      nodes.confirm.addEventListener("click", onConfirm);
      nodes.input.addEventListener("keydown", onKeydown);
      promptDialog.addEventListener("cancel", onCancel);

      if (typeof promptDialog.showModal === "function" && !promptDialog.open) {
        promptDialog.showModal();
      } else {
        promptDialog.setAttribute("open", "");
      }
      (wantsText ? nodes.input : nodes.confirm).focus();
    });
  }

  function bindDeleteTriggers(selector) {
    var dialogSelector = selector || "[data-confirm-delete-dialog]";
    document.querySelectorAll(dialogSelector).forEach(function (deleteDialog) {
      var form = deleteDialog.querySelector("[data-confirm-delete-form]");
      var nameEl = deleteDialog.querySelector("[data-confirm-delete-name]");

      document.querySelectorAll("[data-confirm-delete-open]").forEach(function (trigger) {
        trigger.addEventListener("click", function (event) {
          event.preventDefault();
          if (form) {
            form.action =
              trigger.getAttribute("data-confirm-delete-action") ||
              trigger.getAttribute("href") ||
              form.action;
          }
          if (nameEl) {
            nameEl.textContent = trigger.getAttribute("data-confirm-delete-label") || "";
          }
          if (typeof deleteDialog.showModal === "function") {
            if (!deleteDialog.open) deleteDialog.showModal();
          } else {
            deleteDialog.setAttribute("open", "");
          }
        });
      });

      deleteDialog.querySelectorAll("[data-confirm-delete-cancel]").forEach(function (button) {
        button.addEventListener("click", function (event) {
          event.preventDefault();
          if (typeof deleteDialog.close === "function" && deleteDialog.open) {
            deleteDialog.close();
          } else {
            deleteDialog.removeAttribute("open");
          }
        });
      });

      deleteDialog.addEventListener("click", function (event) {
        if (event.target !== deleteDialog) return;
        if (typeof deleteDialog.close === "function" && deleteDialog.open) {
          deleteDialog.close();
        } else {
          deleteDialog.removeAttribute("open");
        }
      });
    });
  }

  window.APP = window.APP || {};

  function bindDialogTriggers(options) {
    var opts = options || {};
    var openSelector = opts.openSelector;
    var closeSelector = opts.closeSelector;
    if (!openSelector) return;
    var bodyClass = opts.bodyClass || '';
    var triggers = new WeakMap();

    function show(dialog, trigger) {
      if (!dialog) return;
      if (trigger) triggers.set(dialog, trigger);
      if (typeof dialog.showModal === 'function') {
        if (!dialog.open) dialog.showModal();
      } else {
        dialog.setAttribute('open', '');
        dialog.classList.add('is-open');
      }
      if (bodyClass) document.body.classList.add(bodyClass);
    }

    function hide(dialog) {
      if (!dialog) return;
      if (typeof dialog.close === 'function' && dialog.open) {
        dialog.close();
      } else {
        dialog.removeAttribute('open');
        dialog.classList.remove('is-open');
      }
      if (bodyClass) document.body.classList.remove(bodyClass);
      var trigger = triggers.get(dialog);
      if (trigger && typeof trigger.focus === 'function') trigger.focus();
    }

    document.addEventListener('click', function (event) {
      var opener = event.target.closest(openSelector);
      if (opener) {
        event.preventDefault();
        show(document.getElementById(opener.getAttribute('aria-controls')), opener);
        return;
      }
      if (!closeSelector) return;
      var closer = event.target.closest(closeSelector);
      if (closer) {
        event.preventDefault();
        hide(closer.closest('dialog'));
      }
    });

    document.querySelectorAll('dialog').forEach(function (dialog) {
      dialog.addEventListener('click', function (event) {
        if (event.target === dialog) hide(dialog);
      });
    });
  }

  window.APP.Confirm = {
    request: request,
    notify: notify,
    prompt: prompt,
    bindDeleteTriggers: bindDeleteTriggers,
    bindDialogTriggers: bindDialogTriggers
  };

  bindForms();
  bindControls();

  function autoBind() {
    bindDeleteTriggers();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', autoBind);
  } else {
    autoBind();
  }

})();
