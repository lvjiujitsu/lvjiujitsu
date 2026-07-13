(function () {
  'use strict';

  function clearChildren(node) {
    if (!node) return;
    while (node.firstChild) node.removeChild(node.firstChild);
  }

  (function () {
    var overlay = document.getElementById('calendar-day-modal');
    var title = document.getElementById('calendar-day-modal-title');
    var body = document.getElementById('calendar-day-modal-body');
    if (!overlay || !title || !body) return;

    function closeModal() {
      overlay.setAttribute('hidden', '');
      document.body.style.overflow = '';
      clearChildren(body);
    }

    document.addEventListener('click', function (event) {
      var button = event.target.closest('.js-open-day-detail');
      if (!button) return;
      var detailId = button.getAttribute('data-detail-id');
      var source = detailId ? document.getElementById(detailId) : null;
      if (!source) return;
      title.textContent = button.getAttribute('data-day-title') || 'Dia';
      clearChildren(body);
      Array.prototype.forEach.call(source.childNodes, function (node) {
        body.appendChild(node.cloneNode(true));
      });
      overlay.removeAttribute('hidden');
      document.body.style.overflow = 'hidden';
    });

    var closeButton = overlay.querySelector('.js-close-day-detail');
    if (closeButton) closeButton.addEventListener('click', closeModal);
    overlay.addEventListener('click', function (event) {
      if (event.target === overlay) closeModal();
    });
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && !overlay.hasAttribute('hidden')) closeModal();
    });
  })();

  (function () {
    function getCsrfToken() {
      var input = document.querySelector('input[name="csrfmiddlewaretoken"]');
      return input ? input.value : '';
    }

    function readConfig() {
      var node = document.getElementById('cal-config');
      if (!node) return {};
      try { return JSON.parse(node.textContent || '{}'); } catch (e) { return {}; }
    }

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

    if (closeBtn) closeBtn.addEventListener('click', closeModal);
    overlay.addEventListener('click', function (e) { if (e.target === overlay) closeModal(); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !overlay.hasAttribute('hidden')) closeModal(); });

    if (form) {
      form.addEventListener('submit', function (e) {
        e.preventDefault();
        var url = config.specialCreateUrl;
        if (!url) return;
        var submitBtn = form.querySelector('[type="submit"]');
        submitBtn.disabled = true;
        if (errorEl) errorEl.textContent = '';

        var payload = {
          title: (form.querySelector('[name="title"]') || {}).value || '',
          date: (form.querySelector('[name="date"]') || {}).value || '',
          start_time: (form.querySelector('[name="start_time"]') || {}).value || ''
        };
        var dur = form.querySelector('[name="duration_minutes"]');
        if (dur && dur.value) payload.duration_minutes = parseInt(dur.value, 10);

        fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
          body: JSON.stringify(payload)
        })
          .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, data: d }; }); })
          .then(function (result) {
            if (!result.ok || !result.data.success) {
              submitBtn.disabled = false;
              if (errorEl) errorEl.textContent = (result.data && result.data.error) || 'Erro ao criar aulão.';
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
  })();

})();
