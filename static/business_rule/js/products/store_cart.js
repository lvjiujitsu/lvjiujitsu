(function () {
  var form = document.getElementById('store-cart-form');
  if (!form) return;
  var payloadField = document.getElementById('cart-payload');

  form.addEventListener('submit', function (event) {
    var submitter = event.submitter;
    if (submitter && submitter.getAttribute('formaction')) {
      return;
    }
    var items = [];
    document.querySelectorAll('.js-cart-qty').forEach(function (input) {
      var qty = parseInt(input.value, 10);
      if (qty > 0) {
        items.push({ variant_id: parseInt(input.getAttribute('data-variant-id'), 10), qty: qty });
      }
    });
    payloadField.value = JSON.stringify(items);
  });
})();
