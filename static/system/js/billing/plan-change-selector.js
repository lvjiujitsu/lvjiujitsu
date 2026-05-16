(function () {
  'use strict';

  var dataNode = document.getElementById('plan-catalog-data');
  var form = document.getElementById('plan-change-form');
  if (!dataNode || !form) {
    return;
  }

  var planCatalog = [];
  try {
    planCatalog = JSON.parse(dataNode.textContent || '[]');
  } catch (err) {
    planCatalog = [];
  }

  var membershipSummary = null;
  var summaryNode = document.getElementById('membership-summary-data');
  if (summaryNode) {
    try {
      membershipSummary = JSON.parse(summaryNode.textContent || 'null');
    } catch (err) {
      membershipSummary = null;
    }
  }

  var pixIconUrl = form.dataset.pixIconUrl || '';
  var cardIconUrl = form.dataset.cardIconUrl || '';

  var listContainer = form.querySelector('[data-plan-list]');
  var hiddenPlanInput = form.querySelector('#selected-plan');
  var hiddenLeftoverInput = form.querySelector('#leftover-action');
  var ctaRow = form.querySelector('[data-cta-row]');
  var ctaSubmit = form.querySelector('[data-cta-submit]');

  var CYCLE_LABELS = {
    monthly: 'Mensal',
    quarterly: 'Trimestral',
    semiannual: 'Semestral',
    annual: 'Anual'
  };
  var CYCLE_ORDER = ['monthly', 'quarterly', 'semiannual', 'annual'];

  var planSelectorState = {
    audience: '',
    commercial_tier: '',
    weekly_frequency: null,
    billing_cycle: '',
    payment_method: '',
    leftover_action: 'keep_credit'
  };

  var COMMERCIAL_TIER_ORDER = ['individual', 'fidelity', 'family'];

  function planCommercialTierKey(plan) {
    if (plan.commercial_tier) {
      return plan.commercial_tier;
    }
    return plan.is_family_plan ? 'family' : 'individual';
  }

  function commercialTierLabelForKey(tierKey, plans) {
    var sample = plans.find(function (p) { return planCommercialTierKey(p) === tierKey; });
    if (sample && sample.commercial_tier_label) {
      return sample.commercial_tier_label;
    }
    if (tierKey === 'fidelity') return 'Fidelidade';
    if (tierKey === 'family') return 'Família';
    return 'Individual';
  }

  var selectedPlanId = null;

  function formatBRL(value) {
    var n = Number(value);
    if (!isFinite(n)) {
      return 'R$ 0,00';
    }
    return 'R$ ' + n.toFixed(2).replace('.', ',');
  }

  function formatDateBR(iso) {
    if (!iso) return '';
    var d = new Date(iso);
    if (isNaN(d.getTime())) return '';
    var dd = String(d.getDate()).padStart(2, '0');
    var mm = String(d.getMonth() + 1).padStart(2, '0');
    var yyyy = d.getFullYear();
    return dd + '/' + mm + '/' + yyyy;
  }

  function pluralCycle(plan, count) {
    if (plan.billing_cycle === 'monthly') {
      return count === 1 ? 'mês' : 'meses';
    }
    if (plan.billing_cycle === 'quarterly') {
      return count === 1 ? 'trimestre' : 'trimestres';
    }
    if (plan.billing_cycle === 'semiannual') {
      return count === 1 ? 'semestre' : 'semestres';
    }
    return count === 1 ? 'ano' : 'anos';
  }

  function getPlanDimensionOptions(plans) {
    var audiences = [];
    var tiers = [];
    var frequencies = [];
    var cycles = [];
    var methods = [];
    plans.forEach(function (plan) {
      if (audiences.indexOf(plan.audience) === -1) audiences.push(plan.audience);
      var tk = planCommercialTierKey(plan);
      if (tiers.indexOf(tk) === -1) tiers.push(tk);
      var freq = Number(plan.weekly_frequency);
      if (frequencies.indexOf(freq) === -1) frequencies.push(freq);
      if (cycles.indexOf(plan.billing_cycle) === -1) cycles.push(plan.billing_cycle);
      if (methods.indexOf(plan.payment_method) === -1) methods.push(plan.payment_method);
    });
    return {
      audiences: audiences,
      commercial_tiers: tiers,
      weekly_frequencies: frequencies,
      billing_cycles: cycles,
      payment_methods: methods
    };
  }

  function ensurePlanSelectorDefaults(plans) {
    var dims = getPlanDimensionOptions(plans);
    if (!planSelectorState.audience || dims.audiences.indexOf(planSelectorState.audience) === -1) {
      planSelectorState.audience = dims.audiences.indexOf('adult') !== -1
        ? 'adult'
        : (dims.audiences[0] || '');
    }
    var availableTiers = dims.commercial_tiers.slice();
    if (!planSelectorState.commercial_tier || availableTiers.indexOf(planSelectorState.commercial_tier) === -1) {
      planSelectorState.commercial_tier = availableTiers.indexOf('individual') !== -1
        ? 'individual'
        : (availableTiers[0] || '');
    }
    if (planSelectorState.weekly_frequency === null
      || dims.weekly_frequencies.indexOf(planSelectorState.weekly_frequency) === -1) {
      planSelectorState.weekly_frequency = dims.weekly_frequencies.indexOf(5) !== -1
        ? 5
        : (dims.weekly_frequencies[0] || null);
    }
    if (!planSelectorState.billing_cycle || dims.billing_cycles.indexOf(planSelectorState.billing_cycle) === -1) {
      planSelectorState.billing_cycle = dims.billing_cycles.indexOf('monthly') !== -1
        ? 'monthly'
        : (dims.billing_cycles[0] || '');
    }
  }

  function getPlanForState(method) {
    return planCatalog.find(function (plan) {
      return plan.audience === planSelectorState.audience
        && planCommercialTierKey(plan) === planSelectorState.commercial_tier
        && Number(plan.weekly_frequency) === planSelectorState.weekly_frequency
        && plan.billing_cycle === planSelectorState.billing_cycle
        && plan.payment_method === method;
    }) || null;
  }

  function createPaymentIcon(paymentMethod) {
    var icon = document.createElement('span');
    icon.className = 'checkout-payment-icon checkout-payment-icon--' + paymentMethod;
    icon.setAttribute('aria-hidden', 'true');
    var iconUrl = paymentMethod === 'pix' ? pixIconUrl : cardIconUrl;
    if (iconUrl) {
      var image = document.createElement('img');
      image.className = 'checkout-payment-icon-image';
      image.src = iconUrl;
      image.alt = '';
      icon.appendChild(image);
    } else {
      icon.textContent = paymentMethod === 'pix' ? 'PIX' : 'CARD';
    }
    return icon;
  }

  function buildPlanMeta(plan) {
    var parts = [plan.cycle, plan.payment_method_label || ''];
    if (plan.weekly_frequency_label) parts.push(plan.weekly_frequency_label);
    if (plan.audience_label) parts.push(plan.audience_label);
    if (plan.commercial_tier_label) {
      parts.push(plan.commercial_tier_label);
    } else {
      parts.push(plan.is_family_plan ? 'Família' : 'Individual');
    }
    return parts.filter(Boolean).join(' · ');
  }

  function buildPlanSelectorRow(rowOptions) {
    var row = document.createElement('div');
    row.className = 'plan-selector-row';

    var label = document.createElement('span');
    label.className = 'plan-selector-label';
    label.textContent = rowOptions.label;
    row.appendChild(label);

    var chips = document.createElement('div');
    chips.className = 'plan-selector-chips';

    rowOptions.options.forEach(function (opt) {
      var chip = document.createElement('button');
      chip.type = 'button';
      chip.className = 'plan-selector-chip';
      if (String(opt.value) === String(rowOptions.currentValue)) {
        chip.classList.add('is-selected');
      }
      chip.textContent = opt.label;
      chip.addEventListener('click', function () {
        rowOptions.onChange(opt.value);
      });
      chips.appendChild(chip);
    });

    row.appendChild(chips);
    return row;
  }

  function buildPlanSelectorPaymentCard(plan, paymentMethod) {
    var card = document.createElement('button');
    card.type = 'button';
    card.className = 'plan-selector-payment-card';
    if (planSelectorState.payment_method === paymentMethod) {
      card.classList.add('is-selected');
    }
    card.dataset.paymentMethod = paymentMethod;

    var iconWrapper = document.createElement('span');
    iconWrapper.className = 'plan-selector-payment-icon';
    iconWrapper.appendChild(createPaymentIcon(paymentMethod));
    card.appendChild(iconWrapper);

    var info = document.createElement('span');
    info.className = 'plan-selector-payment-info';

    var title = document.createElement('span');
    title.className = 'plan-selector-payment-title';
    title.textContent = paymentMethod === 'pix' ? 'PIX' : 'Cartão';
    info.appendChild(title);

    var subtitle = document.createElement('span');
    subtitle.className = 'plan-selector-payment-subtitle';
    subtitle.textContent = paymentMethod === 'pix' ? 'Desconto comercial' : 'Cartão sem juros';
    info.appendChild(subtitle);

    var price = document.createElement('span');
    price.className = 'plan-selector-payment-price';
    price.textContent = formatBRL(plan.price);
    info.appendChild(price);

    if (plan.monthly_reference_price
      && parseFloat(plan.monthly_reference_price) !== parseFloat(plan.price)) {
      var hint = document.createElement('span');
      hint.className = 'plan-selector-payment-hint';
      hint.textContent = formatBRL(plan.monthly_reference_price) + ' por mês';
      info.appendChild(hint);
    }

    card.appendChild(info);

    card.addEventListener('click', function () {
      planSelectorState.payment_method = paymentMethod;
      planSelectorState.leftover_action = 'keep_credit';
      selectedPlanId = plan.id;
      renderPlanList();
    });

    return card;
  }

  function buildPlanSelectorSummary(plan) {
    var summary = document.createElement('div');
    summary.className = 'plan-selector-summary';

    var title = document.createElement('span');
    title.className = 'plan-selector-summary-title';
    title.textContent = 'Plano selecionado';
    summary.appendChild(title);

    var name = document.createElement('span');
    name.className = 'plan-selector-summary-name';
    name.textContent = plan.name;
    summary.appendChild(name);

    var meta = document.createElement('span');
    meta.className = 'plan-selector-summary-meta';
    meta.textContent = buildPlanMeta(plan);
    summary.appendChild(meta);

    var total = document.createElement('span');
    total.className = 'plan-selector-summary-total';
    total.textContent = formatBRL(plan.price);
    summary.appendChild(total);

    summary.appendChild(buildSwapBreakdown(plan));
    return summary;
  }

  function buildSwapBreakdown(plan) {
    var dl = document.createElement('dl');
    dl.className = 'plan-selector-summary-breakdown';

    var proration = plan.proration || {};

    if (membershipSummary) {
      appendBreakdownRow(dl, 'Saldo do plano atual', formatBRL(membershipSummary.available_credit));
    }

    if (proration.is_upgrade) {
      appendBreakdownRow(dl, 'Saldo aplicado',
        formatBRL(membershipSummary ? membershipSummary.available_credit : 0));
      appendBreakdownRow(
        dl,
        'Diferença a pagar',
        formatBRL(proration.additional_charge),
        { netClass: 'plan-selector-summary-net plan-selector-summary-net--upgrade', boldLabel: true }
      );
      appendBreakdownRow(
        dl,
        'Vigência cheia',
        formatPlanCycleLabel(plan, 1),
        { muted: true }
      );
    } else {
      appendBreakdownRow(
        dl,
        'Saldo cobre',
        formatPlanCycleLabel(plan, proration.cycles_covered)
      );
      appendBreakdownRow(
        dl,
        'Nova vigência até',
        formatDateBR(proration.new_period_end),
        { muted: true }
      );
      if (proration.has_leftover) {
        appendBreakdownRow(
          dl,
          'Sobra disponível',
          formatBRL(proration.leftover_credit),
          { netClass: 'plan-selector-summary-net plan-selector-summary-net--free', boldLabel: true }
        );
      } else {
        appendBreakdownRow(
          dl,
          'Sem sobra',
          'Saldo aplicado integralmente',
          { muted: true }
        );
      }
    }

    return dl;
  }

  function appendBreakdownRow(dl, label, value, opts) {
    opts = opts || {};
    var dt = document.createElement('dt');
    if (opts.boldLabel) {
      dt.classList.add('plan-selector-summary-net-label');
    }
    if (opts.muted) {
      dt.classList.add('plan-selector-summary-row-muted');
    }
    dt.textContent = label;
    dl.appendChild(dt);
    var dd = document.createElement('dd');
    if (opts.netClass) {
      dd.className = opts.netClass;
    }
    if (opts.muted) {
      dd.classList.add('plan-selector-summary-row-muted');
    }
    dd.textContent = value;
    dl.appendChild(dd);
  }

  function formatPlanCycleLabel(plan, cycles) {
    var months = (plan.proration && plan.proration.extension_months)
      || (cycles * cycleMonthsByPlan(plan.billing_cycle));
    var unitLabel = pluralCycle(plan, cycles);
    return cycles + ' ' + unitLabel + ' (' + months + ' ' + (months === 1 ? 'mês' : 'meses') + ')';
  }

  function cycleMonthsByPlan(cycle) {
    switch (cycle) {
      case 'monthly': return 1;
      case 'quarterly': return 3;
      case 'semiannual': return 6;
      case 'annual': return 12;
      default: return 1;
    }
  }

  function buildLeftoverActionPanel(plan) {
    var panel = document.createElement('div');
    panel.className = 'plan-leftover-action';

    var heading = document.createElement('p');
    heading.className = 'plan-leftover-action-heading';
    heading.textContent = 'Sobra de R$ ' + formatBRL(plan.proration.leftover_credit).replace('R$ ', '');
    panel.appendChild(heading);

    var description = document.createElement('p');
    description.className = 'plan-leftover-action-description';
    description.textContent = 'Por padrão, mantemos esse valor como crédito para a próxima renovação. Se preferir, podemos devolver no ato.';
    panel.appendChild(description);

    var refundSupported = !!(membershipSummary && membershipSummary.refund_supported);

    var optionGrid = document.createElement('div');
    optionGrid.className = 'plan-leftover-action-options';

    optionGrid.appendChild(buildLeftoverActionOption({
      value: 'keep_credit',
      title: 'Manter como crédito',
      description: 'Aplica desconto na próxima renovação.',
      currentValue: planSelectorState.leftover_action,
      disabled: false
    }));

    optionGrid.appendChild(buildLeftoverActionOption({
      value: 'refund',
      title: 'Receber valor de volta',
      description: refundSupported
        ? 'Devolve no provedor original (' + (membershipSummary.payment_provider || 'cartão/PIX') + ').'
        : 'Indisponível: pagamento original não suporta estorno automático.',
      currentValue: planSelectorState.leftover_action,
      disabled: !refundSupported
    }));

    panel.appendChild(optionGrid);
    return panel;
  }

  function buildLeftoverActionOption(opt) {
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'plan-leftover-option';
    if (String(opt.value) === String(opt.currentValue)) {
      btn.classList.add('is-selected');
    }
    if (opt.disabled) {
      btn.classList.add('is-disabled');
      btn.disabled = true;
    }
    var title = document.createElement('span');
    title.className = 'plan-leftover-option-title';
    title.textContent = opt.title;
    btn.appendChild(title);
    var desc = document.createElement('span');
    desc.className = 'plan-leftover-option-description';
    desc.textContent = opt.description;
    btn.appendChild(desc);
    btn.addEventListener('click', function () {
      if (opt.disabled) return;
      planSelectorState.leftover_action = opt.value;
      renderPlanList();
    });
    return btn;
  }

  function buildPlanSelectorHint(pixPlan, creditPlan) {
    var hint = document.createElement('p');
    hint.className = 'plan-selector-hint';
    if (!pixPlan && !creditPlan) {
      hint.textContent = 'Nenhuma combinação disponível para os filtros atuais.';
    } else {
      hint.textContent = 'Escolha PIX ou Cartão para ver o cálculo da troca.';
    }
    return hint;
  }

  function syncCta(resolvedPlan) {
    if (!ctaRow || !ctaSubmit || !hiddenPlanInput || !hiddenLeftoverInput) return;
    if (resolvedPlan) {
      hiddenPlanInput.value = String(resolvedPlan.id);
      hiddenLeftoverInput.value = planSelectorState.leftover_action;
      var proration = resolvedPlan.proration || {};
      if (proration.is_upgrade) {
        ctaSubmit.textContent = 'Confirmar e pagar';
      } else if (proration.has_leftover && planSelectorState.leftover_action === 'refund') {
        ctaSubmit.textContent = 'Confirmar troca e devolver sobra';
      } else {
        ctaSubmit.textContent = 'Confirmar troca';
      }
      ctaRow.hidden = false;
    } else {
      hiddenPlanInput.value = '';
      hiddenLeftoverInput.value = 'keep_credit';
      ctaSubmit.textContent = 'Trocar para este plano';
      ctaRow.hidden = true;
    }
  }

  function renderPlanList() {
    if (!listContainer) return;
    listContainer.innerHTML = '';

    if (planCatalog.length === 0) {
      var empty = document.createElement('p');
      empty.className = 'plan-selector-hint';
      empty.textContent = 'Nenhum plano disponível para troca no momento.';
      listContainer.appendChild(empty);
      syncCta(null);
      return;
    }

    ensurePlanSelectorDefaults(planCatalog);

    var dims = getPlanDimensionOptions(planCatalog);

    var selector = document.createElement('div');
    selector.className = 'plan-selector';

    if (dims.audiences.length > 1) {
      selector.appendChild(buildPlanSelectorRow({
        label: 'Quem treina',
        options: dims.audiences.map(function (audience) {
          var sample = planCatalog.find(function (p) { return p.audience === audience; });
          return {
            value: audience,
            label: sample && sample.audience_label
              ? sample.audience_label
              : (audience === 'adult' ? 'Adulto' : 'Kids/Juvenil')
          };
        }),
        currentValue: planSelectorState.audience,
        onChange: function (value) {
          planSelectorState.audience = value;
          planSelectorState.payment_method = '';
          planSelectorState.leftover_action = 'keep_credit';
          selectedPlanId = null;
          renderPlanList();
        }
      }));
    }

    if (dims.commercial_tiers.length > 1) {
      var sortedTiers = dims.commercial_tiers.slice().sort(function (a, b) {
        var ai = COMMERCIAL_TIER_ORDER.indexOf(a);
        var bi = COMMERCIAL_TIER_ORDER.indexOf(b);
        return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi);
      });
      selector.appendChild(buildPlanSelectorRow({
        label: 'Categoria do plano',
        options: sortedTiers.map(function (tierKey) {
          return {
            value: tierKey,
            label: commercialTierLabelForKey(tierKey, planCatalog)
          };
        }),
        currentValue: planSelectorState.commercial_tier,
        onChange: function (value) {
          planSelectorState.commercial_tier = value;
          planSelectorState.payment_method = '';
          planSelectorState.leftover_action = 'keep_credit';
          selectedPlanId = null;
          renderPlanList();
        }
      }));
    }

    if (dims.weekly_frequencies.length > 1) {
      var sortedFrequencies = dims.weekly_frequencies.slice().sort(function (a, b) { return b - a; });
      selector.appendChild(buildPlanSelectorRow({
        label: 'Frequência',
        options: sortedFrequencies.map(function (freq) {
          return { value: freq, label: freq + 'x por semana' };
        }),
        currentValue: planSelectorState.weekly_frequency,
        onChange: function (value) {
          planSelectorState.weekly_frequency = Number(value);
          planSelectorState.payment_method = '';
          planSelectorState.leftover_action = 'keep_credit';
          selectedPlanId = null;
          renderPlanList();
        }
      }));
    }

    selector.appendChild(buildPlanSelectorRow({
      label: 'Recorrência',
      options: CYCLE_ORDER
        .filter(function (c) { return dims.billing_cycles.indexOf(c) !== -1; })
        .map(function (c) { return { value: c, label: CYCLE_LABELS[c] }; }),
      currentValue: planSelectorState.billing_cycle,
      onChange: function (value) {
        planSelectorState.billing_cycle = value;
        planSelectorState.payment_method = '';
        planSelectorState.leftover_action = 'keep_credit';
        selectedPlanId = null;
        renderPlanList();
      }
    }));

    var paymentLabel = document.createElement('span');
    paymentLabel.className = 'plan-selector-label';
    paymentLabel.textContent = 'Forma de pagamento';
    selector.appendChild(paymentLabel);

    var paymentGrid = document.createElement('div');
    paymentGrid.className = 'plan-selector-payment-grid';

    var pixPlan = getPlanForState('pix');
    var creditPlan = getPlanForState('credit_card');

    if (pixPlan) {
      paymentGrid.appendChild(buildPlanSelectorPaymentCard(pixPlan, 'pix'));
    }
    if (creditPlan) {
      paymentGrid.appendChild(buildPlanSelectorPaymentCard(creditPlan, 'credit_card'));
    }
    selector.appendChild(paymentGrid);

    var resolvedPlan = planSelectorState.payment_method
      ? getPlanForState(planSelectorState.payment_method)
      : null;

    if (resolvedPlan) {
      selector.appendChild(buildPlanSelectorSummary(resolvedPlan));
      if (resolvedPlan.proration && resolvedPlan.proration.has_leftover) {
        selector.appendChild(buildLeftoverActionPanel(resolvedPlan));
      }
      selectedPlanId = resolvedPlan.id;
    } else {
      selector.appendChild(buildPlanSelectorHint(pixPlan, creditPlan));
      selectedPlanId = null;
    }

    listContainer.appendChild(selector);
    syncCta(resolvedPlan);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', renderPlanList);
  } else {
    renderPlanList();
  }
})();
