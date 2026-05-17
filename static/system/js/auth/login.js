(function () {
  'use strict';

  var STORAGE_KEY = 'lv-theme';

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(STORAGE_KEY, theme);
  }

  // Toggle de tema
  var toggleBtn = document.getElementById('theme-toggle');
  if (toggleBtn) {
    toggleBtn.addEventListener('click', function () {
      var current = document.documentElement.getAttribute('data-theme');
      applyTheme(current === 'dark' ? 'light' : 'dark');
    });
  }

  // Visibilidade de senha
  var passwordToggle = document.getElementById('password-toggle');
  var passwordInput = passwordToggle
    ? document.getElementById(passwordToggle.getAttribute('aria-controls'))
    : null;

  if (passwordToggle && passwordInput) {
    passwordToggle.addEventListener('click', function () {
      var isHidden = passwordInput.type === 'password';
      passwordInput.type = isHidden ? 'text' : 'password';
      passwordToggle.setAttribute('aria-label', isHidden ? 'Ocultar senha' : 'Mostrar senha');
    });
  }

})();
