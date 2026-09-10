(function () {
  'use strict';

  window.APP = window.APP || {};

  var CLOSE_TYPE = 'modal-close';
  var COMPLETE_TYPE = 'modal-complete';

  function bridge() {
    return window.APP.FrameBridge || null;
  }

  function modalName() {
    return (document.body && document.body.getAttribute('data-modal-name')) || '';
  }

  function close(payload) {
    var api = bridge();
    if (!api || !api.isChild()) return false;
    var data = payload || {};
    return api.post(CLOSE_TYPE, { name: data.name || modalName() });
  }

  function complete(payload) {
    var api = bridge();
    if (!api || !api.isChild()) return false;
    var data = payload || {};
    return api.post(COMPLETE_TYPE, { name: data.name || modalName(), result: data.result || null });
  }

  function publishHeight(opts) {
    if (!window.APP.FrameHeight) return function () {};
    return window.APP.FrameHeight.publish(opts || { name: modalName() });
  }

  function bindTriggers() {
    document.addEventListener('click', function (event) {
      var closeTrigger = event.target.closest('[data-modal-close]');
      if (closeTrigger) {
        event.preventDefault();
        close({ name: closeTrigger.getAttribute('data-modal-close') || '' });
        return;
      }
      var completeTrigger = event.target.closest('[data-modal-complete]');
      if (completeTrigger) {
        event.preventDefault();
        complete({ name: completeTrigger.getAttribute('data-modal-complete') || '' });
      }
    });
  }

  function start() {
    if (!bridge() || !bridge().isChild()) return;
    bindTriggers();
    if (document.body && document.body.hasAttribute('data-modal-auto-complete')) {
      complete({});
    }
    if (document.body && document.body.hasAttribute('data-modal-height-sync')) {
      publishHeight({ name: modalName() });
    }
  }

  window.APP.ModalChild = {
    close: close,
    complete: complete,
    publishHeight: publishHeight
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
  } else {
    start();
  }
})();
