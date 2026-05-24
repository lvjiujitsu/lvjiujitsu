(function () {
  'use strict';

  function applyTheme(theme) {
    var toggle = document.getElementById('theme-toggle');
    var iconSun = document.getElementById('icon-sun');
    var iconMoon = document.getElementById('icon-moon');
    var isDark = theme === 'dark';

    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('lv-theme', theme);

    if (iconSun) iconSun.hidden = isDark;
    if (iconMoon) iconMoon.hidden = !isDark;
    if (toggle) {
      toggle.setAttribute('aria-label', isDark ? 'Mudar para tema claro' : 'Mudar para tema escuro');
    }
  }

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

  function bindTabs() {
    var tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(function (button) {
      button.addEventListener('click', function () {
        var index = button.getAttribute('data-tab');
        tabButtons.forEach(function (item) {
          item.classList.remove('tab-btn--active');
          item.setAttribute('aria-selected', 'false');
        });
        document.querySelectorAll('.tab-panel').forEach(function (panel) {
          panel.classList.remove('tab-panel--active');
        });
        button.classList.add('tab-btn--active');
        button.setAttribute('aria-selected', 'true');
        var panel = document.getElementById('tab-panel-' + index);
        if (panel) panel.classList.add('tab-panel--active');
      });
    });
  }

  function bindCheckins() {
    var config = readConfig();
    var csrfToken = getCsrfToken();
    document.querySelectorAll('.js-checkin').forEach(function (button) {
      button.addEventListener('click', function () {
        var isSpecial = button.getAttribute('data-checkin-kind') === 'special';
        var url = isSpecial ? config.studentSpecialCheckinUrl : config.studentCheckinUrl;
        var id = isSpecial ? button.getAttribute('data-special-id') : button.getAttribute('data-schedule-id');
        var payload = {};

        if (!url || !id) {
          showCheckinError(button, 'Aula sem identificador de check-in.');
          return;
        }

        payload[isSpecial ? 'special_id' : 'schedule_id'] = id;
        button.disabled = true;
        button.textContent = 'Aguardando...';

        fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
          },
          body: JSON.stringify(payload)
        })
          .then(function (response) {
            return response.json().then(function (data) {
              return { ok: response.ok, data: data };
            });
          })
          .then(function (result) {
            if (!result.ok || !result.data.success) {
              button.disabled = false;
              button.textContent = 'Check-in';
              showCheckinError(button, result.data.error);
              return;
            }
            replaceButtonWithPill(button, 'Aguardando aprovação', 'warning');
          })
          .catch(function () {
            button.disabled = false;
            button.textContent = 'Check-in';
            showCheckinError(button, 'Falha de conexão ao registrar check-in.');
          });
      });
    });
  }

  function replaceButtonWithPill(button, text, modifier) {
    var pill = createStatusPill(text, modifier);
    button.replaceWith(pill);
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
        // Update the row that contains the clicked button (works in modal or anywhere)
        var row = button.closest('.modal-checkin-item, .checkin-row');
        if (row) {
          var waitingPill = row.querySelector('.status-pill--warning');
          if (waitingPill) waitingPill.remove();
          button.replaceWith(createStatusPill('Confirmado', 'success'));
        }
        // Mirror the update into the hidden source container so re-opening modal shows updated state
        var sourceRow = document.querySelector('.js-checkin-source [data-checkin-id="' + checkinId + '"]');
        if (sourceRow && sourceRow !== row) {
          var sourcePill = sourceRow.querySelector('.status-pill--warning');
          if (sourcePill) sourcePill.remove();
          var sourceBtn = sourceRow.querySelector('.js-approve-checkin');
          if (sourceBtn) sourceBtn.replaceWith(createStatusPill('Confirmado', 'success'));
        }
      })
      .catch(function () {
        button.disabled = false;
        button.textContent = 'Aprovar';
      });
  }

  function bindApproveCheckins() {
    // Event delegation: works for buttons in modal AND in hidden source containers
    document.addEventListener('click', function (e) {
      var button = e.target.closest('.js-approve-checkin');
      if (!button) return;
      handleApproveCheckin(button);
    });
  }

  function bindSpecialClassModal() {
    var config = readConfig();
    var csrfToken = getCsrfToken();
    var openBtn = document.querySelector('.js-open-special-modal');
    var overlay = document.getElementById('special-class-modal');
    if (!openBtn || !overlay) return;

    var closeButtons = overlay.querySelectorAll('.js-close-modal');
    var form = overlay.querySelector('.js-special-class-form');
    var errorEl = form ? form.querySelector('.modal__error') : null;

    function closeModal() {
      overlay.setAttribute('hidden', '');
      document.body.style.overflow = '';
    }

    openBtn.addEventListener('click', function () {
      overlay.removeAttribute('hidden');
      document.body.style.overflow = 'hidden';
      if (errorEl) errorEl.textContent = '';
    });

    closeButtons.forEach(function (btn) {
      btn.addEventListener('click', closeModal);
    });

    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) closeModal();
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !overlay.hasAttribute('hidden')) closeModal();
    });

    if (form) {
      form.addEventListener('submit', function (e) {
        e.preventDefault();
        var url = config.instructorSpecialCreateUrl;
        if (!url) return;

        var submitBtn = form.querySelector('[type="submit"]');
        submitBtn.disabled = true;
        if (errorEl) errorEl.textContent = '';

        var titleInput = form.querySelector('[name="title"]');
        var dateInput = form.querySelector('[name="date"]');
        var timeInput = form.querySelector('[name="start_time"]');
        var durationInput = form.querySelector('[name="duration_minutes"]');

        var payload = {
          title: titleInput ? titleInput.value : '',
          date: dateInput ? dateInput.value : '',
          start_time: timeInput ? timeInput.value : ''
        };
        if (durationInput && durationInput.value) {
          payload.duration_minutes = parseInt(durationInput.value, 10);
        }

        fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
          body: JSON.stringify(payload)
        })
          .then(function (response) {
            return response.json().then(function (data) { return { ok: response.ok, data: data }; });
          })
          .then(function (result) {
            if (!result.ok || !result.data.success) {
              submitBtn.disabled = false;
              if (errorEl) {
                errorEl.textContent = (result.data && result.data.error) || 'Erro ao criar aulão.';
              }
              return;
            }
            closeModal();
            location.reload();
          })
          .catch(function () {
            submitBtn.disabled = false;
            if (errorEl) errorEl.textContent = 'Falha de conexão.';
          });
      });
    }
  }

  function bindPresenceModal() {
    var overlay = document.getElementById('class-presence-modal');
    var modalBody = document.getElementById('presence-modal-body');
    var modalTitle = document.getElementById('presence-modal-title');
    if (!overlay || !modalBody || !modalTitle) return;

    var currentSourceId = null;

    function closeModal() {
      overlay.setAttribute('hidden', '');
      document.body.style.overflow = '';
      modalBody.innerHTML = '';
      currentSourceId = null;
    }

    // Open handler via event delegation (multiple buttons on page)
    document.addEventListener('click', function (e) {
      var btn = e.target.closest('.js-open-presence-modal');
      if (!btn) return;

      var sourceId = btn.getAttribute('data-checkins-id');
      var sourceDiv = sourceId ? document.getElementById(sourceId) : null;
      if (!sourceDiv) return;

      currentSourceId = sourceId;
      var className = sourceDiv.getAttribute('data-class-name') || 'Turma';
      modalTitle.textContent = 'Presenças — ' + className;

      // Clone source children into modal body
      modalBody.innerHTML = '';
      var children = sourceDiv.childNodes;
      for (var i = 0; i < children.length; i += 1) {
        modalBody.appendChild(children[i].cloneNode(true));
      }

      overlay.removeAttribute('hidden');
      document.body.style.overflow = 'hidden';
    });

    var closeBtn = overlay.querySelector('.js-close-presence-modal');
    if (closeBtn) closeBtn.addEventListener('click', closeModal);

    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) closeModal();
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !overlay.hasAttribute('hidden')) closeModal();
    });
  }

  function bindAttendanceHistoryModal() {
    var overlay = document.getElementById('attendance-history-modal');
    if (!overlay) return;

    var openButtons = document.querySelectorAll('.js-open-attendance-history-modal');
    var closeButton = overlay.querySelector('.js-close-attendance-history-modal');
    var classFilter = overlay.querySelector('.js-attendance-history-class');
    var teacherFilter = overlay.querySelector('.js-attendance-history-teacher');
    var monthFilter = overlay.querySelector('.js-attendance-history-month');
    var yearFilter = overlay.querySelector('.js-attendance-history-year');
    var clearButton = overlay.querySelector('.js-attendance-history-clear');
    var emptyState = overlay.querySelector('.js-attendance-history-empty');
    var prevButton = overlay.querySelector('.js-attendance-history-prev');
    var nextButton = overlay.querySelector('.js-attendance-history-next');
    var pageStatus = overlay.querySelector('.js-attendance-history-page');
    var items = Array.prototype.slice.call(overlay.querySelectorAll('[data-attendance-history-item]'));
    var pageSize = 6;
    var currentPage = 1;
    var filteredItems = items.slice();

    function addOption(select, value, label) {
      if (!select || !value) return;
      var option = document.createElement('option');
      option.value = value;
      option.textContent = label || value;
      select.appendChild(option);
    }

    function uniqueOptions(attribute, labelAttribute) {
      var values = [];
      var seen = {};
      items.forEach(function (item) {
        var value = item.getAttribute(attribute) || '';
        if (!value || seen[value]) return;
        seen[value] = true;
        values.push({
          value: value,
          label: labelAttribute ? (item.getAttribute(labelAttribute) || value) : value
        });
      });
      return values.sort(function (a, b) {
        return a.label.localeCompare(b.label, 'pt-BR', { numeric: true });
      });
    }

    function populateFilters() {
      uniqueOptions('data-class-filter').forEach(function (option) {
        addOption(classFilter, option.value, option.label);
      });
      uniqueOptions('data-teacher-filter').forEach(function (option) {
        addOption(teacherFilter, option.value, option.label);
      });
      uniqueOptions('data-month-filter', 'data-month-label').forEach(function (option) {
        addOption(monthFilter, option.value, option.label);
      });
      uniqueOptions('data-year-filter').forEach(function (option) {
        addOption(yearFilter, option.value, option.label);
      });
    }

    function updateList() {
      var totalPages = Math.max(1, Math.ceil(filteredItems.length / pageSize));
      if (currentPage > totalPages) currentPage = totalPages;

      var start = (currentPage - 1) * pageSize;
      var end = start + pageSize;
      var visibleItems = filteredItems.slice(start, end);

      items.forEach(function (item) {
        item.hidden = true;
      });
      visibleItems.forEach(function (item) {
        item.hidden = false;
      });

      if (emptyState) emptyState.hidden = filteredItems.length > 0;
      if (prevButton) prevButton.disabled = currentPage <= 1 || filteredItems.length === 0;
      if (nextButton) nextButton.disabled = currentPage >= totalPages || filteredItems.length === 0;
      if (pageStatus) {
        pageStatus.textContent = filteredItems.length
          ? 'Página ' + currentPage + ' de ' + totalPages
          : 'Sem resultados';
      }
    }

    function applyFilter() {
      var selectedClass = classFilter ? classFilter.value : '';
      var selectedTeacher = teacherFilter ? teacherFilter.value : '';
      var selectedMonth = monthFilter ? monthFilter.value : '';
      var selectedYear = yearFilter ? yearFilter.value : '';
      filteredItems = items.filter(function (item) {
        return (!selectedClass || item.getAttribute('data-class-filter') === selectedClass)
          && (!selectedTeacher || item.getAttribute('data-teacher-filter') === selectedTeacher)
          && (!selectedMonth || item.getAttribute('data-month-filter') === selectedMonth)
          && (!selectedYear || item.getAttribute('data-year-filter') === selectedYear);
      });
      currentPage = 1;
      updateList();
    }

    function clearFilters() {
      if (classFilter) classFilter.value = '';
      if (teacherFilter) teacherFilter.value = '';
      if (monthFilter) monthFilter.value = '';
      if (yearFilter) yearFilter.value = '';
      applyFilter();
    }

    function openModal() {
      overlay.removeAttribute('hidden');
      document.body.style.overflow = 'hidden';
      currentPage = 1;
      applyFilter();
      if (classFilter) classFilter.focus();
    }

    function closeModal() {
      overlay.setAttribute('hidden', '');
      document.body.style.overflow = '';
    }

    openButtons.forEach(function (button) {
      button.addEventListener('click', openModal);
    });

    if (closeButton) closeButton.addEventListener('click', closeModal);
    if (classFilter) classFilter.addEventListener('change', applyFilter);
    if (teacherFilter) teacherFilter.addEventListener('change', applyFilter);
    if (monthFilter) monthFilter.addEventListener('change', applyFilter);
    if (yearFilter) yearFilter.addEventListener('change', applyFilter);
    if (clearButton) clearButton.addEventListener('click', clearFilters);
    if (prevButton) {
      prevButton.addEventListener('click', function () {
        currentPage -= 1;
        updateList();
      });
    }
    if (nextButton) {
      nextButton.addEventListener('click', function () {
        currentPage += 1;
        updateList();
      });
    }

    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) closeModal();
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !overlay.hasAttribute('hidden')) closeModal();
    });

    populateFilters();
    updateList();
  }

  function bindGradHistoryModal() {
    var overlay = document.getElementById('grad-history-modal');
    if (!overlay) return;

    function closeModal() {
      overlay.setAttribute('hidden', '');
      document.body.style.overflow = '';
    }

    var openBtn = document.querySelector('.js-open-grad-modal');
    if (openBtn) {
      openBtn.addEventListener('click', function () {
        overlay.removeAttribute('hidden');
        document.body.style.overflow = 'hidden';
      });
    }

    var closeBtn = overlay.querySelector('.js-close-grad-modal');
    if (closeBtn) closeBtn.addEventListener('click', closeModal);

    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) closeModal();
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !overlay.hasAttribute('hidden')) closeModal();
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
    try { stored = JSON.parse(localStorage.getItem('lv-sections') || '{}'); } catch (e) {}

    document.querySelectorAll('.section__toggle').forEach(function (btn) {
      var key = btn.getAttribute('data-section');
      var bodyId = btn.getAttribute('aria-controls');
      var body = bodyId ? document.getElementById(bodyId) : null;
      if (!body) return;

      // Restore persisted state
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
        try { localStorage.setItem('lv-sections', JSON.stringify(stored)); } catch (e) {}
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
          var targetId = btn.getAttribute('data-presence-target');
          var container = targetId ? document.getElementById(targetId) : null;
          if (container) {
            var time = data.checked_in_at ? ' · ' + data.checked_in_at : '';
            container.innerHTML =
              '<span class="status-pill status-pill--success">Presente' + time + '</span>';
          }
        })
        .catch(function () { btn.disabled = false; });
    });
  }

  bindThemeToggle();
  bindTabs();
  bindCheckins();
  bindApproveCheckins();
  bindSpecialClassModal();
  bindPresenceModal();
  bindAttendanceHistoryModal();
  bindGradHistoryModal();
  bindGradDetailsToggle();
  bindBillingDetailsToggle();
  bindInstructorSelfCheckin();
  bindSectionCollapse();
})();
