(function () {
  'use strict';

  var Wz = window.LV && window.LV.Wizard;
  if (!Wz) {
    if (typeof console !== 'undefined' && console.error) {
      console.error('[LV dependent] wizard_shared.js é obrigatório');
    }
    return;
  }

  var depWizardForm = document.getElementById('dep-wizard-form');
  var wizardEndpoints = Wz.getFormEndpoints(depWizardForm);
  var escHtml = Wz.escapeHtml;

  function notifyParent(type) {
    if (window.parent === window) return;
    window.parent.postMessage({ type: type }, window.location.origin);
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
      if (
        form.querySelector('input[name="_modal"]') &&
        modalSubmissionStartsCheckout(form)
      ) {
        form.target = '_top';
      } else {
        form.removeAttribute('target');
      }
      if (button.type !== 'submit') return;
      button.disabled = true;
      button.textContent = 'Enviando...';
    });
  }

  function modalSubmissionStartsCheckout(form) {
    var paymentConfirmed = form.getAttribute('data-payment-confirmed') === 'true';
    var financialMode = getVal('id_financial_mode');
    if (!paymentConfirmed && financialMode !== 'family_existing') return true;

    var materialsConfirmed = form.getAttribute('data-materials-confirmed') === 'true';
    var materialsAction = getVal('id_materials_checkout_action');
    if (materialsConfirmed || materialsAction === 'pay_later') return false;
    return Array.prototype.some.call(
      form.querySelectorAll('input[id^="id_material_variant_"]'),
      function (input) { return (parseInt(input.value, 10) || 0) > 0; }
    );
  }

  function bindKinshipOtherToggle() {
    var select = document.getElementById('id_dependent_kinship_type');
    var otherField = document.getElementById('dep-kinship-other-field');
    if (!select || !otherField) return;
    function sync() { otherField.hidden = select.value !== 'other'; }
    select.addEventListener('change', sync);
    sync();
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

  var ibjjfCategories = Wz.readJsonScript('dep-ibjjf-json') || [];
  var depProductCatalog = Wz.readJsonScript('dep-product-catalog-json') || [];

  var CHECK_CIRCLE = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>';

  function resolveAudience(birthdateStr) {
    return Wz.resolveAudience(birthdateStr, ibjjfCategories);
  }

  function getDependentPerson() {
    return {
      birthdate: getVal('id_dependent_birthdate'),
      sex: getVal('id_dependent_biological_sex'),
    };
  }

  function filterGroupsByPerson(groups, person) {
    var audience = resolveAudience(person.birthdate);
    if (!audience) return groups;
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
    var catalog = Wz.readJsonScript('dep-class-catalog-json');
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

  var FINANCIAL_MODE_DEPENDENT_OWN = 'dependent_own';
  var FINANCIAL_MODE_FAMILY_EXISTING = 'family_existing';
  var FINANCIAL_MODE_FAMILY_UPGRADE = 'family_upgrade';

  var depEligibility = { fetchKey: null, planIds: null, pending: false };

  function getWizardCsrfToken() {
    return window.LV.getCsrfToken();
  }

  function getSelectedValues(id) {
    var el = document.getElementById(id);
    if (!el || !el.selectedOptions) return [];
    return Array.prototype.map.call(el.selectedOptions, function (o) { return o.value; });
  }

  function buildDependentEligibilityPayload() {
    return {
      registration_profile: 'holder',
      include_dependent: false,
      holder_birthdate: getVal('id_dependent_birthdate') || '',
      holder_class_groups: getSelectedValues('id_dependent_class_groups'),
    };
  }

  function refreshDependentEligibilityFromServer(onUpdated) {
    Wz.fetchEligibility({
      url: wizardEndpoints.eligibilityUrl,
      csrfToken: getWizardCsrfToken(),
      payload: buildDependentEligibilityPayload(),
      cache: depEligibility,
      onUpdated: onUpdated,
    });
  }

  function bindPlanCatalog() {
    var filtersArea = document.getElementById('dep-plan-filters-area');
    var cardsArea = document.getElementById('dep-plan-cards-area');
    var planSelect = document.getElementById('id_selected_plan');
    var checkoutSelect = document.getElementById('id_checkout_action');
    var financialModeSelect = document.getElementById('id_financial_mode');
    var familyCheckbox = document.getElementById('id_use_family_plan');
    var modeHint = document.getElementById('dep-plan-mode-hint');
    var form = document.getElementById('dep-wizard-form');
    var ownerContext = Wz.readJsonScript('dep-owner-plan-context-json') || {};
    var catalog = Wz.readJsonScript('dep-plan-catalog-json');
    if (!filtersArea || !cardsArea || !planSelect || !checkoutSelect || !catalog) return null;

    var filter = { frequency: null, cycle: null, method: null };
    var selectedPlanId = planSelect.value || null;
    var familyPlanAvailable = form && form.getAttribute('data-family-plan-available') === 'true';

    function currentFinancialMode() {
      var mode = financialModeSelect ? financialModeSelect.value : '';
      if (!mode && familyCheckbox && familyCheckbox.checked) {
        mode = FINANCIAL_MODE_FAMILY_EXISTING;
      }
      if (mode === FINANCIAL_MODE_FAMILY_EXISTING && !familyPlanAvailable) {
        mode = FINANCIAL_MODE_DEPENDENT_OWN;
      }
      if (
        mode !== FINANCIAL_MODE_FAMILY_EXISTING &&
        mode !== FINANCIAL_MODE_FAMILY_UPGRADE &&
        mode !== FINANCIAL_MODE_DEPENDENT_OWN
      ) {
        return FINANCIAL_MODE_DEPENDENT_OWN;
      }
      return mode;
    }

    function hasMinimumFilters() {
      return filter.frequency !== null && !!filter.cycle;
    }

    function familyUpgradePlanEligible(plan, audience) {
      if (plan.is_loyalty_plan && !ownerContext.veteran_eligible) return false;
      var adultCount = parseInt(ownerContext.adult_active_count || 0, 10) || 0;
      if (!adultCount && ownerContext.adult_active) adultCount = 1;
      var kidsCount = parseInt(ownerContext.kids_juvenile_active_count || 0, 10) || 0;
      if (!audience) return true;
      if (audience === 'adult') adultCount += 1;
      if (audience === 'kids' || audience === 'juvenile') kidsCount += 1;
      var total = adultCount + kidsCount;
      if (plan.audience === 'adult') return adultCount > 0 && total >= 2;
      if (plan.audience === 'kids_juvenile') return kidsCount >= 2;
      return false;
    }

    function dependentOwnPlanEligible(plan, audience) {
      if (plan.is_family_plan) return false;
      if (plan.is_loyalty_plan) return false;
      if (!audience) return true;
      if (plan.audience === 'adult') return audience === 'adult';
      if (plan.audience === 'kids_juvenile') {
        return audience === 'kids' || audience === 'juvenile';
      }
      return false;
    }

    function eligiblePlans() {
      var audience = resolveAudience(getVal('id_dependent_birthdate'));
      var serverKey = Wz.eligibilityFetchKey(buildDependentEligibilityPayload());
      var serverAuthorized = null;
      if (depEligibility.planIds && depEligibility.fetchKey === serverKey) {
        serverAuthorized = {};
        depEligibility.planIds.forEach(function (id) { serverAuthorized[id] = true; });
      }
      return catalog.filter(function (p) {
        if (p.is_family_plan) {
          return p.is_family_plan && familyUpgradePlanEligible(p, audience);
        }
        if (serverAuthorized) return !!serverAuthorized[p.id];

        return dependentOwnPlanEligible(p, audience);
      });
    }

    function uniqueValues(getter) {
      var seen = {};
      eligiblePlans().forEach(function (p) { seen[getter(p)] = true; });
      return Object.keys(seen);
    }

    function getFiltered() {
      if (!hasMinimumFilters()) return [];
      return eligiblePlans().filter(function (p) {
        if (p.weekly_frequency !== filter.frequency) return false;
        if (p.billing_cycle !== filter.cycle) return false;
        if (filter.method && p.payment_method !== filter.method) return false;
        return true;
      }).sort(function (a, b) {
        if (a.is_family_plan !== b.is_family_plan) return a.is_family_plan ? 1 : -1;
        var aStripe = a.gateway_code === 'stripe_card' ? 1 : 0;
        var bStripe = b.gateway_code === 'stripe_card' ? 1 : 0;
        if (aStripe !== bStripe) return aStripe - bStripe;
        return parseFloat(a.price || '0') - parseFloat(b.price || '0');
      });
    }

    function syncFinancialMode(mode) {
      if (financialModeSelect) financialModeSelect.value = mode;
      if (familyCheckbox) familyCheckbox.checked = mode === FINANCIAL_MODE_FAMILY_EXISTING;
    }

    function syncHint(message, isError) {
      if (modeHint) {
        modeHint.textContent = message;
        modeHint.classList.toggle('plan-mode-hint--error', !!isError);
      }
    }

    function resetInvalidSelectedPlan() {
      if (currentFinancialMode() === FINANCIAL_MODE_FAMILY_EXISTING) {
        selectedPlanId = null;
        planSelect.value = '';
        checkoutSelect.value = 'pay_later';
        return;
      }
      if (!selectedPlanId) return;
      var allowed = getFiltered().some(function (plan) { return plan.id === selectedPlanId; });
      if (!allowed) {
        selectedPlanId = null;
        planSelect.value = '';
        checkoutSelect.value = 'pay_later';
        syncFinancialMode(FINANCIAL_MODE_DEPENDENT_OWN);
      }
    }

    function renderFilters() {
      var freqs = uniqueValues(function (p) { return p.weekly_frequency; }).map(Number).sort(function (a, b) { return a - b; });
      var cycles = uniqueValues(function (p) { return p.billing_cycle; });
      var methods = uniqueValues(function (p) { return p.payment_method; });

      var html = '';
      if (freqs.length > 0) {
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
          resetInvalidSelectedPlan();
          renderFilters();
          renderCards();
        });
      });
    }

    function selectPlan(planId) {
      selectedPlanId = planId;
      var plan = catalog.filter(function (p) { return p.id === planId; })[0];
      if (!plan) return;
      planSelect.value = String(planId);
      checkoutSelect.value = resolvePlanCheckoutAction(plan);
      syncFinancialMode(
        plan.is_family_plan
          ? FINANCIAL_MODE_FAMILY_UPGRADE
          : FINANCIAL_MODE_DEPENDENT_OWN
      );
      planSelect.dispatchEvent(new Event('change', { bubbles: true }));
      renderCards();
    }

    function selectExistingFamilyPlan() {
      if (!familyPlanAvailable) return;
      selectedPlanId = null;
      planSelect.value = '';
      checkoutSelect.value = 'pay_later';
      syncFinancialMode(FINANCIAL_MODE_FAMILY_EXISTING);
      renderCards();
    }

    function renderPlanCard(plan) {
        var isSelected = plan.id === selectedPlanId;
        var price = plan.payment_method === 'pix' ? plan.charge_pix : plan.charge_card;
        var isStripe = plan.gateway_code === 'stripe_card';
        var tierLabel = plan.commercial_tier_label || plan.name || plan.code;
        var cycleLabel = isStripe ? 'mês' : (plan.cycle || '');
        var modeLabel = plan.is_family_plan
          ? 'Troca o plano do titular para familiar e inclui o dependente.'
          : 'Mensalidade própria do dependente.';
        var discountPct = parseFloat(plan.family_discount_percentage) || 0;
        var fullPrice = parseFloat(price) || 0;
        var discountedPrice = discountPct > 0 ? (fullPrice * (1 - discountPct)).toFixed(2) : null;
        var html = '';

        html += '<button type="button" class="plan-card' + (isSelected ? ' plan-card--selected' : '') + '" data-plan-id="' + plan.id + '" aria-pressed="' + (isSelected ? 'true' : 'false') + '">';
        html += '<div class="plan-card__radio"><div class="plan-card__radio-dot"></div></div>';
        html += '<div class="plan-card__body">';
        html += '<div class="plan-card__header"><p class="plan-card__tier">' + escHtml(tierLabel) + '</p>';
        if (isStripe) html += '<span class="plan-card__badge plan-card__badge--stripe">Recorrente</span>';
        html += '</div>';
        if (discountedPrice) {
          html += '<div class="plan-card__price-wrap plan-card__price-wrap--discounted">';
          html += '<span class="plan-card__price plan-card__price--original">' + fmtPrice(price) + '</span>';
          html += '<span class="plan-card__price plan-card__price--discounted">' + fmtPrice(discountedPrice) + '</span>';
          html += '<span class="plan-card__price-cycle">/' + escHtml(cycleLabel) + '</span>';
          html += '</div>';
          html += '<p class="plan-card__family-discount-note">Com desconto família, quando 2+ pessoas compartilham este plano</p>';
        } else {
          html += '<div class="plan-card__price-wrap"><span class="plan-card__price">' + fmtPrice(price) + '</span>';
          html += '<span class="plan-card__price-cycle">/' + escHtml(cycleLabel) + '</span></div>';
        }
        if (!isStripe && plan.installment_count > 1 && plan.installment_label) {
          html += '<p class="plan-card__installment">' + escHtml(plan.installment_label) + '</p>';
        }
        if (plan.weekly_frequency_label) {
          html += '<p class="plan-card__meta">' + escHtml(plan.weekly_frequency_label) + '</p>';
        }
        html += '<p class="plan-card__auth-note">' + escHtml(modeLabel) + '</p>';
        html += '</div></button>';
        return html;
    }

    function renderExistingFamilyCard() {
      var selected = currentFinancialMode() === FINANCIAL_MODE_FAMILY_EXISTING;
      return '<button type="button" class="plan-card' + (selected ? ' plan-card--selected' : '') + '" data-family-existing="true" aria-pressed="' + (selected ? 'true' : 'false') + '">' +
        '<div class="plan-card__radio"><div class="plan-card__radio-dot"></div></div>' +
        '<div class="plan-card__body">' +
        '<div class="plan-card__header"><p class="plan-card__tier">Plano familiar ativo</p></div>' +
        '<p class="plan-card__auth-note">Usar a cobertura familiar já ativa do titular.</p>' +
        '</div></button>';
    }

    function showPlanCardsEmpty(message, prominent) {
      cardsArea.textContent = '';
      Wz.setElementText(
        cardsArea,
        message,
        prominent ? 'plan-cards--empty plan-cards--empty-prominent' : 'plan-cards--empty'
      );
    }

    function renderCards() {
      if (!hasMinimumFilters()) {
        selectedPlanId = null;
        planSelect.value = '';
        checkoutSelect.value = 'pay_later';
        syncFinancialMode(FINANCIAL_MODE_DEPENDENT_OWN);
        syncHint('Escolha frequência e período para ver os planos.', false);
        showPlanCardsEmpty('Escolha frequência e período para ver os planos disponíveis.', true);
        return;
      }

      var plans = getFiltered();
      syncHint(
        familyPlanAvailable
          ? 'Escolha o plano familiar ativo ou uma nova mensalidade para o dependente.'
          : 'Escolha uma mensalidade própria ou um plano família para migrar o titular.',
        false
      );

      if (!plans.length && !familyPlanAvailable) {
        showPlanCardsEmpty('Nenhum plano disponível para os filtros selecionados.', false);
        return;
      }

      var html = '<div class="plan-cards">';
      if (familyPlanAvailable) {
        html += renderExistingFamilyCard();
      }
      plans.forEach(function (plan) {
        html += renderPlanCard(plan);
      });
      html += '</div>';
      cardsArea.innerHTML = html;
      var existingCard = cardsArea.querySelector('[data-family-existing="true"]');
      if (existingCard) {
        existingCard.addEventListener('click', selectExistingFamilyPlan);
      }
      cardsArea.querySelectorAll('.plan-card').forEach(function (card) {
        if (card.getAttribute('data-family-existing') === 'true') return;
        card.addEventListener('click', function () {
          selectPlan(card.getAttribute('data-plan-id'));
        });
      });
      renderCardStrategyArea();
    }

    function renderCardStrategyArea() {
      var area = document.getElementById('dep-card-strategy-area');
      var cardStrategyField = document.getElementById('id_card_strategy');
      if (!area || !cardStrategyField) return;
      var eligible = checkoutSelect.value === 'stripe_card' && currentFinancialMode() === FINANCIAL_MODE_DEPENDENT_OWN;
      if (!eligible) {
        area.hidden = true;
        cardStrategyField.value = 'new_card';
        var newCardInput = area.querySelector('input[value="new_card"]');
        if (newCardInput) newCardInput.checked = true;
        return;
      }
      area.hidden = false;
      var mergedInput = area.querySelector('input[value="same_card_merged"]');
      if (mergedInput) {
        mergedInput.disabled = !ownerContext.owner_has_stripe_subscription;
        if (mergedInput.disabled && mergedInput.checked) {
          mergedInput.checked = false;
          var fallbackInput = area.querySelector('input[value="new_card"]');
          if (fallbackInput) fallbackInput.checked = true;
          cardStrategyField.value = 'new_card';
        }
      }
    }

    function bindCardStrategyRadios() {
      var area = document.getElementById('dep-card-strategy-area');
      var cardStrategyField = document.getElementById('id_card_strategy');
      if (!area || !cardStrategyField) return;
      area.querySelectorAll('input[name="dep_card_strategy_choice"]').forEach(function (input) {
        input.addEventListener('change', function () {
          if (input.checked) cardStrategyField.value = input.value;
        });
      });
    }

    function bindHiddenFinancialFields() {
      if (financialModeSelect) {
        financialModeSelect.addEventListener('change', function () {
          if (financialModeSelect.value === FINANCIAL_MODE_FAMILY_EXISTING) {
            selectExistingFamilyPlan();
            return;
          }
          syncFinancialMode(currentFinancialMode());
          renderCards();
        });
      }
      if (familyCheckbox) {
        familyCheckbox.addEventListener('change', function () {
          if (familyCheckbox.checked) selectExistingFamilyPlan();
          else syncFinancialMode(FINANCIAL_MODE_DEPENDENT_OWN);
          renderCards();
        });
      }
    }

    function isPaymentConfirmed() {
      return form && form.getAttribute('data-payment-confirmed') === 'true';
    }

    function renderPlanPaidBanner() {
      if (modeHint) modeHint.textContent = '';
      var plan = selectedPlanId
        ? catalog.filter(function (p) { return p.id === selectedPlanId; })[0]
        : null;
      var html = '<div class="checkout-confirmed-banner">';
      html += '<span class="checkout-confirmed-banner__icon" aria-hidden="true">' + CHECK_CIRCLE + '</span>';
      html += '<span class="checkout-confirmed-banner__text">Pagamento confirmado</span>';
      html += '</div>';
      if (plan) {
        var price = plan.payment_method === 'pix' ? plan.charge_pix : plan.charge_card;
        var cycle = plan.gateway_code === 'stripe_card' ? 'mês' : (plan.cycle || '');
        var tierLabel = plan.commercial_tier_label || plan.name || plan.code;
        html += '<div class="checkout-summary"><div class="checkout-summary__section">';
        html += '<p class="checkout-summary__label">Plano contratado</p>';
        html += '<p class="checkout-summary__value">' + escHtml(tierLabel) + '</p>';
        html += '<p class="checkout-summary__plan-meta">Total: ' + fmtPrice(price) + '/' + escHtml(cycle) + '</p>';
        html += '</div></div>';
      }
      if (filtersArea) filtersArea.innerHTML = html;
      if (cardsArea) cardsArea.innerHTML = '';
    }

    function refresh() {
      if (isPaymentConfirmed()) {
        renderPlanPaidBanner();
        return;
      }
      refreshDependentEligibilityFromServer(refresh);
      var freqs = uniqueValues(function (p) { return p.weekly_frequency; }).map(Number).sort(function (a, b) { return a - b; });
      if (filter.frequency !== null && freqs.indexOf(filter.frequency) === -1) filter.frequency = null;
      if (!filter.frequency && freqs.length) filter.frequency = freqs[0];

      var cycles = uniqueValues(function (p) { return p.billing_cycle; });
      if (filter.cycle !== null && cycles.indexOf(filter.cycle) === -1) filter.cycle = null;
      if (!filter.cycle && cycles.length) filter.cycle = cycles[0];

      var methods = uniqueValues(function (p) { return p.payment_method; });
      if (filter.method !== null && methods.indexOf(filter.method) === -1) filter.method = null;
      if (!filter.method && methods.length) filter.method = methods[0];

      resetInvalidSelectedPlan();
      syncFinancialMode(currentFinancialMode());
      renderFilters();
      renderCards();
    }

    refresh.validate = function () {
      if (isPaymentConfirmed()) return true;
      if (currentFinancialMode() === FINANCIAL_MODE_FAMILY_EXISTING) return true;
      if (!hasMinimumFilters()) {
        syncHint('Escolha frequência e período antes de continuar.', true);
        showPlanCardsEmpty('Escolha frequência e período para ver os planos disponíveis.', true);
        return false;
      }
      if (!selectedPlanId) {
        syncHint('Selecione um plano para continuar.', true);
        return false;
      }
      return true;
    };

    bindHiddenFinancialFields();
    bindCardStrategyRadios();
    refresh();
    return refresh;
  }

  function bindDepProductsSection() {
    var catalogArea    = document.getElementById('dep-products-catalog-area');
    var viewCartBtn     = document.getElementById('dep-products-btn-view-cart');
    var skipCatalogBtn  = document.getElementById('dep-products-btn-skip-catalog');
    var backCatalogBtn  = document.getElementById('dep-products-btn-back-catalog');
    var cancelCfgBtn    = document.getElementById('dep-products-btn-cancel-configure');
    var addToCartBtn    = document.getElementById('dep-products-btn-add-to-cart');
    var backToCatalogBtn = document.getElementById('dep-products-btn-back-to-catalog');
    var payCardBtn      = document.getElementById('dep-products-btn-pay-card');
    var payPixBtn       = document.getElementById('dep-products-btn-pay-pix');
    var skipCartBtn     = document.getElementById('dep-products-btn-skip-cart');
    var configureArea   = document.getElementById('dep-products-configure-area');
    var cartArea        = document.getElementById('dep-products-cart-area');
    var confirmArea     = document.getElementById('dep-products-confirm-area');
    var checkoutActionSelect = document.getElementById('id_materials_checkout_action');
    var form = document.getElementById('dep-wizard-form');
    var hasProductsUi = !!catalogArea;

    var cart = [];
    var configureProduct = null, configureColor = null, configureVariantId = null, configureQty = 1;

    function isMaterialsConfirmed() {
      return form && form.getAttribute('data-materials-confirmed') === 'true';
    }

    function getVariantInput(variantId) {
      return document.getElementById('id_material_variant_' + variantId);
    }

    function rebuildCartFromFields() {
      cart = [];
      depProductCatalog.forEach(function (product) {
        product.variants.forEach(function (variant) {
          var input = getVariantInput(variant.id);
          var qty = input ? parseInt(input.value, 10) || 0 : 0;
          if (!qty) return;
          cart.push({
            variantId: variant.id,
            variantLabel: [variant.color, variant.size].filter(Boolean).join(' · ') || 'Padrão',
            productId: product.id,
            productName: product.name,
            qty: qty,
            unitPrice: parseFloat(product.price) || 0,
          });
        });
      });
    }

    function syncCartToFields() {
      depProductCatalog.forEach(function (product) {
        product.variants.forEach(function (variant) {
          var input = getVariantInput(variant.id);
          if (!input) return;
          var inCart = cart.filter(function (c) { return c.variantId === variant.id; })[0];
          input.value = inCart ? inCart.qty : 0;
          input.dispatchEvent(new Event('input', { bubbles: true }));
          input.dispatchEvent(new Event('change', { bubbles: true }));
        });
      });
    }

    function showSubview(name) {
      var catalog = document.getElementById('dep-products-subview-catalog');
      var configure = document.getElementById('dep-products-subview-configure');
      var cartEl = document.getElementById('dep-products-subview-cart');
      if (catalog) catalog.hidden = (name !== 'catalog');
      if (configure) configure.hidden = (name !== 'configure');
      if (cartEl) cartEl.hidden = (name !== 'cart');
    }

    function getCartTotal() {
      return cart.reduce(function (sum, item) { return sum + item.unitPrice * item.qty; }, 0);
    }

    function getCartCount() {
      return cart.reduce(function (sum, item) { return sum + item.qty; }, 0);
    }

    function renderCatalog() {
      if (!catalogArea) return;
      if (!depProductCatalog.length) {
        catalogArea.innerHTML = '<p class="wizard-step__subtitle" style="text-align:center;padding:2rem 0">Nenhum produto disponível no momento.</p>';
        if (viewCartBtn) viewCartBtn.hidden = true;
        return;
      }
      var html = '';
      depProductCatalog.forEach(function (product) {
        var hasStock = product.total_stock > 0;
        var inCart = cart.some(function (c) { return c.productId === product.id; });
        html += '<div class="prod-card' + (hasStock ? '' : ' prod-card--unavailable') + '">';
        html += '<div class="prod-card__body">';
        html += '<div class="prod-card__header">';
        html += '<p class="prod-card__name">' + escHtml(product.name) + '</p>';
        if (inCart) html += '<span class="prod-card__badge prod-card__badge--cart">✓ No carrinho</span>';
        html += '</div>';
        html += '<p class="prod-card__category">' + escHtml(product.category) + '</p>';
        if (product.description) {
          html += '<p class="prod-card__desc">' + escHtml(product.description) + '</p>';
        }
        html += '<div class="prod-card__price-row">';
        html += '<span class="prod-card__price">' + fmtPrice(product.price) + '</span>';
        if (!hasStock) {
          html += '<span class="prod-card__stock-badge prod-card__stock-badge--out">Sem estoque</span>';
        } else {
          html += '<span class="prod-card__stock-badge">' + product.total_stock + ' un.</span>';
        }
        html += '</div>';
        if (hasStock) {
          html += '<div class="prod-card__footer">';
          html += '<button type="button" class="prod-card__add-btn" data-product-id="' + product.id + '">' + (inCart ? 'Alterar seleção' : 'Adicionar') + '</button>';
          html += '</div>';
        }
        html += '</div></div>';
      });
      catalogArea.innerHTML = html;

      catalogArea.querySelectorAll('.prod-card__add-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
          var pid = parseInt(this.getAttribute('data-product-id'), 10);
          var product = depProductCatalog.filter(function (p) { return p.id === pid; })[0];
          if (product) startConfigureProduct(product);
        });
      });

      var cartCount = getCartCount();
      if (viewCartBtn) {
        viewCartBtn.hidden = cartCount === 0;
        if (cartCount > 0) {
          viewCartBtn.innerHTML = 'Ver carrinho (' + cartCount + ' item' + (cartCount !== 1 ? 'ns' : '') + ')' +
            '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>';
        }
      }
    }

    function getUniqueColors(product) {
      var seen = {}, colors = [];
      product.variants.forEach(function (v) {
        if (v.color && !seen[v.color]) { seen[v.color] = true; colors.push(v.color); }
      });
      return colors;
    }

    function getVariantsForColor(product, color) {
      if (!color) return product.variants;
      return product.variants.filter(function (v) { return v.color === color; });
    }

    function startConfigureProduct(product) {
      configureProduct = product;
      configureColor = null;
      configureVariantId = null;
      configureQty = 1;

      var existing = cart.filter(function (c) { return c.productId === product.id; })[0];
      if (existing) {
        var variant = product.variants.filter(function (v) { return v.id === existing.variantId; })[0];
        configureVariantId = existing.variantId;
        configureColor = variant ? (variant.color || null) : null;
        configureQty = existing.qty;
      }

      if (configureColor === null) {
        var uniqueColors = getUniqueColors(product);
        if (uniqueColors.length === 1) configureColor = uniqueColors[0];
      }

      renderConfigure();
      showSubview('configure');
    }

    function renderConfigure() {
      if (!configureArea || !configureProduct) return;
      var product = configureProduct;
      var uniqueColors = getUniqueColors(product);
      var showColorPicker = uniqueColors.length > 1;

      if (!configureColor && uniqueColors.length === 1) configureColor = uniqueColors[0];

      var variantsForColor = getVariantsForColor(product, configureColor);
      var uniqueSizes = [], seenSizes = {};
      variantsForColor.forEach(function (v) {
        if (v.size && !seenSizes[v.size]) { seenSizes[v.size] = true; uniqueSizes.push(v.size); }
      });
      var showSizePicker = uniqueSizes.length > 0;

      if (!configureVariantId && !showColorPicker && !showSizePicker && product.variants.length > 0) {
        for (var k = 0; k < product.variants.length; k++) {
          if (product.variants[k].is_in_stock) { configureVariantId = product.variants[k].id; break; }
        }
      }
      if (!configureVariantId && variantsForColor.length === 1 && !showSizePicker) {
        if (variantsForColor[0].is_in_stock) configureVariantId = variantsForColor[0].id;
      }

      var html = '';

      if (showColorPicker) {
        html += '<div class="prod-configure__section">';
        html += '<p class="prod-configure__section-label">Cor</p><div class="color-pills">';
        uniqueColors.forEach(function (color) {
          var isSelected = color === configureColor;
          var hasStock = product.variants.some(function (v) { return v.color === color && v.is_in_stock; });
          html += '<button type="button" class="color-pill' +
            (isSelected ? ' color-pill--selected' : '') +
            (!hasStock ? ' color-pill--disabled' : '') +
            '" data-color="' + escHtml(color) + '">' + escHtml(color) + '</button>';
        });
        html += '</div></div>';
      }

      if (showSizePicker && (configureColor !== null || !showColorPicker)) {
        html += '<div class="prod-configure__section">';
        html += '<p class="prod-configure__section-label">Tamanho</p><div class="size-pills">';
        variantsForColor.forEach(function (v) {
          if (!v.size) return;
          var isSelected = v.id === configureVariantId;
          var stockText = v.is_in_stock ? v.stock_quantity + ' un.' : 'Esgotado';
          html += '<button type="button" class="size-pill' +
            (isSelected ? ' size-pill--selected' : '') +
            (!v.is_in_stock ? ' size-pill--disabled' : '') +
            '" data-variant-id="' + v.id + '">';
          html += '<span class="size-pill__size">' + escHtml(v.size) + '</span>';
          html += '<span class="size-pill__stock">' + escHtml(stockText) + '</span>';
          html += '</button>';
        });
        html += '</div></div>';
      }

      var selectedVariant = product.variants.filter(function (v) { return v.id === configureVariantId; })[0] || null;
      var maxQty = selectedVariant ? Math.min(selectedVariant.stock_quantity, 10) : 1;
      configureQty = Math.max(1, Math.min(configureQty, maxQty));
      var stepperDisabled = !configureVariantId;

      html += '<div class="prod-configure__section">';
      html += '<div class="configure-qty-row">';
      html += '<span class="configure-qty-label">Quantidade</span>';
      html += '<div class="configure-qty-stepper">';
      html += '<button type="button" class="configure-qty-stepper__btn" id="dep-cfg-qty-dec" aria-label="Diminuir"' +
        (configureQty <= 1 || stepperDisabled ? ' disabled' : '') + '>−</button>';
      html += '<span class="configure-qty-stepper__value" id="dep-cfg-qty-val">' + configureQty + '</span>';
      html += '<button type="button" class="configure-qty-stepper__btn" id="dep-cfg-qty-inc" aria-label="Aumentar"' +
        (configureQty >= maxQty || stepperDisabled ? ' disabled' : '') + '>+</button>';
      html += '</div></div>';
      if (selectedVariant) {
        html += '<p class="prod-configure__stock-hint">' + selectedVariant.stock_quantity + ' unidade' +
          (selectedVariant.stock_quantity !== 1 ? 's' : '') + ' disponível' +
          (selectedVariant.stock_quantity !== 1 ? 'is' : '') + '</p>';
      }
      html += '</div>';

      configureArea.innerHTML = html;

      configureArea.querySelectorAll('.color-pill[data-color]').forEach(function (pill) {
        pill.addEventListener('click', function () {
          configureColor = this.getAttribute('data-color');
          configureVariantId = null;
          configureQty = 1;
          renderConfigure();
        });
      });
      configureArea.querySelectorAll('.size-pill[data-variant-id]').forEach(function (pill) {
        pill.addEventListener('click', function () {
          configureVariantId = parseInt(this.getAttribute('data-variant-id'), 10);
          configureQty = 1;
          renderConfigure();
        });
      });

      var dec = document.getElementById('dep-cfg-qty-dec');
      var inc = document.getElementById('dep-cfg-qty-inc');
      var valEl = document.getElementById('dep-cfg-qty-val');
      function refreshStepper() {
        if (valEl) valEl.textContent = configureQty;
        if (dec) dec.disabled = configureQty <= 1 || !configureVariantId;
        if (inc) inc.disabled = configureQty >= maxQty || !configureVariantId;
      }
      if (dec) dec.addEventListener('click', function () { if (configureQty > 1) { configureQty--; refreshStepper(); } });
      if (inc) inc.addEventListener('click', function () { if (configureQty < maxQty) { configureQty++; refreshStepper(); } });

      if (addToCartBtn) addToCartBtn.disabled = !configureVariantId;
    }

    function renderCart() {
      if (!cartArea) return;
      if (!cart.length) {
        cartArea.innerHTML = '<p class="wizard-step__subtitle" style="text-align:center;padding:1.5rem 0">Carrinho vazio.</p>';
        return;
      }
      var html = '<div class="cart-item-list">';
      cart.forEach(function (item) {
        html += '<div class="cart-item">';
        html += '<div class="cart-item__info">';
        html += '<p class="cart-item__name">' + escHtml(item.productName) + '</p>';
        html += '<p class="cart-item__meta">' + escHtml(item.variantLabel) + ' · Qtd: ' + item.qty + '</p>';
        html += '</div>';
        html += '<span class="cart-item__subtotal">' + fmtPrice(item.unitPrice * item.qty) + '</span>';
        html += '<button type="button" class="cart-item__remove" data-variant-id="' + item.variantId + '" aria-label="Remover">×</button>';
        html += '</div>';
      });
      html += '</div>';
      html += '<div class="cart-total-row"><span>Total</span><strong>' + fmtPrice(getCartTotal()) + '</strong></div>';
      cartArea.innerHTML = html;

      cartArea.querySelectorAll('.cart-item__remove').forEach(function (btn) {
        btn.addEventListener('click', function () {
          var vid = parseInt(this.getAttribute('data-variant-id'), 10);
          cart = cart.filter(function (c) { return c.variantId !== vid; });
          if (!cart.length) { showSubview('catalog'); renderCatalog(); } else { renderCart(); }
        });
      });
    }

    function advanceWizard() {
      var nextBtn = document.getElementById('dep-wizard-next-btn');
      if (nextBtn) nextBtn.click();
    }

    function submitMaterials(checkoutAction) {
      syncCartToFields();
      if (checkoutActionSelect) {
        checkoutActionSelect.value = checkoutAction;
        checkoutActionSelect.dispatchEvent(new Event('change', { bubbles: true }));
      }
      advanceWizard();
    }

    function renderConfirmedBanner() {
      if (!confirmArea) return;
      var html = '<div class="checkout-confirmed-banner">';
      html += '<span class="checkout-confirmed-banner__icon" aria-hidden="true">' + CHECK_CIRCLE + '</span>';
      html += '<span class="checkout-confirmed-banner__text">Materiais confirmados</span>';
      html += '</div>';

      if (cart.length) {
        html += '<div class="checkout-summary"><div class="checkout-summary__section">';
        html += '<p class="checkout-summary__label">Materiais adquiridos</p>';
        cart.forEach(function (item) {
          html += '<div class="order-review-item"><span>' + escHtml(item.productName) + ' (' + escHtml(item.variantLabel) + ') × ' + item.qty + '</span>';
          html += '<span>' + fmtPrice(item.unitPrice * item.qty) + '</span></div>';
        });
        html += '<p class="checkout-summary__plan-meta" style="margin-top:.5rem">Total: ' + fmtPrice(getCartTotal()) + '</p>';
        html += '</div></div>';
      }
      confirmArea.innerHTML = html;
    }

    function bindButtons() {
      if (viewCartBtn) viewCartBtn.addEventListener('click', function () { renderCart(); showSubview('cart'); });
      if (skipCatalogBtn) skipCatalogBtn.addEventListener('click', function () { submitMaterials('pay_later'); });
      if (backCatalogBtn) backCatalogBtn.addEventListener('click', function () { showSubview('catalog'); renderCatalog(); });
      if (cancelCfgBtn) cancelCfgBtn.addEventListener('click', function () { showSubview('catalog'); renderCatalog(); });
      if (addToCartBtn) addToCartBtn.addEventListener('click', function () {
        if (!configureProduct || !configureVariantId) return;
        var variant = configureProduct.variants.filter(function (v) { return v.id === configureVariantId; })[0];
        var variantLabel = variant ? ([variant.color, variant.size].filter(Boolean).join(' · ') || 'Padrão') : 'Padrão';
        var newItem = {
          variantId: configureVariantId,
          variantLabel: variantLabel,
          productId: configureProduct.id,
          productName: configureProduct.name,
          qty: configureQty,
          unitPrice: parseFloat(configureProduct.price) || 0,
        };
        var replaced = false;
        for (var j = 0; j < cart.length; j++) {
          if (cart[j].productId === configureProduct.id) { cart[j] = newItem; replaced = true; break; }
        }
        if (!replaced) cart.push(newItem);
        showSubview('catalog');
        renderCatalog();
      });
      if (backToCatalogBtn) backToCatalogBtn.addEventListener('click', function () { showSubview('catalog'); renderCatalog(); });
      if (payCardBtn) payCardBtn.addEventListener('click', function () { submitMaterials('asaas_card'); });
      if (payPixBtn) payPixBtn.addEventListener('click', function () { submitMaterials('pix'); });
      if (skipCartBtn) skipCartBtn.addEventListener('click', function () { submitMaterials('pay_later'); });
    }

    function refresh() {
      var nextBtn = document.getElementById('dep-wizard-next-btn');
      rebuildCartFromFields();

      if (isMaterialsConfirmed()) {
        var subCatalog = document.getElementById('dep-products-subview-catalog');
        var subConfigure = document.getElementById('dep-products-subview-configure');
        var subCart = document.getElementById('dep-products-subview-cart');
        if (subCatalog) subCatalog.hidden = true;
        if (subConfigure) subConfigure.hidden = true;
        if (subCart) subCart.hidden = true;
        renderConfirmedBanner();
        if (nextBtn) nextBtn.hidden = false;
        return;
      }

      if (confirmArea) confirmArea.innerHTML = '';
      if (!hasProductsUi) return;
      showSubview('catalog');
      renderCatalog();
      if (nextBtn) nextBtn.hidden = true;
    }

    if (hasProductsUi) bindButtons();
    return refresh;
  }

  function bindReviewSummary() {
    var box = document.getElementById('dep-review-summary');
    if (!box) return null;

    function addRowData(rows, label, value) {
      if (!value) return;
      rows.push({ label: label, value: value });
    }

    function renderReviewRow(label, value) {
      var row = document.createElement('div');
      row.className = 'review-row';
      var labelEl = document.createElement('span');
      labelEl.className = 'review-row__label';
      labelEl.textContent = label;
      var valueEl = document.createElement('span');
      valueEl.className = 'review-row__value';
      valueEl.textContent = value;
      row.appendChild(labelEl);
      row.appendChild(valueEl);
      return row;
    }

    function classesSummary() {
      var nativeSelect = document.getElementById('id_dependent_class_groups');
      var catalog = Wz.readJsonScript('dep-class-catalog-json') || [];
      if (!nativeSelect) return '';
      var selectedIds = Array.prototype.map.call(nativeSelect.selectedOptions || [], function (o) { return o.value; });
      var names = catalog
        .filter(function (g) { return selectedIds.indexOf(String(g.id)) !== -1; })
        .map(function (g) { return g.category_name + (g.display_name ? ' · ' + g.display_name : ''); });
      return names.join(', ');
    }

    function planSummary() {
      var mode = getVal('id_financial_mode');
      var useFamilyPlan = document.getElementById('id_use_family_plan');
      if (!mode && useFamilyPlan && useFamilyPlan.checked) {
        mode = FINANCIAL_MODE_FAMILY_EXISTING;
      }
      if (mode === FINANCIAL_MODE_FAMILY_EXISTING) {
        return 'Plano familiar ativo do titular/responsável';
      }
      var planId = getVal('id_selected_plan');
      if (!planId) return '';
      var catalog = Wz.readJsonScript('dep-plan-catalog-json') || [];
      var plan = catalog.filter(function (p) { return String(p.id) === String(planId); })[0];
      if (!plan) return '';
      var price = plan.payment_method === 'pix' ? plan.charge_pix : plan.charge_card;
      var cycle = plan.gateway_code === 'stripe_card' ? 'mês' : (plan.cycle || '');
      var tierLabel = plan.commercial_tier_label || plan.name || plan.code;
      if (mode === FINANCIAL_MODE_FAMILY_UPGRADE) {
        return 'Upgrade familiar do titular — ' + tierLabel + ' — ' + fmtPrice(price) + '/' + cycle;
      }
      return tierLabel + ' — ' + fmtPrice(price) + '/' + cycle;
    }

    function materialsSummary() {
      var parts = [];
      depProductCatalog.forEach(function (product) {
        product.variants.forEach(function (variant) {
          var input = document.getElementById('id_material_variant_' + variant.id);
          var qty = input ? parseInt(input.value, 10) || 0 : 0;
          if (!qty) return;
          var variantLabel = [variant.color, variant.size].filter(Boolean).join(' · ');
          parts.push(product.name + (variantLabel ? ' (' + variantLabel + ')' : '') + ' x' + qty);
        });
      });
      return parts.join(', ');
    }

    function refresh() {
      var rows = [];
      addRowData(rows, 'Nome', getVal('id_dependent_name'));
      addRowData(rows, 'CPF', getVal('id_dependent_cpf'));
      addRowData(rows, 'Data de nascimento', Wz.formatIsoDateForDisplay(getVal('id_dependent_birthdate')));
      addRowData(rows, 'Parentesco', getSelectedOptionText('id_dependent_kinship_type'));
      addRowData(rows, 'Turma(s)', classesSummary());
      addRowData(rows, 'Plano', planSummary());
      addRowData(rows, 'Materiais', materialsSummary() || 'Nenhum material selecionado');
      box.textContent = '';
      if (!rows.length) {
        var empty = document.createElement('p');
        empty.className = 'review-empty';
        empty.textContent = 'Nenhum dado preenchido.';
        box.appendChild(empty);
        return;
      }
      rows.forEach(function (row) {
        box.appendChild(renderReviewRow(row.label, row.value));
      });
    }

    refresh();
    return refresh;
  }

  function bindStepNavigation(refreshClasses, refreshPlans, refreshMaterials, refreshReview) {
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

    var REFRESH_BY_KEY = { classes: refreshClasses, plan: refreshPlans, materials: refreshMaterials, review: refreshReview };

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
      if (
        (paymentConfirmed || materialsConfirmed) &&
        !getVal('id_dependent_password')
      ) {
        return 0;
      }
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

    function currentFinalLabel() {
      var paymentConfirmed = form.getAttribute('data-payment-confirmed') === 'true';
      var familyMode = getVal('id_financial_mode') === FINANCIAL_MODE_FAMILY_EXISTING;
      return (paymentConfirmed || familyMode) ? 'Continuar' : finalLabel;
    }

    function render() {
      steps.forEach(function (step, index) { step.hidden = index !== current; });
      if (stepCurrentEl) stepCurrentEl.textContent = String(current + 1);
      if (stepFillEl) stepFillEl.style.width = (((current + 1) / total) * 100) + '%';
      if (progressBarEl) progressBarEl.setAttribute('aria-valuenow', String(current + 1));
      if (backIsModalButton) backBtn.hidden = current === 0;
      if (actionBtn) {
        var isLast = current === total - 1;
        actionBtn.type = isLast ? 'submit' : 'button';
        actionBtn.hidden = false;
        if (actionLabelEl) actionLabelEl.textContent = isLast ? currentFinalLabel() : 'Próximo';
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
      var key = steps[current].getAttribute('data-step-key');
      if (key === 'plan' && refreshPlans && typeof refreshPlans.validate === 'function') {
        return refreshPlans.validate();
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
  bindMask(document.getElementById('id_dependent_cpf'), maskCpf);
  bindMask(document.getElementById('id_dependent_phone'), maskPhone);
  setupPasswordToggle('id_dependent_password', 'dep-pw-toggle');
  setupPasswordToggle('id_dependent_password_confirm', 'dep-pwc-toggle');
  var refreshClasses = bindClassCatalog();
  var refreshPlans = bindPlanCatalog();
  var refreshMaterials = bindDepProductsSection();
  var refreshReview = bindReviewSummary();
  bindStepNavigation(refreshClasses, refreshPlans, refreshMaterials, refreshReview);
})();
