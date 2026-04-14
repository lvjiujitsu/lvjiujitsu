(function () {
  var openBtn = document.getElementById('js-menu-open');
  var closeBtn = document.getElementById('js-menu-close');
  var drawer = document.getElementById('js-drawer');
  var overlay = document.getElementById('js-overlay');

  if (!openBtn || !drawer || !overlay) return;

  function open() {
    drawer.style.transform = 'translateX(0)';
    overlay.style.display = 'block';
  }

  function close() {
    drawer.style.transform = 'translateX(-100%)';
    overlay.style.display = 'none';
  }

  openBtn.addEventListener('click', open);
  if (closeBtn) closeBtn.addEventListener('click', close);
  overlay.addEventListener('click', close);

  drawer.addEventListener('click', function (e) {
    if (e.target.closest && e.target.closest('a')) close();
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && overlay.style.display === 'block') close();
  });
})();
