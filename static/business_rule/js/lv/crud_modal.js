(function () {
  function initCrudModal(dialog) {
    var frame = dialog.querySelector('[data-crud-modal-frame]');
    if (!frame) return;

    if (window.APP && window.APP.Modal) {
      window.APP.Modal.bindBackdropClose(dialog);
    }

    document.querySelectorAll('[data-crud-modal-open]').forEach(function (trigger) {
      trigger.addEventListener('click', function (event) {
        event.preventDefault();
        frame.src = trigger.getAttribute('data-crud-modal-open');
        if (window.APP && window.APP.Modal) {
          window.APP.Modal.openDialog(dialog);
        } else if (typeof dialog.showModal === 'function') {
          dialog.showModal();
        } else {
          dialog.setAttribute('open', '');
        }
      });
    });

    dialog.addEventListener('click', function (event) {
      if (event.target === dialog) {
        dialog.close();
      }
    });

    var closeButton = dialog.querySelector('[data-crud-modal-dialog-close]');
    if (closeButton) {
      closeButton.addEventListener('click', function () {
        dialog.close();
      });
    }

    dialog.addEventListener('close', function () {
      frame.src = 'about:blank';
    });

    window.addEventListener('message', function (event) {
      if (event.origin !== window.location.origin) return;
      var data = event.data || {};
      if (data.type === 'lv-modal-close') {
        dialog.close();
      } else if (data.type === 'lv-modal-complete') {
        dialog.close();
        window.location.reload();
      }
    });
  }

  document.querySelectorAll('[data-crud-modal]').forEach(initCrudModal);
})();
