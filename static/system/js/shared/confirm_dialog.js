(function () {
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

  window.APP = window.APP || {};
  window.APP.Confirm = { request: request, notify: notify };

  bindForms();
  bindControls();
})();
