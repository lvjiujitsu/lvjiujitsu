(function () {
  function postToParent(type) {
    if (window.parent && window.parent !== window) {
      window.parent.postMessage(
        { type: type, modalName: document.body.getAttribute('data-modal-name') || '' },
        window.location.origin
      );
    }
  }

  document.addEventListener('click', function (event) {
    var closeTrigger = event.target.closest('[data-modal-close]');
    if (closeTrigger) {
      postToParent('lv-modal-close');
    }
  });

  if (document.body.hasAttribute('data-modal-auto-complete')) {
    postToParent('lv-modal-complete');
  }
})();
