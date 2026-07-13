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

  function getCsrfToken() {
    return window.LV.getCsrfToken();
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

  function bindCalendarModal() {
    var overlay = document.getElementById('calendar-modal');
    if (!overlay) return;

    var frame = overlay.querySelector('.js-calendar-frame');
    var closeButtons = overlay.querySelectorAll('.js-close-calendar-modal');

    function openModal(url) {
      if (frame && url && frame.getAttribute('src') !== url) {
        frame.setAttribute('src', url);
      }
      overlay.removeAttribute('hidden');
      document.body.style.overflow = 'hidden';
    }

    function closeModal() {
      overlay.setAttribute('hidden', '');
      document.body.style.overflow = '';
      if (frame) frame.setAttribute('src', 'about:blank');
    }

    document.addEventListener('click', function (e) {
      var button = e.target.closest('.js-open-calendar-modal');
      if (!button) return;
      e.preventDefault();
      openModal(button.getAttribute('data-calendar-url') || '/calendar/?embedded=1');
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
  }

  function bindDependentRegistrationModal() {
    var overlay = document.getElementById('dependent-registration-modal');
    if (!overlay) return;

    var frame = overlay.querySelector('.js-dependent-registration-frame');
    var modalTitle = overlay.querySelector('.dependent-modal__title');
    var closeButtons = overlay.querySelectorAll('.js-close-dependent-modal');
    var defaultTitle = modalTitle ? modalTitle.textContent : 'Adicionar dependente';

    function cleanUrlState() {
      var url = new URL(window.location.href);
      if (!url.searchParams.has('dependent_modal')) return;
      url.searchParams.delete('dependent_modal');
      url.searchParams.delete('dependent_modal_url');
      var next = url.pathname + (url.search ? url.search : '') + url.hash;
      window.history.replaceState({}, '', next);
    }

    function openModal(url, title) {
      var frameUrl = url || (frame && frame.getAttribute('data-src')) || '/dependents/add/?modal=1';
      var nextTitle = title || defaultTitle;
      if (modalTitle) modalTitle.textContent = nextTitle;
      if (frame) frame.setAttribute('title', nextTitle);
      if (frame && frame.getAttribute('src') !== frameUrl) {
        frame.setAttribute('src', frameUrl);
      }
      overlay.removeAttribute('hidden');
      document.body.style.overflow = 'hidden';
    }

    function closeModal() {
      overlay.setAttribute('hidden', '');
      document.body.style.overflow = '';
      cleanUrlState();
      if (frame) frame.setAttribute('src', 'about:blank');
    }

    document.addEventListener('click', function (e) {
      var trigger = e.target.closest('.js-open-dependent-modal');
      if (!trigger) return;
      e.preventDefault();
      openModal(
        trigger.getAttribute('data-dependent-modal-url') || trigger.getAttribute('href'),
        trigger.getAttribute('data-dependent-modal-title')
      );
    });

    closeButtons.forEach(function (button) {
      button.addEventListener('click', closeModal);
    });

    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) closeModal();
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !overlay.hasAttribute('hidden')) closeModal();
    });

    window.addEventListener('message', function (event) {
      if (event.origin !== window.location.origin) return;
      var data = event.data || {};
      if (data.type === 'dependent-modal-close') {
        closeModal();
      }
      if (data.type === 'dependent-modal-done') {
        closeModal();
        window.location.href = window.location.pathname;
      }
    });

    if (overlay.getAttribute('data-open-on-load') === 'true') {
      var params = new URL(window.location.href).searchParams;
      openModal(params.get('dependent_modal_url') || (frame ? frame.getAttribute('data-src') : null));
    }
  }

  function bindClientProfileModal() {
    var overlay = document.getElementById('client-profile-modal');
    if (!overlay) return;
    var deleteForm = overlay.querySelector('.js-client-profile-delete');
    var deleteError = overlay.querySelector('[data-client-profile-delete-error]');
    var nameEl = overlay.querySelector('[data-client-profile-name]');
    var avatarEl = overlay.querySelector('[data-client-profile-avatar]');
    var roleBadgesEl = overlay.querySelector('[data-client-profile-role-badges]');
    var ownerRoleBadgesHtml = roleBadgesEl ? roleBadgesEl.innerHTML : '';

    function getActivePanel() {
      return overlay.querySelector('.tab-panel[data-tab-group="client-profile"].tab-panel--active')
        || overlay.querySelector('.tab-panel[data-tab-group="client-profile"]');
    }

    function openModal() {
      overlay.removeAttribute('hidden');
      document.body.classList.add('modal-open');
    }

    function closeModal() {
      overlay.setAttribute('hidden', '');
      document.body.classList.remove('modal-open');
      resetAllPanelsToView();
    }

    function resetAllPanelsToView() {
      overlay.querySelectorAll('.tab-panel[data-tab-group="client-profile"]').forEach(function (panel) {
        showView(panel);
      });
      if (deleteForm) deleteForm.setAttribute('hidden', '');
      if (deleteError) deleteError.textContent = '';
    }

    function showView(panel) {
      var viewPanel = panel.querySelector('[data-client-profile-view]');
      var editForm = panel.querySelector('.js-client-profile-form');
      var messageEl = panel.querySelector('.client-profile-form__message');
      if (viewPanel) viewPanel.removeAttribute('hidden');
      if (editForm) editForm.setAttribute('hidden', '');
      clearClientProfileErrors(panel);
      if (messageEl) messageEl.setAttribute('hidden', '');
      if (deleteForm) deleteForm.setAttribute('hidden', '');
      if (deleteError) deleteError.textContent = '';
    }

    function showEdit(panel) {
      var viewPanel = panel.querySelector('[data-client-profile-view]');
      var editForm = panel.querySelector('.js-client-profile-form');
      var messageEl = panel.querySelector('.client-profile-form__message');
      if (viewPanel) viewPanel.setAttribute('hidden', '');
      if (deleteForm) deleteForm.setAttribute('hidden', '');
      if (editForm) editForm.removeAttribute('hidden');
      clearClientProfileErrors(panel);
      if (messageEl) messageEl.setAttribute('hidden', '');
    }

    function showDelete(panel) {
      var viewPanel = panel.querySelector('[data-client-profile-view]');
      var editForm = panel.querySelector('.js-client-profile-form');
      if (viewPanel) viewPanel.setAttribute('hidden', '');
      if (editForm) editForm.setAttribute('hidden', '');
      if (deleteForm) deleteForm.removeAttribute('hidden');
      if (deleteError) deleteError.textContent = '';
    }

    function clearClientProfileErrors(panel) {
      panel.querySelectorAll('[data-client-profile-error]').forEach(function (node) {
        node.textContent = '';
      });
      var messageEl = panel.querySelector('.client-profile-form__message');
      if (messageEl) {
        messageEl.textContent = '';
        messageEl.setAttribute('hidden', '');
      }
    }

    function setClientProfileErrors(panel, errors) {
      clearClientProfileErrors(panel);
      var messageEl = panel.querySelector('.client-profile-form__message');
      if (errors && errors.__all__ && messageEl) {
        messageEl.textContent = errors.__all__.join(' ');
        messageEl.removeAttribute('hidden');
      }
      Object.keys(errors || {}).forEach(function (fieldName) {
        if (fieldName === '__all__') return;
        var node = panel.querySelector('[data-client-profile-error="' + fieldName + '"]');
        if (node) node.textContent = (errors[fieldName] || []).join(' ');
      });
    }

    function setText(panel, selector, value) {
      var node = panel.querySelector(selector);
      if (node) node.textContent = value || '—';
    }

    function updateHeader(panel, person) {
      if (nameEl) nameEl.textContent = (person && person.full_name) || panel.getAttribute('data-person-full-name') || '';
      if (avatarEl) {
        var initial = (person && person.initial)
          || (panel.getAttribute('data-person-full-name') || '').slice(0, 1).toUpperCase();
        avatarEl.textContent = initial;
      }
      if (roleBadgesEl) {
        var role = panel.getAttribute('data-person-role');
        if (role === 'Titular') {
          roleBadgesEl.innerHTML = ownerRoleBadgesHtml;
        } else {
          roleBadgesEl.innerHTML = '<span class="role-badge">Dependente</span>';
        }
      }
    }

    function updateClientProfileDisplay(panel, person) {
      if (!person) return;
      setText(panel, '[data-client-profile-cpf]', person.cpf);
      setText(panel, '[data-client-profile-email]', person.email);
      setText(panel, '[data-client-profile-phone]', person.phone);
      setText(panel, '[data-client-profile-birth-date]', person.birth_date);
      setText(panel, '[data-client-profile-address]', person.address);
      if (person.full_name) panel.setAttribute('data-person-full-name', person.full_name);
      updateHeader(panel, person);
    }

    document.addEventListener('click', function (e) {
      var openBtn = e.target.closest('.js-open-client-profile');
      if (!openBtn) return;
      e.preventDefault();
      openModal();
      var activePanel = getActivePanel();
      if (activePanel) updateHeader(activePanel, null);
    });

    document.addEventListener('click', function (e) {
      var closeBtn = e.target.closest('.js-close-client-profile');
      if (!closeBtn || !overlay.contains(closeBtn)) return;
      closeModal();
    });

    var tabList = overlay.querySelector('.tabs[data-tab-group="client-profile"]');
    if (tabList) {
      tabList.querySelectorAll('.tab-btn').forEach(function (button) {
        button.addEventListener('click', function () {
          resetAllPanelsToView();
          var activePanel = getActivePanel();
          if (activePanel) updateHeader(activePanel, null);
        });
      });
    }

    document.addEventListener('click', function (e) {
      if (!overlay.contains(e.target)) return;
      var panel = e.target.closest('.tab-panel[data-tab-group="client-profile"]') || getActivePanel();
      if (!panel) return;
      if (e.target.closest('.js-client-profile-edit')) {
        showEdit(panel);
        return;
      }
      if (e.target.closest('.js-client-profile-cancel')) {
        showView(panel);
        return;
      }
      if (e.target.closest('.js-client-profile-delete-open')) {
        showDelete(panel);
        return;
      }
      if (e.target.closest('.js-client-profile-delete-cancel')) {
        showView(panel);
      }
    });

    overlay.querySelectorAll('.js-client-profile-form').forEach(function (editForm) {
      editForm.addEventListener('submit', function (e) {
        e.preventDefault();
        var panel = editForm.closest('.tab-panel[data-tab-group="client-profile"]');
        clearClientProfileErrors(panel);
        var submit = editForm.querySelector('button[type="submit"]');
        if (submit) {
          submit.disabled = true;
          submit.textContent = 'Salvando...';
        }
        fetch(editForm.action, {
          method: 'POST',
          headers: { 'X-CSRFToken': getCsrfToken() },
          body: new FormData(editForm),
        })
          .then(function (response) {
            return response.json().then(function (data) {
              return { ok: response.ok, data: data };
            });
          })
          .then(function (result) {
            if (submit) {
              submit.disabled = false;
              submit.textContent = 'Salvar alterações';
            }
            if (!result.ok || !result.data.success) {
              setClientProfileErrors(panel, result.data.errors || {});
              return;
            }
            updateClientProfileDisplay(panel, result.data.person);
            var messageEl = panel.querySelector('.client-profile-form__message');
            if (messageEl) {
              messageEl.textContent = result.data.message || 'Cadastro atualizado.';
              messageEl.removeAttribute('hidden');
            }
            showView(panel);
          })
          .catch(function () {
            if (submit) {
              submit.disabled = false;
              submit.textContent = 'Salvar alterações';
            }
            setClientProfileErrors(panel, { __all__: ['Falha de conexão ao salvar.'] });
          });
      });
    });

    if (deleteForm) {
      deleteForm.addEventListener('submit', function (e) {
        e.preventDefault();
        if (deleteError) deleteError.textContent = '';
        var submit = deleteForm.querySelector('button[type="submit"]');
        if (submit) {
          submit.disabled = true;
          submit.textContent = 'Encerrando...';
        }
        fetch(deleteForm.action, {
          method: 'POST',
          headers: { 'X-CSRFToken': getCsrfToken() },
          body: new FormData(deleteForm),
        })
          .then(function (response) {
            return response.json().then(function (data) {
              return { ok: response.ok, data: data };
            });
          })
          .then(function (result) {
            if (!result.ok || !result.data.success) {
              if (submit) {
                submit.disabled = false;
                submit.textContent = 'Confirmar exclusão';
              }
              if (deleteError) deleteError.textContent = result.data.error || 'Não foi possível encerrar o cadastro.';
              return;
            }
            window.location.href = result.data.redirect_url || '/login/';
          })
          .catch(function () {
            if (submit) {
              submit.disabled = false;
              submit.textContent = 'Confirmar exclusão';
            }
            if (deleteError) deleteError.textContent = 'Falha de conexão.';
          });
      });
    }

    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) closeModal();
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !overlay.hasAttribute('hidden')) closeModal();
    });
  }

  function bindPaymentHistoryModal() {
    var overlay = document.getElementById('payment-history-modal');
    if (!overlay) return;
    var items = Array.prototype.slice.call(overlay.querySelectorAll('[data-payment-history-item]'));
    var emptyEl = overlay.querySelector('.js-payment-history-empty');

    function getActivePersonId() {
      var activeTab = document.querySelector('.tabs[data-tab-group="billing"] .tab-btn--active');
      return activeTab ? activeTab.getAttribute('data-person-id') : null;
    }

    function applyFilter() {
      var personId = getActivePersonId();
      var visibleCount = 0;
      items.forEach(function (item) {
        var matches = !personId || item.getAttribute('data-person-filter') === personId;
        item.hidden = !matches;
        if (matches) visibleCount += 1;
      });
      if (emptyEl) emptyEl.hidden = visibleCount !== 0;
    }

    function openModal() {
      applyFilter();
      overlay.removeAttribute('hidden');
      document.body.classList.add('modal-open');
    }

    function closeModal() {
      overlay.setAttribute('hidden', '');
      document.body.classList.remove('modal-open');
    }

    document.addEventListener('click', function (e) {
      if (e.target.closest('.js-open-payment-history-modal')) {
        e.preventDefault();
        openModal();
      }
    });

    document.addEventListener('click', function (e) {
      var closeBtn = e.target.closest('.js-close-payment-history-modal');
      if (closeBtn && overlay.contains(closeBtn)) closeModal();
    });

    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) closeModal();
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !overlay.hasAttribute('hidden')) closeModal();
    });
  }

  function bindMembershipTimelineModal() {
    var overlay = document.getElementById('membership-timeline-modal');
    if (!overlay) return;

    function openModal() {
      overlay.removeAttribute('hidden');
      document.body.classList.add('modal-open');
    }

    function closeModal() {
      overlay.setAttribute('hidden', '');
      document.body.classList.remove('modal-open');
    }

    document.addEventListener('click', function (e) {
      if (e.target.closest('.js-open-membership-timeline-modal')) {
        e.preventDefault();
        openModal();
      }
    });

    document.addEventListener('click', function (e) {
      var closeBtn = e.target.closest('.js-close-membership-timeline-modal');
      if (closeBtn && overlay.contains(closeBtn)) closeModal();
    });

    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) closeModal();
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !overlay.hasAttribute('hidden')) closeModal();
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

    function closeModal() {
      overlay.setAttribute('hidden', '');
      document.body.style.overflow = '';
      modalBody.replaceChildren();
    }

    document.addEventListener('click', function (e) {
      var btn = e.target.closest('.js-open-presence-modal');
      if (!btn) return;

      var sourceId = btn.getAttribute('data-checkins-id');
      var sourceDiv = sourceId ? document.getElementById(sourceId) : null;
      if (!sourceDiv) return;

      var className = sourceDiv.getAttribute('data-class-name') || 'Turma';
      modalTitle.textContent = 'Presenças — ' + className;

      modalBody.replaceChildren();
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

    var activePersonId = '';

    function getActivePersonId() {
      var tabList = document.querySelector('.tabs[data-tab-group="classes"]');
      if (!tabList) return '';
      var activeBtn = tabList.querySelector('.tab-btn--active');
      return activeBtn ? (activeBtn.getAttribute('data-person-id') || '') : '';
    }

    function personScopedItems() {
      if (!activePersonId) return items;
      return items.filter(function (item) {
        return item.getAttribute('data-person-filter') === activePersonId;
      });
    }

    function addOption(select, value, label) {
      if (!select || !value) return;
      var option = document.createElement('option');
      option.value = value;
      option.textContent = label || value;
      select.appendChild(option);
    }

    function clearOptions(select) {
      if (!select) return;
      while (select.options.length > 1) select.remove(1);
    }

    function uniqueOptions(source, attribute, labelAttribute) {
      var values = [];
      var seen = {};
      source.forEach(function (item) {
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
      var source = personScopedItems();
      clearOptions(classFilter);
      clearOptions(teacherFilter);
      clearOptions(monthFilter);
      clearOptions(yearFilter);
      uniqueOptions(source, 'data-class-filter').forEach(function (option) {
        addOption(classFilter, option.value, option.label);
      });
      uniqueOptions(source, 'data-teacher-filter').forEach(function (option) {
        addOption(teacherFilter, option.value, option.label);
      });
      uniqueOptions(source, 'data-month-filter', 'data-month-label').forEach(function (option) {
        addOption(monthFilter, option.value, option.label);
      });
      uniqueOptions(source, 'data-year-filter').forEach(function (option) {
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
      filteredItems = personScopedItems().filter(function (item) {
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
      activePersonId = getActivePersonId();
      overlay.removeAttribute('hidden');
      document.body.style.overflow = 'hidden';
      currentPage = 1;
      if (classFilter) classFilter.value = '';
      if (teacherFilter) teacherFilter.value = '';
      if (monthFilter) monthFilter.value = '';
      if (yearFilter) yearFilter.value = '';
      populateFilters();
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
  }

  function bindGradHistoryModal() {
    var overlay = document.getElementById('grad-history-modal');
    if (!overlay) return;

    var titleEl = document.getElementById('modal-grad-title');
    var defaultTitle = titleEl ? titleEl.textContent : 'Histórico de graduações';

    function closeModal() {
      overlay.setAttribute('hidden', '');
      document.body.style.overflow = '';
    }

    document.addEventListener('click', function (e) {
      var openBtn = e.target.closest('.js-open-grad-modal');
      if (!openBtn) return;
      var historyFor = openBtn.getAttribute('data-history-for');
      var personName = openBtn.getAttribute('data-person-name');
      overlay.querySelectorAll('.grad-history-list').forEach(function (list) {
        list.hidden = list.getAttribute('data-history-for') !== historyFor;
      });
      if (titleEl) {
        titleEl.textContent = personName ? defaultTitle + ' — ' + personName : defaultTitle;
      }
      overlay.removeAttribute('hidden');
      document.body.style.overflow = 'hidden';
    });

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

  function bindPlanChangeModal() {
    var config = readConfig();
    var csrfToken = getCsrfToken();
    var openBtn = document.querySelector('.js-open-plan-change-modal');
    var overlay = document.getElementById('plan-change-modal');
    if (!openBtn || !overlay) return;

    var closeButtons = overlay.querySelectorAll('.js-close-plan-change-modal');
    var form = overlay.querySelector('.js-plan-change-form');
    var cards = overlay.querySelectorAll('.js-plan-change-card');
    var filterPills = overlay.querySelectorAll('.js-plan-change-filter-pill');
    var upgradeNotice = overlay.querySelector('.js-plan-change-upgrade-notice');
    var leftoverChoice = overlay.querySelector('.js-plan-change-leftover-choice');
    var errorEl = form ? form.querySelector('.modal__error') : null;
    var submitBtn = form ? form.querySelector('[type="submit"]') : null;

    var planFilter = { frequency: null, cycle: null, method: null };

    function closeModal() {
      overlay.setAttribute('hidden', '');
      document.body.style.overflow = '';
    }

    function getSelectedInput() {
      return form ? form.querySelector('input[name="selected_plan"]:checked') : null;
    }

    function updateSelectionState() {
      var input = getSelectedInput();
      cards.forEach(function (card) {
        var cardInput = card.querySelector('input[name="selected_plan"]');
        card.classList.toggle('plan-change-card--selected', !!input && cardInput === input);
      });

      if (!input) {
        if (upgradeNotice) upgradeNotice.hidden = true;
        if (leftoverChoice) leftoverChoice.hidden = true;
        if (submitBtn) submitBtn.disabled = true;
        return;
      }

      if (submitBtn) submitBtn.disabled = false;
      var isUpgrade = input.getAttribute('data-is-upgrade') === '1';
      var hasLeftover = input.getAttribute('data-has-leftover') === '1';
      if (upgradeNotice) upgradeNotice.hidden = !isUpgrade;
      if (leftoverChoice) leftoverChoice.hidden = isUpgrade || !hasLeftover;
    }

    function applyCardFilter() {
      cards.forEach(function (card) {
        var matches =
          (!planFilter.frequency || card.getAttribute('data-weekly-frequency') === planFilter.frequency) &&
          (!planFilter.cycle || card.getAttribute('data-billing-cycle') === planFilter.cycle) &&
          (!planFilter.method || card.getAttribute('data-payment-method') === planFilter.method);
        card.hidden = !matches;
        if (!matches) {
          var input = card.querySelector('input[name="selected_plan"]');
          if (input && input.checked) input.checked = false;
        }
      });
      updateSelectionState();
    }

    function selectPill(pill) {
      var filterType = pill.getAttribute('data-filter');
      var value = pill.getAttribute('data-value');
      planFilter[filterType] = value;
      overlay.querySelectorAll('.js-plan-change-filter-pill[data-filter="' + filterType + '"]').forEach(function (btn) {
        btn.classList.toggle('plan-filter-pill--active', btn === pill);
      });
      applyCardFilter();
    }

    filterPills.forEach(function (pill) {
      pill.addEventListener('click', function () { selectPill(pill); });
    });

    openBtn.addEventListener('click', function () {

      ['frequency', 'cycle', 'method'].forEach(function (filterType) {
        var firstPill = overlay.querySelector('.js-plan-change-filter-pill[data-filter="' + filterType + '"]');
        if (firstPill) selectPill(firstPill);
      });
      applyCardFilter();
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

    cards.forEach(function (card) {
      card.addEventListener('click', function () {
        var input = card.querySelector('input[name="selected_plan"]');
        if (input) {
          input.checked = true;
          updateSelectionState();
        }
      });
    });

    if (form) {
      form.addEventListener('submit', function (e) {
        e.preventDefault();
        var url = config.planChangeUrl;
        var selectedInput = getSelectedInput();
        if (!url || !selectedInput) return;

        if (submitBtn) submitBtn.disabled = true;
        if (errorEl) errorEl.textContent = '';

        var leftoverInput = form.querySelector('input[name="leftover_action"]:checked');
        var body = new URLSearchParams();
        body.append('selected_plan', selectedInput.value);
        if (leftoverInput) body.append('leftover_action', leftoverInput.value);

        fetch(url, {
          method: 'POST',
          headers: { 'X-CSRFToken': csrfToken },
          body: body
        })
          .then(function (response) {
            return response.json().then(function (data) { return { ok: response.ok, data: data }; });
          })
          .then(function (result) {
            if (!result.ok || !result.data.success) {
              if (submitBtn) submitBtn.disabled = false;
              if (errorEl) errorEl.textContent = (result.data && result.data.error) || 'Erro ao trocar plano.';
              return;
            }
            if (result.data.redirect_url) {
              window.location.href = result.data.redirect_url;
              return;
            }
            closeModal();
            location.reload();
          })
          .catch(function () {
            if (submitBtn) submitBtn.disabled = false;
            if (errorEl) errorEl.textContent = 'Falha de conexão.';
          });
      });
    }
  }

  function bindPauseModal() {
    var config = readConfig();
    var csrfToken = getCsrfToken();
    var openBtns = document.querySelectorAll('.js-open-pause-modal');
    var overlay = document.getElementById('pause-modal');
    if (!openBtns.length || !overlay) return;

    var closeButtons = overlay.querySelectorAll('.js-close-pause-modal');
    var form = overlay.querySelector('.js-pause-form');
    var errorEl = form ? form.querySelector('.modal__error') : null;
    var submitBtn = form ? form.querySelector('[type="submit"]') : null;

    function closeModal() {
      overlay.setAttribute('hidden', '');
      document.body.style.overflow = '';
    }

    openBtns.forEach(function (btn) {
      btn.addEventListener('click', function () {
        if (form) form.reset();
        if (errorEl) errorEl.textContent = '';
        overlay.removeAttribute('hidden');
        document.body.style.overflow = 'hidden';
      });
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
        var url = config.membershipPauseCreateUrl;
        if (!url) return;

        if (submitBtn) submitBtn.disabled = true;
        if (errorEl) errorEl.textContent = '';

        var body = new URLSearchParams(new FormData(form));

        fetch(url, {
          method: 'POST',
          headers: { 'X-CSRFToken': csrfToken },
          body: body
        })
          .then(function (response) {
            return response.json().then(function (data) { return { ok: response.ok, data: data }; });
          })
          .then(function (result) {
            if (submitBtn) submitBtn.disabled = false;
            if (!result.ok || !result.data.success) {
              if (errorEl) errorEl.textContent = (result.data && result.data.error) || 'Erro ao solicitar pausa.';
              return;
            }
            closeModal();
            location.reload();
          })
          .catch(function () {
            if (submitBtn) submitBtn.disabled = false;
            if (errorEl) errorEl.textContent = 'Falha de conexão.';
          });
      });
    }
  }

  function bindSubstituteTeacherModal() {
    var cfg = readConfig();
    var overlay = document.getElementById('substitute-teacher-modal');
    if (!overlay) return;

    var form = overlay.querySelector('.js-substitute-teacher-form');
    var closeButtons = overlay.querySelectorAll('.js-close-substitute-modal');
    var errorEl = form ? form.querySelector('.modal__error') : null;
    var scheduleInput = form ? form.querySelector('[name="schedule_id"]') : null;
    var specialInput = form ? form.querySelector('[name="special_id"]') : null;
    var isSpecialInput = form ? form.querySelector('[name="is_special"]') : null;
    var targetInput = form ? form.querySelector('[name="presence_target"]') : null;
    var teacherSelect = form ? form.querySelector('[name="substitute_teacher_id"]') : null;

    function closeModal() {
      overlay.setAttribute('hidden', '');
      document.body.style.overflow = '';
    }

    document.addEventListener('click', function (e) {
      var btn = e.target.closest('.js-open-substitute-modal');
      if (!btn) return;

      if (scheduleInput) scheduleInput.value = btn.getAttribute('data-schedule-id') || '';
      if (specialInput) specialInput.value = btn.getAttribute('data-special-id') || '';
      if (isSpecialInput) isSpecialInput.value = btn.getAttribute('data-is-special') || 'false';
      if (targetInput) targetInput.value = btn.getAttribute('data-presence-target') || '';
      if (teacherSelect) teacherSelect.value = '';
      if (errorEl) errorEl.textContent = '';
      overlay.removeAttribute('hidden');
      document.body.style.overflow = 'hidden';
      if (teacherSelect) teacherSelect.focus();
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

    if (!form) return;
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var isSpecial = isSpecialInput && isSpecialInput.value === 'true';
      var url = cfg.instructorSessionSubstituteUrl;
      var submitBtn = form.querySelector('[type="submit"]');
      if (!url || !teacherSelect || !teacherSelect.value) {
        if (errorEl) errorEl.textContent = 'Selecione um professor substituto.';
        return;
      }
      if (!isSpecial && (!scheduleInput || !scheduleInput.value)) {
        if (errorEl) errorEl.textContent = 'Turma inválida.';
        return;
      }
      if (isSpecial && (!specialInput || !specialInput.value)) {
        if (errorEl) errorEl.textContent = 'Aulão inválido.';
        return;
      }

      if (submitBtn) submitBtn.disabled = true;
      if (errorEl) errorEl.textContent = '';

      var payload = {
        substitute_teacher_id: parseInt(teacherSelect.value, 10),
      };
      if (isSpecial) {
        payload.special_id = parseInt(specialInput.value, 10);
      } else {
        payload.schedule_id = parseInt(scheduleInput.value, 10);
      }

      fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
        body: JSON.stringify(payload),
      })
        .then(function (response) {
          return response.json().then(function (data) {
            return { ok: response.ok, data: data };
          });
        })
        .then(function (result) {
          if (!result.ok || !result.data.success) {
            if (submitBtn) submitBtn.disabled = false;
            if (errorEl) errorEl.textContent = result.data.error || 'Não foi possível indicar substituto.';
            return;
          }
          closeModal();
          location.reload();
        })
        .catch(function () {
          if (submitBtn) submitBtn.disabled = false;
          if (errorEl) errorEl.textContent = 'Falha de conexão.';
        });
    });
  }

  function bindInstructorCancelClass() {
    var cfg = readConfig();
    document.addEventListener('click', function (e) {
      var cancelBtn = e.target.closest('.js-instructor-cancel-class');
      var restoreBtn = e.target.closest('.js-instructor-restore-class');
      var btn = cancelBtn || restoreBtn;
      if (!btn) return;
      var isSpecial = btn.getAttribute('data-is-special') === 'true';
      var url = cfg.instructorCancelClassUrl;
      if (!url) return;
      var message;
      if (restoreBtn) {
        message = isSpecial ? 'Deseja restaurar este aulão?' : 'Deseja restaurar esta aula?';
      } else {
        message = isSpecial
          ? 'Ninguém vai ministrar este aulão. Deseja cancelá-lo?'
          : 'Ninguém vai ministrar esta aula. Deseja cancelá-la?';
      }
      if (!window.confirm(message)) return;

      btn.disabled = true;
      var payload = isSpecial
        ? { special_id: parseInt(btn.getAttribute('data-special-id'), 10) }
        : { schedule_id: parseInt(btn.getAttribute('data-schedule-id'), 10) };
      fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
        body: JSON.stringify(payload),
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (!data.success) {
            btn.disabled = false;
            if (data.error) window.alert(data.error);
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
  bindCalendarModal();
  bindClientProfileModal();
  bindDependentRegistrationModal();
  bindDependentRemoveConfirm();
  bindSpecialClassModal();
  bindPresenceModal();
  bindAttendanceHistoryModal();
  bindPaymentHistoryModal();
  bindMembershipTimelineModal();
  bindGradHistoryModal();
  bindGradDetailsToggle();
  bindBillingDetailsToggle();
  bindPlanChangeModal();
  bindPauseModal();
  bindInstructorSelfCheckin();
  bindInstructorSelfCheckinCancel();
  bindSubstituteTeacherModal();
  bindInstructorCancelClass();
  bindSectionCollapse();
})();
