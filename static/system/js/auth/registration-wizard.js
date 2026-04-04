(function () {
  const form = document.getElementById("client-registration-form");
  if (!form) {
    return;
  }

  const registrationCatalogNode = document.getElementById("registration-catalog");
  const ibjjfCatalogNode = document.getElementById("ibjjf-age-categories");
  const registrationCatalog = registrationCatalogNode ? JSON.parse(registrationCatalogNode.textContent) : [];
  const ibjjfCategories = ibjjfCatalogNode ? JSON.parse(ibjjfCatalogNode.textContent) : [];
  const hasCatalog = registrationCatalog.length > 0;
  const groupMap = new Map(registrationCatalog.map((item) => [String(item.id), item]));

  const profileInputs = Array.from(form.querySelectorAll('input[name="registration_profile"]'));
  const otherTypeInputs = Array.from(form.querySelectorAll('input[name="other_type_codes"]'));
  const dependentToggle = document.getElementById("include-dependent");
  const dependentToggleCard = document.getElementById("dependent-toggle-card");
  const otherTypePanel = form.querySelector("[data-other-type-panel]");
  const stepPanels = Array.from(form.querySelectorAll("[data-step-panel]"));
  const stepTriggers = Array.from(form.querySelectorAll("[data-step-trigger]"));
  const backButton = form.querySelector("[data-step-back]");
  const nextButton = form.querySelector("[data-step-next]");
  const submitButton = form.querySelector("[data-step-submit]");
  const progressFill = form.querySelector("[data-progress-fill]");
  const extraPayloadInput = document.getElementById("extra-dependents-payload");

  const extraIdentityList = form.querySelector("[data-extra-dependent-identity-list]");
  const extraAssignmentList = form.querySelector("[data-extra-dependent-assignment-list]");
  const extraMedicalList = form.querySelector("[data-extra-dependent-medical-list]");
  const addDependentButton = form.querySelector("[data-add-dependent]");

  const staticAssignments = {
    holder: buildStaticAssignmentConfig("holder", "holder-birthdate"),
    dependent: buildStaticAssignmentConfig("dependent", "dependent-birthdate"),
    student: buildStaticAssignmentConfig("student", "student-birthdate"),
    other: buildStaticAssignmentConfig("other", "other-birthdate"),
  };

  const dateInputs = Array.from(form.querySelectorAll("[data-date-mask]"));
  const kinshipSelects = Array.from(form.querySelectorAll("[data-kinship-select]"));

  let currentStep = normalizeStep(Number(form.dataset.initialStep || "1"));
  let dependentSequence = 0;
  let extraDependents = parseInitialDependents();

  function buildStaticAssignmentConfig(entityKey, birthInputId) {
    return {
      entityKey,
      categoryInput: form.querySelector(`[data-category-input="${entityKey}"]`),
      groupSelect: form.querySelector(`[data-group-select][data-entity-key="${entityKey}"]`),
      scheduleSelect: form.querySelector(`[data-schedule-select][data-entity-key="${entityKey}"]`),
      summary: form.querySelector(`[data-assignment-summary="${entityKey}"]`),
      suggestions: form.querySelector(`[data-suggestion-box="${entityKey}"]`),
      birthInput: birthInputId ? document.getElementById(birthInputId) : null,
    };
  }

  function normalizeStep(step) {
    if (Number.isNaN(step) || step < 1) {
      return 1;
    }
    return Math.min(step, 4);
  }

  function parseInitialDependents() {
    if (!extraPayloadInput || !extraPayloadInput.value) {
      return [];
    }

    try {
      const parsed = JSON.parse(extraPayloadInput.value);
      if (!Array.isArray(parsed)) {
        return [];
      }
      return parsed.map((item) => ({
        uid: String(++dependentSequence),
        full_name: item.full_name || "",
        cpf: item.cpf || "",
        birth_date: item.birth_date || "",
        email: item.email || "",
        phone: item.phone || "",
        password: item.password || "",
        password_confirm: item.password_confirm || "",
        kinship_type: item.kinship_type || "",
        kinship_other_label: item.kinship_other_label || "",
        class_category: item.class_category || "",
        class_group: item.class_group || "",
        class_schedule: item.class_schedule || "",
        blood_type: item.blood_type || "",
        allergies: item.allergies || "",
        injuries: item.previous_injuries || item.injuries || "",
        emergency_contact: item.emergency_contact || "",
      }));
    } catch (_error) {
      return [];
    }
  }

  function createEmptyDependent() {
    return {
      uid: String(++dependentSequence),
      full_name: "",
      cpf: "",
      birth_date: "",
      email: "",
      phone: "",
      password: "",
      password_confirm: "",
      kinship_type: "",
      kinship_other_label: "",
      class_category: "",
      class_group: "",
      class_schedule: "",
      blood_type: "",
      allergies: "",
      injuries: "",
      emergency_contact: "",
    };
  }

  function getCurrentProfile() {
    const selected = form.querySelector('input[name="registration_profile"]:checked');
    return selected ? selected.value : "holder";
  }

  function isDependentFlowActive() {
    return getCurrentProfile() === "holder" && Boolean(dependentToggle && dependentToggle.checked);
  }

  function allowsExtraDependents() {
    const profile = getCurrentProfile();
    return profile === "guardian" || isDependentFlowActive();
  }

  function setHiddenState(element, shouldHide) {
    if (!element) {
      return;
    }
    element.classList.toggle("is-hidden", shouldHide);
    element.hidden = shouldHide;
  }

  function syncChoiceStates() {
    form.querySelectorAll("[data-choice-card]").forEach((card) => {
      const input = card.querySelector("input");
      card.classList.toggle("is-selected", Boolean(input && input.checked));
    });
    form.querySelectorAll("[data-pill-choice]").forEach((card) => {
      const input = card.querySelector("input");
      card.classList.toggle("is-selected", Boolean(input && input.checked));
    });
    if (dependentToggleCard) {
      dependentToggleCard.classList.toggle("is-active", Boolean(dependentToggle && dependentToggle.checked));
    }
  }

  function syncFlowSections() {
    const profile = getCurrentProfile();
    const visibleKeys = new Set();

    if (profile === "holder") {
      visibleKeys.add("holder-data");
      visibleKeys.add("holder-assignment");
      visibleKeys.add("holder-medical");
      if (isDependentFlowActive()) {
        visibleKeys.add("holder-primary-dependent-data");
        visibleKeys.add("holder-primary-dependent-assignment");
        visibleKeys.add("holder-primary-dependent-medical");
        visibleKeys.add("extra-dependents-data");
        visibleKeys.add("extra-dependents-assignment");
        visibleKeys.add("extra-dependents-medical");
      }
    } else if (profile === "guardian") {
      visibleKeys.add("guardian-data");
      visibleKeys.add("guardian-primary-dependent-data");
      visibleKeys.add("guardian-primary-dependent-assignment");
      visibleKeys.add("guardian-primary-dependent-medical");
      visibleKeys.add("extra-dependents-data");
      visibleKeys.add("extra-dependents-assignment");
      visibleKeys.add("extra-dependents-medical");
    } else {
      visibleKeys.add("other-data");
      visibleKeys.add("other-assignment");
    }

    form.querySelectorAll("[data-flow-section]").forEach((section) => {
      setHiddenState(section, !visibleKeys.has(section.dataset.flowSection));
    });

    setHiddenState(dependentToggleCard, profile !== "holder");
    if (dependentToggleCard && profile !== "holder" && dependentToggle) {
      dependentToggle.checked = false;
    }
    setHiddenState(otherTypePanel, profile !== "other");
  }

  function syncSteps() {
    stepPanels.forEach((panel) => {
      setHiddenState(panel, Number(panel.dataset.stepPanel) !== currentStep);
    });

    stepTriggers.forEach((trigger) => {
      const step = Number(trigger.dataset.stepTrigger);
      trigger.classList.toggle("is-active", step === currentStep);
      trigger.classList.toggle("is-complete", step < currentStep);
    });

    if (progressFill) {
      progressFill.style.width = `${((currentStep - 1) / 3) * 100}%`;
    }

    setHiddenState(backButton, currentStep === 1);
    setHiddenState(nextButton, currentStep === 4);
    setHiddenState(submitButton, currentStep !== 4);
  }

  function handleDateMask(input) {
    const digits = input.value.replace(/\D/g, "").slice(0, 8);
    const parts = [];
    if (digits.length > 0) parts.push(digits.slice(0, 2));
    if (digits.length > 2) parts.push(digits.slice(2, 4));
    if (digits.length > 4) parts.push(digits.slice(4, 8));
    input.value = parts.join("/");
  }

  function parseBirthDate(rawValue) {
    if (!rawValue || !/^\d{2}\/\d{2}\/\d{4}$/.test(rawValue)) {
      return null;
    }
    const [day, month, year] = rawValue.split("/").map(Number);
    return new Date(year, month - 1, day);
  }

  function resolveAgeCategory(rawBirthDate) {
    const birthDate = parseBirthDate(rawBirthDate);
    if (!birthDate) {
      return "Categoria IBJJF não calculada";
    }

    const today = new Date();
    let age = today.getFullYear() - birthDate.getFullYear();
    const hasBirthday = today.getMonth() > birthDate.getMonth() || (today.getMonth() === birthDate.getMonth() && today.getDate() >= birthDate.getDate());
    if (!hasBirthday) {
      age -= 1;
    }

    const category = ibjjfCategories.find((item) => {
      if (age < item.minimum_age) {
        return false;
      }
      if (item.maximum_age === null) {
        return true;
      }
      return age <= item.maximum_age;
    });

    return category ? category.display_name : "Categoria IBJJF não calculada";
  }

  function buildScheduleOptions(select, schedules, selectedValue) {
    select.innerHTML = '<option value="">Selecione</option>';
    schedules.forEach((schedule) => {
      const option = document.createElement("option");
      option.value = String(schedule.id);
      option.textContent = `${schedule.weekday_display} · ${schedule.start_time}`;
      if (String(schedule.id) === String(selectedValue || "")) {
        option.selected = true;
      }
      select.appendChild(option);
    });
  }

  function renderAssignmentSummary(summaryNode, suggestionNode, groupId, scheduleId, birthDateValue) {
    if (!summaryNode || !suggestionNode) {
      return;
    }

    const group = groupMap.get(String(groupId || ""));
    const schedule = group ? group.schedules.find((item) => String(item.id) === String(scheduleId || "")) : null;

    if (!group) {
      summaryNode.innerHTML = '<div class="empty-state-box empty-state-box-compact"><p>Selecione a turma para visualizar o resumo.</p></div>';
      suggestionNode.innerHTML = "";
      return;
    }

    summaryNode.innerHTML = `
      <div class="assignment-summary-grid">
        <div><span class="info-summary-label">Turma</span><p class="info-summary-value">${group.category_name || group.audience_display}</p></div>
        <div><span class="info-summary-label">Professor</span><p class="info-summary-value">${group.teacher_name || 'Não definido'}</p></div>
        <div><span class="info-summary-label">Horário</span><p class="info-summary-value">${schedule ? `${schedule.weekday_display} · ${schedule.start_time}` : 'Selecione o horário'}</p></div>
        <div><span class="info-summary-label">Categoria IBJJF</span><p class="info-summary-value">${resolveAgeCategory(birthDateValue)}</p></div>
      </div>`;

    const suggestedGroups = registrationCatalog.filter((item) => item.id !== group.id && (item.category_id === group.category_id || item.audience === group.audience)).slice(0, 3);
    if (!suggestedGroups.length) {
      suggestionNode.innerHTML = "";
      return;
    }

    suggestionNode.innerHTML = `
      <strong>Outras opções disponíveis</strong>
      <ul class="suggestion-list">${suggestedGroups.map((item) => {
        const firstSchedule = item.schedules[0];
        const scheduleLabel = firstSchedule ? `${firstSchedule.weekday_display} · ${firstSchedule.start_time}` : "Sem horário ativo";
        return `<li>${item.category_name || item.audience_display} · ${scheduleLabel}</li>`;
      }).join("")}</ul>`;
  }

  function syncStaticAssignment(config) {
    if (!config.groupSelect || !config.scheduleSelect) {
      return;
    }

    const group = groupMap.get(String(config.groupSelect.value || ""));
    const selectedSchedule = config.scheduleSelect.dataset.selectedValue || config.scheduleSelect.value;
    buildScheduleOptions(config.scheduleSelect, group ? group.schedules : [], selectedSchedule);

    if (group && config.categoryInput) {
      config.categoryInput.value = group.category_id || "";
    } else if (config.categoryInput) {
      config.categoryInput.value = "";
    }

    renderAssignmentSummary(
      config.summary,
      config.suggestions,
      config.groupSelect.value,
      config.scheduleSelect.value,
      config.birthInput ? config.birthInput.value : ""
    );

    config.scheduleSelect.dataset.selectedValue = config.scheduleSelect.value;
  }

  function serializeDependents() {
    if (extraPayloadInput) {
      extraPayloadInput.value = JSON.stringify(extraDependents.map((dependent) => ({
        full_name: dependent.full_name,
        cpf: dependent.cpf,
        birth_date: dependent.birth_date,
        email: dependent.email,
        phone: dependent.phone,
        password: dependent.password,
        password_confirm: dependent.password_confirm,
        kinship_type: dependent.kinship_type,
        kinship_other_label: dependent.kinship_other_label,
        class_category: dependent.class_category,
        class_group: dependent.class_group,
        class_schedule: dependent.class_schedule,
        blood_type: dependent.blood_type,
        allergies: dependent.allergies,
        injuries: dependent.injuries,
        emergency_contact: dependent.emergency_contact,
      })));
    }
  }

  function bindDependentField(card, dependent, fieldName) {
    const field = card.querySelector(`[data-dependent-field="${fieldName}"]`);
    if (!field) {
      return;
    }
    field.value = dependent[fieldName] || "";
    field.addEventListener("input", () => {
      dependent[fieldName] = field.value;
      if (field.hasAttribute("data-date-mask")) {
        handleDateMask(field);
        dependent[fieldName] = field.value;
      }
      serializeDependents();
      syncAllAssignments();
    });
    field.addEventListener("change", () => {
      dependent[fieldName] = field.value;
      serializeDependents();
      syncAllAssignments();
    });
  }

  function renderDependentIdentityCards() {
    if (!extraIdentityList) {
      return;
    }
    extraIdentityList.innerHTML = "";
    const template = document.getElementById("extra-dependent-identity-template");
    extraDependents.forEach((dependent, index) => {
      const fragment = template.content.cloneNode(true);
      const card = fragment.querySelector("[data-dependent-card]");
      card.dataset.dependentUid = dependent.uid;
      fragment.querySelector("[data-dependent-number]").textContent = String(index + 1);
      ["full_name", "cpf", "birth_date", "phone", "email", "kinship_type", "kinship_other_label", "password", "password_confirm"].forEach((fieldName) => bindDependentField(card, dependent, fieldName));
      const kinshipSelect = card.querySelector("[data-kinship-select-dynamic]");
      const otherField = card.querySelector("[data-dependent-kinship-other]");
      const syncKinship = () => setHiddenState(otherField, kinshipSelect.value !== "other");
      kinshipSelect.addEventListener("change", syncKinship);
      syncKinship();
      card.querySelector("[data-remove-dependent]").addEventListener("click", () => {
        extraDependents = extraDependents.filter((item) => item.uid !== dependent.uid);
        renderExtraDependents();
      });
      extraIdentityList.appendChild(fragment);
    });
  }

  function renderDependentAssignmentCards() {
    if (!extraAssignmentList) {
      return;
    }
    extraAssignmentList.innerHTML = "";
    const template = document.getElementById("extra-dependent-assignment-template");

    extraDependents.forEach((dependent, index) => {
      const fragment = template.content.cloneNode(true);
      const card = fragment.querySelector("[data-dependent-card]");
      fragment.querySelector("[data-dependent-number]").textContent = String(index + 1);
      const groupSelect = card.querySelector("[data-group-select-dynamic]");
      const scheduleSelect = card.querySelector("[data-schedule-select-dynamic]");
      registrationCatalog.forEach((group) => {
        const option = document.createElement("option");
        option.value = String(group.id);
        option.textContent = `${group.category_name || group.audience_display} · ${group.display_name}`;
        if (String(group.id) === String(dependent.class_group || "")) {
          option.selected = true;
        }
        groupSelect.appendChild(option);
      });
      const applyScheduleOptions = () => {
        const group = groupMap.get(String(groupSelect.value || ""));
        buildScheduleOptions(scheduleSelect, group ? group.schedules : [], dependent.class_schedule);
        dependent.class_group = groupSelect.value;
        dependent.class_category = group ? String(group.category_id || "") : "";
        dependent.class_schedule = scheduleSelect.value;
        renderAssignmentSummary(card.querySelector("[data-dependent-summary]"), card.querySelector("[data-dependent-suggestions]"), dependent.class_group, dependent.class_schedule, dependent.birth_date);
        serializeDependents();
      };
      groupSelect.addEventListener("change", applyScheduleOptions);
      scheduleSelect.addEventListener("change", () => {
        dependent.class_schedule = scheduleSelect.value;
        renderAssignmentSummary(card.querySelector("[data-dependent-summary]"), card.querySelector("[data-dependent-suggestions]"), dependent.class_group, dependent.class_schedule, dependent.birth_date);
        serializeDependents();
      });
      applyScheduleOptions();
      extraAssignmentList.appendChild(fragment);
    });
  }

  function renderDependentMedicalCards() {
    if (!extraMedicalList) {
      return;
    }
    extraMedicalList.innerHTML = "";
    const template = document.getElementById("extra-dependent-medical-template");
    extraDependents.forEach((dependent, index) => {
      const fragment = template.content.cloneNode(true);
      const card = fragment.querySelector("[data-dependent-card]");
      fragment.querySelector("[data-dependent-number]").textContent = String(index + 1);
      ["blood_type", "allergies", "injuries", "emergency_contact"].forEach((fieldName) => bindDependentField(card, dependent, fieldName));
      extraMedicalList.appendChild(fragment);
    });
  }

  function renderExtraDependents() {
    renderDependentIdentityCards();
    renderDependentAssignmentCards();
    renderDependentMedicalCards();
    serializeDependents();
  }

  function syncAllAssignments() {
    Object.values(staticAssignments).forEach((config) => syncStaticAssignment(config));
    renderDependentAssignmentCards();
  }

  function validateStepOne() {
    if (getCurrentProfile() !== "other" || otherTypeInputs.length === 0) {
      return true;
    }
    const hasChoice = otherTypeInputs.some((input) => input.checked);
    if (!hasChoice) {
      otherTypePanel.setAttribute("data-invalid", "true");
      return false;
    }
    otherTypePanel.removeAttribute("data-invalid");
    return true;
  }

  function validateRequiredField(name) {
    const field = form.querySelector(`[name="${name}"]`);
    if (!field || field.closest(".is-hidden")) {
      return true;
    }
    const valid = Boolean(field.value && field.value.trim());
    if (!valid) {
      field.setAttribute("aria-invalid", "true");
    } else {
      field.removeAttribute("aria-invalid");
    }
    return valid;
  }

  function validateDependentsIdentity() {
    return extraDependents.every((dependent) => dependent.full_name && dependent.cpf && dependent.birth_date && dependent.password && dependent.password_confirm && dependent.kinship_type && (dependent.kinship_type !== "other" || dependent.kinship_other_label));
  }

  function validateDependentsAssignment() {
    if (!hasCatalog) {
      return true;
    }
    return extraDependents.every((dependent) => dependent.class_group && dependent.class_schedule);
  }

  function validateStepTwo() {
    const profile = getCurrentProfile();
    let requiredFields = [];
    if (profile === "holder") {
      requiredFields = ["holder_name", "holder_cpf", "holder_birthdate", "holder_password", "holder_password_confirm"];
      if (isDependentFlowActive()) {
        requiredFields.push("dependent_name", "dependent_cpf", "dependent_birthdate", "dependent_password", "dependent_password_confirm", "dependent_kinship_type");
      }
    } else if (profile === "guardian") {
      requiredFields = ["guardian_name", "guardian_cpf", "guardian_password", "guardian_password_confirm", "student_name", "student_cpf", "student_birthdate", "student_password", "student_password_confirm", "student_kinship_type"];
    } else {
      requiredFields = ["other_name", "other_cpf", "other_birthdate", "other_password", "other_password_confirm"];
    }
    const staticValid = requiredFields.every((fieldName) => validateRequiredField(fieldName));
    const dynamicValid = !allowsExtraDependents() || validateDependentsIdentity();
    return staticValid && dynamicValid;
  }

  function validateStepThree() {
    if (!hasCatalog) {
      return true;
    }
    const profile = getCurrentProfile();
    const assignments = [];
    if (profile === "holder") {
      assignments.push(staticAssignments.holder);
      if (isDependentFlowActive()) {
        assignments.push(staticAssignments.dependent);
      }
    } else if (profile === "guardian") {
      assignments.push(staticAssignments.student);
    } else {
      return true;
    }
    const staticValid = assignments.every((config) => config.groupSelect && config.groupSelect.value && config.scheduleSelect && config.scheduleSelect.value);
    const dynamicValid = !allowsExtraDependents() || validateDependentsAssignment();
    return staticValid && dynamicValid;
  }

  function validateCurrentStep() {
    if (currentStep === 1) return validateStepOne();
    if (currentStep === 2) return validateStepTwo();
    if (currentStep === 3) return validateStepThree();
    return true;
  }

  function updateWizard() {
    syncFlowSections();
    syncChoiceStates();
    syncSteps();
    syncAllAssignments();
  }

  function goToStep(step) {
    currentStep = normalizeStep(step);
    updateWizard();
    form.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  profileInputs.forEach((input) => input.addEventListener("change", updateWizard));
  otherTypeInputs.forEach((input) => input.addEventListener("change", syncChoiceStates));
  if (dependentToggle) {
    dependentToggle.addEventListener("change", updateWizard);
  }
  if (addDependentButton) {
    addDependentButton.addEventListener("click", () => {
      extraDependents.push(createEmptyDependent());
      renderExtraDependents();
      updateWizard();
    });
  }

  stepTriggers.forEach((trigger) => {
    trigger.addEventListener("click", () => {
      const step = Number(trigger.dataset.stepTrigger);
      if (step > currentStep && !validateCurrentStep()) {
        return;
      }
      goToStep(step);
    });
  });
  if (backButton) {
    backButton.addEventListener("click", () => goToStep(currentStep - 1));
  }
  if (nextButton) {
    nextButton.addEventListener("click", () => {
      if (!validateCurrentStep()) {
        return;
      }
      goToStep(currentStep + 1);
    });
  }

  Object.values(staticAssignments).forEach((config) => {
    if (!config.groupSelect || !config.scheduleSelect) {
      return;
    }
    config.groupSelect.addEventListener("change", () => syncStaticAssignment(config));
    config.scheduleSelect.addEventListener("change", () => syncStaticAssignment(config));
    if (config.birthInput) {
      config.birthInput.addEventListener("input", () => syncStaticAssignment(config));
    }
  });

  kinshipSelects.forEach((select) => {
    const otherTarget = document.getElementById(select.dataset.otherTarget || "");
    const sync = () => setHiddenState(otherTarget, select.value !== "other");
    select.addEventListener("change", sync);
    sync();
  });

  dateInputs.forEach((input) => input.addEventListener("input", () => handleDateMask(input)));

  form.querySelectorAll("input, select, textarea").forEach((field) => {
    field.addEventListener("input", () => field.removeAttribute("aria-invalid"));
  });

  renderExtraDependents();
  updateWizard();
})();
