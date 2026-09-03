(function () {
  var dialog = document.querySelector('[data-confirm-delete-dialog]');
  if (!dialog) return;
  var form = dialog.querySelector('[data-confirm-delete-form]');
  var nameEl = dialog.querySelector('[data-confirm-delete-name]');

  document.querySelectorAll('[data-confirm-delete-open]').forEach(function (trigger) {
    trigger.addEventListener('click', function (event) {
      event.preventDefault();
      form.action = trigger.getAttribute('href');
      if (nameEl) {
        nameEl.textContent = trigger.getAttribute('data-confirm-delete-label') || '';
      }
      if (typeof dialog.showModal === 'function') {
        dialog.showModal();
      } else {
        dialog.setAttribute('open', '');
      }
    });
  });

  var cancelButton = dialog.querySelector('[data-confirm-delete-cancel]');
  if (cancelButton) {
    cancelButton.addEventListener('click', function () {
      dialog.close();
    });
  }
})();
