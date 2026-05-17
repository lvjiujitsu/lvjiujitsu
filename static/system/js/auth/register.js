(function () {
  'use strict';

  // ── Constantes ────────────────────────────────────────────────────────────────

  var PROFILE_HOLDER   = 'holder';
  var PROFILE_GUARDIAN = 'guardian';
  var TOTAL_STEPS      = 6;
  var MAX_DEPENDENTS   = 5;

  // ── Estado ────────────────────────────────────────────────────────────────────

  var state = {
    currentStep:          1,
    profile:              null,
    holderDepCount:       1,
    guardianStudentCount: 1,
  };

  // ── Utilitários de máscara ────────────────────────────────────────────────────

  function maskCpf(value) {
    var digits = value.replace(/\D/g, '').slice(0, 11);
    if (digits.length <= 3) return digits;
    if (digits.length <= 6) return digits.slice(0, 3) + '.' + digits.slice(3);
    if (digits.length <= 9) return digits.slice(0, 3) + '.' + digits.slice(3, 6) + '.' + digits.slice(6);
    return digits.slice(0, 3) + '.' + digits.slice(3, 6) + '.' + digits.slice(6, 9) + '-' + digits.slice(9);
  }

  function maskPhone(value) {
    var digits = value.replace(/\D/g, '').slice(0, 11);
    if (digits.length <= 2) return digits.length ? '(' + digits : '';
    if (digits.length <= 7) return '(' + digits.slice(0, 2) + ') ' + digits.slice(2);
    return '(' + digits.slice(0, 2) + ') ' + digits.slice(2, 7) + '-' + digits.slice(7);
  }

  function maskDate(value) {
    var digits = value.replace(/\D/g, '').slice(0, 8);
    if (digits.length <= 2) return digits;
    if (digits.length <= 4) return digits.slice(0, 2) + '/' + digits.slice(2);
    return digits.slice(0, 2) + '/' + digits.slice(2, 4) + '/' + digits.slice(4);
  }

  function bindMask(inputEl, maskFn) {
    inputEl.addEventListener('input', function () {
      var pos = inputEl.selectionStart;
      var old = inputEl.value;
      var masked = maskFn(old);
      inputEl.value = masked;
      var diff = masked.length - old.length;
      inputEl.setSelectionRange(pos + diff, pos + diff);
    });
  }

  // ── Utilitários de erro ───────────────────────────────────────────────────────

  function showFieldError(inputEl, errorEl, message) {
    if (errorEl) { errorEl.textContent = message; errorEl.hidden = false; }
    if (inputEl) inputEl.classList.add('input-error');
  }

  function clearFieldError(inputEl, errorEl) {
    if (errorEl) { errorEl.textContent = ''; errorEl.hidden = true; }
    if (inputEl) inputEl.classList.remove('input-error');
  }

  function setupPasswordToggle(inputId, btnId) {
    var input = document.getElementById(inputId);
    var btn   = document.getElementById(btnId);
    if (!input || !btn) return;
    btn.addEventListener('click', function () {
      var showing = input.type === 'text';
      input.type  = showing ? 'password' : 'text';
      btn.setAttribute('aria-label', showing ? 'Mostrar senha' : 'Ocultar senha');
    });
  }

  // ── Elementos — Etapa 1 ───────────────────────────────────────────────────────

  var elProfileHolder   = document.getElementById('profile-card-holder');
  var elProfileGuardian = document.getElementById('profile-card-guardian');

  var elHolderSub       = document.getElementById('holder-suboption');
  var elHolderDepChk    = document.getElementById('include-dependent-checkbox');
  var elHolderCountArea = document.getElementById('holder-count-area');
  var elHolderDepVal    = document.getElementById('holder-dep-value');
  var elHolderDepDec    = document.getElementById('holder-dep-dec');
  var elHolderDepInc    = document.getElementById('holder-dep-inc');

  var elGuardianSub     = document.getElementById('guardian-suboption');
  var elStudentCountVal = document.getElementById('student-count-value');
  var elStudentDec      = document.getElementById('student-count-dec');
  var elStudentInc      = document.getElementById('student-count-inc');

  var elStep1Next = document.getElementById('step-1-next');

  // Campos hidden do form
  var elProfileInput    = document.getElementById('id_registration_profile');
  var elIncludeDepInput = document.getElementById('id_include_dependent');
  var elExtraDepInput   = document.getElementById('id_extra_dependents_payload');

  // Progresso e navegação
  var elStepCurrent  = document.getElementById('wizard-step-current');
  var elProgressFill = document.getElementById('wizard-progress-fill');
  var elProgressBar  = document.querySelector('.wizard-progress-bar');
  var elWizardBack   = document.getElementById('wizard-back');

  // ── Elementos — Etapa 2 ───────────────────────────────────────────────────────

  var s2Name            = document.getElementById('ui-s2-name');
  var s2NameError       = document.getElementById('ui-s2-name-error');
  var s2Cpf             = document.getElementById('ui-s2-cpf');
  var s2CpfError        = document.getElementById('ui-s2-cpf-error');
  var s2BirthdateField  = document.getElementById('s2-birthdate-field');
  var s2Birthdate       = document.getElementById('ui-s2-birthdate');
  var s2BirthdateError  = document.getElementById('ui-s2-birthdate-error');
  var s2Sex             = document.getElementById('ui-s2-sex');
  var s2SexError        = document.getElementById('ui-s2-sex-error');
  var s2Phone           = document.getElementById('ui-s2-phone');
  var s2Email           = document.getElementById('ui-s2-email');
  var s2EmailError      = document.getElementById('ui-s2-email-error');
  var s2Password        = document.getElementById('ui-s2-password');
  var s2PasswordError   = document.getElementById('ui-s2-password-error');
  var s2PwConfirm       = document.getElementById('ui-s2-password-confirm');
  var s2PwConfirmError  = document.getElementById('ui-s2-password-confirm-error');
  var elStep2Next       = document.getElementById('step-2-next');
  var s2Subtitle        = document.getElementById('s2-subtitle');

  // ── Sync campos hidden — Etapa 1 ─────────────────────────────────────────────

  function syncHolderDependents() {
    var count = state.holderDepCount;
    elIncludeDepInput.value = count > 0 ? 'on' : '';
    var extras = [];
    for (var i = 0; i < Math.max(0, count - 1); i++) { extras.push({}); }
    elExtraDepInput.value = JSON.stringify(extras);
  }

  function syncGuardianStudents() {
    var extras = [];
    for (var i = 0; i < state.guardianStudentCount - 1; i++) { extras.push({}); }
    elExtraDepInput.value = JSON.stringify(extras);
    elIncludeDepInput.value = '';
  }

  // ── Renderização de contadores ────────────────────────────────────────────────

  function renderHolderDepCount() {
    var count = state.holderDepCount;
    if (elHolderDepVal) elHolderDepVal.textContent = count;
    if (elHolderDepDec) elHolderDepDec.disabled = (count <= 1);
    if (elHolderDepInc) elHolderDepInc.disabled = (count >= MAX_DEPENDENTS);
  }

  function renderGuardianStudentCount() {
    var count = state.guardianStudentCount;
    if (elStudentCountVal) elStudentCountVal.textContent = count;
    if (elStudentDec) elStudentDec.disabled = (count <= 1);
    if (elStudentInc) elStudentInc.disabled = (count >= MAX_DEPENDENTS);
  }

  // ── Seleção de perfil ─────────────────────────────────────────────────────────

  function selectProfile(profile) {
    state.profile = profile;
    [elProfileHolder, elProfileGuardian].forEach(function (el) {
      el.setAttribute('aria-pressed', el.getAttribute('data-profile') === profile ? 'true' : 'false');
    });
    elHolderSub.hidden   = (profile !== PROFILE_HOLDER);
    elGuardianSub.hidden = (profile !== PROFILE_GUARDIAN);
    if (profile === PROFILE_HOLDER) {
      state.holderDepCount = 0;
      if (elHolderDepChk) elHolderDepChk.checked = false;
      if (elHolderCountArea) elHolderCountArea.hidden = true;
      renderHolderDepCount();
      syncHolderDependents();
    }
    if (profile === PROFILE_GUARDIAN) {
      state.guardianStudentCount = 1;
      renderGuardianStudentCount();
      syncGuardianStudents();
    }
    elProfileInput.value = profile;
    elStep1Next.disabled = false;
    elStep1Next.setAttribute('aria-disabled', 'false');
  }

  // ── Progresso e navegação ─────────────────────────────────────────────────────

  function updateProgress() {
    var step = state.currentStep;
    var pct  = ((step / TOTAL_STEPS) * 100).toFixed(2) + '%';
    if (elStepCurrent)  elStepCurrent.textContent = step;
    if (elProgressFill) elProgressFill.style.width = pct;
    if (elProgressBar)  elProgressBar.setAttribute('aria-valuenow', step);
  }

  function goToStep(step) {
    var current = document.getElementById('step-' + state.currentStep);
    var next    = document.getElementById('step-' + step);
    if (current) current.hidden = true;
    if (next)    next.hidden    = false;
    state.currentStep = step;
    updateProgress();
    if (step === 2) onEnterStep2();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // ── Etapa 2 — entrada ────────────────────────────────────────────────────────

  function onEnterStep2() {
    var isHolder = (state.profile === PROFILE_HOLDER);

    if (s2BirthdateField) s2BirthdateField.hidden = !isHolder;
    if (s2Subtitle) {
      s2Subtitle.textContent = isHolder
        ? 'Preencha suas informações de cadastro'
        : 'Seus dados como responsável pelo aluno';
    }

    var prefix = isHolder ? 'holder' : 'guardian';
    restoreStep2Field(s2Name,     'id_' + prefix + '_name');
    restoreStep2Field(s2Cpf,      'id_' + prefix + '_cpf');
    restoreStep2Field(s2Sex,      'id_' + prefix + '_biological_sex');
    restoreStep2Field(s2Phone,    'id_' + prefix + '_phone');
    restoreStep2Field(s2Email,    'id_' + prefix + '_email');
    if (isHolder) restoreStep2Field(s2Birthdate, 'id_holder_birthdate');
  }

  function restoreStep2Field(uiEl, hiddenId) {
    var hidden = document.getElementById(hiddenId);
    if (uiEl && hidden && hidden.value) uiEl.value = hidden.value;
  }

  // ── Etapa 2 — validação ───────────────────────────────────────────────────────

  function validateStep2() {
    var valid    = true;
    var isHolder = (state.profile === PROFILE_HOLDER);

    // Nome
    if (!s2Name.value.trim()) {
      showFieldError(s2Name, s2NameError, 'Campo obrigatório.');
      valid = false;
    } else {
      clearFieldError(s2Name, s2NameError);
    }

    // CPF
    var cpfDigits = s2Cpf.value.replace(/\D/g, '');
    if (!cpfDigits) {
      showFieldError(s2Cpf, s2CpfError, 'Campo obrigatório.');
      valid = false;
    } else if (cpfDigits.length !== 11) {
      showFieldError(s2Cpf, s2CpfError, 'CPF inválido.');
      valid = false;
    } else {
      clearFieldError(s2Cpf, s2CpfError);
    }

    // Nascimento (só HOLDER)
    if (isHolder) {
      var dateVal = s2Birthdate.value.trim();
      if (!dateVal) {
        showFieldError(s2Birthdate, s2BirthdateError, 'Campo obrigatório.');
        valid = false;
      } else if (!/^\d{2}\/\d{2}\/\d{4}$/.test(dateVal)) {
        showFieldError(s2Birthdate, s2BirthdateError, 'Use o formato DD/MM/AAAA.');
        valid = false;
      } else {
        clearFieldError(s2Birthdate, s2BirthdateError);
      }
    }

    // Sexo biológico
    if (!s2Sex.value) {
      showFieldError(s2Sex, s2SexError, 'Campo obrigatório.');
      valid = false;
    } else {
      clearFieldError(s2Sex, s2SexError);
    }

    // E-mail
    var emailVal = s2Email.value.trim();
    if (!emailVal) {
      showFieldError(s2Email, s2EmailError, 'Campo obrigatório.');
      valid = false;
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailVal)) {
      showFieldError(s2Email, s2EmailError, 'E-mail inválido.');
      valid = false;
    } else {
      clearFieldError(s2Email, s2EmailError);
    }

    // Senha
    if (!s2Password.value) {
      showFieldError(s2Password, s2PasswordError, 'Campo obrigatório.');
      valid = false;
    } else if (s2Password.value.length < 8) {
      showFieldError(s2Password, s2PasswordError, 'A senha deve ter pelo menos 8 caracteres.');
      valid = false;
    } else {
      clearFieldError(s2Password, s2PasswordError);
    }

    // Confirmar senha
    if (!s2PwConfirm.value) {
      showFieldError(s2PwConfirm, s2PwConfirmError, 'Campo obrigatório.');
      valid = false;
    } else if (s2PwConfirm.value !== s2Password.value) {
      showFieldError(s2PwConfirm, s2PwConfirmError, 'As senhas não coincidem.');
      valid = false;
    } else {
      clearFieldError(s2PwConfirm, s2PwConfirmError);
    }

    return valid;
  }

  // ── Etapa 2 — coleta para hidden inputs ──────────────────────────────────────

  function collectStep2() {
    var isHolder = (state.profile === PROFILE_HOLDER);
    var prefix   = isHolder ? 'holder' : 'guardian';

    setHidden('id_' + prefix + '_name',             s2Name.value.trim());
    setHidden('id_' + prefix + '_cpf',              s2Cpf.value);
    setHidden('id_' + prefix + '_biological_sex',   s2Sex.value);
    setHidden('id_' + prefix + '_phone',            s2Phone.value);
    setHidden('id_' + prefix + '_email',            s2Email.value.trim());
    setHidden('id_' + prefix + '_password',         s2Password.value);
    setHidden('id_' + prefix + '_password_confirm', s2PwConfirm.value);
    if (isHolder) setHidden('id_holder_birthdate', s2Birthdate.value);
  }

  function setHidden(id, value) {
    var el = document.getElementById(id);
    if (el) el.value = value;
  }

  // ── Eventos — Etapa 1 ─────────────────────────────────────────────────────────

  if (elHolderDepChk) {
    elHolderDepChk.addEventListener('change', function () {
      var checked = elHolderDepChk.checked;
      elHolderCountArea.hidden = !checked;
      state.holderDepCount = checked ? 1 : 0;
      if (checked) renderHolderDepCount();
      syncHolderDependents();
    });
  }

  if (elHolderDepDec) {
    elHolderDepDec.addEventListener('click', function () {
      if (state.holderDepCount > 1) {
        state.holderDepCount--;
        renderHolderDepCount();
        syncHolderDependents();
      }
    });
  }

  if (elHolderDepInc) {
    elHolderDepInc.addEventListener('click', function () {
      if (state.holderDepCount < MAX_DEPENDENTS) {
        state.holderDepCount++;
        renderHolderDepCount();
        syncHolderDependents();
      }
    });
  }

  if (elStudentDec) {
    elStudentDec.addEventListener('click', function () {
      if (state.guardianStudentCount > 1) {
        state.guardianStudentCount--;
        renderGuardianStudentCount();
        syncGuardianStudents();
      }
    });
  }

  if (elStudentInc) {
    elStudentInc.addEventListener('click', function () {
      if (state.guardianStudentCount < MAX_DEPENDENTS) {
        state.guardianStudentCount++;
        renderGuardianStudentCount();
        syncGuardianStudents();
      }
    });
  }

  if (elProfileHolder)   elProfileHolder.addEventListener('click',   function () { selectProfile(PROFILE_HOLDER); });
  if (elProfileGuardian) elProfileGuardian.addEventListener('click', function () { selectProfile(PROFILE_GUARDIAN); });

  if (elStep1Next) {
    elStep1Next.addEventListener('click', function () {
      if (state.profile) goToStep(2);
    });
  }

  // ── Eventos — Etapa 2 ─────────────────────────────────────────────────────────

  if (s2Cpf)   bindMask(s2Cpf,   maskCpf);
  if (s2Phone) bindMask(s2Phone, maskPhone);
  if (s2Birthdate) bindMask(s2Birthdate, maskDate);

  setupPasswordToggle('ui-s2-password',         'ui-s2-pw-toggle');
  setupPasswordToggle('ui-s2-password-confirm', 'ui-s2-pwc-toggle');

  if (elStep2Next) {
    elStep2Next.addEventListener('click', function () {
      if (validateStep2()) {
        collectStep2();
        goToStep(3);
      }
    });
  }

  // ── Voltar — intercepta quando step > 1 ──────────────────────────────────────

  if (elWizardBack) {
    elWizardBack.addEventListener('click', function (e) {
      if (state.currentStep > 1) {
        e.preventDefault();
        goToStep(state.currentStep - 1);
      }
    });
  }

  // ── Inicialização ─────────────────────────────────────────────────────────────

  var initialProfile = elProfileInput ? elProfileInput.value : '';
  if (initialProfile === PROFILE_HOLDER || initialProfile === PROFILE_GUARDIAN) {
    selectProfile(initialProfile);
    if (initialProfile === PROFILE_HOLDER && elIncludeDepInput && elIncludeDepInput.value) {
      if (elHolderDepChk) {
        elHolderDepChk.checked = true;
        elHolderCountArea.hidden = false;
        state.holderDepCount = 1;
        try {
          var extras = JSON.parse(elExtraDepInput.value || '[]');
          state.holderDepCount = extras.length + 1;
        } catch (e) {}
        renderHolderDepCount();
      }
    }
  }

  renderGuardianStudentCount();
  renderHolderDepCount();
  updateProgress();

})();
