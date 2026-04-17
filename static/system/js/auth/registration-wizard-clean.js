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
        steps.push(STEP_DEFINITIONS.holder_classes);
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
    martialArtSelects.forEach(function (selectField) {
      updateMartialFields(selectField);
    });
  }

  function updateMartialFields(selectField) {
    if (!selectField) {
      return;
    }
    var prefix = selectField.dataset.martialPrefix;
    if (!prefix) {
      return;
    }
    var jiuWrappers = form.querySelectorAll('[data-jiu-jitsu-only-wrapper="' + prefix + '"]');
    var nonJiuWrappers = form.querySelectorAll('[data-non-jiu-jitsu-only-wrapper="' + prefix + '"]');
    var shouldShowJiu = selectField.value === 'jiu_jitsu';
    var shouldShowNonJiu = !!selectField.value && selectField.value !== 'jiu_jitsu';
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

  martialArtSelects.forEach(function (selectField) {
    selectField.addEventListener('change', function () {
      updateMartialFields(selectField);
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
    if (!selectField || !container) {
      return;
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
      container.appendChild(buildClassCard(prefix, option, selectField));
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

  function buildClassCard(prefix, option, selectField) {
    var selectedValues = new Set(getSelectMultipleValues(prefix + '_class_groups').map(String));
    var button = document.createElement('button');
    button.type = 'button';
    button.className = 'class-option-card';
    button.classList.toggle('is-selected', selectedValues.has(String(option.id)));
    button.dataset.classOption = String(option.id);

    var title = document.createElement('span');
    title.className = 'class-option-title';
    title.textContent = option.category_name + ' · ' + option.display_name;

    var teacher = document.createElement('span');
    teacher.className = 'class-option-meta';
    teacher.textContent = option.teacher_label || 'Equipe docente não definida';

    var schedules = document.createElement('span');
    schedules.className = 'class-option-schedules';
    schedules.textContent = buildClassScheduleText(option);

    button.appendChild(title);
    button.appendChild(teacher);
    button.appendChild(schedules);
    button.addEventListener('click', function () {
      toggleClassSelection(selectField, option.id);
      renderClassGroupCards(prefix);
      renderPlanList();
      renderSummary();
      saveDraft();
    });
    return button;
  }

  function buildClassScheduleText(option) {
    if (!option.schedules || option.schedules.length === 0) {
      return 'Sem horários ativos.';
    }
    return option.schedules.map(function (schedule) {
      return schedule.weekday_display + ' ' + schedule.start_time;
    }).join(' · ');
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
    var childFieldNames = [];
    if (getSelectedProfile() === 'guardian') {
      childFieldNames.push('student_class_groups');
    }
    if (getSelectedProfile() === 'holder' && dependentToggle && dependentToggle.checked) {
      childFieldNames.push('dependent_class_groups');
    }
    for (var i = 0; i < childFieldNames.length; i++) {
      if (hasKidsAndJuvenile(getSelectedAudiences(childFieldNames[i]))) {
        return 2;
      }
    }
    for (var j = 0; j < extraDependents.length; j++) {
      var audiences = (extraDependents[j].class_groups || []).map(function (value) {
        var option = findClassCatalogOption(value);
        return option ? option.category_audience : '';
      });
      if (hasKidsAndJuvenile(audiences)) {
        return 2;
      }
    }
    return 1;
  }

  function hasKidsAndJuvenile(audiences) {
    return audiences.indexOf('kids') !== -1 && audiences.indexOf('juvenile') !== -1;
  }

  function isFamilyPlanEligible() {
    var profile = getSelectedProfile();
    if (profile === 'holder') {
      return Boolean(dependentToggle && dependentToggle.checked);
    }
    if (profile === 'guardian') {
      return getDependentCount() >= 2;
    }
    return false;
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

  function renderPlanList() {
    var container = form.querySelector('[data-plan-list]');
    if (!container) return;
    container.innerHTML = '';

    if (planCatalog.length === 0) {
      container.innerHTML = '<p class="checkout-empty-note">Nenhum plano disponível no momento.</p>';
      return;
    }

    var visiblePlans = getVisiblePlanCatalog();
    if (selectedPlanId && !visiblePlans.some(function (plan) { return plan.id === selectedPlanId; })) {
      selectedPlanId = null;
      syncCheckoutHiddenFields();
    }
    if (visiblePlans.length === 0) {
      container.innerHTML = '<p class="checkout-empty-note">Nenhum plano disponível para este cadastro.</p>';
      return;
    }

    var groupedPlans = groupPlansForDropdown(visiblePlans);
    groupedPlans.forEach(function (group, index) {
      var dropdown = document.createElement('details');
      dropdown.className = 'checkout-dropdown';
      if (index === 0 || group.hasSelection) {
        dropdown.open = true;
      }

      var summary = document.createElement('summary');
      summary.className = 'checkout-dropdown-summary';

      var summaryTitle = document.createElement('span');
      summaryTitle.className = 'checkout-dropdown-title';
      summaryTitle.textContent = group.title;

      var summaryMeta = document.createElement('span');
      summaryMeta.className = 'checkout-dropdown-meta';
      summaryMeta.textContent = group.plans.length + (group.plans.length === 1 ? ' opção' : ' opções');

      summary.appendChild(summaryTitle);
      summary.appendChild(summaryMeta);
      dropdown.appendChild(summary);

      var content = document.createElement('div');
      content.className = 'checkout-dropdown-content';
      group.plans.forEach(function (plan) {
        content.appendChild(buildPlanCard(plan));
      });
      dropdown.appendChild(content);
      container.appendChild(dropdown);
    });
  }

  function buildPlanCard(plan) {
    var card = document.createElement('label');
    card.className = 'checkout-option-card' + (selectedPlanId === plan.id ? ' is-selected' : '');

    var radio = document.createElement('input');
    radio.type = 'radio';
    radio.name = '_plan_radio';
    radio.className = 'checkout-option-radio';
    radio.value = String(plan.id);
    radio.checked = selectedPlanId === plan.id;
    radio.addEventListener('change', function () {
      selectedPlanId = plan.id;
      setCheckoutAction(getCheckoutActionForPlan(plan));
      syncCheckoutHiddenFields();
      renderPlanList();
    });

    var icon = createPaymentIcon(plan.payment_method);

    var info = document.createElement('div');
    info.className = 'checkout-option-info';
    var name = document.createElement('span');
    name.className = 'checkout-option-name';
    name.textContent = plan.name;
    var meta = document.createElement('span');
    meta.className = 'checkout-option-meta';
    meta.textContent = buildPlanMeta(plan);
    info.appendChild(name);
    info.appendChild(meta);

    var price = document.createElement('span');
    price.className = 'checkout-option-price';
    price.textContent = formatBRL(plan.price);

    card.appendChild(radio);
    card.appendChild(icon);
    card.appendChild(info);
    card.appendChild(price);
    return card;
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

  function groupPlansForDropdown(plans) {
    var cycleOrder = { monthly: 1, quarterly: 2, semiannual: 3, annual: 4 };
    var grouped = {};

    plans.forEach(function (plan) {
      var section = plan.is_family_plan ? 'family' : 'standard';
      var cycle = plan.billing_cycle || 'other';
      var key = section + ':' + cycle;
      if (!grouped[key]) {
        grouped[key] = {
          section: section,
          cycle: cycle,
          title: buildPlanGroupTitle(plan),
          plans: [],
          hasSelection: false
        };
      }
      grouped[key].plans.push(plan);
      if (selectedPlanId === plan.id) {
        grouped[key].hasSelection = true;
      }
    });

    return Object.keys(grouped)
      .map(function (key) { return grouped[key]; })
      .sort(function (a, b) {
        if (a.section !== b.section) {
          return a.section === 'standard' ? -1 : 1;
        }
        var orderA = cycleOrder[a.cycle] || 99;
        var orderB = cycleOrder[b.cycle] || 99;
        if (orderA !== orderB) {
          return orderA - orderB;
        }
        return a.title.localeCompare(b.title);
      });
  }

  function buildPlanGroupTitle(plan) {
    var cycleLabel = plan.cycle || 'Plano';
    if (plan.is_family_plan) {
      return 'Plano família - ' + cycleLabel;
    }
    return 'Plano ' + cycleLabel.toLowerCase();
  }

  function getVisiblePlanCatalog() {
    var familyEligible = isFamilyPlanEligible();
    return planCatalog.filter(function (plan) {
      return !plan.is_family_plan || familyEligible;
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
    if (plan.is_family_plan) {
      parts.push('Irmãos / Pais e Filhos');
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
      container.innerHTML = '<p class="checkout-empty-note">Nenhum material disponível no momento.</p>';
      return;
    }

    var groupedProducts = groupProductsForDropdown(productCatalog);
    groupedProducts.forEach(function (group, index) {
      var dropdown = document.createElement('details');
      dropdown.className = 'checkout-dropdown';
      if (index === 0 || group.hasSelection) {
        dropdown.open = true;
      }

      var summary = document.createElement('summary');
      summary.className = 'checkout-dropdown-summary';

      var summaryTitle = document.createElement('span');
      summaryTitle.className = 'checkout-dropdown-title';
      summaryTitle.textContent = group.title;

      var summaryMeta = document.createElement('span');
      summaryMeta.className = 'checkout-dropdown-meta';
      summaryMeta.textContent = group.products.length + (group.products.length === 1 ? ' item' : ' itens');

      summary.appendChild(summaryTitle);
      summary.appendChild(summaryMeta);
      dropdown.appendChild(summary);

      var content = document.createElement('div');
      content.className = 'checkout-dropdown-content';
      group.products.forEach(function (product) {
        content.appendChild(buildProductCard(product));
      });

      dropdown.appendChild(content);
      container.appendChild(dropdown);
    });
  }

  function groupProductsForDropdown(products) {
    var grouped = {};
    products.forEach(function (product) {
      var category = product.category || 'Outros materiais';
      if (!grouped[category]) {
        grouped[category] = {
          title: category,
          products: [],
          hasSelection: false
        };
      }
      grouped[category].products.push(product);
      if ((selectedProducts[product.id] || 0) > 0) {
        grouped[category].hasSelection = true;
      }
    });
    return Object.keys(grouped)
      .sort(function (a, b) { return a.localeCompare(b); })
      .map(function (key) { return grouped[key]; });
  }

  function buildProductCard(product) {
    var qty = selectedProducts[product.id] || 0;

    var card = document.createElement('div');
    card.className = 'checkout-option-card' + (qty > 0 ? ' is-selected' : '');

    var info = document.createElement('div');
    info.className = 'checkout-option-info';

    var name = document.createElement('span');
    name.className = 'checkout-option-name';
    name.textContent = product.name;

    var meta = document.createElement('span');
    meta.className = 'checkout-option-meta';
    meta.textContent = product.category;

    info.appendChild(name);
    info.appendChild(meta);

    var price = document.createElement('span');
    price.className = 'checkout-option-price';
    price.textContent = formatBRL(product.price);

    var qtyControl = document.createElement('div');
    qtyControl.className = 'checkout-qty-control';

    var minusBtn = document.createElement('button');
    minusBtn.type = 'button';
    minusBtn.className = 'checkout-qty-btn';
    minusBtn.textContent = '\u2212';
    minusBtn.addEventListener('click', function () {
      var current = selectedProducts[product.id] || 0;
      if (current > 0) {
        selectedProducts[product.id] = current - 1;
        if (selectedProducts[product.id] === 0) delete selectedProducts[product.id];
        syncCheckoutHiddenFields();
        renderProductList();
      }
    });

    var qtySpan = document.createElement('span');
    qtySpan.className = 'checkout-qty-value';
    qtySpan.textContent = String(qty);

    var plusBtn = document.createElement('button');
    plusBtn.type = 'button';
    plusBtn.className = 'checkout-qty-btn';
    plusBtn.textContent = '+';
    plusBtn.addEventListener('click', function () {
      var current = selectedProducts[product.id] || 0;
      selectedProducts[product.id] = current + 1;
      syncCheckoutHiddenFields();
      renderProductList();
    });

    qtyControl.appendChild(minusBtn);
    qtyControl.appendChild(qtySpan);
    qtyControl.appendChild(plusBtn);

    card.appendChild(info);
    card.appendChild(price);
    card.appendChild(qtyControl);
    return card;
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

    var productIds = Object.keys(selectedProducts);
    for (var i = 0; i < productIds.length; i++) {
      var pid = parseInt(productIds[i], 10);
      var qty = selectedProducts[pid];
      if (!qty) continue;
      var product = productCatalog.find(function (p) { return p.id === pid; });
      if (!product) continue;
      var subtotal = parseFloat(product.price) * qty;
      total += subtotal;
      itemsContainer.innerHTML += '<div class="checkout-summary-row"><span class="checkout-summary-row-label">' + product.name + ' x' + qty + '</span><span class="checkout-summary-row-value">' + formatBRL(subtotal) + '</span></div>';
    }

    if (!selectedPlanId && productIds.length === 0) {
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
      var ids = Object.keys(selectedProducts);
      for (var i = 0; i < ids.length; i++) {
        var id = parseInt(ids[i], 10);
        var qty = selectedProducts[id];
        if (qty > 0) items.push({ id: id, qty: qty });
      }
      productsInput.value = JSON.stringify(items);
    }
    if (checkoutActionInput) {
      checkoutActionInput.value = checkoutAction;
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
