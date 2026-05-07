(function () {
  'use strict';

  var root = document.querySelector('[data-instructor-home]');
  if (!root) return;

  var approveUrl = root.dataset.approveUrl;
  var approveSpecialUrl = root.dataset.approveSpecialUrl;
  var toggleSessionUrl = root.dataset.toggleSessionUrl;
  var specialCreateUrl = root.dataset.specialCreateUrl;
  var quickOpen = root.querySelector('[data-quick-special-open]');
  var quickPanel = root.querySelector('[data-quick-special-panel]');
  var quickClose = root.querySelector('[data-quick-special-close]');
  var specialForm = root.querySelector('[data-special-class-form]');
  var specialErrors = root.querySelector('[data-special-form-errors]');

  function getCsrfToken() {
    var input = root.querySelector('input[name="csrfmiddlewaretoken"]');
    if (input && input.value) return input.value;
    var value = '; ' + document.cookie;
    var parts = value.split('; csrftoken=');
    if (parts.length === 2) return parts.pop().split(';').shift();
    return '';
  }

  function postJson(url, payload) {
    return fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken()
      },
      body: JSON.stringify(payload)
    }).then(function (response) {
      return response.json().then(function (data) {
        return { ok: response.ok, data: data };
      });
    });
  }

  function setSpecialError(message) {
    if (specialErrors) specialErrors.textContent = message || '';
  }

  function setQuickPanel(open) {
    if (!quickPanel || !quickOpen) return;
    quickPanel.hidden = !open;
    quickOpen.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (open) {
      var timeInput = quickPanel.querySelector('input[name="start_time"]');
      if (timeInput) timeInput.focus();
    }
  }

  if (quickOpen) {
    quickOpen.addEventListener('click', function () {
      setQuickPanel(quickPanel ? quickPanel.hidden : true);
    });
  }

  if (quickClose) {
    quickClose.addEventListener('click', function () {
      setSpecialError('');
      setQuickPanel(false);
    });
  }

  if (specialForm) {
    specialForm.addEventListener('submit', function (event) {
      event.preventDefault();
      setSpecialError('');
      var formData = new FormData(specialForm);
      var payload = {
        title: formData.get('title') || '',
        date: formData.get('date') || '',
        start_time: formData.get('start_time') || '',
        duration_minutes: Number(formData.get('duration_minutes') || 0),
        notes: formData.get('notes') || ''
      };
      postJson(specialCreateUrl, payload)
        .then(function (result) {
          if (!result.ok) {
            setSpecialError((result.data && result.data.error) || 'Erro ao criar aulão.');
            return;
          }
          window.location.reload();
        })
        .catch(function () {
          setSpecialError('Erro ao criar aulão.');
        });
    });
  }

  root.querySelectorAll('[data-approve-checkin]').forEach(function (button) {
    button.addEventListener('click', function () {
      var row = button.closest('[data-checkin-row]');
      if (!row) return;
      button.disabled = true;
      var isSpecial = row.dataset.checkinSpecial === '1';
      var url = isSpecial ? approveSpecialUrl : approveUrl;
      postJson(url, { checkin_id: Number(row.dataset.checkinId || 0) })
        .then(function (result) {
          if (!result.ok) {
            button.disabled = false;
            return;
          }
          var status = row.querySelector('[data-checkin-status]');
          if (status) {
            status.textContent = result.data.status_label || 'Confirmado';
            status.classList.remove('checkin-status-pill--pending');
            status.classList.add('checkin-status-pill--approved');
          }
          button.remove();
        })
        .catch(function () {
          button.disabled = false;
        });
    });
  });

  root.querySelectorAll('[data-quick-cancel-session], [data-quick-reactivate-session]').forEach(function (button) {
    button.addEventListener('click', function () {
      var isReactivation = button.hasAttribute('data-quick-reactivate-session');
      var reason = '';
      if (!isReactivation) {
        var promptedReason = window.prompt('Motivo do cancelamento (opcional):');
        if (promptedReason === null) return;
        reason = promptedReason;
      }
      button.disabled = true;
      postJson(toggleSessionUrl, {
        schedule_id: Number(button.dataset.scheduleId || 0),
        date: button.dataset.sessionDate || '',
        reason: reason
      })
        .then(function (result) {
          if (!result.ok) {
            button.disabled = false;
            return;
          }
          window.location.reload();
        })
        .catch(function () {
          button.disabled = false;
        });
    });
  });
})();
