(function () {
  var trigger = document.querySelector('[data-portal-menu-trigger]');
  var drawer = document.querySelector('[data-portal-drawer]');
  var backdrop = document.querySelector('[data-portal-drawer-backdrop]');
  var closeBtn = document.querySelector('[data-portal-drawer-close]');
  var lastFocused = null;
  var focusableSelector = 'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])';

  if (!trigger || !drawer || !backdrop) return;

  function getFocusableElements() {
    return drawer.querySelectorAll(focusableSelector);
  }

  function setMenuState(isOpen) {
    drawer.classList.toggle('is-open', isOpen);
    backdrop.classList.toggle('is-visible', isOpen);
    drawer.setAttribute('aria-hidden', isOpen ? 'false' : 'true');
    backdrop.setAttribute('aria-hidden', isOpen ? 'false' : 'true');
    trigger.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    document.body.classList.toggle('is-lock-scroll', isOpen);
  }

  function open() {
    lastFocused = document.activeElement;
    setMenuState(true);
    window.setTimeout(function () {
      if (closeBtn) {
        closeBtn.focus();
        return;
      }

      var focusable = getFocusableElements();
      if (focusable.length) focusable[0].focus();
    }, 0);
  }

  function close() {
    setMenuState(false);
    if (lastFocused && typeof lastFocused.focus === 'function') {
      lastFocused.focus();
    }
  }

  trigger.addEventListener('click', function () {
    var isOpen = drawer.classList.contains('is-open');
    isOpen ? close() : open();
  });

  if (backdrop) backdrop.addEventListener('click', close);
  if (closeBtn) closeBtn.addEventListener('click', close);
  drawer.addEventListener('click', function (event) {
    var clickTarget = event.target instanceof Element ? event.target.closest('a[href]') : null;
    if (clickTarget) close();
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && drawer.classList.contains('is-open')) close();

    if (e.key !== 'Tab' || !drawer.classList.contains('is-open')) return;

    var focusable = Array.prototype.slice.call(getFocusableElements());
    if (!focusable.length) return;

    var first = focusable[0];
    var last = focusable[focusable.length - 1];

    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    }

    if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  });

  setMenuState(false);
})();
