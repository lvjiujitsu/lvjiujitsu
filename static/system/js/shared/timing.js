(function () {
  'use strict';

  window.APP = window.APP || {};

  function debounce(fn, ms) {
    var delay = typeof ms === 'number' ? ms : 200;
    var timer = null;
    function debounced() {
      var context = this;
      var args = arguments;
      if (timer) window.clearTimeout(timer);
      timer = window.setTimeout(function () {
        timer = null;
        fn.apply(context, args);
      }, delay);
    }
    debounced.cancel = function () {
      if (timer) window.clearTimeout(timer);
      timer = null;
    };
    return debounced;
  }

  function throttle(fn, ms) {
    var interval = typeof ms === 'number' ? ms : 200;
    var last = 0;
    var timer = null;
    var pendingArgs = null;
    var pendingContext = null;

    function invoke(context, args) {
      last = Date.now();
      fn.apply(context, args);
    }

    function throttled() {
      var now = Date.now();
      var remaining = interval - (now - last);
      pendingContext = this;
      pendingArgs = arguments;
      if (remaining <= 0) {
        if (timer) {
          window.clearTimeout(timer);
          timer = null;
        }
        invoke(pendingContext, pendingArgs);
        pendingArgs = null;
        pendingContext = null;
        return;
      }
      if (timer) return;
      timer = window.setTimeout(function () {
        timer = null;
        if (!pendingArgs) return;
        invoke(pendingContext, pendingArgs);
        pendingArgs = null;
        pendingContext = null;
      }, remaining);
    }

    throttled.cancel = function () {
      if (timer) window.clearTimeout(timer);
      timer = null;
      pendingArgs = null;
      pendingContext = null;
    };
    return throttled;
  }

  window.APP.debounce = debounce;
  window.APP.throttle = throttle;
})();
