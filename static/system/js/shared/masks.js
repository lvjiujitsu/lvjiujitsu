(function () {
  'use strict';

  window.APP = window.APP || {};

  function digits(value) {
    return String(value == null ? '' : value).replace(/\D/g, '');
  }

  function cpf(value) {
    var d = digits(value).slice(0, 11);
    if (d.length <= 3) return d;
    if (d.length <= 6) return d.slice(0, 3) + '.' + d.slice(3);
    if (d.length <= 9) return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6);
    return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9);
  }

  function cnpj(value) {
    var d = digits(value).slice(0, 14);
    if (d.length <= 2) return d;
    if (d.length <= 5) return d.slice(0, 2) + '.' + d.slice(2);
    if (d.length <= 8) return d.slice(0, 2) + '.' + d.slice(2, 5) + '.' + d.slice(5);
    if (d.length <= 12) {
      return d.slice(0, 2) + '.' + d.slice(2, 5) + '.' + d.slice(5, 8) + '/' + d.slice(8);
    }
    return (
      d.slice(0, 2) +
      '.' +
      d.slice(2, 5) +
      '.' +
      d.slice(5, 8) +
      '/' +
      d.slice(8, 12) +
      '-' +
      d.slice(12)
    );
  }

  function phone(value) {
    var d = digits(value).slice(0, 11);
    if (d.length <= 2) return d.length ? '(' + d : '';
    if (d.length <= 6) return '(' + d.slice(0, 2) + ') ' + d.slice(2);
    if (d.length <= 10) return '(' + d.slice(0, 2) + ') ' + d.slice(2, 6) + '-' + d.slice(6);
    return '(' + d.slice(0, 2) + ') ' + d.slice(2, 7) + '-' + d.slice(7);
  }

  function cep(value) {
    var d = digits(value).slice(0, 8);
    if (d.length <= 5) return d;
    return d.slice(0, 5) + '-' + d.slice(5);
  }

  function date(value) {
    var d = digits(value).slice(0, 8);
    if (d.length <= 2) return d;
    if (d.length <= 4) return d.slice(0, 2) + '/' + d.slice(2);
    return d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
  }

  var FORMATTERS = {
    cpf: cpf,
    cnpj: cnpj,
    phone: phone,
    cep: cep,
    date: date
  };

  function bind(el, fn) {
    if (!el || typeof fn !== 'function') return;
    if (el.dataset.maskBound === 'true') return;
    el.dataset.maskBound = 'true';
    el.addEventListener('input', function () {
      var caret = el.selectionStart;
      var previous = el.value;
      var masked = fn(previous);
      if (masked === previous) return;
      el.value = masked;
      if (typeof caret !== 'number') return;
      var next = caret + masked.length - previous.length;
      if (next < 0) next = 0;
      if (next > masked.length) next = masked.length;
      try {
        el.setSelectionRange(next, next);
      } catch (error) {
        el.value = masked;
      }
    });
  }

  function bindAll(root) {
    var scope = root || document;
    if (!scope || typeof scope.querySelectorAll !== 'function') return;
    scope.querySelectorAll('[data-mask]').forEach(function (el) {
      var fn = FORMATTERS[el.getAttribute('data-mask')];
      if (fn) bind(el, fn);
    });
  }

  window.APP.Mask = {
    digits: digits,
    cpf: cpf,
    cnpj: cnpj,
    phone: phone,
    cep: cep,
    date: date,
    bind: bind,
    bindAll: bindAll
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      bindAll(document);
    });
  } else {
    bindAll(document);
  }
})();
