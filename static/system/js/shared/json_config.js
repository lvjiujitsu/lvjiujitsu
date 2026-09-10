(function () {
  'use strict';

  window.APP = window.APP || {};

  function readJsonScript(id, fallback) {
    var value = fallback === undefined ? null : fallback;
    if (!id) {
      return value;
    }
    var node = document.getElementById(id);
    if (!node) {
      return value;
    }
    var raw = node.textContent;
    if (raw === null || raw === undefined || String(raw).trim() === '') {
      return value;
    }
    try {
      var parsed = JSON.parse(raw);
      return parsed === null && fallback !== undefined ? fallback : parsed;
    } catch (error) {
      return value;
    }
  }

  window.APP.readJsonScript = readJsonScript;
})();
