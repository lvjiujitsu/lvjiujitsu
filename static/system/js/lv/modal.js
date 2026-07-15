(function (window) {
  'use strict';

  var FOCUSABLE =
    'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';

  function getFocusable(dialog) {
    return Array.prototype.filter.call(
      dialog.querySelectorAll(FOCUSABLE),
      function (el) {
        return !el.hasAttribute('disabled') && el.getAttribute('aria-hidden') !== 'true';
      }
    );
  }

  function trapFocus(dialog) {
    var focusables = getFocusable(dialog);
    if (!focusables.length) {
      return function () {};
    }
    var first = focusables[0];
    var last = focusables[focusables.length - 1];

    function onKeydown(event) {
      if (event.key !== 'Tab') return;
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }

    dialog.addEventListener('keydown', onKeydown);
    first.focus();
    return function release() {
      dialog.removeEventListener('keydown', onKeydown);
    };
  }

  function openDialog(dialog, options) {
    options = options || {};
    var releaseTrap = null;
    var previousFocus = document.activeElement;

    function onClose() {
      if (releaseTrap) releaseTrap();
      dialog.removeEventListener('close', onClose);
      if (previousFocus && typeof previousFocus.focus === 'function') {
        previousFocus.focus();
      }
      if (options.onClose) options.onClose();
    }

    dialog.addEventListener('close', onClose);
    if (typeof dialog.showModal === 'function') {
      dialog.showModal();
    } else {
      dialog.setAttribute('open', '');
    }
    releaseTrap = trapFocus(dialog);
    return function close() {
      dialog.close();
    };
  }

  function bindBackdropClose(dialog) {
    dialog.addEventListener('click', function (event) {
      if (event.target === dialog) {
        dialog.close();
      }
    });
  }

  window.LV = window.LV || {};
  window.LV.Modal = {
    trapFocus: trapFocus,
    openDialog: openDialog,
    bindBackdropClose: bindBackdropClose,
  };
})(window);
