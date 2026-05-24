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

  function replaceButtonWithPill(button, text, modifier) {
    var pill = createStatusPill(text, modifier);
    button.replaceWith(pill);
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

  function bindApproveCheckins() {
    var config = readConfig();
    var csrfToken = getCsrfToken();

    document.querySelectorAll('.js-approve-checkin').forEach(function (button) {
      button.addEventListener('click', function () {
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
            var actionsDiv = button.closest('.checkin-row__actions');
            if (actionsDiv) {
              var waitingPill = actionsDiv.querySelector('.status-pill--warning');
              if (waitingPill) waitingPill.remove();
              button.replaceWith(createStatusPill('Confirmado', 'success'));
            }
          })
          .catch(function () {
            button.disabled = false;
            button.textContent = 'Aprovar';
          });
      });
    });
  }

  function bindSpecialClassModal() {
    var config = readConfig();
    var csrfToken = getCsrfToken();
    var openBtn = document.querySelector('.js-open-special-modal');
    var overlay = document.getElementById('special-class-modal');
    if (!openBtn || !overlay) return;

    var closeBtn = overlay.querySelector('.js-close-modal');
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

    if (closeBtn) {
      closeBtn.addEventListener('click', closeModal);
    }

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

  function bindGradHistoryToggle() {
    var btn = document.getElementById('grad-history-btn');
    var panel = document.getElementById('grad-history-panel');
    var chevron = document.getElementById('grad-history-chevron');
    if (!btn || !panel) return;

    btn.addEventListener('click', function () {
      var expanded = btn.getAttribute('aria-expanded') === 'true';
      btn.setAttribute('aria-expanded', expanded ? 'false' : 'true');
      if (expanded) {
        panel.setAttribute('hidden', '');
        if (chevron) chevron.style.transform = '';
      } else {
        panel.removeAttribute('hidden');
        if (chevron) chevron.style.transform = 'rotate(180deg)';
      }
    });
  }

  bindThemeToggle();
  bindTabs();
  bindCheckins();
  bindApproveCheckins();
  bindSpecialClassModal();
  bindGradHistoryToggle();
})();
