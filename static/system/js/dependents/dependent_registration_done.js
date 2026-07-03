(function () {
  'use strict';

  if (window.parent !== window) {
    window.parent.postMessage({ type: 'dependent-modal-done' }, window.location.origin);
  }
})();
