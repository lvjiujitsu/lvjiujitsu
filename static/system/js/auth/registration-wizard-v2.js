(function () {
  var form = document.getElementById("client-registration-form");
  if (!form) return;

  // Catalogs
  var registrationCatalogNode = document.getElementById("registration-catalog");
  var ibjjfCatalogNode = document.getElementById("ibjjf-age-categories");
  var registrationCatalog = registrationCatalogNode ? JSON.parse(registrationCatalogNode.textContent) : [];
  var ibjjfCategories = ibjjfCatalogNode ? JSON.parse(ibjjfCatalogNode.textContent) : [];
  var hasCatalog = registrationCatalog.length > 0;
  var groupMap = new Map(registrationCatalog.map(function (item) { return [String(item.id), item]; }));

  // DOM Elements
  var profileInputs = Array.from(form.querySelectorAll('input[name="registration_profile"]'));
  var otherTypeSelect = form.querySelector('select[name="other_type_code"]');
  var dependentToggle = document.getElementById("include-dependent");
  var dependentToggleCard = form.querySelector("[data-dependent-toggle-card]");
  var otherTypePanel = form.querySelector("[data-other-type-panel]");
  var stepPanels = Array.from(form.querySelectorAll("[data-step-panel]"));
  var stepsContainer = form.querySelector("[data-wizard-steps-container]");
  var backButton = form.querySelector("[data-step-back]");
  var nextButton = form.querySelector("[data-step-next]");
  var submitButton = form.querySelector("[data-step-submit]");
  var progressFill = form.querySelector("[data-progress-fill]");
  var extraPayloadInput = document.getElementById("extra-dependents-payload");
  var addDependentButton = form.querySelector("[data-add-dependent]");
  var extraIdentityList = form.querySelector("[data-extra-dependent-identity-list]");
  var extraAssignmentList = form.querySelector("[data-extra-dependent-assignment-list]");
  var extraMedicalList = form.querySelector("[data-extra-dependent-medical-list]");
  var dateInputs = Array.from(form.querySelectorAll("[data-date-mask]"));
  var kinshipSelects = Array.from(form.querySelectorAll("[data-kinship-select]"));
  var draftNote = document.querySelector("[data-registration-draft-note]");
  var draftLabel = document.querySelector("[data-registration-draft-label]");
  var discardButton = document.querySelector("[data-registration-discard]");
  var draftKey = "lv-register-draft-v2";
  var draftTtlMs = 30 * 60 * 1000;
  var canRestoreDraft = form.dataset.canRestoreDraft === "true";
  var draftSaveTimeout = null;

  // Step definitions by panel key
  var STEP_KEYS = {
    TYPE: "type",
    MAIN_DATA: "main-data",
    DEPENDENT_DATA: "dependent-data",
    CLASSES: "classes",
    MEDICAL: "medical"
  };

  // State
  var currentStepIndex = 0;
  var activeSteps = [];
  var dependentSequence = 0;
  var extraDependents = parseInitialDependents();

  // Static selection configs
  var staticSelections = {
    holder: buildStaticSelectionConfig("holder", "holder-birthdate"),
    dependent: buildStaticSelectionConfig("dependent", "dependent-birthdate"),
    student: buildStaticSelectionConfig("student", "student-birthdate")
  };

  function buildStaticSelectionConfig(entityKey, birthInputId) {
    return {
      entityKey: entityKey,
      inputName: entityKey + "_class_groups",
      container: form.querySelector('[data-class-group-options="' + entityKey + '"]'),
      summary: form.querySelector('[data-class-group-summary="' + entityKey + '"]'),
      birthInput: birthInputId ? document.getElementById(birthInputId) : null,
      sexInput: form.querySelector('[data-biological-sex-input="' + entityKey + '"]')
    };
  }

  // --- STEP FLOW LOGIC ---
  function getCurrentProfile() {
    var checked = profileInputs.find(function (input) { return input.checked; });
    return checked ? checked.value : "holder";
  }

  function hasDependentFlow() {
    var profile = getCurrentProfile();
    if (profile === "guardian") return true;
    if (profile === "holder" && dependentToggle && dependentToggle.checked) return true;
    return false;
  }

  function isOtherProfile() {
    return getCurrentProfile() === "other";
  }

  function computeActiveSteps() {
    var profile = getCurrentProfile();
    var steps = [];

    steps.push({ key: STEP_KEYS.TYPE, label: "Tipo" });

    if (profile === "other") {
      steps.push({ key: STEP_KEYS.MAIN_DATA, label: "Dados" });
    } else if (profile === "guardian") {
      steps.push({ key: STEP_KEYS.MAIN_DATA, label: "Responsável" });
      steps.push({ key: STEP_KEYS.DEPENDENT_DATA, label: "Aluno" });
      steps.push({ key: STEP_KEYS.CLASSES, label: "Turmas" });
      steps.push({ key: STEP_KEYS.MEDICAL, label: "Prontuário" });
    } else {
      // holder
      if (hasDependentFlow()) {
        steps.push({ key: STEP_KEYS.MAIN_DATA, label: "Titular" });
        steps.push({ key: STEP_KEYS.DEPENDENT_DATA, label: "Dependente" });
      } else {
        steps.push({ key: STEP_KEYS.MAIN_DATA, label: "Aluno" });
      }
      steps.push({ key: STEP_KEYS.CLASSES, label: "Turmas" });
      steps.push({ key: STEP_KEYS.MEDICAL, label: "Prontuário" });
    }

    return steps;
  }

  function renderStepIndicators() {
    stepsContainer.innerHTML = "";
    activeSteps.forEach(function (step, index) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "wizard-progress-step";
      btn.dataset.stepIndex = String(index);
      btn.innerHTML = '<span class="wizard-progress-index">' + (index + 1) + '</span><small>' + step.label + '</small>';
      if (index === currentStepIndex) btn.classList.add("is-active");
      if (index < currentStepIndex) btn.classList.add("is-complete");
      btn.addEventListener("click", function () {
        if (index < currentStepIndex) {
          goToStep(index);
        } else if (index > currentStepIndex) {
          if (validateAllStepsUpTo(index - 1)) {
            goToStep(index);
          }
        }
      });
      stepsContainer.appendChild(btn);
    });
  }

  function updateStepLabels() {
    var totalSteps = activeSteps.length;
    var stepLabels = form.querySelectorAll("[data-step-label]");
    stepLabels.forEach(function (label) {
      label.textContent = "Etapa " + (currentStepIndex + 1) + " de " + totalSteps;
    });
  }

  function updateProgressBar() {
    if (!progressFill) return;
    var totalSteps = activeSteps.length;
    var progress = totalSteps > 1 ? (currentStepIndex / (totalSteps - 1)) * 100 : 0;
    progressFill.style.width = progress + "%";
  }

  function updateStepIndicatorStates() {
    var indicators = stepsContainer.querySelectorAll(".wizard-progress-step");
    indicators.forEach(function (btn, index) {
      btn.classList.toggle("is-active", index === currentStepIndex);
      btn.classList.toggle("is-complete", index < currentStepIndex);
    });
  }

  function syncFlowSections() {
    var profile = getCurrentProfile();
    var hasDependent = hasDependentFlow();

    // Hide all flow sections first
    form.querySelectorAll("[data-flow-section]").forEach(function (section) {
      setHiddenState(section, true);
    });

    if (profile === "holder") {
      setHiddenState(form.querySelector('[data-flow-section="holder-data"]'), false);
      setHiddenState(form.querySelector('[data-flow-section="holder-classes"]'), false);
      setHiddenState(form.querySelector('[data-flow-section="holder-medical"]'), false);

      if (hasDependent) {
        setHiddenState(form.querySelector('[data-flow-section="holder-dependent-data"]'), false);
        setHiddenState(form.querySelector('[data-flow-section="dependent-classes"]'), false);
        setHiddenState(form.querySelector('[data-flow-section="dependent-medical"]'), false);
        setHiddenState(form.querySelector('[data-flow-section="extra-dependents-data"]'), false);
        setHiddenState(form.querySelector('[data-flow-section="extra-dependents-classes"]'), false);
        setHiddenState(form.querySelector('[data-flow-section="extra-dependents-medical"]'), false);

        // Update holder title
        var holderTitle = form.querySelector('[data-flow-section="holder-data"] [data-section-title]');
        if (holderTitle) holderTitle.textContent = "Dados do titular";
      } else {
        var holderTitle = form.querySelector('[data-flow-section="holder-data"] [data-section-title]');
        if (holderTitle) holderTitle.textContent = "Dados do aluno";
      }
    } else if (profile === "guardian") {
      setHiddenState(form.querySelector('[data-flow-section="guardian-data"]'), false);
      setHiddenState(form.querySelector('[data-flow-section="guardian-student-data"]'), false);
      setHiddenState(form.querySelector('[data-flow-section="student-classes"]'), false);
      setHiddenState(form.querySelector('[data-flow-section="student-medical"]'), false);
      setHiddenState(form.querySelector('[data-flow-section="extra-dependents-data"]'), false);
      setHiddenState(form.querySelector('[data-flow-section="extra-dependents-classes"]'), false);
      setHiddenState(form.querySelector('[data-flow-section="extra-dependents-medical"]'), false);
    } else if (profile === "other") {
      setHiddenState(form.querySelector('[data-flow-section="other-data"]'), false);
    }

    // Toggle dependent toggle card visibility
    setHiddenState(dependentToggleCard, profile !== "holder");
    if (profile !== "holder" && dependentToggle) {
      dependentToggle.checked = false;
    }

    // Toggle other type panel
    setHiddenState(otherTypePanel, profile !== "other");
  }

  function syncStepPanels() {
    var currentKey = activeSteps[currentStepIndex] ? activeSteps[currentStepIndex].key : null;
    stepPanels.forEach(function (panel) {
      var panelKey = panel.dataset.stepPanel;
      setHiddenState(panel, panelKey !== currentKey);
    });
  }

  function syncButtons() {
    var isFirst = currentStepIndex === 0;
    var isLast = currentStepIndex === activeSteps.length - 1;

    setHiddenState(backButton, isFirst);
    setHiddenState(nextButton, isLast);
    setHiddenState(submitButton, !isLast);
  }

  function goToStep(index) {
    if (index < 0 || index >= activeSteps.length) return;
    currentStepIndex = index;
    syncStepPanels();
    syncButtons();
    updateStepLabels();
    updateProgressBar();
    updateStepIndicatorStates();
    queueDraftSave();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function updateWizard() {
    activeSteps = computeActiveSteps();
    if (currentStepIndex >= activeSteps.length) {
      currentStepIndex = activeSteps.length - 1;
    }
    renderStepIndicators();
    syncFlowSections();
    syncStepPanels();
    syncButtons();
    updateStepLabels();
    updateProgressBar();
    renderClassOptions();
    queueDraftSave();
  }

  // --- VALIDATION ---
  function setHiddenState(element, shouldHide) {
    if (!element) return;
    element.classList.toggle("is-hidden", shouldHide);
    element.hidden = shouldHide;
  }

  function validateRequiredField(name) {
    var field = form.querySelector('[name="' + name + '"]');
    if (!field || field.closest(".is-hidden")) return true;
    var valid = Boolean(field.value && field.value.trim());
    if (!valid) {
      field.setAttribute("aria-invalid", "true");
      field.focus();
    } else {
      field.removeAttribute("aria-invalid");
    }
    return valid;
  }

  function validateStep(index) {
    var step = activeSteps[index];
    if (!step) return true;

    var profile = getCurrentProfile();
    var hasDependent = hasDependentFlow();

    if (step.key === STEP_KEYS.TYPE) {
      if (profile === "other" && otherTypeSelect) {
        var hasChoice = otherTypeSelect.value && otherTypeSelect.value.trim();
        if (!hasChoice) {
          otherTypePanel.setAttribute("data-invalid", "true");
          return false;
        }
        otherTypePanel.removeAttribute("data-invalid");
      }
      return true;
    }

    if (step.key === STEP_KEYS.MAIN_DATA) {
      var requiredFields = [];
      if (profile === "holder") {
        requiredFields = ["holder_name", "holder_cpf", "holder_birthdate", "holder_biological_sex", "holder_password", "holder_password_confirm"];
      } else if (profile === "guardian") {
        requiredFields = ["guardian_name", "guardian_cpf", "guardian_password", "guardian_password_confirm"];
      } else if (profile === "other") {
        requiredFields = ["other_name", "other_cpf", "other_birthdate", "other_password", "other_password_confirm"];
      }
      return requiredFields.every(validateRequiredField);
    }

    if (step.key === STEP_KEYS.DEPENDENT_DATA) {
      var requiredFields = [];
      if (profile === "holder" && hasDependent) {
        requiredFields = ["dependent_name", "dependent_cpf", "dependent_birthdate", "dependent_biological_sex", "dependent_password", "dependent_password_confirm", "dependent_kinship_type"];
      } else if (profile === "guardian") {
        requiredFields = ["student_name", "student_cpf", "student_birthdate", "student_biological_sex", "student_password", "student_password_confirm", "student_kinship_type"];
      }
      return requiredFields.every(validateRequiredField);
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

  // --- DRAFT ---
  function buildDraftPayload() {
    var data = {};
    var inputs = form.querySelectorAll("input, select, textarea");
    inputs.forEach(function (input) {
      if (!input.name || input.type === "hidden" || input.type === "password") return;
      if (input.type === "checkbox") {
        data[input.name] = input.checked;
      } else if (input.type === "radio") {
        if (input.checked) data[input.name] = input.value;
      } else {
        data[input.name] = input.value;
      }
    });
    data._step = currentStepIndex;
    data._extraDependents = extraDependents;
    return data;
  }

  function saveDraft() {
    var payload = {
      data: buildDraftPayload(),
      timestamp: Date.now()
    };
    try {
      localStorage.setItem(draftKey, JSON.stringify(payload));
      syncDraftNoteVisibility();
    } catch (e) {}
  }

  function queueDraftSave() {
    if (draftSaveTimeout) clearTimeout(draftSaveTimeout);
    draftSaveTimeout = setTimeout(saveDraft, 800);
  }

  function readStoredDraft() {
    try {
      var raw = localStorage.getItem(draftKey);
      if (!raw) return null;
      var parsed = JSON.parse(raw);
      if (Date.now() - parsed.timestamp > draftTtlMs) {
        localStorage.removeItem(draftKey);
        return null;
      }
      return parsed.data;
    } catch (e) {
      return null;
    }
  }

  function restoreDraft(data) {
    Object.keys(data).forEach(function (key) {
      if (key.startsWith("_")) return;
      var input = form.querySelector('[name="' + key + '"]');
      if (!input) return;
      if (input.type === "checkbox") {
        input.checked = Boolean(data[key]);
      } else if (input.type === "radio") {
        var radios = form.querySelectorAll('[name="' + key + '"]');
        radios.forEach(function (r) {
          r.checked = r.value === data[key];
        });
      } else {
        input.value = data[key] || "";
      }
    });
    if (data._extraDependents) {
      extraDependents = data._extraDependents;
    }
    if (typeof data._step === "number") {
      currentStepIndex = data._step;
    }
    updateWizard();
    syncChoiceCards();
  }

  function clearDraft() {
    try {
      localStorage.removeItem(draftKey);
    } catch (e) {}
    syncDraftNoteVisibility();
  }

  function discardAndReset() {
    clearDraft();
    form.reset();
    extraDependents = [];
    currentStepIndex = 0;
    updateWizard();
    syncChoiceCards();
    syncDraftNoteVisibility();
  }

  function hasAnyFieldFilled() {
    var inputs = form.querySelectorAll("input, select, textarea");
    for (var i = 0; i < inputs.length; i++) {
      var input = inputs[i];
      if (input.type === "hidden" || input.type === "password") continue;
      if (input.name === "registration_profile" || input.name === "other_type_code") continue;
      if (input.name === "include_dependent") continue;
      if (input.type === "checkbox" && input.checked) return true;
      if (input.type === "radio") continue;
      if (input.value && input.value.trim()) return true;
    }
    return false;
  }

  function syncDraftNoteVisibility() {
    if (!draftNote) return;
    var hasDraft = readStoredDraft() !== null;
    var hasData = hasAnyFieldFilled();
    setHiddenState(draftNote, !hasDraft && !hasData);
  }

  // --- CLASS OPTIONS ---
  function renderClassOptions() {
    Object.values(staticSelections).forEach(function (config) {
      if (config.container) {
        renderClassGrid(config);
      }
    });
  }

  function renderClassGrid(config) {
    if (!config.container) return;
    var selectedValues = (config.container.dataset.selectedValues || "").split(",").filter(Boolean);
    var html = "";

    registrationCatalog.forEach(function (group) {
      var isSelected = selectedValues.indexOf(String(group.id)) !== -1;
      html += '<label class="class-option-card' + (isSelected ? " is-selected" : "") + '">';
      html += '<input type="checkbox" name="' + config.inputName + '" value="' + group.id + '"' + (isSelected ? " checked" : "") + '>';
      html += '<span class="class-option-card-marker"></span>';
      html += '<span class="class-option-card-label">' + group.name + '</span>';
      html += '</label>';
    });

    config.container.innerHTML = html;

    config.container.querySelectorAll("input").forEach(function (input) {
      input.addEventListener("change", function () {
        input.closest(".class-option-card").classList.toggle("is-selected", input.checked);
        queueDraftSave();
      });
    });
  }

  // --- EXTRA DEPENDENTS ---
  function parseInitialDependents() {
    if (!extraPayloadInput || !extraPayloadInput.value) return [];
    try {
      var parsed = JSON.parse(extraPayloadInput.value);
      if (!Array.isArray(parsed)) return [];
      return parsed.map(function (item) {
        dependentSequence += 1;
        return Object.assign({ id: dependentSequence }, item);
      });
    } catch (e) {
      return [];
    }
  }

  function createEmptyDependent() {
    dependentSequence += 1;
    return {
      id: dependentSequence,
      full_name: "",
      cpf: "",
      birth_date: "",
      biological_sex: "",
      phone: "",
      email: "",
      kinship_type: "",
      kinship_other_label: "",
      password: "",
      password_confirm: "",
      class_groups: [],
      blood_type: "",
      allergies: "",
      injuries: "",
      emergency_contact: ""
    };
  }

  function renderExtraDependents() {
    // Identity
    if (extraIdentityList) {
      extraIdentityList.innerHTML = "";
      var identityTemplate = document.getElementById("extra-dependent-identity-template");
      if (identityTemplate) {
        extraDependents.forEach(function (dep, index) {
          var clone = identityTemplate.content.cloneNode(true);
          var card = clone.querySelector("[data-dependent-card]");
          if (card) {
            card.dataset.dependentId = dep.id;
            var numberSpan = card.querySelector("[data-dependent-number]");
            if (numberSpan) numberSpan.textContent = String(index + 1);
            bindDependentCardFields(card, dep);
          }
          extraIdentityList.appendChild(clone);
        });
      }
    }
    syncExtraDependentsPayload();
  }

  function bindDependentCardFields(card, dep) {
    card.querySelectorAll("[data-dependent-field]").forEach(function (field) {
      var key = field.dataset.dependentField;
      if (field.tagName === "SELECT" || field.tagName === "TEXTAREA" || field.type !== "password") {
        field.value = dep[key] || "";
      }
      field.addEventListener("input", function () {
        dep[key] = field.value;
        queueDraftSave();
      });
      field.addEventListener("change", function () {
        dep[key] = field.value;
        queueDraftSave();
      });
    });

    var removeBtn = card.querySelector("[data-remove-dependent]");
    if (removeBtn) {
      removeBtn.addEventListener("click", function () {
        extraDependents = extraDependents.filter(function (d) { return d.id !== dep.id; });
        renderExtraDependents();
        queueDraftSave();
      });
    }
  }

  function syncExtraDependentsPayload() {
    if (!extraPayloadInput) return;
    extraPayloadInput.value = JSON.stringify(extraDependents);
  }

  // --- CHOICE CARDS ---
  function syncChoiceCards() {
    form.querySelectorAll("[data-choice-card]").forEach(function (card) {
      var input = card.querySelector("input");
      if (input) {
        card.classList.toggle("is-selected", input.checked);
      }
    });
  }

  // --- DATE MASK ---
  function applyDateMask(input) {
    input.addEventListener("input", function (e) {
      var value = input.value.replace(/\D/g, "");
      if (value.length >= 2) value = value.slice(0, 2) + "/" + value.slice(2);
      if (value.length >= 5) value = value.slice(0, 5) + "/" + value.slice(5);
      input.value = value.slice(0, 10);
    });
  }

  // --- KINSHIP SELECT ---
  function bindKinshipSelect(select) {
    var targetId = select.dataset.otherTarget;
    var targetField = targetId ? document.getElementById(targetId) : null;
    if (!targetField) return;

    function sync() {
      var isOther = select.value === "other";
      setHiddenState(targetField, !isOther);
    }
    select.addEventListener("change", sync);
    sync();
  }

  // --- INITIALIZATION ---
  function init() {
    // Bind profile changes
    profileInputs.forEach(function (input) {
      input.addEventListener("change", function () {
        syncChoiceCards();
        currentStepIndex = 0;
        updateWizard();
      });
    });

    // Bind dependent toggle
    if (dependentToggle) {
      dependentToggle.addEventListener("change", function () {
        currentStepIndex = 0;
        updateWizard();
      });
    }

    // Bind navigation buttons
    if (backButton) {
      backButton.addEventListener("click", function () {
        if (currentStepIndex > 0) {
          goToStep(currentStepIndex - 1);
        }
      });
    }

    if (nextButton) {
      nextButton.addEventListener("click", function () {
        if (validateCurrentStep()) {
          goToStep(currentStepIndex + 1);
        }
      });
    }

    // Add dependent
    if (addDependentButton) {
      addDependentButton.addEventListener("click", function () {
        extraDependents.push(createEmptyDependent());
        renderExtraDependents();
        queueDraftSave();
      });
    }

    // Discard button
    if (discardButton) {
      discardButton.addEventListener("click", function () {
        discardAndReset();
      });
    }

    // Date masks
    dateInputs.forEach(applyDateMask);

    // Kinship selects
    kinshipSelects.forEach(bindKinshipSelect);

    // Form input listeners for draft
    form.addEventListener("input", function () {
      queueDraftSave();
      syncDraftNoteVisibility();
    });
    form.addEventListener("change", function () {
      queueDraftSave();
      syncDraftNoteVisibility();
    });

    // Restore draft
    if (canRestoreDraft) {
      var draft = readStoredDraft();
      if (draft) {
        restoreDraft(draft);
      }
    }

    // Initial render
    syncChoiceCards();
    updateWizard();
    renderExtraDependents();
    syncDraftNoteVisibility();
  }

  init();
})();
