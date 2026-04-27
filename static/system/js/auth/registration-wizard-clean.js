/**
 * LV JIU JITSU - Registration Wizard (Clean Implementation)
 * Dynamic multi-step registration form with profile-based flows
 */
(function () {
  'use strict';

  // ============================================================================
  // DOM Elements
  // ============================================================================
  var form = document.getElementById('client-registration-form');
  if (!form) return;
  var pixIconUrl = form.dataset.pixIconUrl || '';
  var cardIconUrl = form.dataset.cardIconUrl || '';

  var profileInputs = Array.from(form.querySelectorAll('input[name="registration_profile"]'));
  var profileChoiceCards = Array.from(form.querySelectorAll('[data-choice-card]'));
  var dependentToggle = document.getElementById('include-dependent');
  var dependentToggleCard = form.querySelector('[data-dependent-toggle-card]');
  var dependentCountSelect = form.querySelector('[data-dependent-count]');
  var dependentCountHelp = form.querySelector('[data-dependent-count-help]');
  var otherTypePanel = form.querySelector('[data-other-type-panel]');
  var extraDependentsPayloadInput = document.getElementById('extra-dependents-payload');
  
  var stepsContainer = form.querySelector('[data-wizard-steps-container]');
  var stepPanels = form.querySelector('[data-step-panels]');
  var progressFill = form.querySelector('[data-progress-fill]');
  
  var backButton = form.querySelector('[data-step-back]');
  var nextButton = form.querySelector('[data-step-next]');
  var submitButton = form.querySelector('[data-step-submit]');
  var dateInputs = Array.from(form.querySelectorAll('[data-date-mask]'));
  var kinshipSelects = Array.from(form.querySelectorAll('[data-kinship-select]'));
  var martialArtPresenceSelects = Array.from(form.querySelectorAll('[data-martial-art-presence-select]'));
  var martialArtSelects = Array.from(form.querySelectorAll('[data-martial-art-select]'));
  
  var draftNote = document.querySelector('[data-registration-draft-note]');
  var draftLabel = document.querySelector('[data-registration-draft-label]');
  var discardButton = document.querySelector('[data-registration-discard]');
  
  var registrationCatalogNode = document.getElementById('registration-catalog');
  var registrationCatalog = registrationCatalogNode ? JSON.parse(registrationCatalogNode.textContent) : [];
  var ibjjfAgeCategoriesNode = document.getElementById('ibjjf-age-categories');
  var ibjjfAgeCategories = ibjjfAgeCategoriesNode ? JSON.parse(ibjjfAgeCategoriesNode.textContent) : [];
  var stepValidateUrl = form.dataset.stepValidateUrl || '';
  var csrfTokenInput = form.querySelector('[name="csrfmiddlewaretoken"]');
  var csrfToken = csrfTokenInput ? csrfTokenInput.value : '';

  var planCatalogNode = document.getElementById('plan-catalog');
  var planCatalog = planCatalogNode ? JSON.parse(planCatalogNode.textContent) : [];

  var productCatalogNode = document.getElementById('product-catalog');
  var productCatalog = productCatalogNode ? JSON.parse(productCatalogNode.textContent) : [];
  var checkoutActionInput = document.getElementById('checkout-action');
  var checkoutActionButtons = Array.from(form.querySelectorAll('[data-checkout-action]'));
  var checkoutActionHelp = form.querySelector('[data-checkout-action-help]');
  var checkoutDecision = form.querySelector('[data-checkout-decision]');

  // ============================================================================
  // State
  // ============================================================================
  var currentStepIndex = 0;
  var selectedPlanId = null;
  var selectedProducts = {};
  var checkoutTotal = 0;
  var checkoutAction = normalizeCheckoutAction(checkoutActionInput ? checkoutActionInput.value : 'pay_later');
  var activeSteps = [];
  var extraDependents = [];
  var dependentSequence = 0;
  var isAdvancing = false;
  
  var DRAFT_KEY = 'lv-register-draft-clean';
  var DRAFT_TTL_MS = 30 * 60 * 1000;
  var REGISTRATION_COMPLETED_KEY = 'lv-registration-completed';
  var draftSaveTimeout = null;

  // ============================================================================
  // Step Definitions
  // ============================================================================
  var STEP_DEFINITIONS = {
    type: {
      key: 'type',
      label: 'Tipo',
      title: 'Tipo de cadastro',
      panelSelector: '[data-panel="type"]',
      requiredFields: ['registration_profile']
    },
    holder: {
      key: 'holder',
      label: 'Aluno',
      title: 'Dados do aluno',
      panelSelector: '[data-panel="holder"]',
      requiredFields: ['holder_name', 'holder_cpf', 'holder_birthdate', 'holder_biological_sex', 'holder_password', 'holder_password_confirm']
    },
    holder_titular: {
      key: 'holder_titular',
      label: 'Titular',
      title: 'Dados do titular',
      panelSelector: '[data-panel="holder"]',
      requiredFields: ['holder_name', 'holder_cpf', 'holder_birthdate', 'holder_biological_sex', 'holder_password', 'holder_password_confirm']
    },
    dependent: {
      key: 'dependent',
      label: 'Dependente',
      title: 'Dados do dependente',
      panelSelector: '[data-panel="dependent"]',
      requiredFields: ['dependent_name', 'dependent_cpf', 'dependent_birthdate', 'dependent_biological_sex', 'dependent_kinship_type']
    },
    guardian: {
      key: 'guardian',
      label: 'Responsável',
      title: 'Dados do responsável',
      panelSelector: '[data-panel="guardian"]',
      requiredFields: ['guardian_name', 'guardian_cpf', 'guardian_password', 'guardian_password_confirm']
    },
    guardian_dependent_count: {
      key: 'dependent_count',
      label: 'Qtd. dep.',
      title: 'Quantidade de dependentes',
      panelSelector: '[data-panel="dependent-count"]',
      requiredFields: ['dependent_count']
    },
    student: {
      key: 'student',
      label: 'Aluno',
      title: 'Dados do aluno',
      panelSelector: '[data-panel="student"]',
      requiredFields: ['student_name', 'student_cpf', 'student_birthdate', 'student_biological_sex', 'student_password', 'student_password_confirm', 'student_kinship_type']
    },
    holder_classes: {
      key: 'holder_classes',
      label: 'Turmas titular',
      title: 'Turmas do titular/aluno',
      panelSelector: '[data-panel="holder-classes"]',
      requiredFields: []
    },
    holder_medical: {
      key: 'holder_medical',
      label: 'Prontuário titular',
      title: 'Prontuário do titular/aluno',
      panelSelector: '[data-panel="holder-medical"]',
      requiredFields: []
    },
    dependent_classes: {
      key: 'dependent_classes',
      label: 'Turmas dependente',
      title: 'Turmas do dependente',
      panelSelector: '[data-panel="dependent-classes"]',
      requiredFields: []
    },
    dependent_medical: {
      key: 'dependent_medical',
      label: 'Prontuário dependente',
      title: 'Prontuário do dependente',
      panelSelector: '[data-panel="dependent-medical"]',
      requiredFields: []
    },
    student_classes: {
      key: 'student_classes',
      label: 'Turmas aluno',
      title: 'Turmas do aluno',
      panelSelector: '[data-panel="student-classes"]',
      requiredFields: []
    },
    student_medical: {
      key: 'student_medical',
      label: 'Prontuário aluno',
      title: 'Prontuário do aluno',
      panelSelector: '[data-panel="student-medical"]',
      requiredFields: []
    },
    other: {
      key: 'other',
      label: 'Dados',
      title: 'Seus dados',
      panelSelector: '[data-panel="other"]',
      requiredFields: ['other_name', 'other_cpf', 'other_birthdate', 'other_password', 'other_password_confirm']
    },
    plan: {
      key: 'plan',
      label: 'Plano',
      title: 'Escolha seu plano',
      panelSelector: '[data-panel="plan"]',
      requiredFields: []
    },
    materials: {
      key: 'materials',
      label: 'Materiais',
      title: 'Materiais',
      panelSelector: '[data-panel="materials"]',
      requiredFields: []
    },
    summary: {
      key: 'summary',
      label: 'Resumo',
      title: 'Resumo',
      panelSelector: '[data-panel="summary"]',
      requiredFields: []
    }
  };

  // ============================================================================
  // Flow Computation
  // ============================================================================
  function computeActiveSteps() {
    var profile = getSelectedProfile();
    var hasDependentFlow = dependentToggle && dependentToggle.checked;
    var dependentCount = getDependentCount();
    var steps = [];

    // Always start with type selection
    steps.push(STEP_DEFINITIONS.type);

    if (profile === 'other') {
      // OTHER: Tipo → Dados (2 steps)
      steps.push(STEP_DEFINITIONS.other);
    } else if (profile === 'guardian') {
      // RESPONSÁVEL: Tipo -> Responsável -> Quantidade -> Dependente(s) -> Plano -> Resumo
      steps.push(STEP_DEFINITIONS.guardian);
      steps.push(STEP_DEFINITIONS.guardian_dependent_count);
      for (var guardianDependentIndex = 1; guardianDependentIndex <= dependentCount; guardianDependentIndex += 1) {
        steps.push(buildDependentStep(STEP_DEFINITIONS.student, guardianDependentIndex, dependentCount, 'student', 'Dados'));
        steps.push(buildDependentStep(STEP_DEFINITIONS.student_classes, guardianDependentIndex, dependentCount, 'student', 'Turmas'));
        steps.push(buildDependentStep(STEP_DEFINITIONS.student_medical, guardianDependentIndex, dependentCount, 'student', 'Pront.'));
      }
      trimExtraDependentsToCount(dependentCount);
      steps.push(STEP_DEFINITIONS.plan);
      steps.push(STEP_DEFINITIONS.materials);
      steps.push(STEP_DEFINITIONS.summary);
    } else if (profile === 'holder') {
      if (hasDependentFlow) {
        // TITULAR + DEPENDENTE(S): fluxo completo por pessoa -> Plano -> Resumo
        steps.push(STEP_DEFINITIONS.holder_titular);
        steps.push(STEP_DEFINITIONS.holder_classes);
        steps.push(STEP_DEFINITIONS.holder_medical);
        steps.push(STEP_DEFINITIONS.guardian_dependent_count);
        for (var holderDependentIndex = 1; holderDependentIndex <= dependentCount; holderDependentIndex += 1) {
          steps.push(buildDependentStep(STEP_DEFINITIONS.dependent, holderDependentIndex, dependentCount, 'dependent', 'Dados'));
          steps.push(buildDependentStep(STEP_DEFINITIONS.dependent_classes, holderDependentIndex, dependentCount, 'dependent', 'Turmas'));
          steps.push(buildDependentStep(STEP_DEFINITIONS.dependent_medical, holderDependentIndex, dependentCount, 'dependent', 'Pront.'));
        }
        trimExtraDependentsToCount(dependentCount);
      } else {
        // ALUNO: fluxo completo da própria pessoa
        steps.push(STEP_DEFINITIONS.holder);
        steps.push(
          Object.assign({}, STEP_DEFINITIONS.holder_classes, {
            label: 'Jiu Jitsu',
            title: 'Jiu Jitsu Adulto'
          })
        );
        steps.push(STEP_DEFINITIONS.holder_medical);
        trimExtraDependentsToCount(1);
      }
      steps.push(STEP_DEFINITIONS.plan);
      steps.push(STEP_DEFINITIONS.materials);
      steps.push(STEP_DEFINITIONS.summary);
    } else {
      trimExtraDependentsToCount(1);
    }

    syncExtraDependentsPayload();
    return steps;
  }

  function getSelectedProfile() {
    var selected = profileInputs.find(function (input) { return input.checked; });
    return selected ? selected.value : 'holder';
  }

  function buildDependentStep(stepDefinition, dependentIndex, dependentCount, dependentPrefix, labelPrefix) {
    if (dependentCount <= 1) {
      return Object.assign({}, stepDefinition, { dependentIndex: 1, dependentTotal: 1, dependentPrefix: dependentPrefix });
    }
    return Object.assign({}, stepDefinition, {
      label: labelPrefix + ' dep. ' + dependentIndex,
      title: stepDefinition.title + ' (' + dependentIndex + ' de ' + dependentCount + ')',
      dependentIndex: dependentIndex,
      dependentTotal: dependentCount,
      dependentPrefix: dependentPrefix
    });
  }

  // ============================================================================
  // Rendering
  // ============================================================================
  function renderStepIndicators() {
    if (!stepsContainer) return;
    
    stepsContainer.innerHTML = '';
    
    activeSteps.forEach(function (step, index) {
      var button = document.createElement('button');
      button.className = 'wizard-progress-step';
      button.type = 'button';
      button.dataset.stepIndex = index;
      
      if (index === currentStepIndex) {
        button.classList.add('is-active');
      } else if (index < currentStepIndex) {
        button.classList.add('is-complete');
      }
      
      var indexSpan = document.createElement('span');
      indexSpan.className = 'wizard-progress-index';
      indexSpan.textContent = String(index + 1);
      
      var labelSmall = document.createElement('small');
      labelSmall.textContent = step.label;
      
      button.appendChild(indexSpan);
      button.appendChild(labelSmall);
      button.addEventListener('click', function () {
        if (index < currentStepIndex) {
          goToStep(index);
        }
      });
      
      stepsContainer.appendChild(button);
    });
  }

  function renderStepPanels() {
    if (!stepPanels) return;
    
    var currentStep = activeSteps[currentStepIndex];
    if (!currentStep) return;

    hydrateStepDependentData(currentStep);
    
    var allPanels = Array.from(stepPanels.querySelectorAll('[data-panel]'));
    allPanels.forEach(function (panel) {
      var isActive = panel.matches(currentStep.panelSelector);
      panel.classList.toggle('is-hidden', !isActive);
      panel.hidden = !isActive;
      
      // Update panel title
      var titleElement = panel.querySelector('[data-panel-title]');
      if (titleElement && isActive) {
        titleElement.textContent = currentStep.title;
      }
      
      // Update step label
      var stepLabel = panel.querySelector('[data-step-label]');
      if (stepLabel && isActive) {
        stepLabel.textContent = 'Etapa ' + (currentStepIndex + 1) + ' de ' + activeSteps.length;
      }
    });

    // Render checkout panels when active
    if (currentStep.key === 'holder_classes') {
      renderClassGroupCards('holder');
    }
    if (currentStep.key === 'dependent_classes') {
      renderClassGroupCards('dependent');
    }
    if (currentStep.key === 'student_classes') {
      renderClassGroupCards('student');
    }
    if (currentStep.key === 'plan') {
      renderPlanList();
    }
    if (currentStep.key === 'materials') {
      renderProductList();
    }
    if (currentStep.key === 'summary') {
      renderSummary();
    }
  }

  function updateProgressBar() {
    if (!progressFill) return;
    var percentage = activeSteps.length > 0 ? ((currentStepIndex + 1) / activeSteps.length) * 100 : 0;
    progressFill.style.width = percentage + '%';
  }

  function updateNavigation() {
    var isFirstStep = currentStepIndex === 0;
    var isLastStep = currentStepIndex === activeSteps.length - 1;
    
    if (backButton) {
      backButton.classList.toggle('is-hidden', isFirstStep);
      backButton.hidden = isFirstStep;
    }
    
    if (nextButton) {
      nextButton.classList.toggle('is-hidden', isLastStep);
      nextButton.hidden = isLastStep;
    }
    
    if (submitButton) {
      submitButton.classList.toggle('is-hidden', !isLastStep);
      submitButton.hidden = !isLastStep;
    }
  }

  function updateUI() {
    syncProfileChoiceCards();
    syncDependentToggleState();
    syncKinshipOtherFields();
    syncMartialFields();
    renderStepIndicators();
    scrollActiveStepIntoView();
    renderStepPanels();
    updateProgressBar();
    updateNavigation();
    updateDependentToggleVisibility();
    updateOtherTypeVisibility();
  }

  function scrollActiveStepIntoView() {
    if (!stepsContainer || !window.matchMedia('(max-width: 767px)').matches) {
      return;
    }
    var activeStepIndicator = stepsContainer.querySelector('.wizard-progress-step.is-active');
    if (!activeStepIndicator) {
      return;
    }
    window.requestAnimationFrame(function () {
      activeStepIndicator.scrollIntoView({
        behavior: 'smooth',
        inline: 'center',
        block: 'nearest'
      });
    });
  }

  function updateDependentToggleVisibility() {
    if (!dependentToggleCard) return;
    var profile = getSelectedProfile();
    var shouldShow = profile === 'holder';
    dependentToggleCard.classList.toggle('is-hidden', !shouldShow);
    dependentToggleCard.hidden = !shouldShow;

    updateDependentCountHelp();
  }

  function updateOtherTypeVisibility() {
    if (!otherTypePanel) return;
    var profile = getSelectedProfile();
    var shouldShow = profile === 'other';
    otherTypePanel.classList.toggle('is-hidden', !shouldShow);
    otherTypePanel.hidden = !shouldShow;
  }

  function syncProfileChoiceCards() {
    profileChoiceCards.forEach(function (card) {
      var input = card.querySelector('input[name="registration_profile"]');
      card.classList.toggle('is-selected', Boolean(input && input.checked));
    });
  }

  function syncDependentToggleState() {
    if (!dependentToggleCard || !dependentToggle) {
      return;
    }
    dependentToggleCard.classList.toggle('is-active', dependentToggle.checked);
  }

  function getDependentCount() {
    if (!dependentCountSelect) {
      return 1;
    }
    var rawValue = Number(dependentCountSelect.value || '1');
    if (Number.isNaN(rawValue)) {
      return 1;
    }
    return Math.max(1, Math.min(5, rawValue));
  }

  function updateDependentCountHelp() {
    if (!dependentCountHelp) {
      return;
    }
    var dependentCount = getDependentCount();
    dependentCountHelp.textContent = 'As etapas de dependente serão ajustadas para ' + dependentCount + ' dependente' + (dependentCount > 1 ? 's.' : '.');
  }

  function syncKinshipOtherFields() {
    kinshipSelects.forEach(function (selectField) {
      updateKinshipOtherField(selectField);
    });
  }

  function updateKinshipOtherField(selectField) {
    if (!selectField) {
      return;
    }
    var wrapper = form.querySelector('[data-kinship-other-wrapper="' + selectField.name + '"]');
    if (!wrapper) {
      return;
    }
    var input = wrapper.querySelector('input');
    var shouldShow = selectField.value === 'other';
    wrapper.classList.toggle('is-hidden', !shouldShow);
    wrapper.hidden = !shouldShow;
    if (input) {
      input.disabled = !shouldShow;
      if (!shouldShow) {
        input.value = '';
      }
    }
  }

  function syncMartialFields() {
    getMartialArtPrefixes().forEach(function (prefix) {
      updateMartialFields(prefix);
    });
  }

  function getMartialArtPrefixes() {
    var prefixes = {};
    martialArtPresenceSelects.forEach(function (selectField) {
      if (selectField.dataset.martialPrefix) {
        prefixes[selectField.dataset.martialPrefix] = true;
      }
    });
    martialArtSelects.forEach(function (selectField) {
      if (selectField.dataset.martialPrefix) {
        prefixes[selectField.dataset.martialPrefix] = true;
      }
    });
    return Object.keys(prefixes);
  }

  function updateMartialFields(prefix) {
    if (!prefix) {
      return;
    }
    var presenceField = form.querySelector('[name="' + prefix + '_has_martial_art"]');
    var martialArtField = form.querySelector('[name="' + prefix + '_martial_art"]');
    var detailsWrapper = form.querySelector('[data-martial-art-details-wrapper="' + prefix + '"]');
    var hasMartialArt = Boolean(
      (presenceField && presenceField.value === 'yes') ||
      (!presenceField || !presenceField.value) && martialArtField && martialArtField.value
    );
    if (detailsWrapper) {
      detailsWrapper.classList.toggle('is-hidden', !hasMartialArt);
      detailsWrapper.hidden = !hasMartialArt;
      if (martialArtField) {
        martialArtField.disabled = !hasMartialArt;
        if (!hasMartialArt) {
          martialArtField.value = '';
        }
      }
    }
    var jiuWrappers = form.querySelectorAll('[data-jiu-jitsu-only-wrapper="' + prefix + '"]');
    var nonJiuWrappers = form.querySelectorAll('[data-non-jiu-jitsu-only-wrapper="' + prefix + '"]');
    var martialArtValue = martialArtField ? martialArtField.value : '';
    var shouldShowJiu = hasMartialArt && martialArtValue === 'jiu_jitsu';
    var shouldShowNonJiu = hasMartialArt && !!martialArtValue && martialArtValue !== 'jiu_jitsu';
    jiuWrappers.forEach(function (wrapper) {
      wrapper.classList.toggle('is-hidden', !shouldShowJiu);
      wrapper.hidden = !shouldShowJiu;
      var field = wrapper.querySelector('select, input');
      if (field) {
        field.disabled = !shouldShowJiu;
        if (!shouldShowJiu) {
          if (field.tagName === 'SELECT') {
            field.value = '';
          } else {
            field.value = '';
          }
        }
      }
    });
    nonJiuWrappers.forEach(function (wrapper) {
      wrapper.classList.toggle('is-hidden', !shouldShowNonJiu);
      wrapper.hidden = !shouldShowNonJiu;
      var field = wrapper.querySelector('select, input, textarea');
      if (field) {
        field.disabled = !shouldShowNonJiu;
        if (!shouldShowNonJiu) {
          field.value = '';
        }
      }
    });
  }

  function trimExtraDependentsToCount(totalDependents) {
    var targetExtras = Math.max(0, totalDependents - 1);
    while (extraDependents.length > targetExtras) {
      extraDependents.pop();
    }
    while (extraDependents.length < targetExtras) {
      extraDependents.push(buildEmptyDependentData());
    }
    syncExtraDependentsPayload();
  }

  function buildEmptyDependentData() {
    return {
      full_name: '',
      cpf: '',
      birth_date: '',
      biological_sex: '',
      email: '',
      phone: '',
      password: '',
      password_confirm: '',
      kinship_type: '',
      kinship_other_label: '',
      class_groups: [],
      blood_type: '',
      allergies: '',
      injuries: '',
      emergency_contact: '',
      has_martial_art: '',
      martial_art: '',
      martial_art_graduation: '',
      jiu_jitsu_belt: '',
      jiu_jitsu_stripes: ''
    };
  }

  function getDependentContext(step) {
    if (!step || !step.dependentPrefix || !step.dependentIndex) {
      return null;
    }
    if (step.dependentIndex <= 1) {
      return null;
    }
    return {
      prefix: step.dependentPrefix,
      index: step.dependentIndex,
      extraIndex: step.dependentIndex - 2,
      panelSelector: step.panelSelector
    };
  }

  function getField(selector) {
    return form.querySelector(selector);
  }

  function getInputValue(name) {
    var field = getField('[name="' + name + '"]');
    return field ? field.value : '';
  }

  function setInputValue(name, value) {
    var field = getField('[name="' + name + '"]');
    if (!field) {
      return;
    }
    field.value = value || '';
  }

  function getSelectMultipleValues(name) {
    var selectField = getField('select[name="' + name + '"]');
    if (!selectField) {
      return [];
    }
    return Array.from(selectField.selectedOptions || []).map(function (option) {
      return option.value;
    }).filter(Boolean);
  }

  function setSelectMultipleValues(name, values) {
    var selectField = getField('select[name="' + name + '"]');
    if (!selectField) {
      return;
    }
    var selectedValues = new Set(Array.isArray(values) ? values.map(String) : []);
    Array.from(selectField.options).forEach(function (option) {
      option.selected = selectedValues.has(String(option.value));
    });
  }

  function readPrimaryDependentData(prefix) {
    return {
      full_name: getInputValue(prefix + '_name'),
      cpf: getInputValue(prefix + '_cpf'),
      birth_date: getInputValue(prefix + '_birthdate'),
      biological_sex: getInputValue(prefix + '_biological_sex'),
      email: getInputValue(prefix + '_email'),
      phone: getInputValue(prefix + '_phone'),
      password: getInputValue(prefix + '_password'),
      password_confirm: getInputValue(prefix + '_password_confirm'),
      kinship_type: getInputValue(prefix + '_kinship_type'),
      kinship_other_label: getInputValue(prefix + '_kinship_other_label'),
      class_groups: getSelectMultipleValues(prefix + '_class_groups'),
      blood_type: getInputValue(prefix + '_blood_type'),
      allergies: getInputValue(prefix + '_allergies'),
      injuries: getInputValue(prefix + '_injuries'),
      emergency_contact: getInputValue(prefix + '_emergency_contact'),
      has_martial_art: getInputValue(prefix + '_has_martial_art'),
      martial_art: getInputValue(prefix + '_martial_art'),
      martial_art_graduation: getInputValue(prefix + '_martial_art_graduation'),
      jiu_jitsu_belt: getInputValue(prefix + '_jiu_jitsu_belt'),
      jiu_jitsu_stripes: getInputValue(prefix + '_jiu_jitsu_stripes')
    };
  }

  function writePrimaryDependentData(prefix, dependentData) {
    var payload = dependentData || buildEmptyDependentData();
    setInputValue(prefix + '_name', payload.full_name);
    setInputValue(prefix + '_cpf', payload.cpf);
    setInputValue(prefix + '_birthdate', payload.birth_date);
    setInputValue(prefix + '_biological_sex', payload.biological_sex);
    setInputValue(prefix + '_email', payload.email);
    setInputValue(prefix + '_phone', payload.phone);
    setInputValue(prefix + '_password', payload.password);
    setInputValue(prefix + '_password_confirm', payload.password_confirm);
    setInputValue(prefix + '_kinship_type', payload.kinship_type);
    setInputValue(prefix + '_kinship_other_label', payload.kinship_other_label);
    setSelectMultipleValues(prefix + '_class_groups', payload.class_groups);
    setInputValue(prefix + '_blood_type', payload.blood_type);
    setInputValue(prefix + '_allergies', payload.allergies);
    setInputValue(prefix + '_injuries', payload.injuries);
    setInputValue(prefix + '_emergency_contact', payload.emergency_contact);
    setInputValue(prefix + '_has_martial_art', payload.has_martial_art);
    setInputValue(prefix + '_martial_art', payload.martial_art);
    setInputValue(prefix + '_martial_art_graduation', payload.martial_art_graduation);
    setInputValue(prefix + '_jiu_jitsu_belt', payload.jiu_jitsu_belt);
    setInputValue(prefix + '_jiu_jitsu_stripes', payload.jiu_jitsu_stripes);
  }

  function persistStepDependentData(step) {
    var context = getDependentContext(step);
    if (!context) {
      syncExtraDependentsPayload();
      return;
    }
    trimExtraDependentsToCount(getDependentCount());
    extraDependents[context.extraIndex] = readPrimaryDependentData(context.prefix);
    syncExtraDependentsPayload();
  }

  function hydrateStepDependentData(step) {
    var context = getDependentContext(step);
    if (!context) {
      return;
    }
    trimExtraDependentsToCount(getDependentCount());
    var storedData = extraDependents[context.extraIndex] || buildEmptyDependentData();
    writePrimaryDependentData(context.prefix, storedData);
    syncKinshipOtherFields();
    syncMartialFields();
  }

  function syncExtraDependentsPayload() {
    if (!extraDependentsPayloadInput) {
      return;
    }
    extraDependentsPayloadInput.value = JSON.stringify(extraDependents);
  }

  // ============================================================================
  // Navigation
  // ============================================================================
  function goToStep(index) {
    if (index < 0 || index >= activeSteps.length) return;
    persistStepDependentData(activeSteps[currentStepIndex]);
    currentStepIndex = index;
    updateUI();
    scrollToTop();
  }

  async function nextStep() {
    if (isAdvancing) {
      return;
    }
    if (!validateCurrentStep()) {
      return;
    }
    isAdvancing = true;
    if (nextButton) {
      nextButton.disabled = true;
    }
    var serverValidationPassed = await validateCurrentStepOnServer();
    isAdvancing = false;
    if (nextButton) {
      nextButton.disabled = false;
    }
    if (!serverValidationPassed) {
      return;
    }
    
    if (currentStepIndex < activeSteps.length - 1) {
      goToStep(currentStepIndex + 1);
      saveDraft();
    }
  }

  function prevStep() {
    if (currentStepIndex > 0) {
      goToStep(currentStepIndex - 1);
    }
  }

  function scrollToTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // ============================================================================
  // Validation
  // ============================================================================
  function isFieldVisible(field) {
    if (!field) return false;
    return !field.hidden && !field.disabled && !field.closest('[hidden], .is-hidden');
  }

  function clearFieldValidation(field) {
    if (!field) return;
    field.removeAttribute('aria-invalid');
    if (typeof field.setCustomValidity === 'function') {
      field.setCustomValidity('');
    }
  }

  function markInvalid(field, message) {
    if (!field) return false;
    field.setAttribute('aria-invalid', 'true');
    if (typeof field.setCustomValidity === 'function') {
      field.setCustomValidity(message);
      field.reportValidity();
    }
    field.focus();
    return false;
  }

  function resolveFieldLabel(field) {
    if (!field) {
      return 'Campo';
    }
    var wrapperLabel = field.closest('label');
    if (wrapperLabel) {
      var caption = wrapperLabel.querySelector('span');
      if (caption && caption.textContent) {
        return caption.textContent.trim();
      }
    }
    if (field.name) {
      return field.name.replace(/_/g, ' ').trim();
    }
    return 'Campo';
  }

  function validateRequiredField(fieldName) {
    var field = form.querySelector('[name="' + fieldName + '"]');
    if (!field || !isFieldVisible(field)) return true;
    clearFieldValidation(field);
    var value = field.value ? field.value.trim() : '';
    if (!value) {
      return markInvalid(field, 'O campo "' + resolveFieldLabel(field) + '" é obrigatório.');
    }
    if (typeof field.checkValidity === 'function' && !field.checkValidity()) {
      return markInvalid(field, field.validationMessage || 'Valor inválido.');
    }
    return true;
  }

  function validatePasswordPair(passwordName, confirmName, label) {
    var passwordField = form.querySelector('[name="' + passwordName + '"]');
    var confirmField = form.querySelector('[name="' + confirmName + '"]');
    if (!passwordField || !confirmField) return true;
    if (!isFieldVisible(passwordField) || !isFieldVisible(confirmField)) return true;
    clearFieldValidation(confirmField);
    if ((passwordField.value || '') !== (confirmField.value || '')) {
      return markInvalid(confirmField, 'As senhas de ' + label + ' não coincidem.');
    }
    return true;
  }

  function validateKinshipOtherField(typeName, otherName) {
    var typeField = form.querySelector('[name="' + typeName + '"]');
    var otherField = form.querySelector('[name="' + otherName + '"]');
    if (!typeField || !otherField) return true;
    if (!isFieldVisible(typeField) || !isFieldVisible(otherField)) return true;
    clearFieldValidation(otherField);
    if (typeField.value === 'other' && !(otherField.value || '').trim()) {
      return markInvalid(otherField, 'Informe o grau de parentesco.');
    }
    return true;
  }

  function validateTypeStep() {
    var profile = getSelectedProfile();
    if (profile !== 'other') return true;
    return validateRequiredField('other_type_code');
  }

  function validateSingleClassField(fieldName) {
    var selectField = form.querySelector('select[name="' + fieldName + '"]');
    if (!selectField || !isFieldVisible(selectField)) return true;
    clearFieldValidation(selectField);
    var hasSelectedOption = Array.from(selectField.selectedOptions || []).some(function (option) {
      return Boolean(option.value);
    });
    if (!hasSelectedOption) {
      return markInvalid(selectField, 'Selecione ao menos uma turma em "' + resolveFieldLabel(selectField) + '".');
    }
    return true;
  }

  function validateStep(index) {
    var step = activeSteps[index];
    if (!step) return true;

    if (step.key === 'type') {
      return validateTypeStep();
    }

    for (var i = 0; i < step.requiredFields.length; i++) {
      if (!validateRequiredField(step.requiredFields[i])) {
        return false;
      }
    }

    if (step.key === 'holder' || step.key === 'holder_titular') {
      return validatePasswordPair('holder_password', 'holder_password_confirm', 'aluno titular');
    }
    if (step.key === 'guardian') {
      return validatePasswordPair('guardian_password', 'guardian_password_confirm', 'responsável');
    }
    if (step.key === 'dependent') {
      if (!validatePasswordPair('dependent_password', 'dependent_password_confirm', 'dependente')) {
        return false;
      }
      return validateKinshipOtherField('dependent_kinship_type', 'dependent_kinship_other_label');
    }
    if (step.key === 'student') {
      if (!validatePasswordPair('student_password', 'student_password_confirm', 'dependente')) {
        return false;
      }
      return validateKinshipOtherField('student_kinship_type', 'student_kinship_other_label');
    }
    if (step.key === 'other') {
      return validatePasswordPair('other_password', 'other_password_confirm', 'cadastro');
    }
    if (step.key === 'holder_classes') {
      return validateSingleClassField('holder_class_groups');
    }
    if (step.key === 'dependent_classes') {
      return validateSingleClassField('dependent_class_groups');
    }
    if (step.key === 'student_classes') {
      return validateSingleClassField('student_class_groups');
    }

    return true;
  }

  function validateAllStepsUpTo(targetIndex) {
    for (var i = 0; i <= targetIndex; i++) {
      if (!validateStep(i)) {
        goToStep(i);
        return false;
      }
    }
    return true;
  }

  function validateCurrentStep() {
    return validateStep(currentStepIndex);
  }

  async function validateCurrentStepOnServer() {
    if (!stepValidateUrl) {
      return true;
    }
    var step = activeSteps[currentStepIndex];
    if (!step) {
      return true;
    }
    persistStepDependentData(step);
    syncCheckoutHiddenFields();
    var payload = new FormData(form);
    payload.set('step_key', step.key);
    try {
      var response = await fetch(stepValidateUrl, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken },
        body: payload,
        credentials: 'same-origin'
      });
      if (!response.ok) {
        return true;
      }
      var data = await response.json();
      if (data.valid) {
        return true;
      }
      return applyServerStepErrors(data.errors || {});
    } catch (error) {
      console.warn('Falha ao validar etapa no servidor:', error);
      return true;
    }
  }

  function applyServerStepErrors(errors) {
    var names = Object.keys(errors);
    if (names.length === 0) {
      return true;
    }
    var firstName = names[0];
    var field = form.querySelector('[name="' + firstName + '"]');
    var message = errors[firstName];
    if (field) {
      return markInvalid(field, message);
    }
    alert(message);
    return false;
  }

  // ============================================================================
  // Draft System
  // ============================================================================
  function hasAnyFieldFilled() {
    var fields = form.querySelectorAll('input[name], select[name], textarea[name]');
    for (var i = 0; i < fields.length; i++) {
      var field = fields[i];
      if (isSensitiveField(field.name)) continue;
      if (field.name === 'csrfmiddlewaretoken') continue;
      if (field.type === 'radio' && !field.checked) continue;
      if (field.type === 'checkbox' && !field.checked) continue;
      if (field.value && field.value.trim() !== '') return true;
    }
    return false;
  }

  function isSensitiveField(fieldName) {
    return /password/i.test(fieldName) || 
           /(blood_type|allergies|injuries|emergency_contact)/i.test(fieldName);
  }

  function updateDraftNoteVisibility() {
    if (!draftNote) return;
    var shouldShow = hasAnyFieldFilled();
    draftNote.classList.toggle('is-hidden', !shouldShow);
  }

  function saveDraft() {
    if (draftSaveTimeout) {
      clearTimeout(draftSaveTimeout);
    }
    
    draftSaveTimeout = setTimeout(function () {
      var fields = collectDraftFields();
      try {
        localStorage.setItem(DRAFT_KEY, JSON.stringify({
          savedAt: Date.now(),
          fields: fields,
          currentStep: currentStepIndex,
          extraDependents: extraDependents
        }));
        updateDraftNoteVisibility();
      } catch (e) {
        console.warn('Failed to save draft:', e);
      }
    }, 500);
  }

  function collectDraftFields() {
    var values = {};
    form.querySelectorAll('input[name], select[name], textarea[name]').forEach(function (field) {
      if (isSensitiveField(field.name) || field.name === 'csrfmiddlewaretoken') return;
      
      if (field.type === 'radio') {
        if (field.checked) values[field.name] = field.value;
      } else if (field.type === 'checkbox') {
        if (field.name === 'include_dependent') {
          values[field.name] = field.checked;
        } else if (field.checked) {
          if (!Array.isArray(values[field.name])) values[field.name] = [];
          values[field.name].push(field.value);
        }
      } else {
        values[field.name] = field.value;
      }
    });
    return values;
  }

  function restoreDraft() {
    try {
      var raw = localStorage.getItem(DRAFT_KEY);
      if (!raw) return;
      
      var draft = JSON.parse(raw);
      if (!draft || Date.now() - draft.savedAt > DRAFT_TTL_MS) {
        localStorage.removeItem(DRAFT_KEY);
        return;
      }
      
      // Restore fields
      Object.keys(draft.fields).forEach(function (name) {
        var value = draft.fields[name];
        var field = form.querySelector('[name="' + name + '"]');
        
        if (!field) return;
        
        if (field.type === 'radio') {
          var radio = form.querySelector('[name="' + name + '"][value="' + value + '"]');
          if (radio) radio.checked = true;
        } else if (field.type === 'checkbox') {
          if (name === 'include_dependent') {
            field.checked = Boolean(value);
          } else if (Array.isArray(value)) {
            value.forEach(function (val) {
              var checkbox = form.querySelector('[name="' + name + '"][value="' + val + '"]');
              if (checkbox) checkbox.checked = true;
            });
          }
        } else {
          field.value = value;
        }
      });
      
      // Restore extra dependents
      if (Array.isArray(draft.extraDependents)) {
        extraDependents = draft.extraDependents;
      }
      
      // Restore step
      activeSteps = computeActiveSteps();
      syncExtraDependentsPayload();
      currentStepIndex = Math.min(draft.currentStep || 0, activeSteps.length - 1);
      
      updateUI();
      updateDraftNoteVisibility();
      
      if (draftLabel) {
        draftLabel.textContent = 'Rascunho recuperado';
      }
    } catch (e) {
      console.warn('Failed to restore draft:', e);
    }
  }

  function discardDraft() {
    // Clear localStorage
    try {
      localStorage.removeItem(DRAFT_KEY);
    } catch (e) {
      console.warn('Failed to clear draft:', e);
    }
    
    // Reset form
    form.reset();
    
    // Clear extra dependents
    extraDependents = [];
    dependentSequence = 0;
    syncExtraDependentsPayload();
    
    // Reset to first step
    currentStepIndex = 0;
    activeSteps = computeActiveSteps();
    
    // Clear all aria-invalid
    form.querySelectorAll('[aria-invalid]').forEach(function (el) {
      el.removeAttribute('aria-invalid');
    });
    form.querySelectorAll('input, select, textarea').forEach(function (field) {
      clearFieldValidation(field);
    });
    clearServerFeedback();
    
    // Update UI
    updateUI();
    updateDraftNoteVisibility();
    scrollToTop();
  }

  function clearCompletedRegistrationState() {
    try {
      if (window.sessionStorage.getItem(REGISTRATION_COMPLETED_KEY) !== '1') {
        return false;
      }
      window.sessionStorage.removeItem(REGISTRATION_COMPLETED_KEY);
      localStorage.removeItem(DRAFT_KEY);
      form.reset();
      extraDependents = [];
      dependentSequence = 0;
      currentStepIndex = 0;
      syncExtraDependentsPayload();
      activeSteps = computeActiveSteps();
      clearServerFeedback();
      updateUI();
      updateDraftNoteVisibility();
      return true;
    } catch (_error) {
      return false;
    }
  }

  function clearServerFeedback() {
    var serverErrors = form.querySelector('[data-server-errors]');
    if (serverErrors) {
      serverErrors.remove();
    }
    var statusStack = form.querySelector('[data-server-status]');
    if (statusStack) {
      statusStack.remove();
    }
  }

  // ============================================================================
  // Event Listeners
  // ============================================================================
  profileInputs.forEach(function (input) {
    input.addEventListener('change', function () {
      activeSteps = computeActiveSteps();
      currentStepIndex = 0;
      updateUI();
      saveDraft();
    });
  });

  profileChoiceCards.forEach(function (card) {
    card.addEventListener('click', function () {
      var input = card.querySelector('input[name="registration_profile"]');
      if (!input || input.checked) return;
      input.checked = true;
      input.dispatchEvent(new Event('change', { bubbles: true }));
    });
  });

  if (dependentToggle) {
    dependentToggle.addEventListener('change', function () {
      activeSteps = computeActiveSteps();
      currentStepIndex = Math.min(currentStepIndex, activeSteps.length - 1);
      updateUI();
      saveDraft();
    });
  }

  if (dependentCountSelect) {
    dependentCountSelect.addEventListener('change', function () {
      activeSteps = computeActiveSteps();
      currentStepIndex = Math.min(currentStepIndex, activeSteps.length - 1);
      updateUI();
      saveDraft();
    });
  }

  kinshipSelects.forEach(function (selectField) {
    selectField.addEventListener('change', function () {
      updateKinshipOtherField(selectField);
      saveDraft();
    });
  });

  martialArtPresenceSelects.forEach(function (selectField) {
    selectField.addEventListener('change', function () {
      updateMartialFields(selectField.dataset.martialPrefix || '');
      saveDraft();
    });
  });

  martialArtSelects.forEach(function (selectField) {
    selectField.addEventListener('change', function () {
      updateMartialFields(selectField.dataset.martialPrefix || '');
      saveDraft();
    });
  });

  checkoutActionButtons.forEach(function (button) {
    button.addEventListener('click', function () {
      if (button.disabled) return;
      setCheckoutAction(button.dataset.checkoutAction || 'pay_later');
      var currentStep = activeSteps[currentStepIndex];
      if (!currentStep || currentStep.key !== 'summary') return;
      if (typeof form.requestSubmit === 'function') {
        form.requestSubmit(submitButton || undefined);
      } else {
        form.submit();
      }
    });
  });

  if (backButton) {
    backButton.addEventListener('click', prevStep);
  }

  if (nextButton) {
    nextButton.addEventListener('click', nextStep);
  }

  form.addEventListener('submit', function (event) {
    persistStepDependentData(activeSteps[currentStepIndex]);
    if (!validateAllStepsUpTo(activeSteps.length - 1)) {
      event.preventDefault();
    }
  });

  if (discardButton) {
    discardButton.addEventListener('click', function (e) {
      e.preventDefault();
      if (confirm('Descartar todos os dados e começar novamente?')) {
        discardDraft();
      }
    });
  }

  // Auto-save on input
  form.addEventListener('input', function () {
    clearServerFeedback();
    saveDraft();
  });
  
  form.addEventListener('change', function () {
    clearServerFeedback();
    saveDraft();
  });

  function applyDateMask(value) {
    var digits = String(value || '').replace(/\D/g, '').slice(0, 8);
    if (digits.length <= 2) return digits;
    if (digits.length <= 4) return digits.slice(0, 2) + '/' + digits.slice(2);
    return digits.slice(0, 2) + '/' + digits.slice(2, 4) + '/' + digits.slice(4);
  }

  dateInputs.forEach(function (input) {
    input.addEventListener('input', function () {
      input.value = applyDateMask(input.value);
    });
    input.addEventListener('change', function () {
      input.value = applyDateMask(input.value);
    });
    input.addEventListener('blur', function () {
      input.value = applyDateMask(input.value);
    });
  });

  // ============================================================================
  // Class selection
  // ============================================================================
  function renderClassGroupCards(prefix) {
    var selectField = form.querySelector('select[name="' + prefix + '_class_groups"]');
    var container = form.querySelector('[data-class-card-list="' + prefix + '"]');
    var help = form.querySelector('[data-class-help="' + prefix + '"]');
    var selectLabel = form.querySelector('[data-class-select-label="' + prefix + '"]');
    if (!selectField || !container) {
      return;
    }
    if (selectLabel) {
      var shouldHideLabel = shouldHideClassSelectionLabel(prefix);
      selectLabel.hidden = shouldHideLabel;
      selectLabel.classList.toggle('is-hidden', shouldHideLabel);
    }

    selectField.classList.add('enhanced-class-select');
    selectField.setAttribute('aria-hidden', 'true');
    selectField.tabIndex = -1;
    var allowedOptions = getAllowedClassOptions(prefix);
    syncAllowedClassOptions(selectField, allowedOptions);
    syncAllowedClassSelection(prefix, allowedOptions, selectField);
    container.innerHTML = '';

    if (allowedOptions.length === 0) {
      container.textContent = 'Informe data de nascimento e sexo biológico para liberar as turmas compatíveis.';
      if (help) {
        help.textContent = '';
      }
      return;
    }

    allowedOptions.forEach(function (option) {
      container.appendChild(buildClassCard(prefix, option, selectField, allowedOptions.length));
    });
    updateClassHelp(prefix, help);
  }

  function syncAllowedClassOptions(selectField, allowedOptions) {
    var allowedValues = new Set(allowedOptions.map(function (option) {
      return String(option.id);
    }));
    Array.from(selectField.options).forEach(function (option) {
      var isAllowed = allowedValues.has(String(option.value));
      option.disabled = !isAllowed;
      option.hidden = !isAllowed;
    });
  }

  function buildClassCard(prefix, option, selectField, optionCount) {
    var selectedValues = new Set(getSelectMultipleValues(prefix + '_class_groups').map(String));
    var isSelected = selectedValues.has(String(option.id));
    var teacherLines = buildTeacherLines(option.teacher_label);
    var compactSections = getCompactScheduleSections(option, teacherLines);
    var scheduleCount = countCompactScheduleEntries(compactSections);

    var article = document.createElement('article');
    article.className = 'record-card record-card-catalog class-option-card--record';
    article.classList.toggle('is-selected', isSelected);
    article.dataset.classOption = String(option.id);

    var head = document.createElement('div');
    head.className = 'record-card-head';

    var headInfo = document.createElement('div');
    var nameSpan = document.createElement('span');
    nameSpan.className = 'record-card-name';
    nameSpan.textContent = buildClassCardTitle(prefix, option, optionCount);
    var subtitle = document.createElement('div');
    subtitle.className = 'record-card-subtitle';
    subtitle.textContent = buildClassCardSubtitle(teacherLines.length, scheduleCount);
    headInfo.appendChild(nameSpan);
    headInfo.appendChild(subtitle);

    var badge = document.createElement('button');
    badge.type = 'button';
    badge.className = 'record-card-badge record-card-badge--toggle';
    badge.textContent = isSelected ? 'Selecionada' : 'Selecionar';
    badge.addEventListener('click', function (e) {
      e.stopPropagation();
      toggleClassSelection(selectField, option.id);
      renderClassGroupCards(prefix);
      renderPlanList();
      renderSummary();
      saveDraft();
    });

    head.appendChild(headInfo);
    head.appendChild(badge);

    var details = document.createElement('details');
    details.className = 'catalog-dropdown class-schedule-dropdown';
    details.open = isSelected;
    var summary = document.createElement('summary');
    summary.className = 'catalog-dropdown-summary';
    summary.textContent = 'Ver horários da semana';
    details.appendChild(summary);

    var content = document.createElement('div');
    content.className = 'catalog-dropdown-content class-schedule-dropdown-content';
    content.appendChild(buildCompactScheduleOverview(compactSections));

    details.appendChild(content);
    article.appendChild(head);
    article.appendChild(details);
    return article;
  }

  function buildCompactScheduleOverview(sections) {
    var overview = document.createElement('div');
    overview.className = 'class-schedule-overview';

    if (sections.length === 0) {
      var emptySchedule = document.createElement('p');
      emptySchedule.className = 'class-schedule-empty';
      emptySchedule.textContent = 'Sem horários ativos.';
      overview.appendChild(emptySchedule);
      return overview;
    }

    sections.forEach(function (section) {
      var dayCard = document.createElement('section');
      dayCard.className = 'class-schedule-day';

      var title = document.createElement('h3');
      title.className = 'class-schedule-day-title';
      title.textContent = section.weekdayLabel;

      var rows = document.createElement('ul');
      rows.className = 'class-schedule-simple-list';
      section.entries.forEach(function (entry) {
        var row = document.createElement('li');
        row.className = 'class-schedule-simple-item';
        row.textContent = buildCompactScheduleLine(entry);
        rows.appendChild(row);
      });

      dayCard.appendChild(title);
      dayCard.appendChild(rows);
      overview.appendChild(dayCard);
    });

    return overview;
  }

  function buildScheduleFirstSections(option, teacherLines, weekdaySections) {
    var grouped = {};

    function addEntry(weekdayLabel, timeLabel, teacherLabel) {
      var normalizedWeekday = normalizeWeekdayLabel(weekdayLabel || 'Outro dia');
      var normalizedTime = String(timeLabel || '').trim();
      var normalizedTeacher = String(teacherLabel || '').trim() || 'Equipe docente não definida';
      if (!normalizedTime) {
        return;
      }
      if (!grouped[normalizedWeekday]) {
        grouped[normalizedWeekday] = {
          weekdayLabel: normalizedWeekday,
          entries: [],
          seen: {}
        };
      }
      var key = normalizedTime + '::' + normalizedTeacher;
      if (grouped[normalizedWeekday].seen[key]) {
        return;
      }
      grouped[normalizedWeekday].seen[key] = true;
      grouped[normalizedWeekday].entries.push({
        timeLabel: normalizedTime,
        teacherLabel: normalizedTeacher
      });
    }

    var physicalGroups = option.physical_groups || [];
    if (physicalGroups.length > 0) {
      physicalGroups.forEach(function (pg) {
        var professorLabel = buildPhysicalGroupProfessorLabel(pg, teacherLines);
        var daySummary = pg.schedule_day_summary || [];
        daySummary.forEach(function (section) {
          (section.time_labels || []).forEach(function (timeLabel) {
            addEntry(section.weekday_label, timeLabel, professorLabel);
          });
        });
      });
    } else {
      var fallbackTeacherLabel = teacherLines.join(', ');
      weekdaySections.forEach(function (section) {
        section.times.forEach(function (timeLabel) {
          addEntry(section.weekdayLabel, timeLabel, fallbackTeacherLabel);
        });
      });
    }

    return Object.keys(grouped)
      .sort(function (a, b) {
        var orderA = getWeekdaySortValue(a);
        var orderB = getWeekdaySortValue(b);
        if (orderA !== orderB) {
          return orderA - orderB;
        }
        return a.localeCompare(b);
      })
      .map(function (weekdayLabel) {
        var section = grouped[weekdayLabel];
        section.entries.sort(function (a, b) {
          return String(a.timeLabel).localeCompare(String(b.timeLabel));
        });
        delete section.seen;
        return section;
      });
  }

  function buildPhysicalGroupProfessorLabel(pg, fallbackTeacherLines) {
    var team = pg.teaching_team || [];
    var names = [];
    team.forEach(function (member) {
      var name = String(member.full_name || '').trim();
      if (name && names.indexOf(name) === -1) {
        names.push(name);
      }
    });
    if (names.length > 0) {
      return names.join(', ');
    }
    return fallbackTeacherLines.join(', ') || 'Equipe docente não definida';
  }

  function buildTeacherLines(rawTeacherLabel) {
    if (!rawTeacherLabel) {
      return ['Equipe docente não definida'];
    }
    var uniqueNames = [];
    rawTeacherLabel.split(',').forEach(function (name) {
      var trimmed = (name || '').trim();
      if (trimmed && uniqueNames.indexOf(trimmed) === -1) {
        uniqueNames.push(trimmed);
      }
    });
    return uniqueNames.length > 0 ? uniqueNames : ['Equipe docente não definida'];
  }

  function buildClassCardTitle(prefix, option, optionCount) {
    if (isSoloHolderFlow(prefix) && optionCount === 1) {
      return 'Treinos disponíveis';
    }
    return option.category_name + ' · ' + option.display_name;
  }

  function buildClassCardSubtitle(teacherCount, scheduleCount) {
    if (!scheduleCount) {
      return 'Sem horários ativos';
    }
    var parts = [scheduleCount + ' hor\u00e1rio' + (scheduleCount > 1 ? 's' : '') + ' na semana'];
    if (teacherCount > 0) {
      parts.push(teacherCount + ' professor' + (teacherCount > 1 ? 'es' : ''));
    }
    return parts.join(' \u00b7 ');
  }

  function getCompactScheduleSections(option, teacherLines) {
    if (Array.isArray(option.compact_schedule_sections) && option.compact_schedule_sections.length > 0) {
      return option.compact_schedule_sections.map(function (section) {
        return {
          weekdayLabel: section.weekday_label || '',
          entries: Array.isArray(section.entries) ? section.entries.map(function (entry) {
            return {
              timeLabel: entry.time_label || '',
              teacherLabel: entry.teacher_label || '',
              lineLabel: entry.line_label || ''
            };
          }) : []
        };
      });
    }
    return buildScheduleFirstSections(option, teacherLines, buildClassScheduleSections(option));
  }

  function buildCompactScheduleLine(entry) {
    if (entry.lineLabel) {
      return entry.lineLabel;
    }
    return (entry.timeLabel || '') + ' - ' + (entry.teacherLabel || 'Equipe docente não definida');
  }

  function buildClassScheduleSections(option) {
    if (!option.schedules || option.schedules.length === 0) {
      return [];
    }
    var weekdayOrder = {
      'Segunda-feira': 1,
      'Terça-feira': 2,
      'Quarta-feira': 3,
      'Quinta-feira': 4,
      'Sexta-feira': 5,
      'Sábado': 6,
      'Domingo': 7
    };
    var grouped = {};
    option.schedules.forEach(function (schedule) {
      var weekdayLabel = normalizeWeekdayLabel(schedule.weekday_display || 'Outro dia');
      if (!grouped[weekdayLabel]) {
        grouped[weekdayLabel] = [];
      }
      grouped[weekdayLabel].push(schedule.start_time || '');
    });
    return Object.keys(grouped)
      .sort(function (a, b) {
        var orderA = weekdayOrder[a] || 99;
        var orderB = weekdayOrder[b] || 99;
        return orderA - orderB;
      })
      .map(function (weekdayLabel) {
        var times = grouped[weekdayLabel].slice().sort(function (a, b) {
          return String(a).localeCompare(String(b));
        });
        return {
          weekdayLabel: weekdayLabel,
          times: times
        };
      });
  }

  function normalizeWeekdayLabel(weekdayDisplay) {
    var value = String(weekdayDisplay || '').toLowerCase();
    var map = {
      'segunda-feira': 'Segunda-feira',
      'terça-feira': 'Terça-feira',
      'terca-feira': 'Terça-feira',
      'quarta-feira': 'Quarta-feira',
      'quinta-feira': 'Quinta-feira',
      'sexta-feira': 'Sexta-feira',
      'sábado': 'Sábado',
      'sabado': 'Sábado',
      'domingo': 'Domingo'
    };
    return map[value] || weekdayDisplay;
  }

  function getWeekdaySortValue(weekdayDisplay) {
    var normalized = normalizeWeekdayLabel(weekdayDisplay);
    var weekdayOrder = {
      'Segunda-feira': 1,
      'Terça-feira': 2,
      'Quarta-feira': 3,
      'Quinta-feira': 4,
      'Sexta-feira': 5,
      'Sábado': 6,
      'Domingo': 7
    };
    return weekdayOrder[normalized] || 99;
  }

  function countCompactScheduleEntries(sections) {
    return sections.reduce(function (total, section) {
      return total + ((section.entries || []).length);
    }, 0);
  }

  function shouldHideClassSelectionLabel(prefix) {
    if (prefix !== 'holder') {
      return false;
    }
    return isSoloHolderFlow(prefix);
  }

  function isSoloHolderFlow(prefix) {
    return prefix === 'holder' && getSelectedProfile() === 'holder' && !(dependentToggle && dependentToggle.checked);
  }

  function getAllowedClassOptions(prefix) {
    var allowedAudiences = getAllowedClassAudiences(prefix);
    return registrationCatalog.filter(function (option) {
      return allowedAudiences.indexOf(option.category_audience) !== -1;
    });
  }

  function getAllowedClassAudiences(prefix) {
    var audience = resolveAudienceForPrefix(prefix);
    var biologicalSex = getInputValue(prefix + '_biological_sex');
    if (audience === 'adult') {
      return biologicalSex === 'female' ? ['adult', 'women'] : ['adult'];
    }
    if (audience === 'kids' || audience === 'juvenile') {
      return ['kids', 'juvenile'];
    }
    return [];
  }

  function getDefaultClassAudiences(prefix) {
    var audience = resolveAudienceForPrefix(prefix);
    if (audience === 'adult') {
      return ['adult'];
    }
    if (audience === 'kids' || audience === 'juvenile') {
      return [audience];
    }
    return [];
  }

  function syncAllowedClassSelection(prefix, allowedOptions, selectField) {
    var allowedValues = new Set(allowedOptions.map(function (option) {
      return String(option.id);
    }));
    var currentValues = getSelectMultipleValues(prefix + '_class_groups').filter(function (value) {
      return allowedValues.has(String(value));
    });
    if (currentValues.length === 0) {
      var defaults = getDefaultClassAudiences(prefix);
      allowedOptions.forEach(function (option) {
        if (currentValues.length === 0 && defaults.indexOf(option.category_audience) !== -1) {
          currentValues.push(String(option.id));
        }
      });
    }
    setSelectMultipleValues(selectField.name, currentValues);
    syncExtraDependentsPayload();
  }

  function toggleClassSelection(selectField, value) {
    var selectedValues = new Set(getSelectMultipleValues(selectField.name).map(String));
    var normalized = String(value);
    if (selectedValues.has(normalized)) {
      selectedValues.delete(normalized);
    } else {
      selectedValues.add(normalized);
    }
    setSelectMultipleValues(selectField.name, Array.from(selectedValues));
  }

  function updateClassHelp(prefix, help) {
    if (!help) {
      return;
    }
    var selectedAudiences = getSelectedAudiences(prefix + '_class_groups');
    var audience = resolveAudienceForPrefix(prefix);
    var biologicalSex = getInputValue(prefix + '_biological_sex');
    if (audience === 'adult' && biologicalSex === 'female') {
      help.textContent = 'A turma feminina é opcional e começa sem custo adicional; ela poderá ser cobrada futuramente.';
      return;
    }
    if (audience === 'adult') {
      help.textContent = 'Você pode treinar em todos os horários disponíveis da turma adulto.';
      return;
    }
    if (selectedAudiences.indexOf('kids') !== -1 && selectedAudiences.indexOf('juvenile') !== -1) {
      help.textContent = 'Kids e Juvenil selecionadas: o plano será cobrado em valor dobrado.';
      return;
    }
    help.textContent = 'A turma ideal foi selecionada pela idade. Você pode trocar para Kids, Juvenil ou marcar as duas.';
  }

  function resolveAudienceForPrefix(prefix) {
    var birthDate = parsePtDate(getInputValue(prefix + '_birthdate'));
    if (!birthDate) {
      return '';
    }
    var age = calculateAge(birthDate);
    for (var i = 0; i < ibjjfAgeCategories.length; i++) {
      var category = ibjjfAgeCategories[i];
      var minAge = Number(category.minimum_age);
      var maxAge = category.maximum_age === null ? null : Number(category.maximum_age);
      if (age >= minAge && (maxAge === null || age <= maxAge)) {
        return category.audience;
      }
    }
    return '';
  }

  function parsePtDate(value) {
    var match = /^(\d{2})\/(\d{2})\/(\d{4})$/.exec(value || '');
    if (!match) {
      return null;
    }
    var date = new Date(Number(match[3]), Number(match[2]) - 1, Number(match[1]));
    if (date.getFullYear() !== Number(match[3]) || date.getMonth() !== Number(match[2]) - 1 || date.getDate() !== Number(match[1])) {
      return null;
    }
    return date;
  }

  function calculateAge(birthDate) {
    var today = new Date();
    var age = today.getFullYear() - birthDate.getFullYear();
    var hadBirthday = today.getMonth() > birthDate.getMonth() ||
      (today.getMonth() === birthDate.getMonth() && today.getDate() >= birthDate.getDate());
    return hadBirthday ? age : age - 1;
  }

  function getSelectedAudiences(fieldName) {
    return getSelectMultipleValues(fieldName).map(function (value) {
      var option = findClassCatalogOption(value);
      return option ? option.category_audience : '';
    }).filter(Boolean);
  }

  function findClassCatalogOption(value) {
    var normalized = String(value);
    return registrationCatalog.find(function (option) {
      return String(option.id) === normalized || String(option.code) === normalized;
    });
  }

  function getEnrollmentMultiplier() {
    return 1;
  }

  function classifyPlanAudience(rawAudience) {
    if (rawAudience === 'kids' || rawAudience === 'juvenile') {
      return 'kids_juvenile';
    }
    if (rawAudience === 'adult' || rawAudience === 'women') {
      return 'adult';
    }
    return '';
  }

  function classifyPersonAudience(prefix) {
    var classAudiences = getSelectedAudiences(prefix + '_class_groups');
    for (var i = 0; i < classAudiences.length; i++) {
      var mapped = classifyPlanAudience(classAudiences[i]);
      if (mapped === 'adult') {
        return 'adult';
      }
    }
    for (var j = 0; j < classAudiences.length; j++) {
      var mappedKids = classifyPlanAudience(classAudiences[j]);
      if (mappedKids === 'kids_juvenile') {
        return 'kids_juvenile';
      }
    }
    var ageAudience = resolveAudienceForPrefix(prefix);
    return classifyPlanAudience(ageAudience);
  }

  function classifyExtraDependentAudience(dependent) {
    var rawGroups = dependent.class_groups || [];
    var classAudiences = rawGroups.map(function (value) {
      var option = findClassCatalogOption(value);
      return option ? option.category_audience : '';
    }).filter(Boolean);
    for (var i = 0; i < classAudiences.length; i++) {
      var mapped = classifyPlanAudience(classAudiences[i]);
      if (mapped === 'adult') {
        return 'adult';
      }
    }
    for (var j = 0; j < classAudiences.length; j++) {
      var mappedKids = classifyPlanAudience(classAudiences[j]);
      if (mappedKids === 'kids_juvenile') {
        return 'kids_juvenile';
      }
    }
    if (!dependent.birth_date) {
      return '';
    }
    var birthDate = parsePtDate(dependent.birth_date);
    if (!birthDate) {
      return '';
    }
    var age = calculateAge(birthDate);
    return age < 18 ? 'kids_juvenile' : 'adult';
  }

  function getEligibilityContext() {
    var profile = getSelectedProfile();
    var adultActive = false;
    var kidsJuvenileCount = 0;

    function tally(audience) {
      if (audience === 'adult') {
        adultActive = true;
      } else if (audience === 'kids_juvenile') {
        kidsJuvenileCount += 1;
      }
    }

    if (profile === 'holder') {
      tally(classifyPersonAudience('holder'));
      if (dependentToggle && dependentToggle.checked) {
        tally(classifyPersonAudience('dependent'));
      }
    } else if (profile === 'guardian') {
      tally(classifyPersonAudience('student'));
    }

    for (var i = 0; i < extraDependents.length; i++) {
      tally(classifyExtraDependentAudience(extraDependents[i]));
    }

    return {
      adultActive: adultActive,
      kidsJuvenileCount: kidsJuvenileCount,
      adultFamilyEligible: adultActive && (adultActive ? 1 : 0) + kidsJuvenileCount >= 2,
      kidsFamilyEligible: kidsJuvenileCount >= 2
    };
  }

  function isPlanEligibleByContext(plan, context) {
    if (plan.requires_special_authorization) {
      return false;
    }
    if (plan.audience === 'adult') {
      if (!context.adultActive) {
        return false;
      }
      return !plan.is_family_plan || context.adultFamilyEligible;
    }
    if (plan.audience === 'kids_juvenile') {
      if (context.kidsJuvenileCount < 1) {
        return false;
      }
      return !plan.is_family_plan || context.kidsFamilyEligible;
    }
    return false;
  }

  function isFamilyPlanEligible() {
    var context = getEligibilityContext();
    return context.adultFamilyEligible || context.kidsFamilyEligible;
  }

  // ============================================================================
  // Checkout: Plan & Materials
  // ============================================================================
  function formatBRL(value) {
    var num = parseFloat(value);
    if (isNaN(num)) return 'R$ 0,00';
    return 'R$ ' + num.toFixed(2).replace('.', ',').replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  }

  function normalizeCheckoutAction(value) {
    if (value === 'stripe' || value === 'pix' || value === 'pay_later') {
      return value;
    }
    return 'pay_later';
  }

  function updateCheckoutActionUI() {
    if (checkoutActionInput) {
      checkoutActionInput.value = checkoutAction;
    }
    checkoutActionButtons.forEach(function (button) {
      var isActive = button.dataset.checkoutAction === checkoutAction;
      button.classList.toggle('is-selected', isActive);
    });
    if (!checkoutActionHelp) return;
    if (checkoutTotal <= 0) {
      checkoutActionHelp.textContent = 'Nenhuma cobrança selecionada. O cadastro será concluído sem pagamento.';
      return;
    }
    if (checkoutAction === 'stripe') {
      checkoutActionHelp.textContent = 'Após concluir, você será redirecionado para o checkout de cartão.';
      return;
    }
    if (checkoutAction === 'pix') {
      checkoutActionHelp.textContent = 'Após concluir, você verá o QR Code PIX para pagamento.';
      return;
    }
    checkoutActionHelp.textContent = 'Cadastro concluído agora e pagamento adiado com 1 aula experimental liberada.';
  }

  function setCheckoutAction(action) {
    checkoutAction = normalizeCheckoutAction(action);
    updateCheckoutActionUI();
    saveDraft();
  }

  function updateCheckoutDecisionAvailability(total) {
    var hasCharge = total > 0;
    var selectedPlan = getSelectedPlan();
    checkoutActionButtons.forEach(function (button) {
      var action = button.dataset.checkoutAction || '';
      var mismatchedPlan = selectedPlan && action !== 'pay_later' && action !== getCheckoutActionForPlan(selectedPlan);
      button.disabled = (!hasCharge && action !== 'pay_later') || mismatchedPlan;
    });
    if (!hasCharge) {
      checkoutAction = 'pay_later';
    }
    updateCheckoutActionUI();
  }

  var planSelectorState = {
    audience: '',
    plan_type: '',
    weekly_frequency: null,
    billing_cycle: '',
    payment_method: ''
  };

  var CYCLE_LABELS = {
    monthly: 'Mensal',
    quarterly: 'Trimestral',
    semiannual: 'Semestral',
    annual: 'Anual'
  };

  var CYCLE_ORDER = ['monthly', 'quarterly', 'semiannual', 'annual'];

  function getPlanDimensionOptions(plans) {
    var audiences = [];
    var planTypes = [];
    var frequencies = [];
    var cycles = [];
    var methods = [];
    plans.forEach(function (plan) {
      if (audiences.indexOf(plan.audience) === -1) audiences.push(plan.audience);
      var type = plan.is_family_plan ? 'family' : 'individual';
      if (planTypes.indexOf(type) === -1) planTypes.push(type);
      var freq = Number(plan.weekly_frequency);
      if (frequencies.indexOf(freq) === -1) frequencies.push(freq);
      if (cycles.indexOf(plan.billing_cycle) === -1) cycles.push(plan.billing_cycle);
      if (methods.indexOf(plan.payment_method) === -1) methods.push(plan.payment_method);
    });
    return {
      audiences: audiences,
      plan_types: planTypes,
      weekly_frequencies: frequencies,
      billing_cycles: cycles,
      payment_methods: methods
    };
  }

  function ensurePlanSelectorDefaults(plans) {
    var dims = getPlanDimensionOptions(plans);
    if (!planSelectorState.audience || dims.audiences.indexOf(planSelectorState.audience) === -1) {
      planSelectorState.audience = dims.audiences.indexOf('adult') !== -1 ? 'adult' : (dims.audiences[0] || '');
    }
    var availableTypes = dims.plan_types.slice();
    if (!planSelectorState.plan_type || availableTypes.indexOf(planSelectorState.plan_type) === -1) {
      planSelectorState.plan_type = availableTypes.indexOf('individual') !== -1 ? 'individual' : (availableTypes[0] || '');
    }
    if (planSelectorState.weekly_frequency === null || dims.weekly_frequencies.indexOf(planSelectorState.weekly_frequency) === -1) {
      planSelectorState.weekly_frequency = dims.weekly_frequencies.indexOf(5) !== -1 ? 5 : (dims.weekly_frequencies[0] || null);
    }
    if (!planSelectorState.billing_cycle || dims.billing_cycles.indexOf(planSelectorState.billing_cycle) === -1) {
      planSelectorState.billing_cycle = dims.billing_cycles.indexOf('monthly') !== -1 ? 'monthly' : (dims.billing_cycles[0] || '');
    }
  }

  function getPlanForState(method) {
    return planCatalog.find(function (plan) {
      return plan.audience === planSelectorState.audience
        && (plan.is_family_plan ? 'family' : 'individual') === planSelectorState.plan_type
        && Number(plan.weekly_frequency) === planSelectorState.weekly_frequency
        && plan.billing_cycle === planSelectorState.billing_cycle
        && plan.payment_method === method;
    }) || null;
  }

  function renderPlanList() {
    var container = form.querySelector('[data-plan-list]');
    if (!container) return;
    container.innerHTML = '';

    if (planCatalog.length === 0) {
      container.innerHTML = '<p class="checkout-empty-note">Nenhum plano dispon\u00edvel no momento.</p>';
      return;
    }

    var visiblePlans = getVisiblePlanCatalog();
    if (visiblePlans.length === 0) {
      container.innerHTML = '<p class="checkout-empty-note">Nenhum plano dispon\u00edvel para este cadastro.</p>';
      selectedPlanId = null;
      planSelectorState.payment_method = '';
      syncCheckoutHiddenFields();
      return;
    }

    ensurePlanSelectorDefaults(visiblePlans);

    var dims = getPlanDimensionOptions(visiblePlans);

    var selector = document.createElement('div');
    selector.className = 'plan-selector';

    if (dims.audiences.length > 1) {
      selector.appendChild(buildPlanSelectorRow({
        label: 'Quem treina',
        options: dims.audiences.map(function (audience) {
          var sample = visiblePlans.find(function (p) { return p.audience === audience; });
          return {
            value: audience,
            label: sample && sample.audience_label ? sample.audience_label : (audience === 'adult' ? 'Adulto' : 'Kids/Juvenil')
          };
        }),
        currentValue: planSelectorState.audience,
        onChange: function (value) {
          planSelectorState.audience = value;
          planSelectorState.payment_method = '';
          renderPlanList();
        }
      }));
    }

    if (dims.plan_types.length > 1) {
      selector.appendChild(buildPlanSelectorRow({
        label: 'Tipo de plano',
        options: [
          { value: 'individual', label: 'Individual' },
          { value: 'family', label: 'Fam\u00edlia' }
        ].filter(function (opt) { return dims.plan_types.indexOf(opt.value) !== -1; }),
        currentValue: planSelectorState.plan_type,
        onChange: function (value) {
          planSelectorState.plan_type = value;
          planSelectorState.payment_method = '';
          renderPlanList();
        }
      }));
    }

    if (dims.weekly_frequencies.length > 1) {
      var sortedFrequencies = dims.weekly_frequencies.slice().sort(function (a, b) { return b - a; });
      selector.appendChild(buildPlanSelectorRow({
        label: 'Frequ\u00eancia',
        options: sortedFrequencies.map(function (freq) {
          return { value: freq, label: freq + 'x por semana' };
        }),
        currentValue: planSelectorState.weekly_frequency,
        onChange: function (value) {
          planSelectorState.weekly_frequency = Number(value);
          planSelectorState.payment_method = '';
          renderPlanList();
        }
      }));
    }

    selector.appendChild(buildPlanSelectorRow({
      label: 'Recorr\u00eancia',
      options: CYCLE_ORDER
        .filter(function (c) { return dims.billing_cycles.indexOf(c) !== -1; })
        .map(function (c) { return { value: c, label: CYCLE_LABELS[c] }; }),
      currentValue: planSelectorState.billing_cycle,
      onChange: function (value) {
        planSelectorState.billing_cycle = value;
        planSelectorState.payment_method = '';
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
      selectedPlanId = resolvedPlan.id;
      setCheckoutAction(getCheckoutActionForPlan(resolvedPlan));
    } else {
      selector.appendChild(buildPlanSelectorHint(pixPlan, creditPlan));
      selectedPlanId = null;
    }

    syncCheckoutHiddenFields();
    container.appendChild(selector);
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
    title.textContent = paymentMethod === 'pix' ? 'PIX' : 'Cart\u00e3o';
    info.appendChild(title);

    var subtitle = document.createElement('span');
    subtitle.className = 'plan-selector-payment-subtitle';
    subtitle.textContent = paymentMethod === 'pix' ? 'Desconto comercial' : 'Cart\u00e3o sem juros';
    info.appendChild(subtitle);

    var price = document.createElement('span');
    price.className = 'plan-selector-payment-price';
    price.textContent = formatBRL(plan.price);
    info.appendChild(price);

    if (plan.monthly_reference_price && plan.billing_cycle !== 'monthly') {
      var hint = document.createElement('span');
      hint.className = 'plan-selector-payment-hint';
      hint.textContent = formatBRL(plan.monthly_reference_price) + ' por m\u00eas';
      info.appendChild(hint);
    }

    card.appendChild(info);

    card.addEventListener('click', function () {
      planSelectorState.payment_method = paymentMethod;
      selectedPlanId = plan.id;
      setCheckoutAction(getCheckoutActionForPlan(plan));
      syncCheckoutHiddenFields();
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

    return summary;
  }

  function buildPlanSelectorHint(pixPlan, creditPlan) {
    var hint = document.createElement('p');
    hint.className = 'plan-selector-hint';
    if (!pixPlan && !creditPlan) {
      hint.textContent = 'Nenhuma combina\u00e7\u00e3o dispon\u00edvel para os filtros atuais.';
    } else {
      hint.textContent = 'Escolha PIX ou Cart\u00e3o para confirmar o plano.';
    }
    return hint;
  }

  function createPaymentIcon(paymentMethod) {
    var icon = document.createElement('span');
    icon.className = 'checkout-payment-icon checkout-payment-icon--' + paymentMethod;
    icon.setAttribute('aria-hidden', 'true');
    var isPix = paymentMethod === 'pix';
    var iconUrl = isPix ? pixIconUrl : cardIconUrl;
    if (iconUrl) {
      var image = document.createElement('img');
      image.className = 'checkout-payment-icon-image';
      image.src = iconUrl;
      image.alt = '';
      icon.appendChild(image);
    } else {
      icon.textContent = isPix ? 'PIX' : 'CARD';
    }
    return icon;
  }

  function getVisiblePlanCatalog() {
    var context = getEligibilityContext();
    return planCatalog.filter(function (plan) {
      return isPlanEligibleByContext(plan, context);
    });
  }

  function buildPlanMeta(plan) {
    var parts = [plan.cycle, plan.payment_method_label || ''];
    if (plan.monthly_reference_price && parseFloat(plan.monthly_reference_price) !== parseFloat(plan.price)) {
      parts.push(formatBRL(plan.monthly_reference_price) + ' o mês');
    }
    if (plan.installment_label) {
      parts.push(plan.installment_label);
    }
    if (plan.weekly_frequency_label) {
      parts.push(plan.weekly_frequency_label);
    }
    if (plan.audience_label) {
      parts.push(plan.audience_label);
    }
    if (plan.is_family_plan) {
      parts.push('Família');
    } else {
      parts.push('Individual');
    }
    return parts.filter(Boolean).join(' · ');
  }

  function getCheckoutActionForPlan(plan) {
    if (!plan) {
      return 'pay_later';
    }
    return plan.payment_method === 'pix' ? 'pix' : 'stripe';
  }

  function getSelectedPlan() {
    if (!selectedPlanId) {
      return null;
    }
    return planCatalog.find(function (plan) { return plan.id === selectedPlanId; }) || null;
  }

  function renderProductList() {
    var container = form.querySelector('[data-product-list]');
    if (!container) return;
    container.innerHTML = '';

    if (productCatalog.length === 0) {
      container.innerHTML = '<p class="checkout-empty-note">Nenhum material dispon\u00edvel no momento.</p>';
      return;
    }

    var groupedProducts = groupProductsForDropdown(productCatalog);
    groupedProducts.forEach(function (group) {
      container.appendChild(buildProductGroupCard(group));
    });
    container.appendChild(buildSelectedProductCartPreview());
  }

  function buildProductGroupCard(group) {
    var totalSelected = 0;
    group.products.forEach(function (product) {
      totalSelected += getSelectedProductQuantity(product.id);
    });

    var article = document.createElement('article');
    article.className = 'record-card record-card-catalog class-option-card--record';
    if (totalSelected > 0) {
      article.classList.add('is-selected');
    }

    var head = document.createElement('div');
    head.className = 'record-card-head';
    var headInfo = document.createElement('div');
    var nameSpan = document.createElement('span');
    nameSpan.className = 'record-card-name';
    nameSpan.textContent = group.title;
    var subtitle = document.createElement('div');
    subtitle.className = 'record-card-subtitle';
    subtitle.textContent = group.products.length + (group.products.length === 1 ? ' produto' : ' produtos') + (totalSelected > 0 ? ' \u00b7 ' + totalSelected + ' selecionado' + (totalSelected > 1 ? 's' : '') : '');
    headInfo.appendChild(nameSpan);
    headInfo.appendChild(subtitle);

    var badge = document.createElement('span');
    badge.className = 'record-card-badge';
    badge.textContent = group.title;

    head.appendChild(headInfo);
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
    var optionsList = document.createElement('div');
    optionsList.className = 'catalog-product-options';
    group.products.forEach(function (product) {
      optionsList.appendChild(buildProductCard(product));
    });
    content.appendChild(optionsList);
    details.appendChild(content);

    article.appendChild(head);
    article.appendChild(details);
    return article;
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
    return Object.keys(grouped)
      .sort(function (a, b) {
        var first = grouped[a];
        var second = grouped[b];
        if (first.order !== second.order) {
          return first.order - second.order;
        }
        return a.localeCompare(b);
      })
      .map(function (key) { return grouped[key]; });
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

    if (!hasAvailableProductVariants(product)) {
      var outBadge = document.createElement('span');
      outBadge.className = 'store-product-badge--out';
      outBadge.textContent = 'Esgotado';
      card.appendChild(top);
      card.appendChild(outBadge);
      return card;
    }

    var selectedSummary = document.createElement('span');
    selectedSummary.className = 'catalog-product-item-meta';
    selectedSummary.textContent = qtyInCart > 0 ? 'No carrinho: ' + qtyInCart + ' un.' : 'Nenhuma variante adicionada.';

    var config = document.createElement('div');
    config.className = 'catalog-product-config-grid';

    var variantField = document.createElement('label');
    variantField.className = 'catalog-product-config-field';
    var variantCaption = document.createElement('span');
    variantCaption.textContent = 'Opção';
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
    var minusBtn = document.createElement('button');
    minusBtn.type = 'button';
    minusBtn.className = 'catalog-product-qty-btn';
    minusBtn.textContent = '\u2212';
    var qtySpan = document.createElement('span');
    qtySpan.className = 'catalog-product-qty-value';
    var plusBtn = document.createElement('button');
    plusBtn.type = 'button';
    plusBtn.className = 'catalog-product-qty-btn';
    plusBtn.textContent = '+';
    qtyControl.appendChild(minusBtn);
    qtyControl.appendChild(qtySpan);
    qtyControl.appendChild(plusBtn);
    qtyField.appendChild(qtyCaption);
    qtyField.appendChild(qtyControl);

    var addButton = document.createElement('button');
    addButton.type = 'button';
    addButton.className = 'catalog-product-add-button';
    addButton.textContent = 'Adicionar ao carrinho';

    function getSelectedVariant() {
      return getProductVariantById(product, Number(variantSelect.value || '0'));
    }

    function syncAddState() {
      var selectedVariant = getSelectedVariant();
      var selectedQty = selectedVariant ? getSelectedVariantQuantity(selectedVariant.id) : 0;
      var remaining = selectedVariant ? Math.max(0, selectedVariant.stock_quantity - selectedQty) : 0;
      if (quantity > Math.max(remaining, 1)) {
        quantity = Math.max(1, remaining);
      }
      qtySpan.textContent = String(quantity);
      minusBtn.disabled = quantity <= 1;
      plusBtn.disabled = !selectedVariant || remaining <= quantity;
      addButton.disabled = !selectedVariant || remaining < quantity || quantity < 1;
      if (!selectedVariant) {
        addButton.textContent = 'Selecione uma opção';
        return;
      }
      addButton.textContent = remaining > 0 ? 'Adicionar ao carrinho' : 'Sem estoque disponível';
    }

    minusBtn.addEventListener('click', function () {
      quantity = Math.max(1, quantity - 1);
      syncAddState();
    });
    plusBtn.addEventListener('click', function () {
      quantity += 1;
      syncAddState();
    });
    variantSelect.addEventListener('change', syncAddState);
    addButton.addEventListener('click', function () {
      var selectedVariant = getSelectedVariant();
      if (!selectedVariant) {
        return;
      }
      addSelectedProductVariant(product, selectedVariant, quantity);
      quantity = 1;
      syncCheckoutHiddenFields();
      renderProductList();
      renderSummary();
      saveDraft();
    });

    syncAddState();

    config.appendChild(variantField);
    config.appendChild(qtyField);
    config.appendChild(addButton);

    card.appendChild(top);
    card.appendChild(selectedSummary);
    card.appendChild(config);
    return card;
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

  function buildSelectedProductCartPreview() {
    var entries = getSelectedProductEntries();
    var wrapper = document.createElement('div');
    wrapper.className = 'catalog-cart-preview';

    var title = document.createElement('h3');
    title.className = 'checkout-section-title';
    title.textContent = 'Carrinho de materiais';
    wrapper.appendChild(title);

    if (entries.length === 0) {
      var empty = document.createElement('p');
      empty.className = 'checkout-empty-note';
      empty.textContent = 'Nenhum material adicionado.';
      wrapper.appendChild(empty);
      return wrapper;
    }

    var list = document.createElement('div');
    list.className = 'catalog-cart-preview-list';
    entries.forEach(function (entry) {
      var row = document.createElement('div');
      row.className = 'catalog-cart-preview-row';

      var text = document.createElement('span');
      text.className = 'catalog-cart-preview-label';
      text.textContent = entry.displayName + ' x' + entry.quantity;

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
        syncCheckoutHiddenFields();
        renderProductList();
        renderSummary();
        saveDraft();
      });

      actions.appendChild(subtotal);
      actions.appendChild(removeButton);
      row.appendChild(text);
      row.appendChild(actions);
      list.appendChild(row);
    });
    wrapper.appendChild(list);
    return wrapper;
  }

  function renderSummary() {
    var itemsContainer = form.querySelector('[data-summary-items]');
    var totalEl = form.querySelector('[data-summary-total]');
    if (!itemsContainer || !totalEl) return;

    itemsContainer.innerHTML = '';
    var total = 0;

    if (selectedPlanId) {
      var plan = planCatalog.find(function (p) { return p.id === selectedPlanId; });
      if (plan) {
        var multiplier = getEnrollmentMultiplier();
        var planPrice = parseFloat(plan.price) * multiplier;
        total += planPrice;
        var multiplierLabel = multiplier > 1 ? ' · Kids + Juvenil em valor dobrado' : '';
        itemsContainer.innerHTML += '<div class="checkout-summary-row"><span class="checkout-summary-row-label">' + plan.name + ' (' + plan.cycle + multiplierLabel + ')</span><span class="checkout-summary-row-value">' + formatBRL(planPrice) + '</span></div>';
      }
    }

    var productEntries = getSelectedProductEntries();
    for (var i = 0; i < productEntries.length; i++) {
      var entry = productEntries[i];
      var subtotal = entry.unitPrice * entry.quantity;
      total += subtotal;
      itemsContainer.innerHTML += '<div class="checkout-summary-row"><span class="checkout-summary-row-label">' + entry.displayName + ' x' + entry.quantity + '</span><span class="checkout-summary-row-value">' + formatBRL(subtotal) + '</span></div>';
    }

    if (!selectedPlanId && productEntries.length === 0) {
      itemsContainer.innerHTML = '<p class="checkout-empty-note">Nenhum item selecionado.</p>';
    }

    checkoutTotal = total;
    totalEl.textContent = formatBRL(total);
    updateCheckoutDecisionAvailability(total);
  }

  function syncCheckoutHiddenFields() {
    var planInput = document.getElementById('selected-plan');
    if (planInput) planInput.value = selectedPlanId ? String(selectedPlanId) : '';

    var productsInput = document.getElementById('selected-products-payload');
    if (productsInput) {
      var items = [];
      getSelectedProductEntries().forEach(function (entry) {
        if (entry.quantity > 0) {
          items.push({ variant_id: entry.variantId, qty: entry.quantity });
        }
      });
      productsInput.value = JSON.stringify(items);
    }
    if (checkoutActionInput) {
      checkoutActionInput.value = checkoutAction;
    }
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

  function hydrateCheckoutStateFromHiddenFields() {
    var planInput = document.getElementById('selected-plan');
    selectedPlanId = planInput && planInput.value ? Number(planInput.value) : null;
    selectedProducts = {};

    var productsInput = document.getElementById('selected-products-payload');
    if (!productsInput || !productsInput.value) {
      return;
    }

    try {
      var items = JSON.parse(productsInput.value);
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
        selectedProducts[String(variantId)] = buildSelectedProductState(
          resolved.product,
          resolved.variant,
          quantity
        );
      });
    } catch (_error) {
      selectedProducts = {};
    }
  }

  // ============================================================================
  // Initialization
  // ============================================================================
  function init() {
    clearCompletedRegistrationState();

    // Try to restore draft first
    var canRestoreDraft = form.dataset.canRestoreDraft === 'true';
    if (canRestoreDraft) {
      restoreDraft();
    }
    checkoutAction = normalizeCheckoutAction(
      checkoutActionInput ? checkoutActionInput.value : checkoutAction
    );
    hydrateCheckoutStateFromHiddenFields();
    
    // Compute initial steps
    activeSteps = computeActiveSteps();
    
    // Initial UI update
    updateUI();
    updateCheckoutActionUI();
    updateDraftNoteVisibility();
  }

  init();

  window.addEventListener('pageshow', function (event) {
    var navigationEntry = performance.getEntriesByType('navigation')[0];
    var isBackForward =
      event.persisted || (navigationEntry && navigationEntry.type === 'back_forward');
    if (!isBackForward) return;
    clearCompletedRegistrationState();
  });
})();
