(function () {
  const form = document.getElementById("client-registration-form");

  if (!form) {
    return;
  }

  const profileInputs = form.querySelectorAll('input[name="registration_profile"]');
  const dependentToggle = document.getElementById("include-dependent");
  const dependentToggleCard = document.getElementById("dependent-toggle-card");
  const otherTypePanel = form.querySelector("[data-other-type-panel]");
  const otherTypeInputs = form.querySelectorAll('input[name="other_type_codes"]');
  const choiceCards = form.querySelectorAll("[data-choice-card]");
  const pillChoices = form.querySelectorAll("[data-pill-choice]");
  const flowSections = form.querySelectorAll("[data-flow-section]");
  const stepPanels = form.querySelectorAll("[data-step-panel]");
  const stepTriggers = form.querySelectorAll("[data-step-trigger]");
  const nextButton = form.querySelector("[data-step-next]");
  const backButton = form.querySelector("[data-step-back]");
  const submitButton = form.querySelector("[data-step-submit]");
  const wizardActions = form.querySelector(".wizard-actions");
  const dateInputs = form.querySelectorAll("[data-date-mask]");

  let currentStep = normalizeStep(Number(form.dataset.initialStep || "1"));

  function normalizeStep(step) {
    if (Number.isNaN(step) || step < 1) {
      return 1;
    }
    if (step > 3) {
      return 3;
    }
    return step;
  }

  function getCurrentProfile() {
    const selected = form.querySelector('input[name="registration_profile"]:checked');
    return selected ? selected.value : "holder";
  }

  function hasSelectedOtherType() {
    return Array.from(otherTypeInputs).some((input) => input.checked);
  }

  function setHiddenState(element, shouldHide) {
    if (!element) {
      return;
    }

    element.classList.toggle("is-hidden", shouldHide);
    element.hidden = shouldHide;
  }

  function syncChoiceCards() {
    choiceCards.forEach((card) => {
      const input = card.querySelector("input");
      card.classList.toggle("is-selected", Boolean(input && input.checked));
    });
  }

  function syncPillChoices() {
    pillChoices.forEach((choice) => {
      const input = choice.querySelector("input");
      choice.classList.toggle("is-selected", Boolean(input && input.checked));
    });
  }

  function syncDependentToggle(profile) {
    const showDependentToggle = profile === "holder";

    setHiddenState(dependentToggleCard, !showDependentToggle);
    if (!showDependentToggle) {
      dependentToggle.checked = false;
    }

    dependentToggleCard.classList.toggle("is-active", dependentToggle.checked);
  }

  function syncOtherTypePanel(profile) {
    setHiddenState(otherTypePanel, profile !== "other");
  }

  function setSectionVisibility(profile, includeDependent) {
    const activeFlows = new Set();

    if (profile === "holder") {
      activeFlows.add("holder");
      activeFlows.add("medical-holder");
      if (includeDependent) {
        activeFlows.add("holder-dependent");
        activeFlows.add("medical-dependent");
      }
    }

    if (profile === "guardian") {
      activeFlows.add("guardian");
      activeFlows.add("medical-guardian");
    }

    if (profile === "other") {
      activeFlows.add("other");
      activeFlows.add("medical-other");
    }

    flowSections.forEach((section) => {
      setHiddenState(section, !activeFlows.has(section.dataset.flowSection));
    });
  }

  function syncStepPanels() {
    stepPanels.forEach((panel) => {
      const step = Number(panel.dataset.stepPanel);
      setHiddenState(panel, step !== currentStep);
    });
  }

  function syncStepTriggers() {
    stepTriggers.forEach((trigger) => {
      const step = Number(trigger.dataset.stepTrigger);
      trigger.classList.toggle("is-active", step === currentStep);
      trigger.classList.toggle("is-complete", step < currentStep);
    });
  }

  function syncActionButtons() {
    const showBack = currentStep > 1;
    const showNext = currentStep < 3;
    const showSubmit = currentStep === 3;

    setHiddenState(backButton, !showBack);
    setHiddenState(nextButton, !showNext);
    setHiddenState(submitButton, !showSubmit);

    wizardActions.classList.toggle("wizard-actions-single", !showBack && showNext);
  }

  function getRequiredFieldsForStepTwo() {
    const profile = getCurrentProfile();

    if (profile === "holder") {
      const fields = [
        "holder_name",
        "holder_cpf",
        "holder_birthdate",
        "holder_password",
        "holder_password_confirm",
      ];

      if (dependentToggle.checked) {
        fields.push(
          "dependent_name",
          "dependent_cpf",
          "dependent_birthdate",
          "dependent_password",
          "dependent_password_confirm"
        );
      }

      return fields;
    }

    if (profile === "other") {
      return [
        "other_name",
        "other_cpf",
        "other_birthdate",
        "other_password",
        "other_password_confirm",
      ];
    }

    return [
      "guardian_name",
      "guardian_cpf",
      "guardian_password",
      "guardian_password_confirm",
      "student_name",
      "student_cpf",
      "student_birthdate",
      "student_password",
      "student_password_confirm",
    ];
  }

  function validateStepOne() {
    if (getCurrentProfile() !== "other" || otherTypeInputs.length === 0) {
      return true;
    }

    if (hasSelectedOtherType()) {
      otherTypePanel.removeAttribute("data-invalid");
      return true;
    }

    otherTypePanel.setAttribute("data-invalid", "true");
    otherTypePanel.scrollIntoView({ block: "nearest", behavior: "smooth" });
    return false;
  }

  function validateStepTwo() {
    const requiredFields = getRequiredFieldsForStepTwo();
    let firstInvalidField = null;

    requiredFields.forEach((fieldName) => {
      const field = form.querySelector(`[name="${fieldName}"]`);
      if (!field) {
        return;
      }

      if (!field.value.trim()) {
        field.setAttribute("aria-invalid", "true");
        if (!firstInvalidField) {
          firstInvalidField = field;
        }
        return;
      }

      field.removeAttribute("aria-invalid");
    });

    if (!firstInvalidField) {
      return true;
    }

    firstInvalidField.focus();
    return false;
  }

  function validateCurrentStep() {
    if (currentStep === 1) {
      return validateStepOne();
    }

    if (currentStep === 2) {
      return validateStepTwo();
    }

    return true;
  }

  function updateWizard() {
    const profile = getCurrentProfile();
    const includeDependent = dependentToggle.checked;

    syncChoiceCards();
    syncPillChoices();
    syncDependentToggle(profile);
    syncOtherTypePanel(profile);
    setSectionVisibility(profile, includeDependent);
    syncStepPanels();
    syncStepTriggers();
    syncActionButtons();
  }

  function goToStep(step) {
    currentStep = normalizeStep(step);
    updateWizard();
  }

  function handleMaskedDateInput(input) {
    const digits = input.value.replace(/\D/g, "").slice(0, 8);
    const parts = [];

    if (digits.length > 0) {
      parts.push(digits.slice(0, 2));
    }
    if (digits.length > 2) {
      parts.push(digits.slice(2, 4));
    }
    if (digits.length > 4) {
      parts.push(digits.slice(4, 8));
    }

    input.value = parts.join("/");
  }

  profileInputs.forEach((input) => {
    input.addEventListener("change", () => {
      if (otherTypePanel) {
        otherTypePanel.removeAttribute("data-invalid");
      }
      updateWizard();
    });
  });

  otherTypeInputs.forEach((input) => {
    input.addEventListener("change", () => {
      if (otherTypePanel) {
        otherTypePanel.removeAttribute("data-invalid");
      }
      syncPillChoices();
    });
  });

  if (dependentToggle) {
    dependentToggle.addEventListener("change", updateWizard);
  }

  stepTriggers.forEach((trigger) => {
    trigger.addEventListener("click", () => {
      const targetStep = Number(trigger.dataset.stepTrigger);
      if (targetStep > currentStep && !validateCurrentStep()) {
        return;
      }
      goToStep(targetStep);
    });
  });

  if (nextButton) {
    nextButton.addEventListener("click", () => {
      if (!validateCurrentStep()) {
        return;
      }
      goToStep(currentStep + 1);
    });
  }

  if (backButton) {
    backButton.addEventListener("click", () => {
      goToStep(currentStep - 1);
    });
  }

  form.querySelectorAll("input, select, textarea").forEach((field) => {
    field.addEventListener("input", () => {
      field.removeAttribute("aria-invalid");
    });
  });

  dateInputs.forEach((input) => {
    input.addEventListener("input", () => {
      handleMaskedDateInput(input);
    });
  });

  updateWizard();
})();
