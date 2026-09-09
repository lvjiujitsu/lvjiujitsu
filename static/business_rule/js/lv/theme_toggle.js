(function () {
  var toggle = document.getElementById('theme-toggle');
  if (!toggle) return;
  var sun = document.getElementById('icon-sun');
  var moon = document.getElementById('icon-moon');

  function applyIcons(theme) {
    if (!sun || !moon) return;
    if (theme === 'dark') {
      sun.removeAttribute('hidden');
      moon.setAttribute('hidden', '');
    } else {
      moon.removeAttribute('hidden');
      sun.setAttribute('hidden', '');
    }
  }

  applyIcons(document.documentElement.getAttribute('data-theme') || 'light');

  toggle.addEventListener('click', function () {
    var next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    localStorage.setItem(window.THEME_STORAGE_KEY, next);
    document.documentElement.setAttribute('data-theme', next);
    applyIcons(next);
  });
})();
