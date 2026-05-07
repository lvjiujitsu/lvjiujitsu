(function() {
  var modal = document.getElementById('bjjHistoryModal');
  if (!modal) {
    return;
  }

  function openHistory() {
    modal.hidden = false;
    document.body.classList.add('bjj-history-modal-open');
  }

  function closeHistory() {
    modal.hidden = true;
    document.body.classList.remove('bjj-history-modal-open');
  }

  document.querySelectorAll('[data-bjj-history-open]').forEach(function(button) {
    button.addEventListener('click', openHistory);
  });

  modal.querySelectorAll('[data-bjj-history-close]').forEach(function(button) {
    button.addEventListener('click', closeHistory);
  });

  document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape' && !modal.hidden) {
      closeHistory();
    }
  });
})();
