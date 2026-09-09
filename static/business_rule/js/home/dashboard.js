(function () {
  'use strict';

  function applyTheme(theme) {
    var toggle = document.getElementById('theme-toggle');
    var iconSun = document.getElementById('icon-sun');
    var iconMoon = document.getElementById('icon-moon');
    var isDark = theme === 'dark';

    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(window.THEME_STORAGE_KEY, theme);

    if (iconSun) iconSun.hidden = isDark;
    if (iconMoon) iconMoon.hidden = !isDark;
    if (toggle) {
      toggle.setAttribute('aria-label', isDark ? 'Mudar para tema claro' : 'Mudar para tema escuro');
    }
  }

  function getCsrfToken() {
    return window.APP.getCsrfToken();
  }

  function readConfig() {
    var node = document.getElementById('home-config');
    if (!node) return {};
    try {
      return JSON.parse(node.textContent || '{}');
    } catch (error) {
      return {};
    }
  }

  function createStatusPill(text, modifier) {
    var pill = document.createElement('span');
    pill.className = 'status-pill status-pill--' + modifier;
    pill.textContent = text;
    return pill;
  }

  function showCheckinError(button, message) {
    var holder = button.closest('.class-item__action');
    if (!holder) return;

    var previous = holder.querySelector('.class-item__error');
    if (previous) previous.remove();

    var error = document.createElement('p');
    error.className = 'class-item__error';
    error.setAttribute('role', 'alert');
    error.textContent = message || 'Não foi possível registrar o check-in.';
    holder.appendChild(error);
  }

  function bindThemeToggle() {
    var toggle = document.getElementById('theme-toggle');
    var current = document.documentElement.getAttribute('data-theme') || 'light';
    applyTheme(current);

    if (!toggle) return;
    toggle.addEventListener('click', function () {
      var next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      applyTheme(next);
    });
  }

  function bindAutoDismissMessages() {
    var container = document.querySelector('.system-messages');
    if (!container) return;
    container.style.transition = 'opacity 0.4s';
    setTimeout(function () {
      container.style.opacity = '0';
      setTimeout(function () { container.hidden = true; }, 400);
    }, 5000);
  }

  function bindTabs() {
    document.querySelectorAll('.tabs[role="tablist"]').forEach(function (tabList) {
      var group = tabList.getAttribute('data-tab-group') || '';
      var tabButtons = tabList.querySelectorAll('.tab-btn');
      var panels = document.querySelectorAll('.tab-panel[data-tab-group="' + group + '"]');
      tabButtons.forEach(function (button) {
        button.addEventListener('click', function () {
          var index = button.getAttribute('data-tab');
          tabButtons.forEach(function (item) {
            item.classList.remove('tab-btn--active');
            item.setAttribute('aria-selected', 'false');
          });
          panels.forEach(function (panel) {
            panel.classList.remove('tab-panel--active');
          });
          button.classList.add('tab-btn--active');
          button.setAttribute('aria-selected', 'true');
          var panel = document.querySelector(
            '.tab-panel[data-tab-group="' + group + '"][data-tab="' + index + '"]'
          );
          if (panel) panel.classList.add('tab-panel--active');
        });
      });
    });
  }

  function getStudentCheckinMeta(button) {
    var kind = button.getAttribute('data-checkin-kind') || 'regular';
    var isSpecial = kind === 'special';
    var id = isSpecial ? button.getAttribute('data-special-id') : button.getAttribute('data-schedule-id');
    var personId = button.getAttribute('data-person-id') || '';
    return { kind: kind, isSpecial: isSpecial, id: id, personId: personId };
  }

  function createCheckinButton(kind, id, personId) {
    var button = document.createElement('button');
    button.className = 'btn btn--secondary btn--sm js-checkin';
    button.type = 'button';
    button.setAttribute('data-checkin-kind', kind);
    if (kind === 'special') {
      button.setAttribute('data-special-id', id);
    } else {
      button.setAttribute('data-schedule-id', id);
    }
    if (personId) button.setAttribute('data-person-id', personId);
    button.textContent = 'Check-in';
    return button;
  }

  function createUndoIcon() {
    var ns = 'http://www.w3.org/2000/svg';
    var svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('class', 'checkin-cancel-button__icon');
    svg.setAttribute('width', '13');
    svg.setAttribute('height', '13');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('fill', 'none');
    svg.setAttribute('stroke', 'currentColor');
    svg.setAttribute('stroke-width', '2.1');
    svg.setAttribute('stroke-linecap', 'round');
    svg.setAttribute('stroke-linejoin', 'round');
    svg.setAttribute('aria-hidden', 'true');

    var first = document.createElementNS(ns, 'path');
    first.setAttribute('d', 'M3 7v6h6');
    var second = document.createElementNS(ns, 'path');
    second.setAttribute('d', 'M21 17a9 9 0 0 0-15-6.7L3 13');
    svg.appendChild(first);
    svg.appendChild(second);
    return svg;
  }

  function createPendingCheckinGroup(kind, id, personId) {
    var group = document.createElement('div');
    group.className = 'pending-checkin';
    group.appendChild(createStatusPill('Aguardando aprovação', 'warning'));

    var button = document.createElement('button');
    button.className = 'checkin-cancel-button js-cancel-checkin';
    button.type = 'button';
    button.setAttribute('data-checkin-kind', kind);
    if (kind === 'special') {
      button.setAttribute('data-special-id', id);
    } else {
      button.setAttribute('data-schedule-id', id);
    }
    if (personId) button.setAttribute('data-person-id', personId);
    button.setAttribute('aria-label', 'Desfazer check-in');
    button.appendChild(createUndoIcon());

    var label = document.createElement('span');
    label.textContent = 'Desfazer';
    button.appendChild(label);
    group.appendChild(button);
    return group;
  }

  function postJson(url, payload, csrfToken) {
    return fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
      },
      body: JSON.stringify(payload)
    }).then(function (response) {
      return response.json().then(function (data) {
        return { ok: response.ok, data: data };
      });
    });
  }

  function handleStudentCheckin(button, config, csrfToken) {
    var meta = getStudentCheckinMeta(button);
    var url = meta.isSpecial ? config.studentSpecialCheckinUrl : config.studentCheckinUrl;
    var payload = {};

    if (!url || !meta.id) {
      showCheckinError(button, 'Aula sem identificador de check-in.');
      return;
    }

    payload[meta.isSpecial ? 'special_id' : 'schedule_id'] = meta.id;
    if (meta.personId) payload.person_id = meta.personId;
    button.disabled = true;
    button.textContent = 'Aguardando...';

    postJson(url, payload, csrfToken)
      .then(function (result) {
        if (!result.ok || !result.data.success) {
          button.disabled = false;
          button.textContent = 'Check-in';
          showCheckinError(button, result.data.error);
          return;
        }
        button.replaceWith(createPendingCheckinGroup(meta.kind, meta.id, meta.personId));
      })
      .catch(function () {
        button.disabled = false;
        button.textContent = 'Check-in';
        showCheckinError(button, 'Falha de conexão ao registrar check-in.');
      });
  }

  function handleStudentCheckinCancel(button, config, csrfToken) {
    var meta = getStudentCheckinMeta(button);
    var url = meta.isSpecial ? config.studentSpecialCheckinCancelUrl : config.studentCheckinCancelUrl;
    var payload = {};
    var label = button.querySelector('span');

    if (!url || !meta.id) {
      showCheckinError(button, 'Aula sem identificador para desfazer check-in.');
      return;
    }

    payload[meta.isSpecial ? 'special_id' : 'schedule_id'] = meta.id;
    if (meta.personId) payload.person_id = meta.personId;
    button.disabled = true;
    if (label) label.textContent = 'Desfazendo...';

    postJson(url, payload, csrfToken)
      .then(function (result) {
        if (!result.ok || !result.data.success) {
          button.disabled = false;
          if (label) label.textContent = 'Desfazer';
          showCheckinError(button, result.data.error);
          return;
        }

        var group = button.closest('.pending-checkin');
        var replacement = createCheckinButton(meta.kind, meta.id, meta.personId);
        if (group) {
          group.replaceWith(replacement);
        } else {
          button.replaceWith(replacement);
        }
      })
      .catch(function () {
        button.disabled = false;
        if (label) label.textContent = 'Desfazer';
        showCheckinError(button, 'Falha de conexão ao desfazer check-in.');
      });
  }

  function bindCheckins() {
    var config = readConfig();
    var csrfToken = getCsrfToken();
    document.addEventListener('click', function (e) {
      var cancelButton = e.target.closest('.js-cancel-checkin');
      if (cancelButton) {
        handleStudentCheckinCancel(cancelButton, config, csrfToken);
        return;
      }

      var checkinButton = e.target.closest('.js-checkin');
      if (checkinButton) {
        handleStudentCheckin(checkinButton, config, csrfToken);
      }
    });
  }

  function handleApproveCheckin(button) {
    var config = readConfig();
    var csrfToken = getCsrfToken();
    var checkinId = button.getAttribute('data-checkin-id');
    var isSpecial = button.getAttribute('data-is-special') === 'true';
    var url = isSpecial ? config.instructorApproveSpecialUrl : config.instructorApproveUrl;

    if (!url || !checkinId) return;

    button.disabled = true;
    button.textContent = 'Aprovando…';

    fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
      body: JSON.stringify({ checkin_id: parseInt(checkinId, 10) })
    })
      .then(function (response) {
        return response.json().then(function (data) { return { ok: response.ok, data: data }; });
      })
      .then(function (result) {
        if (!result.ok || !result.data.success) {
          button.disabled = false;
          button.textContent = 'Aprovar';
          return;
        }

        var row = button.closest('.modal-checkin-item, .checkin-row');
        if (row) {
          var waitingPill = row.querySelector('.status-pill--warning');
          if (waitingPill) waitingPill.remove();
          button.replaceWith(createStatusPill('Confirmado', 'success'));
        }

        var sourceRow = document.querySelector('.js-checkin-source [data-checkin-id="' + checkinId + '"]');
        if (sourceRow && sourceRow !== row) {
          var sourcePill = sourceRow.querySelector('.status-pill--warning');
          if (sourcePill) sourcePill.remove();
          var sourceBtn = sourceRow.querySelector('.js-approve-checkin');
          if (sourceBtn) sourceBtn.replaceWith(createStatusPill('Confirmado', 'success'));
        }

        var classItem = sourceRow ? sourceRow.closest('.class-item') : null;
        if (classItem) {
          var approvedCount = parseInt(classItem.getAttribute('data-approved-count') || '0', 10) + 1;
          var pendingCount = Math.max(0, parseInt(classItem.getAttribute('data-pending-count') || '0', 10) - 1);
          classItem.setAttribute('data-approved-count', String(approvedCount));
          classItem.setAttribute('data-pending-count', String(pendingCount));

          var summary = classItem.querySelector('[data-presence-summary]');
          if (summary) {
            summary.textContent = approvedCount + ' confirmado' + (approvedCount === 1 ? '' : 's');
            if (pendingCount > 0) {
              summary.textContent += ' · ' + pendingCount + ' pendente' + (pendingCount === 1 ? '' : 's');
            }
          }

          var approvedLabel = classItem.querySelector('[data-approved-count-label]');
          if (approvedLabel) approvedLabel.textContent = String(approvedCount);
        }
      })
      .catch(function () {
        button.disabled = false;
        button.textContent = 'Aprovar';
      });
  }

  function bindApproveCheckins() {

    document.addEventListener('click', function (e) {
      var button = e.target.closest('.js-approve-checkin');
      if (!button) return;
      handleApproveCheckin(button);
    });
  }

  function bindDependentRemoveConfirm() {
    document.addEventListener('submit', function (e) {
      var form = e.target.closest('.js-dependent-remove-form');
      if (!form) return;
      var message = form.getAttribute('data-confirm-message') || 'Remover dependente?';
      if (!window.confirm(message)) {
        e.preventDefault();
      }
    });
  }


  function bindGradDetailsToggle() {
    document.addEventListener('click', function (e) {
      var btn = e.target.closest('.js-grad-details-toggle');
      if (!btn) return;
      var panelId = btn.getAttribute('aria-controls');
      var panel = panelId ? document.getElementById(panelId) : null;
      if (!panel) return;
      var expanded = btn.getAttribute('aria-expanded') === 'true';
      var next = !expanded;
      btn.setAttribute('aria-expanded', next ? 'true' : 'false');
      panel.hidden = !next;
      var icon = btn.querySelector('.js-grad-toggle-icon');
      if (icon) icon.textContent = next ? '−' : '+';
    });
  }

  function bindBillingDetailsToggle() {
    document.addEventListener('click', function (e) {
      var btn = e.target.closest('.js-billing-details-toggle');
      if (!btn) return;
      var panelId = btn.getAttribute('aria-controls');
      var panel = panelId ? document.getElementById(panelId) : null;
      if (!panel) return;
      var expanded = btn.getAttribute('aria-expanded') === 'true';
      var next = !expanded;
      btn.setAttribute('aria-expanded', next ? 'true' : 'false');
      panel.hidden = !next;
      var icon = btn.querySelector('.js-billing-toggle-icon');
      if (icon) icon.textContent = next ? '−' : '+';
    });
  }

  function bindSectionCollapse() {
    var stored = {};
    try {
      stored = JSON.parse(localStorage.getItem('lv-sections') || '{}');
    } catch (e) {
      if (typeof console !== 'undefined' && console.warn) {
        console.warn('[LV dashboard:storage]', 'Falha ao ler preferências de seção', e);
      }
    }

    document.querySelectorAll('.section__toggle').forEach(function (btn) {
      var key = btn.getAttribute('data-section');
      var bodyId = btn.getAttribute('aria-controls');
      var body = bodyId ? document.getElementById(bodyId) : null;
      if (!body) return;

      if (stored[key] === false) {
        btn.setAttribute('aria-expanded', 'false');
        body.hidden = true;
      }

      btn.addEventListener('click', function () {
        var expanded = btn.getAttribute('aria-expanded') === 'true';
        var next = !expanded;
        btn.setAttribute('aria-expanded', next ? 'true' : 'false');
        body.hidden = !next;

        stored[key] = next;
        try {
          localStorage.setItem('lv-sections', JSON.stringify(stored));
        } catch (e) {
          if (typeof console !== 'undefined' && console.warn) {
            console.warn('[LV dashboard:storage]', 'Falha ao salvar preferências de seção', e);
          }
        }
      });
    });
  }

  function bindInstructorSelfCheckin() {
    var cfg = readConfig();
    document.addEventListener('click', function (e) {
      var btn = e.target.closest('.js-instructor-self-checkin');
      if (!btn) return;

      var isSpecial = btn.getAttribute('data-is-special') === 'true';
      var url = isSpecial ? cfg.instructorSelfSpecialCheckinUrl : cfg.instructorSelfCheckinUrl;
      if (!url) return;

      var payload = isSpecial
        ? { special_id: parseInt(btn.getAttribute('data-special-id'), 10) }
        : { schedule_id: parseInt(btn.getAttribute('data-schedule-id'), 10) };

      btn.disabled = true;

      fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
        body: JSON.stringify(payload),
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (!data.success) {
            btn.disabled = false;
            return;
          }
          location.reload();
        })
        .catch(function () { btn.disabled = false; });
    });
  }

  function bindInstructorSelfCheckinCancel() {
    var cfg = readConfig();
    document.addEventListener('click', function (e) {
      var btn = e.target.closest('.js-instructor-self-checkin-cancel');
      if (!btn) return;

      var isSpecial = btn.getAttribute('data-is-special') === 'true';
      var url = isSpecial ? cfg.instructorSelfSpecialCheckinCancelUrl : cfg.instructorSelfCheckinCancelUrl;
      if (!url) return;

      var payload = isSpecial
        ? { special_id: parseInt(btn.getAttribute('data-special-id'), 10) }
        : { schedule_id: parseInt(btn.getAttribute('data-schedule-id'), 10) };

      btn.disabled = true;

      fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
        body: JSON.stringify(payload),
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (!data.success) {
            btn.disabled = false;
            return;
          }
          location.reload();
        })
        .catch(function () { btn.disabled = false; });
    });
  }

  bindThemeToggle();
  bindAutoDismissMessages();
  bindTabs();
  bindCheckins();
  bindApproveCheckins();
  bindDependentRemoveConfirm();
  bindGradDetailsToggle();
  bindBillingDetailsToggle();
  bindInstructorSelfCheckin();
  bindInstructorSelfCheckinCancel();
  bindSectionCollapse();
})();
