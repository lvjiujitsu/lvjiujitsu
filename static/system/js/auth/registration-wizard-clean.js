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
  var otherTypePanel = form.querySelector('[data-other-type-panel]');
  
  var stepsContainer = form.querySelector('[data-wizard-steps-container]');
  var stepPanels = form.querySelector('[data-step-panels]');
  var progressFill = form.querySelector('[data-progress-fill]');
  
  var backButton = form.querySelector('[data-step-back]');
  var nextButton = form.querySelector('[data-step-next]');
  var submitButton = form.querySelector('[data-step-submit]');
  var dateInputs = Array.from(form.querySelectorAll('[data-date-mask]'));
  
  var draftNote = document.querySelector('[data-registration-draft-note]');
  var draftLabel = document.querySelector('[data-registration-draft-label]');
  var discardButton = document.querySelector('[data-registration-discard]');
  
  var registrationCatalogNode = document.getElementById('registration-catalog');
  var registrationCatalog = registrationCatalogNode ? JSON.parse(registrationCatalogNode.textContent) : [];
  
  // ============================================================================
  // State
  // ============================================================================
  var currentStepIndex = 0;
  var activeSteps = [];
  var extraDependents = [];
  var dependentSequence = 0;
  
  var DRAFT_KEY = 'lv-register-draft-clean';
  var DRAFT_TTL_MS = 30 * 60 * 1000;
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
    }
  };

  // ============================================================================
  // Flow Computation
  // ============================================================================
  function computeActiveSteps() {
    var profile = getSelectedProfile();
    var hasDependentFlow = dependentToggle && dependentToggle.checked;
    var steps = [];

    // Always start with type selection
    steps.push(STEP_DEFINITIONS.type);

    if (profile === 'other') {
      // OTHER: Tipo → Dados (2 steps)
      steps.push(STEP_DEFINITIONS.other);
    } else if (profile === 'guardian') {
      // RESPONSÁVEL: Tipo -> Responsável -> Aluno -> Turmas aluno -> Prontuário aluno
      steps.push(STEP_DEFINITIONS.guardian);
      steps.push(STEP_DEFINITIONS.student);
      steps.push(STEP_DEFINITIONS.student_classes);
      steps.push(STEP_DEFINITIONS.student_medical);
    } else if (profile === 'holder') {
      if (hasDependentFlow) {
        // TITULAR + DEPENDENTE: fluxo completo por pessoa
        steps.push(STEP_DEFINITIONS.holder_titular);
        steps.push(STEP_DEFINITIONS.holder_classes);
        steps.push(STEP_DEFINITIONS.holder_medical);
        steps.push(STEP_DEFINITIONS.dependent);
        steps.push(STEP_DEFINITIONS.dependent_classes);
        steps.push(STEP_DEFINITIONS.dependent_medical);
      } else {
        // ALUNO: fluxo completo da própria pessoa
        steps.push(STEP_DEFINITIONS.holder);
        steps.push(STEP_DEFINITIONS.holder_classes);
        steps.push(STEP_DEFINITIONS.holder_medical);
      }
    }

    return steps;
  }

  function getSelectedProfile() {
    var selected = profileInputs.find(function (input) { return input.checked; });
    return selected ? selected.value : 'holder';
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
    renderStepIndicators();
    renderStepPanels();
    updateProgressBar();
    updateNavigation();
    updateDependentToggleVisibility();
    updateOtherTypeVisibility();
  }

  function updateDependentToggleVisibility() {
    if (!dependentToggleCard) return;
    var profile = getSelectedProfile();
    var shouldShow = profile === 'holder';
    dependentToggleCard.classList.toggle('is-hidden', !shouldShow);
    dependentToggleCard.hidden = !shouldShow;
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

  // ============================================================================
  // Navigation
  // ============================================================================
  function goToStep(index) {
    if (index < 0 || index >= activeSteps.length) return;
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

  function validateRequiredField(fieldName) {
    var field = form.querySelector('[name="' + fieldName + '"]');
    if (!field || !isFieldVisible(field)) return true;
    clearFieldValidation(field);
    var value = field.value ? field.value.trim() : '';
    if (!value) {
      return markInvalid(field, 'Campo obrigatório.');
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
      return markInvalid(selectField, 'Selecione ao menos uma turma.');
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
    
    // Reset to first step
    currentStepIndex = 0;
    activeSteps = computeActiveSteps();
    
    // Clear all aria-invalid
    form.querySelectorAll('[aria-invalid]').forEach(function (el) {
      el.removeAttribute('aria-invalid');
    });
    
    // Update UI
    updateUI();
    updateDraftNoteVisibility();
    scrollToTop();
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

  if (backButton) {
    backButton.addEventListener('click', prevStep);
  }

  if (nextButton) {
    nextButton.addEventListener('click', nextStep);
  }

  form.addEventListener('submit', function (event) {
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
    saveDraft();
  });
  
  form.addEventListener('change', function () {
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
  // Initialization
  // ============================================================================
  function init() {
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
})();
