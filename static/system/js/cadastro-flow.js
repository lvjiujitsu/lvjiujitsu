(function () {
  const form = document.getElementById("client-registration-form");
  if (!form) {
    return;
  }

  const profileInputs = form.querySelectorAll('input[name="registration_profile"]');
  const dependentToggle = document.getElementById("include-dependent");
  const dependentToggleCard = document.getElementById("dependent-toggle-card");
  const choiceCards = form.querySelectorAll("[data-choice-card]");
  const sections = form.querySelectorAll("[data-flow-section]");
  const dateInputs = form.querySelectorAll("[data-date-mask]");

  function setSectionVisibility(profile, includeDependent) {
    sections.forEach((section) => {
      const flow = section.getAttribute("data-flow-section");
      let shouldShow = false;

      if (profile === "holder") {
        shouldShow = flow === "holder" || flow === "medical-holder";
        if (includeDependent) {
          shouldShow = shouldShow || flow === "holder-dependent" || flow === "medical-dependent";
        }
      }

      if (profile === "guardian") {
        shouldShow = flow === "guardian" || flow === "medical-guardian";
      }

      section.classList.toggle("is-hidden", !shouldShow);
    });
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

  function getCurrentProfile() {
    const selected = form.querySelector('input[name="registration_profile"]:checked');
    return selected ? selected.value : "holder";
  }

  function applyFlow() {
    const profile = getCurrentProfile();
    syncChoiceCards();
    syncDependentToggle(profile);
    setSectionVisibility(profile, dependentToggle.checked);
  }

  profileInputs.forEach((input) => {
    input.addEventListener("change", applyFlow);
  });

  dependentToggle.addEventListener("change", applyFlow);

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

  applyFlow();
})();
