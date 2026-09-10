(function () {
  'use strict';

  window.APP = window.APP || {};

  function removeQueryParams(names) {
    if (!names || !names.length) return;
    if (!window.history || !window.history.replaceState) return;

    var url = new URL(window.location.href);
    var changed = false;
    names.forEach(function (name) {
      if (url.searchParams.has(name)) {
        url.searchParams.delete(name);
        changed = true;
      }
    });
    if (!changed) return;
    window.history.replaceState(window.history.state, '', url.pathname + url.search + url.hash);
  }

  function resolveUrl(url) {
    if (!url) return '';
    try {
      return new URL(url, window.location.href).href;
    } catch (error) {
      return url;
    }
  }

  function setFrameUrl(frame, url) {
    if (!frame || !url) return;
    var resolved = resolveUrl(url);
    if (frame.src !== resolved) {
      frame.src = resolved;
    }
  }

  function openElement(el, bodyClass) {
    if (!el) return;
    if (typeof el.showModal === 'function') {
      if (!el.open) el.showModal();
    } else {
      el.hidden = false;
      el.setAttribute('open', '');
      el.classList.add('is-open');
    }
    if (bodyClass && document.body) document.body.classList.add(bodyClass);
  }

  function closeElement(el, bodyClass) {
    if (!el) return;
    if (typeof el.close === 'function' && el.open) {
      el.close();
    } else {
      el.removeAttribute('open');
      el.hidden = true;
      el.classList.remove('is-open');
      if (bodyClass && document.body) document.body.classList.remove(bodyClass);
    }
  }

  function bind(options) {
    var opts = options || {};
    if (!opts.modalSelector) return null;
    var modal = document.querySelector(opts.modalSelector);
    if (!modal) return null;

    var frame = opts.frameSelector ? modal.querySelector(opts.frameSelector) : modal.querySelector('iframe');
    var bodyClass = opts.bodyClass || '';
    var heightSync = opts.heightSync === undefined ? true : Boolean(opts.heightSync);
    var heightOptions = opts.heightOptions || {};
    var blankUrl = opts.blankUrl || 'about:blank';
    var activeTrigger = null;

    function resizeFrame() {
      if (!heightSync || !window.APP.FrameHeight) return;
      window.APP.FrameHeight.sync(modal, frame, heightOptions);
    }

    function resetHeight() {
      modal.style.height = '';
      if (frame) frame.style.height = '';
    }

    if (frame && heightSync) {
      frame.addEventListener('load', function () {
        resizeFrame();
        window.setTimeout(resizeFrame, 50);
      });
    }

    function open(url, trigger) {
      removeQueryParams(opts.clearBeforeOpen || []);
      activeTrigger = trigger || null;
      resetHeight();
      if (url) {
        setFrameUrl(frame, url);
      } else if (modal.dataset.initialSrc) {
        setFrameUrl(frame, modal.dataset.initialSrc);
      }
      openElement(modal, bodyClass);
      resizeFrame();
      if (opts.onOpen) opts.onOpen(modal, frame, activeTrigger);
    }

    function restoreFocus() {
      if (activeTrigger && typeof activeTrigger.focus === 'function') {
        activeTrigger.focus();
      }
      activeTrigger = null;
    }

    function close() {
      removeQueryParams(opts.clearOnClose || []);
      resetHeight();
      closeElement(modal, bodyClass);
      restoreFocus();
      if (opts.onClose) opts.onClose(modal, frame);
    }

    if (opts.openSelector) {
      document.querySelectorAll(opts.openSelector).forEach(function (button) {
        button.addEventListener('click', function (event) {
          event.preventDefault();
          var url = '';
          if (opts.urlDataset && button.dataset[opts.urlDataset]) {
            url = button.dataset[opts.urlDataset];
          } else if (opts.urlAttribute) {
            url = button.getAttribute(opts.urlAttribute) || '';
          } else {
            url = button.getAttribute('href') || '';
          }
          open(url, button);
        });
      });
    }

    if (opts.closeSelector) {
      modal.querySelectorAll(opts.closeSelector).forEach(function (button) {
        button.addEventListener('click', function (event) {
          event.preventDefault();
          close();
        });
      });
    }

    modal.addEventListener('click', function (event) {
      if (event.target === modal) close();
    });

    modal.addEventListener('close', function () {
      if (bodyClass && document.body) document.body.classList.remove(bodyClass);
      resetHeight();
      if (opts.clearFrameOnClose) setFrameUrl(frame, blankUrl);
      removeQueryParams(opts.clearOnClose || []);
      restoreFocus();
      if (opts.onClose) opts.onClose(modal, frame);
    });

    if (window.APP.FrameBridge) {
      window.APP.FrameBridge.on('modal-close', function () {
        close();
      });
      window.APP.FrameBridge.on('modal-complete', function () {
        close();
        if (opts.reloadOnComplete !== false) window.location.reload();
      });
    }

    if (heightSync && window.APP.FrameHeight) {
      window.APP.FrameHeight.listen(function () {
        if (!modal.open && !modal.classList.contains('is-open')) return null;
        return { modal: modal, frame: frame };
      }, heightOptions);
    }

    if (modal.dataset.modalInitialOpen === 'true') {
      open(modal.dataset.initialSrc || '', null);
    }

    return {
      modal: modal,
      frame: frame,
      open: open,
      close: close,
      resize: resizeFrame
    };
  }

  window.APP.FrameModal = {
    bind: bind,
    removeQueryParams: removeQueryParams,
    resolveUrl: resolveUrl,
    setFrameUrl: setFrameUrl
  };
})();
