(function () {
  'use strict';

  window.APP = window.APP || {};

  var DEFAULT_ERROR_SELECTORS =
    '.errorlist, .form-message--error, .messages .error, .input-error, [aria-invalid="true"]';

  function bindSubmitLock(form, button, options) {
    if (!form) return;
    var opts = options || {};
    var target = button || form.querySelector('[data-submit-lock]');
    if (!target) return;
    if (form.dataset.submitLockBound === 'true') return;
    form.dataset.submitLockBound = 'true';

    form.addEventListener('submit', function () {
      if (target.disabled) return;
      target.disabled = true;
      target.dataset.state = 'submitting';
      target.setAttribute('aria-busy', 'true');
      var label = opts.loadingLabel || target.dataset.loadingLabel;
      if (label) {
        target.textContent = label;
      }
    });
  }

  function revealOnDirty(form, target, options) {
    if (!form || !target) return;
    var opts = options || {};
    var targets = typeof target.length === 'number' && !target.tagName
      ? Array.prototype.slice.call(target)
      : [target];
    if (!targets.length) return;

    function reveal() {
      targets.forEach(function (node) {
        if (node) node.hidden = false;
      });
      form.removeEventListener('input', reveal);
      form.removeEventListener('change', reveal);
    }

    var errorSelectors = opts.errorSelectors || DEFAULT_ERROR_SELECTORS;
    if (errorSelectors && document.querySelector(errorSelectors)) {
      reveal();
      return;
    }

    form.addEventListener('input', reveal);
    form.addEventListener('change', reveal);
  }

  window.APP.FormState = {
    bindSubmitLock: bindSubmitLock,
    revealOnDirty: revealOnDirty
  };
})();
