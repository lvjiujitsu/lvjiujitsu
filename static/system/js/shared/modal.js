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
    if (!dialog) {
      return function () {};
    }
    var focusables = getFocusable(dialog);
    if (!focusables.length) {
      return function () {};
    }
    var first = focusables[0];
    var last = focusables[focusables.length - 1];

    function onKeydown(event) {
      if (event.key !== 'Tab') return;
      var current = getFocusable(dialog);
      if (!current.length) return;
      first = current[0];
      last = current[current.length - 1];
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
    if (!dialog) {
      return function () {};
    }
    options = options || {};
    var releaseTrap = null;
    var previousFocus = document.activeElement;

    function onClose() {
      if (releaseTrap) releaseTrap();
      releaseTrap = null;
      dialog.removeEventListener('close', onClose);
      if (previousFocus && typeof previousFocus.focus === 'function') {
        previousFocus.focus();
      }
      if (options.onClose) options.onClose();
    }

    dialog.addEventListener('close', onClose);
    if (typeof dialog.showModal === 'function') {
      if (!dialog.open) {
        dialog.showModal();
      }
    } else {
      dialog.setAttribute('open', '');
    }
    releaseTrap = trapFocus(dialog);
    return function close() {
      if (typeof dialog.close === 'function') {
        dialog.close();
      } else {
        dialog.removeAttribute('open');
        onClose();
      }
    };
  }

  function bindBackdropClose(dialog) {
    if (!dialog) return;
    dialog.addEventListener('click', function (event) {
      if (event.target === dialog) {
        if (typeof dialog.close === 'function') {
          dialog.close();
        } else {
          dialog.removeAttribute('open');
        }
      }
    });
  }

  function isOpen(el) {
    if (typeof el.open === 'boolean' && el.tagName === 'DIALOG') {
      return el.open;
    }
    return !el.hidden;
  }

  function bindOverlay(el, options) {
    if (!el) {
      return null;
    }
    options = options || {};
    var isDialog = el.tagName === 'DIALOG' && typeof el.showModal === 'function';
    var bodyClass = options.bodyClass || '';
    var closeSelector = options.closeSelector || '';
    var openClass = options.openClass || '';
    var releaseTrap = null;
    var previousFocus = null;

    function lockBody(locked) {
      if (!bodyClass || !document.body) return;
      document.body.classList.toggle(bodyClass, locked);
    }

    function show(trigger) {
      previousFocus = trigger || document.activeElement;
      if (isDialog) {
        if (!el.open) el.showModal();
      } else {
        el.hidden = false;
        el.setAttribute('open', '');
      }
      if (openClass) el.classList.add(openClass);
      lockBody(true);
      if (options.trapFocus !== false) {
        releaseTrap = trapFocus(el);
      }
      if (options.onOpen) options.onOpen(el, trigger || null);
    }

    function teardown() {
      if (releaseTrap) releaseTrap();
      releaseTrap = null;
      if (openClass) el.classList.remove(openClass);
      lockBody(false);
      if (previousFocus && typeof previousFocus.focus === 'function') {
        previousFocus.focus();
      }
      previousFocus = null;
      if (options.onClose) options.onClose(el);
    }

    function hide() {
      if (isDialog) {
        if (el.open) {
          el.close();
        } else {
          teardown();
        }
        return;
      }
      el.hidden = true;
      el.removeAttribute('open');
      teardown();
    }

    if (options.backdropClose !== false) {
      el.addEventListener('click', function (event) {
        if (event.target === el) hide();
      });
    }

    if (closeSelector) {
      el.querySelectorAll(closeSelector).forEach(function (button) {
        button.addEventListener('click', function (event) {
          event.preventDefault();
          hide();
        });
      });
    }

    if (isDialog) {
      el.addEventListener('close', teardown);
      if (options.escapeClose === false) {
        el.addEventListener('cancel', function (event) {
          event.preventDefault();
        });
      }
    } else if (options.escapeClose !== false) {
      document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape' && isOpen(el)) hide();
      });
    }

    return { open: show, close: hide, element: el, isOpen: function () { return isOpen(el); } };
  }

  window.APP = window.APP || {};
  window.APP.Modal = {
    trapFocus: trapFocus,
    openDialog: openDialog,
    bindBackdropClose: bindBackdropClose,
    bindOverlay: bindOverlay,
  };
})(window);
