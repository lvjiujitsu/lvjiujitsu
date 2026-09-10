(function () {
  'use strict';

  window.APP = window.APP || {};

  function hide(node, fadeMs) {
    node.style.transition = 'opacity ' + fadeMs + 'ms';
    node.style.opacity = '0';
    window.setTimeout(function () {
      node.hidden = true;
    }, fadeMs);
  }

  function bindAutoDismiss(options) {
    var opts = options || {};
    var selector = opts.selector || '[data-messages], .system-messages';
    var delay = typeof opts.delay === 'number' ? opts.delay : 5000;
    var fadeMs = typeof opts.fadeMs === 'number' ? opts.fadeMs : 400;
    var closeSelector = opts.closeSelector || '[data-message-close]';
    var nodes = document.querySelectorAll(selector);
    if (!nodes.length) return;

    nodes.forEach(function (node) {
      if (node.dataset.autoDismissBound === 'true') return;
      node.dataset.autoDismissBound = 'true';

      if (closeSelector) {
        node.querySelectorAll(closeSelector).forEach(function (button) {
          button.addEventListener('click', function (event) {
            event.preventDefault();
            hide(node, fadeMs);
          });
        });
      }

      if (delay <= 0) return;
      window.setTimeout(function () {
        if (node.hidden) return;
        hide(node, fadeMs);
      }, delay);
    });
  }

  window.APP.Messages = {
    bindAutoDismiss: bindAutoDismiss
  };
})();
