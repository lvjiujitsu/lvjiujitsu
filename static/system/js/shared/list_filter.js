(function () {
  'use strict';

  window.APP = window.APP || {};

  var COMBINING = new RegExp('[\\u0300-\\u036f]', 'g');

  function normalize(value) {
    return String(value == null ? '' : value)
      .normalize('NFD')
      .replace(COMBINING, '')
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, ' ')
      .trim();
  }

  function terms(value) {
    return normalize(value).split(' ').filter(Boolean);
  }

  function setupFacet(facet, names, onChange) {
    var trigger = facet.querySelector(names.trigger);
    var panel = facet.querySelector(names.panel);
    var search = facet.querySelector(names.search);
    var badge = facet.querySelector(names.badge);
    var empty = facet.querySelector(names.empty);
    var selectVisible = facet.querySelector(names.selectVisible);
    var clear = facet.querySelector(names.clear);
    var options = Array.prototype.slice.call(facet.querySelectorAll(names.option));

    function checkboxOf(option) {
      return option.querySelector(names.checkbox) || option.querySelector('input[type="checkbox"]');
    }

    function visibleOptions() {
      return options.filter(function (option) {
        return !option.hidden;
      });
    }

    function selectedValues() {
      return options
        .filter(function (option) {
          var box = checkboxOf(option);
          return Boolean(box) && box.checked;
        })
        .map(function (option) {
          return option.getAttribute(names.optionAttribute);
        });
    }

    function refreshBadge() {
      var selected = selectedValues();
      if (badge) {
        badge.hidden = selected.length === 0;
        badge.textContent = String(selected.length);
      }
      if (trigger) trigger.classList.toggle('is-active', selected.length > 0);
    }

    function filterOptions() {
      if (!search) return;
      var wanted = terms(search.value);
      var visible = 0;
      options.forEach(function (option) {
        var label = normalize(option.textContent);
        var matches = wanted.every(function (term) {
          return label.indexOf(term) >= 0;
        });
        option.hidden = !matches;
        if (matches) visible += 1;
      });
      if (empty) empty.hidden = visible !== 0;
    }

    function open() {
      if (panel) panel.hidden = false;
      if (trigger) trigger.setAttribute('aria-expanded', 'true');
      if (search) search.focus();
    }

    function close() {
      if (panel) panel.hidden = true;
      if (trigger) trigger.setAttribute('aria-expanded', 'false');
    }

    function clearSelection() {
      options.forEach(function (option) {
        var box = checkboxOf(option);
        if (box) box.checked = false;
      });
      refreshBadge();
    }

    if (trigger && panel) {
      trigger.addEventListener('click', function () {
        if (panel.hidden) open();
        else close();
      });
    }

    if (search) search.addEventListener('input', filterOptions);

    options.forEach(function (option) {
      var box = checkboxOf(option);
      if (!box) return;
      box.addEventListener('change', function () {
        refreshBadge();
        onChange();
      });
    });

    if (selectVisible) {
      selectVisible.addEventListener('click', function () {
        visibleOptions().forEach(function (option) {
          var box = checkboxOf(option);
          if (box) box.checked = true;
        });
        refreshBadge();
        onChange();
      });
    }

    if (clear) {
      clear.addEventListener('click', function () {
        visibleOptions().forEach(function (option) {
          var box = checkboxOf(option);
          if (box) box.checked = false;
        });
        refreshBadge();
        onChange();
      });
    }

    refreshBadge();

    return {
      element: facet,
      key: facet.getAttribute(names.facetAttribute),
      selectedValues: selectedValues,
      clearSelection: clearSelection,
      closePanel: close
    };
  }

  function bindFacets(root, opts) {
    var scope = root || document;
    if (!scope || typeof scope.querySelector !== 'function') return null;
    var options = opts || {};
    var names = {
      facet: options.facetSelector || '[data-facet]',
      facetAttribute: options.facetAttribute || 'data-facet',
      trigger: options.triggerSelector || '[data-facet-trigger]',
      panel: options.panelSelector || '[data-facet-panel]',
      search: options.searchSelector || '[data-facet-search]',
      badge: options.badgeSelector || '[data-facet-badge]',
      empty: options.emptySelector || '[data-facet-empty]',
      option: options.optionSelector || '[data-facet-option]',
      optionAttribute: options.optionAttribute || 'data-facet-option',
      checkbox: options.checkboxSelector || '[data-facet-checkbox]',
      selectVisible: options.selectVisibleSelector || '[data-facet-select-visible]',
      clear: options.clearSelector || '[data-facet-clear]'
    };

    var rowSelector = options.rowSelector || '[data-facet-row]';
    var rows = Array.prototype.slice.call(scope.querySelectorAll(rowSelector));
    var facetNodes = Array.prototype.slice.call(scope.querySelectorAll(names.facet));
    if (!facetNodes.length) return null;

    var counter = options.counterSelector ? scope.querySelector(options.counterSelector) : null;
    var emptyState = options.emptyStateSelector ? scope.querySelector(options.emptyStateSelector) : null;
    var wrapper = options.wrapperSelector ? scope.querySelector(options.wrapperSelector) : null;
    var reset = options.resetSelector ? scope.querySelector(options.resetSelector) : null;
    var rowPrefix = options.rowAttributePrefix || 'data-filter-';
    var facets = [];

    function apply() {
      var active = facets
        .map(function (facet) {
          return { key: facet.key, values: facet.selectedValues() };
        })
        .filter(function (entry) {
          return entry.key && entry.values.length > 0;
        });

      var visible = 0;
      rows.forEach(function (row) {
        var matches = active.every(function (entry) {
          return entry.values.indexOf(row.getAttribute(rowPrefix + entry.key)) >= 0;
        });
        row.hidden = !matches;
        if (matches) visible += 1;
      });

      if (counter) counter.textContent = visible + ' / ' + rows.length;
      if (emptyState) emptyState.hidden = visible !== 0;
      if (wrapper) wrapper.hidden = visible === 0;
      if (reset) reset.hidden = active.length === 0;
      if (options.onChange) options.onChange(visible, rows.length);
    }

    facets = facetNodes.map(function (facet) {
      return setupFacet(facet, names, apply);
    });

    if (reset) {
      reset.addEventListener('click', function () {
        facets.forEach(function (facet) {
          facet.clearSelection();
          facet.closePanel();
        });
        apply();
      });
    }

    document.addEventListener('click', function (event) {
      facets.forEach(function (facet) {
        if (!facet.element.contains(event.target)) facet.closePanel();
      });
    });

    document.addEventListener('keydown', function (event) {
      if (event.key !== 'Escape') return;
      facets.forEach(function (facet) {
        facet.closePanel();
      });
    });

    apply();
    return { facets: facets, apply: apply };
  }

  function sortValue(row, index, kind) {
    var cell = row.children[index];
    var raw = cell ? cell.getAttribute('data-sort-value') || cell.textContent : '';
    if (kind === 'number') {
      var parsed = parseFloat(String(raw).replace(/[^0-9.-]/g, ''));
      return isNaN(parsed) ? 0 : parsed;
    }
    return normalize(raw);
  }

  function bindSort(root, opts) {
    var scope = root || document;
    if (!scope || typeof scope.querySelectorAll !== 'function') return;
    var options = opts || {};
    var tableSelector = options.tableSelector || '[data-sortable-table]';
    var headerSelector = options.headerSelector || '[data-sort]';
    var indexAttribute = options.indexAttribute || 'data-sort-index';

    scope.querySelectorAll(tableSelector).forEach(function (table) {
      var body = table.tBodies ? table.tBodies[0] : null;
      if (!body) return;
      var rows = Array.prototype.slice.call(body.rows);
      var headers = Array.prototype.slice.call(table.querySelectorAll(headerSelector));
      if (!headers.length) return;
      var sortIndex = -1;
      var ascending = true;

      function applySort(button) {
        var index = parseInt(button.getAttribute(indexAttribute), 10);
        if (isNaN(index)) return;
        var kind = button.getAttribute('data-sort');
        if (sortIndex === index) {
          ascending = !ascending;
        } else {
          sortIndex = index;
          ascending = true;
        }
        rows
          .slice()
          .sort(function (left, right) {
            var a = sortValue(left, index, kind);
            var b = sortValue(right, index, kind);
            if (a === b) return 0;
            var result = a > b ? 1 : -1;
            return ascending ? result : -result;
          })
          .forEach(function (row) {
            body.appendChild(row);
          });

        headers.forEach(function (candidate) {
          var header = candidate.closest('th');
          var isActive = candidate === button;
          if (header) {
            header.setAttribute(
              'aria-sort',
              isActive ? (ascending ? 'ascending' : 'descending') : 'none'
            );
          }
          candidate.classList.toggle('is-sorted', isActive);
          candidate.classList.toggle('is-descending', isActive && !ascending);
        });
      }

      headers.forEach(function (button) {
        button.addEventListener('click', function () {
          applySort(button);
        });
      });
    });
  }

  window.APP.Text = window.APP.Text || {};
  window.APP.Text.normalize = normalize;
  window.APP.Text.terms = terms;
  window.APP.List = {
    bindFacets: bindFacets,
    bindSort: bindSort,
    sortValue: sortValue
  };
})();
