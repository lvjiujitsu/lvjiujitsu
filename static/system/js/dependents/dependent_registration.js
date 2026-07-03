(function () {
  'use strict';

  function notifyParent(type) {
    if (window.parent === window) return;
    window.parent.postMessage({ type: type }, window.location.origin);
  }

  function readJson(id) {
    var el = document.getElementById(id);
    if (!el) return null;
    try { return JSON.parse(el.textContent || 'null'); } catch (e) { return null; }
  }

  function escHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function fmtPrice(val) {
    var n = parseFloat(val);
    return isNaN(n) ? 'R$ —' : 'R$ ' + n.toFixed(2).replace('.', ',');
  }

  function getVal(id) {
    var el = document.getElementById(id);
    return el ? el.value : '';
  }

  function getSelectedOptionText(id) {
    var el = document.getElementById(id);
    if (!el || el.selectedIndex < 0) return '';
    var option = el.options[el.selectedIndex];
    return option ? option.text.trim() : '';
  }

  function maskCpf(value) {
    var d = value.replace(/\D/g, '').slice(0, 11);
    if (d.length <= 3) return d;
    if (d.length <= 6) return d.slice(0, 3) + '.' + d.slice(3);
    if (d.length <= 9) return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6);
    return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9);
  }

  function maskPhone(value) {
    var d = value.replace(/\D/g, '').slice(0, 11);
    if (d.length <= 2) return d.length ? '(' + d : '';
    if (d.length <= 7) return '(' + d.slice(0, 2) + ') ' + d.slice(2);
    return '(' + d.slice(0, 2) + ') ' + d.slice(2, 7) + '-' + d.slice(7);
  }

  function bindMask(el, fn) {
    if (!el) return;
    el.addEventListener('input', function () {
      var pos = el.selectionStart;
      var old = el.value;
      var masked = fn(old);
      el.value = masked;
      el.setSelectionRange(pos + masked.length - old.length, pos + masked.length - old.length);
    });
  }

  function setupPasswordToggle(inputId, btnId) {
    var input = document.getElementById(inputId);
    var btn = document.getElementById(btnId);
    if (!input || !btn) return;
    btn.addEventListener('click', function () {
      var showing = input.type === 'text';
      input.type = showing ? 'password' : 'text';
      btn.setAttribute('aria-label', showing ? 'Mostrar senha' : 'Ocultar senha');
    });
  }

  function bindEscapeClose() {
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') {
        notifyParent('dependent-modal-close');
      }
    });
  }

  function bindSubmitState() {
    var form = document.getElementById('dep-wizard-form');
    var button = document.getElementById('dep-wizard-next-btn');
    if (!form || !button) return;
    form.addEventListener('submit', function () {
      if (button.type !== 'submit') return;
      button.disabled = true;
      button.textContent = 'Enviando...';
    });
  }

  function bindKinshipOtherToggle() {
    var select = document.getElementById('id_dependent_kinship_type');
    var otherField = document.getElementById('dep-kinship-other-field');
    if (!select || !otherField) return;
    function sync() { otherField.hidden = select.value !== 'other'; }
    select.addEventListener('change', sync);
    sync();
  }

  function bindMaterialsToggle() {
    document.querySelectorAll('.material-item').forEach(function (item) {
      var header = item.querySelector('[data-material-toggle]');
      var variants = item.querySelector('.material-variants');
      var countEl = item.querySelector('.material-item__count');
      if (!header || !variants) return;

      function selectedQty() {
        var total = 0;
        item.querySelectorAll('.material-variant input').forEach(function (input) {
          total += parseInt(input.value, 10) || 0;
        });
        return total;
      }

      function syncCount() {
        var qty = selectedQty();
        if (countEl) {
          countEl.hidden = qty === 0;
          countEl.textContent = qty + (qty === 1 ? ' selecionado' : ' selecionados');
        }
      }

      header.addEventListener('click', function () {
        var expanded = header.getAttribute('aria-expanded') === 'true';
        header.setAttribute('aria-expanded', expanded ? 'false' : 'true');
        variants.hidden = expanded;
      });

      item.querySelectorAll('.material-variant input').forEach(function (input) {
        input.addEventListener('input', syncCount);
      });

      syncCount();
    });
  }

  function bindMartialToggle() {
    var hasSelect = document.getElementById('id_dependent_has_martial_art');
    var toggleNo = document.querySelector('[data-martial-toggle="no"]');
    var toggleYes = document.querySelector('[data-martial-toggle="yes"]');
    var detailSection = document.getElementById('dep-martial-detail-section');
    var modalitySelect = document.getElementById('id_dependent_martial_art');
    var jjSection = document.getElementById('dep-martial-jj-section');
    var otherGradField = document.getElementById('dep-martial-other-grad-field');
    if (!hasSelect || !toggleNo || !toggleYes || !detailSection) return;

    function setHas(value) {
      hasSelect.value = value;
      toggleNo.classList.toggle('martial-has-btn--active', value !== 'yes');
      toggleYes.classList.toggle('martial-has-btn--active', value === 'yes');
      detailSection.hidden = value !== 'yes';
    }

    function syncModality() {
      var isJj = modalitySelect && modalitySelect.value === 'jiu_jitsu';
      if (jjSection) jjSection.hidden = !isJj;
      if (otherGradField) otherGradField.hidden = isJj;
    }

    toggleNo.addEventListener('click', function () { setHas('no'); });
    toggleYes.addEventListener('click', function () { setHas('yes'); });
    if (modalitySelect) modalitySelect.addEventListener('change', syncModality);

    setHas(hasSelect.value === 'yes' ? 'yes' : 'no');
    syncModality();
  }

  var WEEKDAY_ABBREV = {
    'Segunda-feira': 'Seg', 'Terça-feira': 'Ter', 'Quarta-feira': 'Qua',
    'Quinta-feira': 'Qui', 'Sexta-feira': 'Sex', 'Sábado': 'Sáb', 'Domingo': 'Dom',
  };

  var ibjjfCategories = readJson('dep-ibjjf-json') || [];

  function calcAgeYears(birthdateStr) {
    if (!birthdateStr) return null;
    var y, m, day;
    if (birthdateStr.indexOf('-') !== -1) {
      // <input type="date"> sempre envia AAAA-MM-DD
      var isoParts = birthdateStr.split('-');
      if (isoParts.length !== 3) return null;
      y = parseInt(isoParts[0], 10); m = parseInt(isoParts[1], 10); day = parseInt(isoParts[2], 10);
    } else {
      var brParts = birthdateStr.split('/');
      if (brParts.length !== 3) return null;
      day = parseInt(brParts[0], 10); m = parseInt(brParts[1], 10); y = parseInt(brParts[2], 10);
    }
    var d = new Date(y, m - 1, day);
    if (isNaN(d.getTime())) return null;
    var today = new Date();
    var age = today.getFullYear() - d.getFullYear();
    if (today.getMonth() < d.getMonth() || (today.getMonth() === d.getMonth() && today.getDate() < d.getDate())) age--;
    return age;
  }

  function resolveAudience(birthdateStr) {
    var age = calcAgeYears(birthdateStr);
    if (age === null) return null;
    if (ibjjfCategories.length === 0) return age >= 16 ? 'adult' : (age >= 10 ? 'juvenile' : 'kids');
    var sorted = ibjjfCategories.slice().sort(function (a, b) { return a.minimum_age - b.minimum_age; });
    for (var i = 0; i < sorted.length; i++) {
      var cat = sorted[i];
      var maxOk = cat.maximum_age === null || cat.maximum_age === undefined || age <= cat.maximum_age;
      if (age >= cat.minimum_age && maxOk) return cat.audience;
    }
    return null;
  }

  function getDependentPerson() {
    return {
      birthdate: getVal('id_dependent_birthdate'),
      sex: getVal('id_dependent_biological_sex'),
    };
  }

  function filterGroupsByPerson(groups, person) {
    var audience = resolveAudience(person.birthdate);
    if (!audience) return groups; // sem data de nascimento → exibe tudo
    var sex = person.sex;
    return groups.filter(function (g) {
      var ga = g.category_audience;
      if (audience === 'adult') {
        if (ga === 'adult') return true;
        if (ga === 'women' && sex === 'female') return true;
        return false;
      }
      if (audience === 'juvenile') return ga === 'juvenile' || ga === 'kids';
      if (audience === 'kids')     return ga === 'kids' || ga === 'juvenile';
      return ga === audience;
    });
  }

  function bindClassCatalog() {
    var container = document.getElementById('dep-class-catalog');
    var nativeSelect = document.getElementById('id_dependent_class_groups');
    var catalog = readJson('dep-class-catalog-json');
    if (!container || !nativeSelect || !catalog) return null;

    var selectedIds = Array.prototype.map.call(nativeSelect.selectedOptions || [], function (o) { return o.value; });

    function syncNativeSelect() {
      Array.prototype.forEach.call(nativeSelect.options, function (option) {
        option.selected = selectedIds.indexOf(option.value) !== -1;
      });
      nativeSelect.dispatchEvent(new Event('change', { bubbles: true }));
    }

    function render() {
      var groups = filterGroupsByPerson(catalog, getDependentPerson());
      container.innerHTML = '';
      if (!groups.length) {
        var empty = document.createElement('p');
        empty.className = 'class-catalog--empty';
        empty.textContent = catalog.length
          ? 'Nenhuma turma elegível para a idade/sexo informados.'
          : 'Nenhuma turma disponível no momento.';
        container.appendChild(empty);
        return;
      }
      groups.forEach(function (group) {
        var isSelected = selectedIds.indexOf(String(group.id)) !== -1;
        var card = document.createElement('button');
        card.type = 'button';
        card.className = 'class-card' + (isSelected ? ' class-card--selected' : '');
        card.setAttribute('aria-pressed', isSelected ? 'true' : 'false');

        var titleText = escHtml(group.category_name) +
          (group.display_name ? ' · ' + escHtml(group.display_name) : '');

        var scheduleHtml = '';
        var sections = group.compact_schedule_sections || [];
        if (sections.length) {
          var rows = sections.map(function (sec) {
            var abbrev = WEEKDAY_ABBREV[sec.weekday_label] || String(sec.weekday_label).substring(0, 3);
            var times = (sec.entries || []).map(function (e) { return escHtml(e.time_label); }).join('  ·  ');
            return '<div class="class-card__day-row">' +
              '<span class="class-card__day-name">' + escHtml(abbrev) + '</span>' +
              '<span class="class-card__day-times">' + times + '</span>' +
              '</div>';
          }).join('');
          scheduleHtml = '<div class="class-card__divider"></div>' +
            '<div class="class-card__schedule-table">' + rows + '</div>';
        }

        card.innerHTML =
          '<div class="class-card__radio"><div class="class-card__radio-dot"></div></div>' +
          '<div class="class-card__body">' +
            '<p class="class-card__title">' + titleText + '</p>' +
            scheduleHtml +
          '</div>';

        card.addEventListener('click', function () {
          var id = String(group.id);
          var idx = selectedIds.indexOf(id);
          if (idx === -1) selectedIds.push(id); else selectedIds.splice(idx, 1);
          syncNativeSelect();
          render();
        });

        container.appendChild(card);
      });
    }

    render();
    return render;
  }

  var CYCLE_LABELS = { monthly: 'Mensal', quarterly: 'Trimestral', semiannual: 'Semestral', annual: 'Anual' };
  var METHOD_LABELS = { pix: 'PIX', credit_card: 'Cartão' };
  var PAYMENT_METHOD_ICONS = {
    pix: '<span class="payment-method-icons payment-method-icons--pix" aria-hidden="true">' +
      '<img class="payment-method-icon payment-method-icon--pix" src="' + (window.STATIC_URL || '/static/') + 'system/img/icons/pix.svg" alt="">' +
      '</span>',
    credit_card: '<span class="payment-method-icons payment-method-icons--card" aria-hidden="true">' +
      '<img class="payment-method-icon payment-method-icon--brand" src="' + (window.STATIC_URL || '/static/') + 'system/img/icons/mastercard.svg" alt="">' +
      '<img class="payment-method-icon payment-method-icon--brand" src="' + (window.STATIC_URL || '/static/') + 'system/img/icons/visa.svg" alt="">' +
      '</span>',
  };

  function resolvePlanCheckoutAction(plan) {
    if (!plan) return 'asaas_card';
    if (plan.payment_method === 'pix') return 'pix';
    if (plan.gateway_code === 'stripe_card') return 'stripe_card';
    return 'asaas_card';
  }

  function bindPlanCatalog() {
    var filtersArea = document.getElementById('dep-plan-filters-area');
    var cardsArea = document.getElementById('dep-plan-cards-area');
    var planSelect = document.getElementById('id_selected_plan');
    var checkoutSelect = document.getElementById('id_checkout_action');
    var catalog = readJson('dep-plan-catalog-json');
    if (!filtersArea || !cardsArea || !planSelect || !checkoutSelect || !catalog) return null;

    var filter = { frequency: null, cycle: null, method: null };
    var selectedPlanId = planSelect.value ? parseInt(planSelect.value, 10) : null;

    function eligiblePlans() {
      var audience = resolveAudience(getVal('id_dependent_birthdate'));
      return catalog.filter(function (p) {
        if (p.is_family_plan) return false; // plano familiar é reaproveitado via "Usar plano familiar ativo"
        if (!audience) return true;
        if (p.audience === 'adult' && audience !== 'adult') return false;
        if (p.audience === 'kids_juvenile' && audience !== 'kids' && audience !== 'juvenile') return false;
        return true;
      });
    }

    function uniqueValues(getter) {
      var seen = {};
      eligiblePlans().forEach(function (p) { seen[getter(p)] = true; });
      return Object.keys(seen);
    }

    function getFiltered() {
      return eligiblePlans().filter(function (p) {
        if (filter.frequency !== null && p.weekly_frequency !== filter.frequency) return false;
        var isStripe = p.gateway_code === 'stripe_card';
        if (!isStripe && filter.cycle && p.billing_cycle !== filter.cycle) return false;
        if (filter.method && p.payment_method !== filter.method) return false;
        return true;
      }).sort(function (a, b) {
        var aStripe = a.gateway_code === 'stripe_card' ? 1 : 0;
        var bStripe = b.gateway_code === 'stripe_card' ? 1 : 0;
        return aStripe - bStripe;
      });
    }

    function renderFilters() {
      var freqs = uniqueValues(function (p) { return p.weekly_frequency; }).map(Number).sort(function (a, b) { return a - b; });
      var cycles = uniqueValues(function (p) { return p.billing_cycle; });
      var methods = uniqueValues(function (p) { return p.payment_method; });

      if (freqs.length === 1 && filter.frequency === null) filter.frequency = freqs[0];
      if (methods.length === 1 && filter.method === null) filter.method = methods[0];

      var html = '';
      if (freqs.length > 1) {
        html += '<div class="plan-filter-section"><p class="plan-filter-label">Frequência semanal</p><div class="plan-filter-row">';
        freqs.forEach(function (f) {
          var active = filter.frequency === f ? ' plan-filter-pill--active' : '';
          html += '<button type="button" class="plan-filter-pill' + active + '" data-filter="frequency" data-value="' + f + '">' + f + 'x por semana</button>';
        });
        html += '</div></div>';
      }
      if (cycles.length > 0) {
        html += '<div class="plan-filter-section"><p class="plan-filter-label">Período de cobrança</p><div class="plan-filter-row">';
        cycles.forEach(function (c) {
          var active = filter.cycle === c ? ' plan-filter-pill--active' : '';
          var savings = c === 'annual' ? '<span class="plan-filter-pill__badge">Melhor valor</span>' : (c === 'semiannual' ? '<span class="plan-filter-pill__badge">Economize</span>' : '');
          html += '<button type="button" class="plan-filter-pill' + active + '" data-filter="cycle" data-value="' + escHtml(c) + '">' + escHtml(CYCLE_LABELS[c] || c) + savings + '</button>';
        });
        html += '</div></div>';
      }
      if (methods.length > 1) {
        html += '<div class="plan-filter-section"><p class="plan-filter-label">Forma de pagamento</p><div class="plan-filter-row">';
        methods.forEach(function (m) {
          var active = filter.method === m ? ' plan-filter-pill--active' : '';
          var icon = PAYMENT_METHOD_ICONS[m] || '';
          html += '<button type="button" class="plan-filter-pill plan-filter-pill--payment' + active + '" data-filter="method" data-value="' + escHtml(m) + '">' + icon + '<span>' + escHtml(METHOD_LABELS[m] || m) + '</span></button>';
        });
        html += '</div></div>';
      }
      filtersArea.innerHTML = html;
      filtersArea.querySelectorAll('.plan-filter-pill').forEach(function (btn) {
        btn.addEventListener('click', function () {
          var key = btn.getAttribute('data-filter');
          var val = btn.getAttribute('data-value');
          if (key === 'frequency') filter.frequency = parseInt(val, 10);
          else if (key === 'cycle') filter.cycle = val;
          else if (key === 'method') filter.method = val;
          renderFilters();
          renderCards();
        });
      });
    }

    function selectPlan(planId) {
      selectedPlanId = planId;
      var plan = catalog.filter(function (p) { return p.id === planId; })[0];
      planSelect.value = String(planId);
      checkoutSelect.value = resolvePlanCheckoutAction(plan);
      planSelect.dispatchEvent(new Event('change', { bubbles: true }));
      renderCards();
    }

    function renderCards() {
      var plans = getFiltered();
      if (!plans.length) {
        cardsArea.innerHTML = '<p class="plan-cards--empty">Nenhum plano disponível para os filtros selecionados.</p>';
        return;
      }
      var html = '<div class="plan-cards">';
      plans.forEach(function (plan) {
        var isSelected = plan.id === selectedPlanId;
        var price = plan.payment_method === 'pix' ? plan.charge_pix : plan.charge_card;
        var isStripe = plan.gateway_code === 'stripe_card';
        var tierLabel = plan.commercial_tier_label || plan.name || plan.code;
        var cycleLabel = isStripe ? 'mês' : (plan.cycle || '');

        html += '<button type="button" class="plan-card' + (isSelected ? ' plan-card--selected' : '') + '" data-plan-id="' + plan.id + '" aria-pressed="' + (isSelected ? 'true' : 'false') + '">';
        html += '<div class="plan-card__radio"><div class="plan-card__radio-dot"></div></div>';
        html += '<div class="plan-card__body">';
        html += '<div class="plan-card__header"><p class="plan-card__tier">' + escHtml(tierLabel) + '</p>';
        if (isStripe) html += '<span class="plan-card__badge plan-card__badge--stripe">Recorrente</span>';
        html += '</div>';
        html += '<div class="plan-card__price-wrap"><span class="plan-card__price">' + fmtPrice(price) + '</span>';
        html += '<span class="plan-card__price-cycle">/' + escHtml(cycleLabel) + '</span></div>';
        if (!isStripe && plan.installment_count > 1 && plan.installment_label) {
          html += '<p class="plan-card__installment">' + escHtml(plan.installment_label) + '</p>';
        }
        if (plan.weekly_frequency_label) {
          html += '<p class="plan-card__meta">' + escHtml(plan.weekly_frequency_label) + '</p>';
        }
        html += '</div></button>';
      });
      html += '</div>';
      cardsArea.innerHTML = html;
      cardsArea.querySelectorAll('.plan-card').forEach(function (card) {
        card.addEventListener('click', function () {
          selectPlan(parseInt(card.getAttribute('data-plan-id'), 10));
        });
      });
    }

    function bindFamilyPlanToggle() {
      var checkbox = document.getElementById('id_use_family_plan');
      var planSection = document.getElementById('dep-plan-section');
      if (!checkbox || !planSection) return;
      function sync() { planSection.hidden = checkbox.checked; }
      checkbox.addEventListener('change', sync);
      sync();
    }

    function refresh() {
      filter = { frequency: null, cycle: null, method: null };
      renderFilters();
      renderCards();
    }

    refresh();
    bindFamilyPlanToggle();
    return refresh;
  }

  function bindReviewSummary() {
    var box = document.getElementById('dep-review-summary');
    if (!box) return null;

    function addRow(rows, label, value) {
      if (!value) return;
      rows.push(
        '<div class="review-row"><span class="review-row__label">' + escHtml(label) +
        '</span><span class="review-row__value">' + escHtml(value) + '</span></div>'
      );
    }

    function classesSummary() {
      var nativeSelect = document.getElementById('id_dependent_class_groups');
      var catalog = readJson('dep-class-catalog-json') || [];
      if (!nativeSelect) return '';
      var selectedIds = Array.prototype.map.call(nativeSelect.selectedOptions || [], function (o) { return o.value; });
      var names = catalog
        .filter(function (g) { return selectedIds.indexOf(String(g.id)) !== -1; })
        .map(function (g) { return g.category_name + (g.display_name ? ' · ' + g.display_name : ''); });
      return names.join(', ');
    }

    function planSummary() {
      var useFamilyPlan = document.getElementById('id_use_family_plan');
      if (useFamilyPlan && useFamilyPlan.checked) return 'Plano familiar do titular/responsável';
      var planId = getVal('id_selected_plan');
      if (!planId) return '';
      var catalog = readJson('dep-plan-catalog-json') || [];
      var plan = catalog.filter(function (p) { return String(p.id) === String(planId); })[0];
      if (!plan) return '';
      var price = plan.payment_method === 'pix' ? plan.charge_pix : plan.charge_card;
      var cycle = plan.gateway_code === 'stripe_card' ? 'mês' : (plan.cycle || '');
      var tierLabel = plan.commercial_tier_label || plan.name || plan.code;
      return tierLabel + ' — ' + fmtPrice(price) + '/' + cycle;
    }

    function materialsSummary() {
      var parts = [];
      document.querySelectorAll('.material-item').forEach(function (item) {
        var nameEl = item.querySelector('.material-item__header strong');
        var productName = nameEl ? nameEl.textContent.trim() : '';
        item.querySelectorAll('.material-variant').forEach(function (row) {
          var input = row.querySelector('input');
          var qty = input ? parseInt(input.value, 10) : 0;
          if (!qty) return;
          var labelEl = row.querySelector('.material-variant__label');
          var variantLabel = labelEl ? labelEl.textContent.trim().split('\n')[0].trim() : '';
          parts.push(productName + (variantLabel ? ' (' + variantLabel + ')' : '') + ' x' + qty);
        });
      });
      return parts.join(', ');
    }

    function formatIsoDateForDisplay(isoStr) {
      if (!isoStr || isoStr.indexOf('-') === -1) return isoStr;
      var parts = isoStr.split('-');
      if (parts.length !== 3) return isoStr;
      return parts[2] + '/' + parts[1] + '/' + parts[0];
    }

    function refresh() {
      var rows = [];
      addRow(rows, 'Nome', getVal('id_dependent_name'));
      addRow(rows, 'CPF', getVal('id_dependent_cpf'));
      addRow(rows, 'Data de nascimento', formatIsoDateForDisplay(getVal('id_dependent_birthdate')));
      addRow(rows, 'Parentesco', getSelectedOptionText('id_dependent_kinship_type'));
      addRow(rows, 'Turma(s)', classesSummary());
      addRow(rows, 'Plano', planSummary());
      addRow(rows, 'Materiais', materialsSummary() || 'Nenhum material selecionado');
      box.innerHTML = rows.length
        ? rows.join('')
        : '<p class="review-empty">Nenhum dado preenchido.</p>';
    }

    refresh();
    return refresh;
  }

  function bindStepNavigation(refreshClasses, refreshPlans, refreshReview) {
    var form = document.querySelector('.wizard-form');
    if (!form) return;

    var steps = Array.prototype.slice.call(form.querySelectorAll('.wizard-step[data-step]'));
    if (steps.length < 2) return;

    var backBtn = document.getElementById('wizard-back');
    var backIsModalButton = !!(backBtn && backBtn.tagName === 'BUTTON');
    var stepCurrentEl = document.getElementById('wizard-step-current');
    var stepTotalEl = document.getElementById('wizard-step-total');
    var stepFillEl = document.getElementById('wizard-progress-fill');
    var progressBarEl = document.querySelector('.wizard-progress-bar');
    var total = steps.length;
    var current = 0;

    var REFRESH_BY_KEY = { classes: refreshClasses, plan: refreshPlans, review: refreshReview };

    function keyIndex(key) {
      for (var i = 0; i < steps.length; i++) {
        if (steps[i].getAttribute('data-step-key') === key) return i;
      }
      return -1;
    }

    if (stepTotalEl) stepTotalEl.textContent = String(total);
    if (progressBarEl) progressBarEl.setAttribute('aria-valuemax', String(total));

    function startingIndex() {
      var paymentConfirmed = form.getAttribute('data-payment-confirmed') === 'true';
      var materialsConfirmed = form.getAttribute('data-materials-confirmed') === 'true';
      if (materialsConfirmed) {
        var reviewIdx = keyIndex('review');
        return reviewIdx !== -1 ? reviewIdx : total - 1;
      }
      if (paymentConfirmed) {
        var materialsIdx = keyIndex('materials');
        return materialsIdx !== -1 ? materialsIdx : total - 1;
      }
      return 0;
    }

    var actionBtn = document.getElementById('dep-wizard-next-btn');
    var actionLabelEl = actionBtn ? actionBtn.querySelector('[data-btn-label]') : null;
    var finalLabel = actionBtn ? (actionBtn.getAttribute('data-final-label') || (actionLabelEl ? actionLabelEl.textContent.trim() : '')) : '';

    function render() {
      steps.forEach(function (step, index) { step.hidden = index !== current; });
      if (stepCurrentEl) stepCurrentEl.textContent = String(current + 1);
      if (stepFillEl) stepFillEl.style.width = (((current + 1) / total) * 100) + '%';
      if (progressBarEl) progressBarEl.setAttribute('aria-valuenow', String(current + 1));
      if (backIsModalButton) backBtn.hidden = current === 0;
      if (actionBtn) {
        var isLast = current === total - 1;
        actionBtn.type = isLast ? 'submit' : 'button';
        if (actionLabelEl) actionLabelEl.textContent = isLast ? finalLabel : 'Próximo';
      }
      var key = steps[current].getAttribute('data-step-key');
      var refresh = REFRESH_BY_KEY[key];
      if (typeof refresh === 'function') refresh();
      form.scrollTop = 0;
    }

    function currentStepValid() {
      var controls = steps[current].querySelectorAll('input, select, textarea');
      for (var i = 0; i < controls.length; i++) {
        if (controls[i].willValidate && !controls[i].checkValidity()) {
          controls[i].reportValidity();
          return false;
        }
      }
      return true;
    }

    function goNext() {
      if (!currentStepValid()) return;
      current = Math.min(current + 1, total - 1);
      render();
    }

    function goBack(e) {
      if (current === 0) return;
      e.preventDefault();
      current = Math.max(current - 1, 0);
      render();
    }

    if (actionBtn) {
      actionBtn.addEventListener('click', function (e) {
        if (current !== total - 1) {
          e.preventDefault();
          goNext();
        }
      });
    }

    if (backBtn) backBtn.addEventListener('click', goBack);

    current = startingIndex();
    render();
  }

  bindEscapeClose();
  bindSubmitState();
  bindKinshipOtherToggle();
  bindMartialToggle();
  bindMaterialsToggle();
  bindMask(document.getElementById('id_dependent_cpf'), maskCpf);
  bindMask(document.getElementById('id_dependent_phone'), maskPhone);
  setupPasswordToggle('id_dependent_password', 'dep-pw-toggle');
  setupPasswordToggle('id_dependent_password_confirm', 'dep-pwc-toggle');
  var refreshClasses = bindClassCatalog();
  var refreshPlans = bindPlanCatalog();
  var refreshReview = bindReviewSummary();
  bindStepNavigation(refreshClasses, refreshPlans, refreshReview);
})();
