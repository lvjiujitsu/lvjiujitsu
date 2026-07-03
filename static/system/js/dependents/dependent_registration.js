(function () {
  'use strict';

  function notifyParent(type) {
    if (window.parent === window) return;
    window.parent.postMessage({ type: type }, window.location.origin);
  }

  function bindCloseButtons() {
    document.querySelectorAll('[data-dependent-frame-close]').forEach(function (button) {
      button.addEventListener('click', function () {
        notifyParent('dependent-modal-close');
      });
    });
  }

  function bindSubmitState() {
    var form = document.querySelector('.dependent-form');
    if (!form) return;

    form.addEventListener('submit', function () {
      var button = form.querySelector('button[type="submit"]');
      if (!button) return;
      button.disabled = true;
      button.textContent = 'Enviando...';
    });
  }

  function bindEscapeClose() {
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') {
        notifyParent('dependent-modal-close');
      }
    });
  }

  bindCloseButtons();
  bindEscapeClose();
  bindSubmitState();
})();
