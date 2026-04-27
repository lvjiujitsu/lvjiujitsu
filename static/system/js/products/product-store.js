(function () {
  'use strict';

  var catalogNode = document.getElementById('product-store-catalog');
  var listContainer = document.querySelector('[data-store-product-list]');
  var cartPreviewContainer = document.querySelector('[data-store-cart-preview]');
  var cartBar = document.getElementById('cart-bar');
  var cartSummary = document.getElementById('cart-summary');
  var cartCaption = document.getElementById('cart-caption');
  var cartPayloadInput = document.getElementById('cart-payload');
  var submitButton = document.getElementById('store-submit');
  var form = document.getElementById('store-form');
  var STORAGE_KEY = 'lv-store-variant-cart-v1';

  if (!catalogNode || !listContainer || !cartPreviewContainer || !cartPayloadInput || !form) {
    return;
  }

  var productCatalog = [];
  var selectedProducts = {};

  try {
    productCatalog = JSON.parse(catalogNode.textContent || '[]');
  } catch (_error) {
    productCatalog = [];
  }

  function formatBRL(value) {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(Number(value || 0));
  }

  function hasAvailableProductVariants(product) {
    return (product.variants || []).some(function (variant) {
      return variant.is_in_stock;
    });
  }

  function getProductVariantById(product, variantId) {
    return (product.variants || []).find(function (variant) {
      return Number(variant.id) === Number(variantId);
    }) || null;
  }

  function findProductCatalogVariant(variantId) {
    for (var i = 0; i < productCatalog.length; i++) {
      var product = productCatalog[i];
      var variant = getProductVariantById(product, variantId);
      if (variant) {
        return { product: product, variant: variant };
      }
    }
    return null;
  }

  function buildSelectedProductState(product, variant, quantity) {
    return {
      variantId: variant.id,
      productId: product.id,
      displayName: variant.snapshot_name || product.name,
      productName: product.name,
      quantity: quantity,
      unitPrice: parseFloat(product.price || '0'),
      color: variant.color || '',
      size: variant.size || ''
    };
  }

  function getSelectedVariantQuantity(variantId) {
    var item = selectedProducts[String(variantId)];
    return item ? item.quantity : 0;
  }

  function getSelectedProductQuantity(productId) {
    return getSelectedProductEntries().reduce(function (total, entry) {
      return total + (entry.productId === productId ? entry.quantity : 0);
    }, 0);
  }

  function getSelectedProductEntries() {
    return Object.keys(selectedProducts).map(function (variantId) {
      return selectedProducts[variantId];
    }).filter(Boolean).sort(function (a, b) {
      return a.displayName.localeCompare(b.displayName);
    });
  }

  function groupProductsForDropdown(products) {
    var grouped = {};
    products.forEach(function (product) {
      var category = product.category || 'Outros materiais';
      if (!grouped[category]) {
        grouped[category] = {
          order: Number(product.category_order || 999),
          title: category,
          products: [],
          hasSelection: false
        };
      }
      grouped[category].products.push(product);
      if (getSelectedProductQuantity(product.id) > 0) {
        grouped[category].hasSelection = true;
      }
    });

    return Object.keys(grouped).sort(function (a, b) {
      var first = grouped[a];
      var second = grouped[b];
      if (first.order !== second.order) {
        return first.order - second.order;
      }
      return a.localeCompare(b);
    }).map(function (key) {
      return grouped[key];
    });
  }

  function addSelectedProductVariant(product, variant, quantity) {
    var key = String(variant.id);
    var existing = selectedProducts[key];
    if (!existing) {
      existing = buildSelectedProductState(product, variant, 0);
      selectedProducts[key] = existing;
    }

    var maxAllowed = Math.max(0, variant.stock_quantity - existing.quantity);
    if (maxAllowed <= 0) {
      return;
    }
    existing.quantity += Math.min(quantity, maxAllowed);
  }

  function persistCart() {
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(getSelectedProductEntries().map(function (entry) {
        return {
          variant_id: entry.variantId,
          qty: entry.quantity
        };
      })));
    } catch (_error) {
    }
  }

  function hydrateCart() {
    selectedProducts = {};
    try {
      var raw = sessionStorage.getItem(STORAGE_KEY);
      if (!raw) {
        return;
      }
      var items = JSON.parse(raw);
      if (!Array.isArray(items)) {
        return;
      }
      items.forEach(function (item) {
        var variantId = Number(item.variant_id || item.id || 0);
        var quantity = Number(item.qty || item.quantity || 0);
        if (!variantId || quantity <= 0) {
          return;
        }
        var resolved = findProductCatalogVariant(variantId);
        if (!resolved) {
          return;
        }
        var available = Math.min(quantity, resolved.variant.stock_quantity);
        if (available <= 0) {
          return;
        }
        selectedProducts[String(variantId)] = buildSelectedProductState(
          resolved.product,
          resolved.variant,
          available
        );
      });
    } catch (_error) {
      selectedProducts = {};
    }
  }

  function buildProductGroupCard(group) {
    var totalSelected = 0;
    group.products.forEach(function (product) {
      totalSelected += getSelectedProductQuantity(product.id);
    });

    var article = document.createElement('article');
    article.className = 'record-card record-card-catalog';
    if (totalSelected > 0) {
      article.classList.add('is-selected');
    }

    var head = document.createElement('div');
    head.className = 'record-card-head';

    var info = document.createElement('div');
    var title = document.createElement('span');
    title.className = 'record-card-name';
    title.textContent = group.title;
    var subtitle = document.createElement('div');
    subtitle.className = 'record-card-subtitle';
    subtitle.textContent = group.products.length + (group.products.length === 1 ? ' produto' : ' produtos') + (totalSelected > 0 ? ' · ' + totalSelected + ' no carrinho' : '');
    info.appendChild(title);
    info.appendChild(subtitle);

    var badge = document.createElement('span');
    badge.className = 'record-card-badge';
    badge.textContent = group.title;

    head.appendChild(info);
    head.appendChild(badge);

    var details = document.createElement('details');
    details.className = 'catalog-dropdown';
    if (group.hasSelection) {
      details.open = true;
    }

    var summary = document.createElement('summary');
    summary.className = 'catalog-dropdown-summary';
    summary.textContent = 'Ver produtos';
    details.appendChild(summary);

    var content = document.createElement('div');
    content.className = 'catalog-dropdown-content';

    var productOptions = document.createElement('div');
    productOptions.className = 'catalog-product-options';
    group.products.forEach(function (product) {
      productOptions.appendChild(buildProductCard(product));
    });

    content.appendChild(productOptions);
    details.appendChild(content);

    article.appendChild(head);
    article.appendChild(details);
    return article;
  }

  function buildProductCard(product) {
    var qtyInCart = getSelectedProductQuantity(product.id);
    var card = document.createElement('article');
    card.className = 'catalog-product-item' + (qtyInCart > 0 ? ' is-selected' : '');

    var info = document.createElement('div');
    info.className = 'catalog-product-item-info';

    var name = document.createElement('span');
    name.className = 'catalog-product-item-name';
    name.textContent = product.name;

    var meta = document.createElement('span');
    meta.className = 'catalog-product-item-meta';
    meta.textContent = product.description || product.category;

    info.appendChild(name);
    info.appendChild(meta);

    var price = document.createElement('span');
    price.className = 'catalog-product-item-price';
    price.textContent = formatBRL(product.price);

    var top = document.createElement('div');
    top.className = 'catalog-product-item-top';
    top.appendChild(info);
    top.appendChild(price);
    card.appendChild(top);

    if (!hasAvailableProductVariants(product)) {
      var outBadge = document.createElement('span');
      outBadge.className = 'store-product-badge--out';
      outBadge.textContent = 'Esgotado';
      card.appendChild(outBadge);
      return card;
    }

    var selectedSummary = document.createElement('span');
    selectedSummary.className = 'catalog-product-item-meta';
    selectedSummary.textContent = qtyInCart > 0 ? 'No carrinho: ' + qtyInCart + ' un.' : 'Escolha a variante para adicionar.';

    var config = document.createElement('div');
    config.className = 'catalog-product-config-grid';

    var variantField = document.createElement('label');
    variantField.className = 'catalog-product-config-field';
    var variantCaption = document.createElement('span');
    variantCaption.textContent = 'Cor e tamanho';
    var variantSelect = document.createElement('select');
    variantSelect.className = 'catalog-product-select';
    variantSelect.innerHTML = '<option value="">Selecione</option>';
    product.variants.forEach(function (variant) {
      var option = document.createElement('option');
      option.value = String(variant.id);
      option.textContent = variant.label;
      option.disabled = !variant.is_in_stock;
      variantSelect.appendChild(option);
    });
    variantField.appendChild(variantCaption);
    variantField.appendChild(variantSelect);

    var quantity = 1;
    var qtyField = document.createElement('div');
    qtyField.className = 'catalog-product-config-field';
    var qtyCaption = document.createElement('span');
    qtyCaption.textContent = 'Quantidade';
    var qtyControl = document.createElement('div');
    qtyControl.className = 'catalog-product-qty';
    var minusButton = document.createElement('button');
    minusButton.type = 'button';
    minusButton.className = 'catalog-product-qty-btn';
    minusButton.textContent = '-';
    var qtyValue = document.createElement('span');
    qtyValue.className = 'catalog-product-qty-value';
    var plusButton = document.createElement('button');
    plusButton.type = 'button';
    plusButton.className = 'catalog-product-qty-btn';
    plusButton.textContent = '+';
    qtyControl.appendChild(minusButton);
    qtyControl.appendChild(qtyValue);
    qtyControl.appendChild(plusButton);
    qtyField.appendChild(qtyCaption);
    qtyField.appendChild(qtyControl);

    var addButton = document.createElement('button');
    addButton.type = 'button';
    addButton.className = 'catalog-product-add-button';
    addButton.textContent = 'Adicionar ao carrinho';

    function getSelectedVariant() {
      return getProductVariantById(product, Number(variantSelect.value || '0'));
    }

    function syncConfigState() {
      var selectedVariant = getSelectedVariant();
      var selectedQty = selectedVariant ? getSelectedVariantQuantity(selectedVariant.id) : 0;
      var remaining = selectedVariant ? Math.max(0, selectedVariant.stock_quantity - selectedQty) : 0;
      if (quantity > Math.max(remaining, 1)) {
        quantity = Math.max(1, remaining);
      }
      qtyValue.textContent = String(quantity);
      minusButton.disabled = quantity <= 1;
      plusButton.disabled = !selectedVariant || remaining <= quantity;
      addButton.disabled = !selectedVariant || remaining < quantity || quantity < 1;
      if (!selectedVariant) {
        addButton.textContent = 'Selecione uma opção';
        return;
      }
      addButton.textContent = remaining > 0 ? 'Adicionar ao carrinho' : 'Sem estoque disponível';
    }

    minusButton.addEventListener('click', function () {
      quantity = Math.max(1, quantity - 1);
      syncConfigState();
    });

    plusButton.addEventListener('click', function () {
      quantity += 1;
      syncConfigState();
    });

    variantSelect.addEventListener('change', syncConfigState);

    addButton.addEventListener('click', function () {
      var selectedVariant = getSelectedVariant();
      if (!selectedVariant) {
        return;
      }
      addSelectedProductVariant(product, selectedVariant, quantity);
      quantity = 1;
      persistCart();
      render();
    });

    syncConfigState();

    config.appendChild(variantField);
    config.appendChild(qtyField);
    config.appendChild(addButton);

    card.appendChild(selectedSummary);
    card.appendChild(config);
    return card;
  }

  function buildCartPreview() {
    var entries = getSelectedProductEntries();

    cartPreviewContainer.innerHTML = '';
    var wrapper = document.createElement('div');
    wrapper.className = 'catalog-cart-preview store-cart-preview';

    var title = document.createElement('h3');
    title.className = 'checkout-section-title';
    title.textContent = 'Carrinho de materiais';
    wrapper.appendChild(title);

    if (entries.length === 0) {
      var empty = document.createElement('p');
      empty.className = 'checkout-empty-note';
      empty.textContent = 'Nenhum material adicionado.';
      wrapper.appendChild(empty);
      cartPreviewContainer.appendChild(wrapper);
      return;
    }

    var list = document.createElement('div');
    list.className = 'catalog-cart-preview-list';
    entries.forEach(function (entry) {
      var row = document.createElement('div');
      row.className = 'catalog-cart-preview-row';

      var label = document.createElement('span');
      label.className = 'catalog-cart-preview-label';
      label.textContent = entry.displayName + ' x' + entry.quantity;

      var actions = document.createElement('div');
      actions.className = 'catalog-cart-preview-actions';

      var subtotal = document.createElement('span');
      subtotal.className = 'catalog-cart-preview-value';
      subtotal.textContent = formatBRL(entry.unitPrice * entry.quantity);

      var removeButton = document.createElement('button');
      removeButton.type = 'button';
      removeButton.className = 'catalog-cart-preview-remove';
      removeButton.textContent = 'Remover';
      removeButton.addEventListener('click', function () {
        delete selectedProducts[String(entry.variantId)];
        persistCart();
        render();
      });

      actions.appendChild(subtotal);
      actions.appendChild(removeButton);
      row.appendChild(label);
      row.appendChild(actions);
      list.appendChild(row);
    });

    wrapper.appendChild(list);
    cartPreviewContainer.appendChild(wrapper);
  }

  function syncCheckoutState() {
    var total = 0;
    var count = 0;
    var payloadItems = [];

    getSelectedProductEntries().forEach(function (entry) {
      total += entry.unitPrice * entry.quantity;
      count += entry.quantity;
      payloadItems.push({
        variant_id: entry.variantId,
        qty: entry.quantity
      });
    });

    cartPayloadInput.value = JSON.stringify(payloadItems);

    if (cartBar) {
      cartBar.classList.toggle('store-cart-bar--empty', count === 0);
    }
    if (cartSummary) {
      cartSummary.textContent = count + ' ' + (count === 1 ? 'item' : 'itens') + ' · ' + formatBRL(total);
    }
    if (cartCaption) {
      cartCaption.textContent = count > 0
        ? 'Revise o carrinho e prossiga para o checkout.'
        : 'Selecione a categoria, escolha cor e tamanho e adicione ao carrinho.';
    }
    if (submitButton) {
      submitButton.disabled = count === 0;
    }
  }

  function renderProductList() {
    listContainer.innerHTML = '';

    if (productCatalog.length === 0) {
      listContainer.innerHTML = '<p class="checkout-empty-note">Nenhum material disponível no momento.</p>';
      return;
    }

    groupProductsForDropdown(productCatalog).forEach(function (group) {
      listContainer.appendChild(buildProductGroupCard(group));
    });
  }

  function render() {
    renderProductList();
    buildCartPreview();
    syncCheckoutState();
  }

  form.addEventListener('submit', function (event) {
    if (getSelectedProductEntries().length === 0) {
      event.preventDefault();
      return;
    }
    try {
      sessionStorage.removeItem(STORAGE_KEY);
    } catch (_error) {
    }
  });

  hydrateCart();
  render();
})();
