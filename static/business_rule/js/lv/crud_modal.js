(function () {
  'use strict';

  function start() {
    var handle = window.APP.FrameModal.bind({
      modalSelector: '[data-crud-modal]',
      frameSelector: '[data-crud-modal-frame]',
      openSelector: '[data-crud-modal-open]',
      closeSelector: '[data-crud-modal-dialog-close]',
      urlAttribute: 'data-crud-modal-open',
      clearFrameOnClose: true
    });
    if (!handle) return;

    window.APP.FrameBridge.on('modal-close', function () {
      handle.close();
    });

    window.APP.FrameBridge.on('modal-complete', function () {
      handle.close();
      window.location.reload();
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
  } else {
    start();
  }
})();
