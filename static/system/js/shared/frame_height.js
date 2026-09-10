(function () {
  'use strict';

  window.APP = window.APP || {};

  var HEIGHT_TYPE = 'frame-height';
  var DEFAULT_CONTENT_SELECTORS = ['[data-frame-content]', '[data-modal-scroll]'];
  var DEFAULT_HEADER_SELECTORS = ['[data-modal-header]'];
  var DEFAULT_MIN = 280;
  var DEFAULT_MAX_INSET = 32;

  function toList(value, fallback) {
    if (!value) return fallback.slice();
    if (typeof value === 'string') return [value];
    return Array.prototype.slice.call(value);
  }

  function firstMatch(scope, selectors) {
    for (var index = 0; index < selectors.length; index += 1) {
      var found = scope.querySelector(selectors[index]);
      if (found) return found;
    }
    return null;
  }

  function measure(doc, selectors) {
    var scroll = firstMatch(doc, selectors);
    if (!scroll) return null;

    var view = doc.defaultView;
    var styles = view ? view.getComputedStyle(scroll) : null;
    var padTop = styles ? parseFloat(styles.paddingTop) || 0 : 0;
    var padBottom = styles ? parseFloat(styles.paddingBottom) || 0 : 0;
    var innerScroll = scroll.querySelector('[data-frame-form-scroll]');
    var actions = scroll.querySelector('[data-frame-form-actions]');

    if (innerScroll && actions) {
      var form = innerScroll.closest('form');
      var formStyles = form && view ? view.getComputedStyle(form) : null;
      var formGap = formStyles ? parseFloat(formStyles.rowGap) || 0 : 0;
      var formPadTop = formStyles ? parseFloat(formStyles.paddingTop) || 0 : 0;
      var formPadBottom = formStyles ? parseFloat(formStyles.paddingBottom) || 0 : 0;
      return Math.ceil(
        innerScroll.scrollHeight +
          actions.offsetHeight +
          formGap +
          formPadTop +
          formPadBottom +
          padTop +
          padBottom
      );
    }

    var height = Math.max(scroll.scrollHeight - padTop - padBottom, 0);
    if (!height) {
      Array.prototype.forEach.call(scroll.children, function (child) {
        height += child.offsetHeight;
      });
    }
    return Math.ceil(height + padTop + padBottom);
  }

  function sync(modal, frame, opts) {
    if (!modal || !frame) return null;
    var options = opts || {};
    var doc;
    try {
      doc = frame.contentDocument;
    } catch (error) {
      return null;
    }
    if (!doc || !doc.body) return null;

    var contentSelectors = toList(options.contentSelectors, DEFAULT_CONTENT_SELECTORS);
    var contentHeight = measure(doc, contentSelectors);
    if (contentHeight === null && typeof options.height === 'number') {
      contentHeight = options.height;
    }
    if (contentHeight === null) return null;

    var headerSelectors = toList(options.headerSelectors, DEFAULT_HEADER_SELECTORS);
    var header = firstMatch(modal, headerSelectors);
    var headerHeight = header ? header.offsetHeight : 0;
    var min = typeof options.min === 'number' ? options.min : DEFAULT_MIN;
    var maxInset = typeof options.maxInset === 'number' ? options.maxInset : DEFAULT_MAX_INSET;
    var max = Math.max(min, window.innerHeight - maxInset);
    var total = Math.min(Math.max(contentHeight + headerHeight, min), max);

    modal.style.height = total + 'px';
    frame.style.height = total - headerHeight + 'px';
    return total;
  }

  function listen(resolveModal, opts) {
    if (typeof resolveModal !== 'function') return function () {};
    if (!window.APP.FrameBridge) return function () {};
    return window.APP.FrameBridge.on(HEIGHT_TYPE, function (payload, event) {
      var resolved = resolveModal(payload || {}, event);
      if (!resolved) return;
      var modal = resolved.modal || resolved;
      var frame = resolved.frame || (modal && modal.querySelector('iframe'));
      var options = opts || {};
      if (payload && typeof payload.height === 'number') {
        options = {
          contentSelectors: options.contentSelectors,
          headerSelectors: options.headerSelectors,
          min: options.min,
          maxInset: options.maxInset,
          height: payload.height
        };
      }
      sync(modal, frame, options);
    });
  }

  function resolveRoot(selectors) {
    return firstMatch(document, selectors) || document.body;
  }

  function publish(opts) {
    var options = opts || {};
    if (!window.APP.FrameBridge || !window.APP.FrameBridge.isChild()) return function () {};
    var selectors = toList(options.contentSelectors, DEFAULT_CONTENT_SELECTORS);

    function send() {
      var root = resolveRoot(selectors);
      if (!root || !document.body) return;
      var height = Math.ceil(
        Math.max(
          document.documentElement.scrollHeight,
          document.body.scrollHeight,
          root.scrollHeight,
          root.offsetHeight
        )
      );
      window.APP.FrameBridge.post(HEIGHT_TYPE, { height: height, name: options.name || '' });
    }

    send();

    if (typeof ResizeObserver === 'undefined') {
      return function () {};
    }

    var observed = resolveRoot(selectors);
    if (!observed || !(observed instanceof Element)) {
      return function () {};
    }

    var observer = new ResizeObserver(send);
    try {
      observer.observe(observed);
      if (observed !== document.body && document.body) {
        observer.observe(document.body);
      }
    } catch (error) {
      return function () {};
    }
    return function stop() {
      observer.disconnect();
    };
  }

  window.APP.FrameHeight = {
    type: HEIGHT_TYPE,
    measure: measure,
    sync: sync,
    listen: listen,
    publish: publish
  };
})();
