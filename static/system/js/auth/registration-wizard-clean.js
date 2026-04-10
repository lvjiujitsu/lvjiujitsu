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

  var planCatalogNode = document.getElementById('plan-catalog');
  var planCatalog = planCatalogNode ? JSON.parse(planCatalogNode.textContent) : [];

  var productCatalogNode = document.getElementById('product-catalog');
  var productCatalog = productCatalogNode ? JSON.parse(productCatalogNode.textContent) : [];

  // ============================================================================
  // State
  // ============================================================================
  var currentStepIndex = 0;
  var selectedPlanId = null;
  var selectedProducts = {};
  var activeSteps = [];
  var extraDependents = [];
  var dependentSequence = 0;
  
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
    plan_materials: {
      key: 'plan_materials',
      label: 'Plano',
      title: 'Plano e Materiais',
      panelSelector: '[data-panel="plan-materials"]',
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
      steps.push(STEP_DEFINITIONS.plan_materials);
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
      steps.push(STEP_DEFINITIONS.plan_materials);
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
    if (currentStep.key === 'plan_materials') {
      renderPlanList();
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

  function nextStep() {
    if (!validateCurrentStep()) {
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
  // Checkout: Plan & Materials
  // ============================================================================
  function formatBRL(value) {
    var num = parseFloat(value);
    if (isNaN(num)) return 'R$ 0,00';
    return 'R$ ' + num.toFixed(2).replace('.', ',').replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  }

  function renderPlanList() {
    var container = form.querySelector('[data-plan-list]');
    if (!container) return;
    container.innerHTML = '';

    if (planCatalog.length === 0) {
      container.innerHTML = '<p class="checkout-empty-note">Nenhum plano disponível no momento.</p>';
      return;
    }

    planCatalog.forEach(function (plan) {
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
        syncCheckoutHiddenFields();
        renderPlanList();
      });

      var info = document.createElement('div');
      info.className = 'checkout-option-info';
      info.innerHTML = '<span class="checkout-option-name">' + plan.name + '</span><span class="checkout-option-meta">' + plan.cycle + '</span>';

      var price = document.createElement('span');
      price.className = 'checkout-option-price';
      price.textContent = formatBRL(plan.price);

      card.appendChild(radio);
      card.appendChild(info);
      card.appendChild(price);
      container.appendChild(card);
    });
  }

  function renderProductList() {
    var container = form.querySelector('[data-product-list]');
    if (!container) return;
    container.innerHTML = '';

    if (productCatalog.length === 0) {
      container.innerHTML = '<p class="checkout-empty-note">Nenhum material disponível no momento.</p>';
      return;
    }

    productCatalog.forEach(function (product) {
      var qty = selectedProducts[product.id] || 0;

      var card = document.createElement('div');
      card.className = 'checkout-option-card' + (qty > 0 ? ' is-selected' : '');

      var info = document.createElement('div');
      info.className = 'checkout-option-info';
      info.innerHTML = '<span class="checkout-option-name">' + product.name + '</span><span class="checkout-option-meta">' + product.category + '</span>';

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
      container.appendChild(card);
    });
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
        var planPrice = parseFloat(plan.price);
        total += planPrice;
        itemsContainer.innerHTML += '<div class="checkout-summary-row"><span class="checkout-summary-row-label">' + plan.name + ' (' + plan.cycle + ')</span><span class="checkout-summary-row-value">' + formatBRL(plan.price) + '</span></div>';
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

    totalEl.textContent = formatBRL(total);
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
    
    // Compute initial steps
    activeSteps = computeActiveSteps();
    
    // Initial UI update
    updateUI();
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
