(function () {
  var toggle = document.querySelector('[data-dashboard-actions-toggle]');
  var secondary = document.querySelector('[data-dashboard-actions-secondary]');
  var mobileQuery = window.matchMedia ? window.matchMedia('(max-width: 640px)') : null;
  var isExpanded = false;

  if (!toggle || !secondary || !mobileQuery) return;

  function render() {
    if (!mobileQuery.matches) {
      toggle.hidden = true;
      toggle.setAttribute('aria-expanded', 'true');
      secondary.setAttribute('aria-hidden', 'false');
      return;
    }

    toggle.hidden = false;
    toggle.setAttribute('aria-expanded', isExpanded ? 'true' : 'false');
    toggle.textContent = isExpanded ? 'Mostrar menos atalhos' : 'Mostrar mais atalhos';
    secondary.setAttribute('aria-hidden', isExpanded ? 'false' : 'true');
  }

  toggle.addEventListener('click', function () {
    isExpanded = !isExpanded;
    render();
  });

  if (mobileQuery.addEventListener) {
    mobileQuery.addEventListener('change', function (event) {
      if (!event.matches) isExpanded = false;
      render();
    });
  } else if (mobileQuery.addListener) {
    mobileQuery.addListener(function (event) {
      if (!event.matches) isExpanded = false;
      render();
    });
  }

  render();
})();
