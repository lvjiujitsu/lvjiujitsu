(function () {
  'use strict';

  window.APP = window.APP || {};

  var SHOW_LABEL = 'Mostrar senha';
  var HIDE_LABEL = 'Ocultar senha';

  function controlledInput(toggle) {
    var id = toggle.getAttribute('aria-controls');
    return id ? document.getElementById(id) : null;
  }

  function applyState(toggle, isVisible) {
    var input = controlledInput(toggle);
    if (!input) return;
    input.type = isVisible ? 'text' : 'password';
    toggle.dataset.passwordVisible = String(isVisible);
    toggle.setAttribute('aria-pressed', String(isVisible));
    toggle.setAttribute('aria-label', isVisible ? HIDE_LABEL : SHOW_LABEL);
    toggle.setAttribute('title', isVisible ? HIDE_LABEL : SHOW_LABEL);
    var showIcon = toggle.querySelector('[data-password-icon-show]');
    var hideIcon = toggle.querySelector('[data-password-icon-hide]');
    if (showIcon) showIcon.hidden = isVisible;
    if (hideIcon) hideIcon.hidden = !isVisible;
  }

  function bind(toggle) {
    if (!toggle || toggle.dataset.passwordToggleBound === 'true') return;
    if (!controlledInput(toggle)) return;
    toggle.dataset.passwordToggleBound = 'true';
    applyState(toggle, toggle.dataset.passwordVisible === 'true');
    toggle.addEventListener('click', function (event) {
      event.preventDefault();
      var input = controlledInput(toggle);
      var isVisible = Boolean(input) && input.type === 'text';
      applyState(toggle, !isVisible);
      if (input) input.focus();
    });
  }

  function bindAll(root) {
    var scope = root || document;
    if (!scope || typeof scope.querySelectorAll !== 'function') return;
    scope.querySelectorAll('[data-password-toggle][aria-controls]').forEach(bind);
  }

  window.APP.PasswordToggle = {
    bind: bind,
    bindAll: bindAll,
    applyState: applyState
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      bindAll(document);
    });
  } else {
    bindAll(document);
  }
})();
