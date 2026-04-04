(function () {
  const form = document.getElementById("client-registration-form");
  if (!form) {
    return;
  }

  const profileInputs = form.querySelectorAll('input[name="registration_profile"]');
  const dependentToggle = document.getElementById("include-dependent");
  const dependentToggleCard = document.getElementById("dependent-toggle-card");
  const choiceCards = form.querySelectorAll("[data-choice-card]");
  const flowSections = form.querySelectorAll("[data-flow-section]");
  const stepPanels = form.querySelectorAll("[data-step-panel]");
  const stepTriggers = form.querySelectorAll("[data-step-trigger]");
  const nextButton = form.querySelector("[data-step-next]");
  const backButton = form.querySelector("[data-step-back]");
  const submitButton = form.querySelector("[data-step-submit]");
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

  function syncChoiceCards() {
    choiceCards.forEach((card) => {
      const input = card.querySelector("input");
      card.classList.toggle("is-selected", Boolean(input && input.checked));
    });
  }

  function syncDependentToggle(profile) {
    const isHolder = profile === "holder";
    dependentToggleCard.classList.toggle("is-hidden", !isHolder);

    if (!isHolder) {
      dependentToggle.checked = false;
      dependentToggleCard.classList.remove("is-active");
      return;
    }

    dependentToggleCard.classList.toggle("is-active", dependentToggle.checked);
  }

  function setSectionVisibility(profile, includeDependent) {
    flowSections.forEach((section) => {
      const flow = section.getAttribute("data-flow-section");
      let shouldShow = false;

      if (profile === "holder") {
        shouldShow = flow === "holder" || flow === "medical-holder";
        if (includeDependent) {
          shouldShow =
            shouldShow || flow === "holder-dependent" || flow === "medical-dependent";
        }
      }

      if (profile === "guardian") {
        shouldShow = flow === "guardian" || flow === "medical-guardian";
      }

      section.classList.toggle("is-hidden", !shouldShow);
    });
  }

  function updateWizard() {
    const profile = getCurrentProfile();
    const includeDependent = dependentToggle.checked;

    syncChoiceCards();
    syncDependentToggle(profile);
    setSectionVisibility(profile, includeDependent);

    stepPanels.forEach((panel) => {
      const step = Number(panel.getAttribute("data-step-panel"));
      panel.classList.toggle("is-hidden", step !== currentStep);
    });

    stepTriggers.forEach((trigger) => {
      const step = Number(trigger.getAttribute("data-step-trigger"));
      trigger.classList.toggle("is-active", step === currentStep);
      trigger.classList.toggle("is-complete", step < currentStep);
    });

    backButton.classList.toggle("is-hidden", currentStep === 1);
    nextButton.classList.toggle("is-hidden", currentStep === 3);
    submitButton.classList.toggle("is-hidden", currentStep !== 3);
  }

  function getVisibleFieldsForStep(step) {
    if (step !== 2) {
      return [];
    }

    const profile = getCurrentProfile();
    const requiredFieldNames = [];

    if (profile === "holder") {
      requiredFieldNames.push(
        "holder_name",
        "holder_cpf",
        "holder_birthdate",
        "holder_password",
        "holder_password_confirm"
      );
      if (dependentToggle.checked) {
        requiredFieldNames.push(
          "dependent_name",
          "dependent_cpf",
          "dependent_birthdate",
          "dependent_password",
          "dependent_password_confirm"
        );
      }
    } else {
      requiredFieldNames.push(
        "guardian_name",
        "guardian_cpf",
        "guardian_password",
        "guardian_password_confirm",
        "student_name",
        "student_cpf",
        "student_birthdate",
        "student_password",
        "student_password_confirm"
      );
    }

    return requiredFieldNames
      .map((name) => form.querySelector(`[name="${name}"]`))
      .filter(Boolean);
  }

  function validateCurrentStep() {
    const fields = getVisibleFieldsForStep(currentStep);
    let firstInvalidField = null;

    fields.forEach((field) => {
      if (!field.value.trim()) {
        field.setAttribute("aria-invalid", "true");
        if (!firstInvalidField) {
          firstInvalidField = field;
        }
        return;
      }
      field.removeAttribute("aria-invalid");
    });

    if (firstInvalidField) {
      firstInvalidField.focus();
      return false;
    }

    return true;
  }

  function goToStep(step) {
    currentStep = normalizeStep(step);
    updateWizard();
  }

  profileInputs.forEach((input) => {
    input.addEventListener("change", updateWizard);
  });

  dependentToggle.addEventListener("change", updateWizard);

  stepTriggers.forEach((trigger) => {
    trigger.addEventListener("click", () => {
      const targetStep = Number(trigger.getAttribute("data-step-trigger"));
      if (targetStep > currentStep && !validateCurrentStep()) {
        return;
      }
      goToStep(targetStep);
    });
  });

  nextButton.addEventListener("click", () => {
    if (!validateCurrentStep()) {
      return;
    }
    goToStep(currentStep + 1);
  });

  backButton.addEventListener("click", () => {
    goToStep(currentStep - 1);
  });

  dateInputs.forEach((input) => {
    input.addEventListener("input", () => {
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
    });
  });

  updateWizard();
})();
