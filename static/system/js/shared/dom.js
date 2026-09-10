(function () {
  'use strict';

  window.APP = window.APP || {};

  function clearChildren(node) {
    if (!node) return;
    while (node.firstChild) {
      node.removeChild(node.firstChild);
    }
  }

  function el(tag, opts, children) {
    var node = document.createElement(tag);
    opts = opts || {};
    if (opts.className) node.className = opts.className;
    if (opts.text !== undefined && opts.text !== null) node.textContent = opts.text;
    if (opts.attrs) {
      Object.keys(opts.attrs).forEach(function (key) {
        node.setAttribute(key, opts.attrs[key]);
      });
    }
    (children || []).forEach(function (child) {
      if (child) node.appendChild(child);
    });
    return node;
  }

  function parseMarkup(markup) {
    var parser = new DOMParser();
    var doc = parser.parseFromString('<body>' + String(markup) + '</body>', 'text/html');
    var frag = document.createDocumentFragment();
    while (doc.body.firstChild) {
      frag.appendChild(doc.body.firstChild);
    }
    return frag;
  }

  function setSelectOptions(select, options) {
    if (!select) return;
    clearChildren(select);
    (options || []).forEach(function (opt) {
      var option = document.createElement('option');
      option.value = opt.value != null ? String(opt.value) : '';
      option.textContent = opt.label != null ? String(opt.label) : '';
      if (opt.selected) option.selected = true;
      select.appendChild(option);
    });
  }

  function setButtonTextWithSvg(btn, text, svgMarkup, opts) {
    if (!btn) return;
    opts = opts || {};
    var svgFirst = !!opts.svgFirst;
    clearChildren(btn);
    function appendSvg() {
      if (!svgMarkup) return;
      var frag = parseMarkup(svgMarkup);
      while (frag.firstChild) {
        btn.appendChild(frag.firstChild);
      }
    }
    if (svgFirst) {
      appendSvg();
      if (text != null && text !== '') {
        btn.appendChild(document.createTextNode(text));
      }
    } else {
      if (text != null && text !== '') {
        btn.appendChild(document.createTextNode(text));
      }
      appendSvg();
    }
  }

  window.APP.DOM = {
    clearChildren: clearChildren,
    el: el,
    parseMarkup: parseMarkup,
    setSelectOptions: setSelectOptions,
    setButtonTextWithSvg: setButtonTextWithSvg,
  };
})();
