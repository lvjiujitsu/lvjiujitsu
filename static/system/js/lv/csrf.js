(function () {
  'use strict';

  function getCookie(name) {
    var parts = document.cookie ? document.cookie.split(';') : [];
    for (var i = 0; i < parts.length; i += 1) {
      var part = parts[i].trim();
      if (part.substring(0, name.length + 1) === name + '=') {
        return decodeURIComponent(part.substring(name.length + 1));
      }
    }
    return '';
  }

  function getCsrfToken() {
    var input = document.querySelector('input[name="csrfmiddlewaretoken"]');
    return input ? input.value : getCookie('csrftoken');
  }

  window.LV = window.LV || {};
  window.LV.getCsrfToken = getCsrfToken;
})();
