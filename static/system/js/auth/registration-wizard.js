(function () {
  var form = document.getElementById("client-registration-form");
  if (!form) {
    return;
  }

  var registrationCatalogNode = document.getElementById("registration-catalog");
  var ibjjfCatalogNode = document.getElementById("ibjjf-age-categories");
  var registrationCatalog = registrationCatalogNode ? JSON.parse(registrationCatalogNode.textContent) : [];
  var ibjjfCategories = ibjjfCatalogNode ? JSON.parse(ibjjfCatalogNode.textContent) : [];
  var hasCatalog = registrationCatalog.length > 0;
  var groupMap = new Map(registrationCatalog.map(function (item) { return [String(item.id), item]; }));

  var profileInputs = Array.from(form.querySelectorAll('input[name="registration_profile"]'));
  var otherTypeSelect = form.querySelector('select[name="other_type_code"]');
  var dependentToggle = document.getElementById("include-dependent");
  var dependentToggleCard = form.querySelector("[data-dependent-toggle-card]");
  var otherTypePanel = form.querySelector("[data-other-type-panel]");
  var stepPanels = Array.from(form.querySelectorAll("[data-step-panel]"));
  var stepTriggers = Array.from(form.querySelectorAll("[data-step-trigger]"));
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
  var draftMessage = form.querySelector("[data-registration-draft-message]");
  var draftClearButton = form.querySelector("[data-registration-draft-clear]");
  var draftKey = "lv-register-draft-v1";
  var draftTtlMs = 30 * 60 * 1000;
  var canRestoreDraft = form.dataset.canRestoreDraft === "true";
  var draftSaveTimeout = null;
  var defaultDraftMessage = "Se a internet oscilar ou a tela recarregar, este dispositivo mantém um rascunho curto do cadastro. Senhas e dados médicos não são armazenados.";
  var restoredDraftMessage = "Recuperamos um rascunho recente neste dispositivo. Confira os dados antes de continuar. Senhas e dados médicos não são armazenados.";
  var clearedDraftMessage = "O rascunho local foi removido deste dispositivo. Os dados visíveis na tela continuam abertos até você sair.";

  var staticSelections = {
    holder: buildStaticSelectionConfig("holder", "holder-birthdate"),
    dependent: buildStaticSelectionConfig("dependent", "dependent-birthdate"),
    student: buildStaticSelectionConfig("student", "student-birthdate"),
  };

  var currentStep = normalizeStep(Number(form.dataset.initialStep || "1"));
  var dependentSequence = 0;
  var extraDependents = parseInitialDependents();

  function buildStaticSelectionConfig(entityKey, birthInputId) {
    return {
      entityKey: entityKey,
      inputName: entityKey + "_class_groups",
      container: form.querySelector('[data-class-group-options="' + entityKey + '"]'),
      summary: form.querySelector('[data-class-group-summary="' + entityKey + '"]'),
      birthInput: birthInputId ? document.getElementById(birthInputId) : null,
      sexInput: form.querySelector('[data-biological-sex-input="' + entityKey + '"]'),
    };
  }

  function normalizeStep(step) {
    if (Number.isNaN(step) || step < 1) {
      return 1;
    }
    var maxStep = isOtherProfile() ? 2 : 4;
    return Math.min(step, maxStep);
  }

  function parseInitialDependents() {
    if (!extraPayloadInput || !extraPayloadInput.value) {
      return [];
    }

    try {
      var parsed = JSON.parse(extraPayloadInput.value);
      if (!Array.isArray(parsed)) {
        return [];
      }
      return parsed.map(function (item) {
        dependentSequence += 1;
        return {
          uid: String(dependentSequence),
          full_name: item.full_name || "",
          cpf: item.cpf || "",
          birth_date: item.birth_date || "",
          biological_sex: item.biological_sex || "",
          email: item.email || "",
          phone: item.phone || "",
          password: item.password || "",
          password_confirm: item.password_confirm || "",
          kinship_type: item.kinship_type || "",
          kinship_other_label: item.kinship_other_label || "",
          class_groups: Array.isArray(item.class_groups) ? item.class_groups.map(String) : [],
          blood_type: item.blood_type || "",
          allergies: item.allergies || "",
          injuries: item.previous_injuries || item.injuries || "",
          emergency_contact: item.emergency_contact || "",
        };
      });
    } catch (_error) {
      return [];
    }
  }

  function createEmptyDependent() {
    dependentSequence += 1;
    return {
      uid: String(dependentSequence),
      full_name: "",
      cpf: "",
      birth_date: "",
      biological_sex: "",
      email: "",
      phone: "",
      password: "",
      password_confirm: "",
      kinship_type: "",
      kinship_other_label: "",
      class_groups: [],
      blood_type: "",
      allergies: "",
      injuries: "",
      emergency_contact: "",
    };
  }

  function isSensitiveDraftField(fieldName) {
    return !fieldName
      || fieldName === "csrfmiddlewaretoken"
      || fieldName === "extra_dependents_payload"
      || /password/i.test(fieldName)
      || /(blood_type|allergies|injuries|emergency_contact)/i.test(fieldName);
  }

  function setDraftMessage(message, isRestored) {
    if (!draftMessage) {
      return;
    }
    draftMessage.textContent = message;
    var note = draftMessage.closest("[data-registration-draft-note]");
    if (note) {
      note.classList.toggle("is-restored", Boolean(isRestored));
    }
  }

  function syncDraftButtonVisibility() {
    if (!draftClearButton) {
      return;
    }
    draftClearButton.hidden = !Boolean(readStoredDraft());
  }

  function readStoredDraft() {
    try {
      var rawDraft = window.localStorage.getItem(draftKey);
      if (!rawDraft) {
        return null;
      }
      var parsed = JSON.parse(rawDraft);
      if (!parsed || typeof parsed !== "object" || !parsed.savedAt) {
        window.localStorage.removeItem(draftKey);
        return null;
      }
      if (Date.now() - parsed.savedAt > draftTtlMs) {
        window.localStorage.removeItem(draftKey);
        return null;
      }
      return parsed;
    } catch (_error) {
      return null;
    }
  }

  function clearStoredDraft() {
    try {
      window.localStorage.removeItem(draftKey);
    } catch (_error) {
      return;
    }
  }

  function collectDraftFields() {
    var values = {};
    form.querySelectorAll("input[name], select[name], textarea[name]").forEach(function (field) {
      if (isSensitiveDraftField(field.name)) {
        return;
      }
      if (field.type === "radio") {
        if (field.checked) {
          values[field.name] = field.value;
        }
        return;
      }
      if (field.type === "checkbox") {
        if (field.name === "include_dependent") {
          values[field.name] = field.checked;
          return;
        }
        if (!Array.isArray(values[field.name])) {
          values[field.name] = [];
        }
        if (field.checked) {
          values[field.name].push(field.value);
        }
        return;
      }
      if (field.tagName === "SELECT" && field.multiple) {
        values[field.name] = Array.from(field.selectedOptions).map(function (option) {
          return option.value;
        });
        return;
      }
      values[field.name] = field.value;
    });
    return values;
  }

  function collectDraftDependents() {
    return extraDependents.map(function (dependent, index) {
      return {
        uid: dependent.uid || String(index + 1),
        full_name: dependent.full_name,
        cpf: dependent.cpf,
        birth_date: dependent.birth_date,
        biological_sex: dependent.biological_sex,
        email: dependent.email,
        phone: dependent.phone,
        kinship_type: dependent.kinship_type,
        kinship_other_label: dependent.kinship_other_label,
        class_groups: Array.isArray(dependent.class_groups) ? dependent.class_groups : [],
      };
    });
  }

  function saveDraft() {
    try {
      window.localStorage.setItem(draftKey, JSON.stringify({
        savedAt: Date.now(),
        currentStep: currentStep,
        fields: collectDraftFields(),
        extraDependents: collectDraftDependents(),
      }));
      syncDraftButtonVisibility();
    } catch (_error) {
      return;
    }
  }

  function queueDraftSave() {
    window.clearTimeout(draftSaveTimeout);
    draftSaveTimeout = window.setTimeout(saveDraft, 180);
  }

  function restoreFieldValue(fieldName, value) {
    var fieldSelector = '[name="' + fieldName.replace(/"/g, '\\"') + '"]';
    var fields = Array.from(form.querySelectorAll(fieldSelector));
    if (!fields.length) {
      return;
    }
    var sampleField = fields[0];
    if (sampleField.type === "radio") {
      fields.forEach(function (field) {
        field.checked = String(value) === String(field.value);
      });
      return;
    }
    if (sampleField.type === "checkbox") {
      if (fieldName === "include_dependent") {
        sampleField.checked = Boolean(value);
        return;
      }
      var values = Array.isArray(value) ? value.map(String) : [String(value)];
      fields.forEach(function (field) {
        field.checked = values.includes(String(field.value));
      });
      return;
    }
    if (sampleField.tagName === "SELECT" && sampleField.multiple) {
      Array.from(sampleField.options).forEach(function (option) {
        option.selected = Array.isArray(value) && value.map(String).includes(option.value);
      });
      return;
    }
    sampleField.value = value;
  }

  function restoreStoredDraft() {
    var storedDraft = readStoredDraft();
    if (!storedDraft) {
      return false;
    }
    var fieldValues = storedDraft.fields || {};
    Object.keys(fieldValues).forEach(function (fieldName) {
      restoreFieldValue(fieldName, fieldValues[fieldName]);
    });
    extraDependents = Array.isArray(storedDraft.extraDependents)
      ? storedDraft.extraDependents.map(function (dependent, index) {
          return {
            uid: dependent.uid || String(index + 1),
            full_name: dependent.full_name || "",
            cpf: dependent.cpf || "",
            birth_date: dependent.birth_date || "",
            biological_sex: dependent.biological_sex || "",
            email: dependent.email || "",
            phone: dependent.phone || "",
            password: "",
            password_confirm: "",
            kinship_type: dependent.kinship_type || "",
            kinship_other_label: dependent.kinship_other_label || "",
            class_groups: Array.isArray(dependent.class_groups) ? dependent.class_groups.map(String) : [],
            blood_type: "",
            allergies: "",
            injuries: "",
            emergency_contact: "",
          };
        })
      : [];
    dependentSequence = extraDependents.length;
    currentStep = normalizeStep(Number(storedDraft.currentStep || currentStep));
    return true;
  }

  function getCurrentProfile() {
    var selected = form.querySelector('input[name="registration_profile"]:checked');
    return selected ? selected.value : "holder";
  }

  function isOtherProfile() {
    return getCurrentProfile() === "other";
  }

  function isDependentFlowActive() {
    return getCurrentProfile() === "holder" && Boolean(dependentToggle && dependentToggle.checked);
  }

  function allowsExtraDependents() {
    var profile = getCurrentProfile();
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
    form.querySelectorAll("[data-choice-card]").forEach(function (card) {
      var input = card.querySelector("input");
      card.classList.toggle("is-selected", Boolean(input && input.checked));
    });
    if (dependentToggleCard) {
      dependentToggleCard.classList.toggle("is-active", Boolean(dependentToggle && dependentToggle.checked));
    }
  }

  function syncFlowSections() {
    var profile = getCurrentProfile();
    var visibleKeys = new Set();

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
      if (isDependentFlowActive()) {
        visibleKeys.add("guardian-primary-dependent-data");
        visibleKeys.add("guardian-primary-dependent-assignment");
        visibleKeys.add("guardian-primary-dependent-medical");
        visibleKeys.add("extra-dependents-data");
        visibleKeys.add("extra-dependents-assignment");
        visibleKeys.add("extra-dependents-medical");
      }
    } else if (profile === "other") {
      visibleKeys.add("other-data");
    }

    form.querySelectorAll("[data-flow-section]").forEach(function (section) {
      setHiddenState(section, !visibleKeys.has(section.dataset.flowSection));
    });

    setHiddenState(dependentToggleCard, profile !== "holder");
    if (dependentToggleCard && profile !== "holder" && dependentToggle) {
      dependentToggle.checked = false;
    }
    setHiddenState(otherTypePanel, profile !== "other");
  }

  function syncSteps() {
    var maxStep = isOtherProfile() ? 2 : 4;
    var stepsCount = isOtherProfile() ? 2 : 4;
    var stepLabels = form.querySelectorAll("[data-step-label]");
    stepLabels.forEach(function (label) {
      label.textContent = "Etapa " + currentStep + " de " + maxStep;
    });

    stepPanels.forEach(function (panel) {
      var panelStep = Number(panel.dataset.stepPanel);
      setHiddenState(panel, panelStep > maxStep || panelStep !== currentStep);
    });

    stepTriggers.forEach(function (trigger) {
      var step = Number(trigger.dataset.stepTrigger);
      var isOptional = trigger.hasAttribute("data-step-trigger-optional");
      if (isOptional) {
        trigger.classList.toggle("is-visible", !isOtherProfile());
      }
      trigger.classList.toggle("is-active", step === currentStep && step <= maxStep);
      trigger.classList.toggle("is-complete", step < currentStep && step <= maxStep);
      trigger.hidden = step > maxStep;
    });

    if (progressFill) {
      var totalSteps = stepsCount - 1;
      var progress = totalSteps > 0 ? ((currentStep - 1) / totalSteps) * 100 : 0;
      progressFill.style.width = progress + "%";
    }

    setHiddenState(backButton, currentStep === 1);
    setHiddenState(nextButton, currentStep === maxStep);
    setHiddenState(submitButton, currentStep === maxStep);
  }

  function getSubtitleText() {
    var profile = getCurrentProfile();
    if (profile === "other") {
      return "Preencha os dados do cadastro.";
    }
    if (profile === "guardian" && !isDependentFlowActive()) {
      return "Preencha os dados do responsável.";
    }
    var hasDependents = isDependentFlowActive();
    if (hasDependents) {
      return "Preencha os dados do responsável e do dependente.";
    }
    return "Preencha o cadastro em etapas curtas e finalize com turmas liberadas e prontuário.";
  }

  function syncSubtitle() {
    var subtitle = form.querySelector("[data-registration-subtitle]");
    if (subtitle) {
      subtitle.textContent = getSubtitleText();
    }
  }

  function handleDateMask(input) {
    var digits = input.value.replace(/\D/g, "").slice(0, 8);
    var parts = [];
    if (digits.length > 0) parts.push(digits.slice(0, 2));
    if (digits.length > 2) parts.push(digits.slice(2, 4));
    if (digits.length > 4) parts.push(digits.slice(4, 8));
    input.value = parts.join("/");
  }

  function parseBirthDate(rawValue) {
    if (!rawValue || !/^\d{2}\/\d{2}\/\d{4}$/.test(rawValue)) {
      return null;
    }
    var parts = rawValue.split("/").map(Number);
    return new Date(parts[2], parts[1] - 1, parts[0]);
  }

  function getAgeFromBirthDate(rawValue) {
    var birthDate = parseBirthDate(rawValue);
    if (!birthDate) {
      return null;
    }
    var today = new Date();
    var age = today.getFullYear() - birthDate.getFullYear();
    var hasBirthday = today.getMonth() > birthDate.getMonth() || (today.getMonth() === birthDate.getMonth() && today.getDate() >= birthDate.getDate());
    return hasBirthday ? age : age - 1;
  }

  function resolveAgeCategory(rawBirthDate) {
    var age = getAgeFromBirthDate(rawBirthDate);
    if (age === null) {
      return null;
    }
    return ibjjfCategories.find(function (item) {
      if (age < item.minimum_age) {
        return false;
      }
      if (item.maximum_age === null) {
        return true;
      }
      return age <= item.maximum_age;
    }) || null;
  }

  function getGroupEligibility(group, birthDateValue, biologicalSex) {
    var category = resolveAgeCategory(birthDateValue);
    if (!category) {
      return {
        allowed: false,
        reason: "Informe a data de nascimento para liberar as turmas compatíveis.",
      };
    }
    if (group.category_audience === "women") {
      if (biologicalSex !== "female") {
        return {
          allowed: false,
          reason: "A turma feminina aceita apenas alunas do sexo biológico feminino.",
        };
      }
      if (category.audience !== "adult") {
        return {
          allowed: false,
          reason: "A turma feminina está liberada apenas para alunas adultas.",
        };
      }
      return { allowed: true, reason: "" };
    }
    if (category.audience !== group.category_audience) {
      return {
        allowed: false,
        reason: "Turma incompatível com a faixa etária calculada.",
      };
    }
    return { allowed: true, reason: "" };
  }

  function getEligibleGroups(birthDateValue, biologicalSex) {
    return registrationCatalog.filter(function (group) {
      return getGroupEligibility(group, birthDateValue, biologicalSex).allowed;
    });
  }

  function getScheduleLabels(group) {
    return (group.schedules || []).map(function (schedule) {
      return schedule.weekday_display + " · " + schedule.start_time;
    });
  }

  function getSelectedValues(container) {
    if (!container) {
      return [];
    }
    var checkedValues = Array.from(container.querySelectorAll('input[type="checkbox"]:checked')).map(function (input) {
      return String(input.value);
    });
    if (checkedValues.length) {
      return checkedValues;
    }
    return (container.dataset.selectedValues || "").split(",").filter(Boolean);
  }

  function storeSelectedValues(container, values) {
    if (!container) {
      return;
    }
    container.dataset.selectedValues = values.join(",");
  }

  function buildEmptyGroupMessage(message) {
    return '<div class="empty-state-box empty-state-box-compact"><p>' + message + '</p></div>';
  }

  function createClassOptionCard(params) {
    var label = document.createElement("label");
    label.className = "class-option-card" + (params.checked ? " is-selected" : "");
    label.dataset.groupId = String(params.group.id);

    var input = document.createElement("input");
    input.type = "checkbox";
    input.value = String(params.group.id);
    if (params.inputName) {
      input.name = params.inputName;
    }
    input.checked = params.checked;

    var copy = document.createElement("span");
    copy.className = "class-option-copy";

    var eyebrow = document.createElement("span");
    eyebrow.className = "class-option-eyebrow";
    eyebrow.textContent = params.group.category_name || "Sem categoria";

    var title = document.createElement("span");
    title.className = "class-option-title";
    title.textContent = params.group.display_name;

    var description = document.createElement("span");
    description.className = "class-option-description";
    description.textContent = params.group.teacher_name ? ("Professor: " + params.group.teacher_name) : "Professor principal não definido.";

    var detail = document.createElement("span");
    detail.className = "class-option-detail";
    detail.textContent = "Horários ativos: " + getScheduleLabels(params.group).join(", ");

    var check = document.createElement("span");
    check.className = "class-option-check";
    check.setAttribute("aria-hidden", "true");

    copy.appendChild(eyebrow);
    copy.appendChild(title);
    copy.appendChild(description);
    copy.appendChild(detail);

    label.appendChild(input);
    label.appendChild(copy);
    label.appendChild(check);

    input.addEventListener("change", function () {
      label.classList.toggle("is-selected", input.checked);
      params.onChange();
      queueDraftSave();
    });

    return label;
  }

  function renderSelectionSummary(summaryNode, selectedIds, birthDateValue) {
    if (!summaryNode) {
      return;
    }
    var selectedGroups = selectedIds.map(function (groupId) {
      return groupMap.get(String(groupId));
    }).filter(Boolean);
    if (!selectedGroups.length) {
      summaryNode.innerHTML = buildEmptyGroupMessage("Selecione ao menos uma turma para liberar todos os horários ativos compatíveis.");
      return;
    }

    var ageCategory = resolveAgeCategory(birthDateValue);
    summaryNode.innerHTML = "<div class=\"assignment-summary-grid\">"
      + (ageCategory ? "<div class=\"info-summary-block\"><span class=\"info-summary-label\">Categoria IBJJF</span><p class=\"info-summary-value\">" + ageCategory.display_name + "</p><p class=\"info-summary-meta\">As turmas abaixo ja respeitam essa faixa calculada.</p></div>" : "")
      + selectedGroups.map(function (group) {
        return "<div class=\"info-summary-block\"><span class=\"info-summary-label\">Turma liberada</span><p class=\"info-summary-value\">" + group.category_name + " · " + group.display_name + "</p><p class=\"info-summary-meta\">Horarios ativos: " + getScheduleLabels(group).join(", ") + "</p></div>";
      }).join("")
      + "</div>";
  }

  function markSelectionValidity(container, isValid) {
    if (!container) {
      return;
    }
    if (isValid) {
      container.removeAttribute("data-invalid");
      return;
    }
    container.setAttribute("data-invalid", "true");
  }

  function syncStaticSelectionSummary(config) {
    if (!config.container) {
      return;
    }
    var selectedIds = getSelectedValues(config.container);
    storeSelectedValues(config.container, selectedIds);
    renderSelectionSummary(
      config.summary,
      selectedIds,
      config.birthInput ? config.birthInput.value : ""
    );
  }

  function renderStaticSelection(config) {
    if (!config.container) {
      return;
    }
    var eligibleGroups = getEligibleGroups(
      config.birthInput ? config.birthInput.value : "",
      config.sexInput ? config.sexInput.value : ""
    );
    var selectedIds = getSelectedValues(config.container);
    var eligibleIds = new Set(eligibleGroups.map(function (group) { return String(group.id); }));
    selectedIds = selectedIds.filter(function (groupId) {
      return eligibleIds.has(String(groupId));
    });
    storeSelectedValues(config.container, selectedIds);
    config.container.innerHTML = "";

    if (!eligibleGroups.length) {
      config.container.innerHTML = buildEmptyGroupMessage("Nenhuma turma compatível foi encontrada para os dados informados até agora.");
      renderSelectionSummary(config.summary, [], config.birthInput ? config.birthInput.value : "");
      return;
    }

    eligibleGroups.forEach(function (group) {
      config.container.appendChild(
        createClassOptionCard({
          group: group,
          inputName: config.inputName,
          checked: selectedIds.includes(String(group.id)),
          onChange: function () {
            syncStaticSelectionSummary(config);
            markSelectionValidity(config.container, true);
          },
        })
      );
    });
    syncStaticSelectionSummary(config);
  }

  function serializeDependents() {
    if (!extraPayloadInput) {
      return;
    }
    extraPayloadInput.value = JSON.stringify(extraDependents.map(function (dependent) {
      return {
        full_name: dependent.full_name,
        cpf: dependent.cpf,
        birth_date: dependent.birth_date,
        biological_sex: dependent.biological_sex,
        email: dependent.email,
        phone: dependent.phone,
        password: dependent.password,
        password_confirm: dependent.password_confirm,
        kinship_type: dependent.kinship_type,
        kinship_other_label: dependent.kinship_other_label,
        class_groups: dependent.class_groups,
        blood_type: dependent.blood_type,
        allergies: dependent.allergies,
        injuries: dependent.injuries,
        emergency_contact: dependent.emergency_contact,
      };
    }));
  }

  function bindDependentField(card, dependent, fieldName) {
    var field = card.querySelector('[data-dependent-field="' + fieldName + '"]');
    if (!field) {
      return;
    }
    field.value = dependent[fieldName] || "";
    field.addEventListener("input", function () {
      dependent[fieldName] = field.value;
      if (field.hasAttribute("data-date-mask")) {
        handleDateMask(field);
        dependent[fieldName] = field.value;
      }
      serializeDependents();
      if (fieldName === "birth_date" || fieldName === "biological_sex") {
        renderDependentAssignmentCards();
      }
    });
    field.addEventListener("change", function () {
      dependent[fieldName] = field.value;
      serializeDependents();
      if (fieldName === "birth_date" || fieldName === "biological_sex") {
        renderDependentAssignmentCards();
      }
    });
  }

  function renderDependentIdentityCards() {
    if (!extraIdentityList) {
      return;
    }
    extraIdentityList.innerHTML = "";
    var template = document.getElementById("extra-dependent-identity-template");
    extraDependents.forEach(function (dependent, index) {
      var fragment = template.content.cloneNode(true);
      var card = fragment.querySelector("[data-dependent-card]");
      card.dataset.dependentUid = dependent.uid;
      fragment.querySelector("[data-dependent-number]").textContent = String(index + 1);
      ["full_name", "cpf", "birth_date", "biological_sex", "phone", "email", "kinship_type", "kinship_other_label", "password", "password_confirm"].forEach(function (fieldName) {
        bindDependentField(card, dependent, fieldName);
      });
      var kinshipSelect = card.querySelector("[data-kinship-select-dynamic]");
      var otherField = card.querySelector("[data-dependent-kinship-other]");
      var syncKinship = function () {
        setHiddenState(otherField, kinshipSelect.value !== "other");
      };
      kinshipSelect.addEventListener("change", syncKinship);
      syncKinship();
      card.querySelector("[data-remove-dependent]").addEventListener("click", function () {
        extraDependents = extraDependents.filter(function (item) {
          return item.uid !== dependent.uid;
        });
        renderExtraDependents();
        syncAllClassSelections();
        queueDraftSave();
      });
      extraIdentityList.appendChild(fragment);
    });
  }

  function renderDependentAssignmentCards() {
    if (!extraAssignmentList) {
      return;
    }
    extraAssignmentList.innerHTML = "";
    var template = document.getElementById("extra-dependent-assignment-template");

    extraDependents.forEach(function (dependent, index) {
      var fragment = template.content.cloneNode(true);
      var card = fragment.querySelector("[data-dependent-card]");
      var optionsContainer = fragment.querySelector("[data-dependent-class-groups]");
      var summaryNode = fragment.querySelector("[data-dependent-summary]");
      var eligibleGroups = getEligibleGroups(dependent.birth_date, dependent.biological_sex);
      var eligibleIds = new Set(eligibleGroups.map(function (group) { return String(group.id); }));

      fragment.querySelector("[data-dependent-number]").textContent = String(index + 1);
      dependent.class_groups = (dependent.class_groups || []).filter(function (groupId) {
        return eligibleIds.has(String(groupId));
      });

      if (!eligibleGroups.length) {
        optionsContainer.innerHTML = buildEmptyGroupMessage("Nenhuma turma compatível ficou disponível para este dependente.");
      } else {
        eligibleGroups.forEach(function (group) {
          optionsContainer.appendChild(
            createClassOptionCard({
              group: group,
              checked: dependent.class_groups.includes(String(group.id)),
              onChange: function () {
                dependent.class_groups = Array.from(card.querySelectorAll('input[type="checkbox"]:checked')).map(function (input) {
                  return String(input.value);
                });
                serializeDependents();
                renderSelectionSummary(summaryNode, dependent.class_groups, dependent.birth_date);
                markSelectionValidity(optionsContainer, true);
              },
            })
          );
        });
      }

      renderSelectionSummary(summaryNode, dependent.class_groups, dependent.birth_date);
      extraAssignmentList.appendChild(fragment);
    });
  }

  function renderDependentMedicalCards() {
    if (!extraMedicalList) {
      return;
    }
    extraMedicalList.innerHTML = "";
    var template = document.getElementById("extra-dependent-medical-template");
    extraDependents.forEach(function (dependent, index) {
      var fragment = template.content.cloneNode(true);
      var card = fragment.querySelector("[data-dependent-card]");
      fragment.querySelector("[data-dependent-number]").textContent = String(index + 1);
      ["blood_type", "allergies", "injuries", "emergency_contact"].forEach(function (fieldName) {
        bindDependentField(card, dependent, fieldName);
      });
      extraMedicalList.appendChild(fragment);
    });
  }

  function renderExtraDependents() {
    renderDependentIdentityCards();
    renderDependentAssignmentCards();
    renderDependentMedicalCards();
    serializeDependents();
  }

  function syncAllClassSelections() {
    Object.keys(staticSelections).forEach(function (key) {
      renderStaticSelection(staticSelections[key]);
    });
    renderDependentAssignmentCards();
    serializeDependents();
  }

  function validateStepOne() {
    if (getCurrentProfile() !== "other" || !otherTypeSelect) {
      return true;
    }
    var hasChoice = otherTypeSelect.value && otherTypeSelect.value.trim();
    if (!hasChoice) {
      otherTypePanel.setAttribute("data-invalid", "true");
      return false;
    }
    otherTypePanel.removeAttribute("data-invalid");
    return true;
  }

  function validateRequiredField(name) {
    var field = form.querySelector('[name="' + name + '"]');
    if (!field || field.closest(".is-hidden")) {
      return true;
    }
    var valid = Boolean(field.value && field.value.trim());
    if (!valid) {
      field.setAttribute("aria-invalid", "true");
    } else {
      field.removeAttribute("aria-invalid");
    }
    return valid;
  }

  function validateDependentsIdentity() {
    return extraDependents.every(function (dependent) {
      return dependent.full_name && dependent.cpf && dependent.birth_date && dependent.biological_sex && dependent.password && dependent.password_confirm && dependent.kinship_type && (dependent.kinship_type !== "other" || dependent.kinship_other_label);
    });
  }

  function validateDependentsAssignment() {
    if (!hasCatalog) {
      return true;
    }
    return extraDependents.every(function (dependent) {
      return Array.isArray(dependent.class_groups) && dependent.class_groups.length > 0;
    });
  }

  function validateStepTwo() {
    var profile = getCurrentProfile();
    var requiredFields = [];
    if (profile === "holder") {
      requiredFields = ["holder_name", "holder_cpf", "holder_birthdate", "holder_biological_sex", "holder_password", "holder_password_confirm"];
      if (isDependentFlowActive()) {
        requiredFields.push("dependent_name", "dependent_cpf", "dependent_birthdate", "dependent_biological_sex", "dependent_password", "dependent_password_confirm", "dependent_kinship_type");
      }
    } else if (profile === "guardian") {
      requiredFields = ["guardian_name", "guardian_cpf", "guardian_password", "guardian_password_confirm", "student_name", "student_cpf", "student_birthdate", "student_biological_sex", "student_password", "student_password_confirm", "student_kinship_type"];
    } else {
      requiredFields = ["other_name", "other_cpf", "other_birthdate", "other_password", "other_password_confirm"];
    }
    var staticValid = requiredFields.every(validateRequiredField);
    var dynamicValid = !allowsExtraDependents() || validateDependentsIdentity();
    return staticValid && dynamicValid;
  }

  function validateStaticSelection(config) {
    if (!config.container || config.container.closest(".is-hidden")) {
      return true;
    }
    var selectedIds = getSelectedValues(config.container);
    var isValid = selectedIds.length > 0;
    markSelectionValidity(config.container, isValid);
    return isValid;
  }

  function validateStepThree() {
    if (!hasCatalog || isOtherProfile()) {
      return true;
    }
    var profile = getCurrentProfile();
    var staticValid = true;
    if (profile === "holder") {
      staticValid = validateStaticSelection(staticSelections.holder);
      if (isDependentFlowActive()) {
        staticValid = validateStaticSelection(staticSelections.dependent) && staticValid;
      }
    } else if (profile === "guardian") {
      staticValid = validateStaticSelection(staticSelections.student);
    }
    var dynamicValid = !allowsExtraDependents() || validateDependentsAssignment();
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
    syncSubtitle();
    syncAllClassSelections();
  }

  function goToStep(step) {
    currentStep = normalizeStep(step);
    updateWizard();
    queueDraftSave();
    form.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  profileInputs.forEach(function (input) {
    input.addEventListener("change", updateWizard);
  });

  if (otherTypeSelect) {
    otherTypeSelect.addEventListener("change", function () {
      otherTypePanel.removeAttribute("data-invalid");
    });
  }

  if (dependentToggle) {
    dependentToggle.addEventListener("change", updateWizard);
  }

    if (addDependentButton) {
      addDependentButton.addEventListener("click", function () {
        extraDependents.push(createEmptyDependent());
        renderExtraDependents();
        updateWizard();
        queueDraftSave();
      });
    }

  stepTriggers.forEach(function (trigger) {
    trigger.addEventListener("click", function () {
      var step = Number(trigger.dataset.stepTrigger);
      if (step > currentStep && !validateCurrentStep()) {
        return;
      }
      goToStep(step);
    });
  });

  if (backButton) {
    backButton.addEventListener("click", function () {
      goToStep(currentStep - 1);
    });
  }

  if (nextButton) {
    nextButton.addEventListener("click", function () {
      if (!validateCurrentStep()) {
        return;
      }
      goToStep(currentStep + 1);
    });
  }

  Object.keys(staticSelections).forEach(function (key) {
    var config = staticSelections[key];
    if (config.birthInput) {
      config.birthInput.addEventListener("input", function () {
        renderStaticSelection(config);
      });
    }
    if (config.sexInput) {
      config.sexInput.addEventListener("change", function () {
        renderStaticSelection(config);
      });
    }
  });

  kinshipSelects.forEach(function (select) {
    var otherTarget = document.getElementById(select.dataset.otherTarget || "");
    var sync = function () {
      setHiddenState(otherTarget, select.value !== "other");
    };
    select.addEventListener("change", sync);
    sync();
  });

  dateInputs.forEach(function (input) {
    input.addEventListener("input", function () {
      handleDateMask(input);
    });
  });

  form.querySelectorAll("input, select, textarea").forEach(function (field) {
    field.addEventListener("input", function () {
      field.removeAttribute("aria-invalid");
      queueDraftSave();
    });
    field.addEventListener("change", function () {
      queueDraftSave();
    });
  });

  if (draftClearButton) {
    draftClearButton.addEventListener("click", function () {
      clearStoredDraft();
      syncDraftButtonVisibility();
      setDraftMessage(clearedDraftMessage, false);
    });
  }

  var discardButton = form.querySelector("[data-registration-discard]");
  if (discardButton) {
    discardButton.addEventListener("click", function () {
      clearStoredDraft();
      form.reset();
      extraDependents = [];
      serializeDependents();
      currentStep = 1;
      updateWizard();
      window.location.href = form.dataset.redirectAfterDiscard || "/";
    });
  }

  if (canRestoreDraft && restoreStoredDraft()) {
    setDraftMessage(restoredDraftMessage, true);
  } else {
    setDraftMessage(defaultDraftMessage, false);
  }

  renderExtraDependents();
  updateWizard();
  syncDraftButtonVisibility();

  window.addEventListener("beforeunload", function () {
    saveDraft();
  });
})();
