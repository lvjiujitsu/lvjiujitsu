(function () {
  'use strict';

  // ── Constantes ────────────────────────────────────────────────────────────────

  var PROFILE_HOLDER   = 'holder';
  var PROFILE_GUARDIAN = 'guardian';
  var MAX_DEPENDENTS   = 5;

  // Etapas fixas que seguem após seleção de turmas
  var TRAILING_STEPS = ['step-plan', 'step-checkout'];

  // ── Estado central ────────────────────────────────────────────────────────────

  var state = {
    profile:              null,
    holderDepCount:       0,
    guardianStudentCount: 1,
    stepSequence:         [],   // ex: ['step-profile','step-principal','step-dep','step-classes','step-plan',...]
    stepIndex:            0,    // posição atual na sequência
    deps:                 [],   // [{name,cpf,birthdate,sex,phone,email,password,pwConfirm,kinship,kinshipOther,classGroups}]
    classSelections:      [],   // [{ids:[]}] — 1 por pessoa que precisa de turma (holder/deps ou só deps)
  };

  // ── Utilitários de máscara ────────────────────────────────────────────────────

  function maskCpf(value) {
    var d = value.replace(/\D/g, '').slice(0, 11);
    if (d.length <= 3) return d;
    if (d.length <= 6) return d.slice(0, 3) + '.' + d.slice(3);
    if (d.length <= 9) return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6);
    return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9);
  }

  function maskPhone(value) {
    var d = value.replace(/\D/g, '').slice(0, 11);
    if (d.length <= 2) return d.length ? '(' + d : '';
    if (d.length <= 7) return '(' + d.slice(0, 2) + ') ' + d.slice(2);
    return '(' + d.slice(0, 2) + ') ' + d.slice(2, 7) + '-' + d.slice(7);
  }

  function maskDate(value) {
    var d = value.replace(/\D/g, '').slice(0, 8);
    if (d.length <= 2) return d;
    if (d.length <= 4) return d.slice(0, 2) + '/' + d.slice(2);
    return d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
  }

  function bindMask(el, fn) {
    if (!el) return;
    el.addEventListener('input', function () {
      var pos = el.selectionStart;
      var old = el.value;
      var masked = fn(old);
      el.value = masked;
      el.setSelectionRange(pos + masked.length - old.length, pos + masked.length - old.length);
    });
  }

  // ── Utilitários de erro ───────────────────────────────────────────────────────

  function showErr(input, errorEl, msg) {
    if (errorEl) { errorEl.textContent = msg; errorEl.hidden = false; }
    if (input)   input.classList.add('input-error');
  }

  function clearErr(input, errorEl) {
    if (errorEl) { errorEl.textContent = ''; errorEl.hidden = true; }
    if (input)   input.classList.remove('input-error');
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

  function setHidden(id, value) {
    var el = document.getElementById(id);
    if (el) el.value = value;
  }

  function getHidden(id) {
    var el = document.getElementById(id);
    return el ? el.value : '';
  }

  // ── Sequência de etapas ───────────────────────────────────────────────────────

  function buildStepSequence() {
    var numDeps = (state.profile === PROFILE_HOLDER)
      ? state.holderDepCount
      : state.guardianStudentCount;

    var seq = ['step-profile', 'step-principal'];

    if (state.profile === PROFILE_HOLDER) {
      // Holder treina: saúde + marcial antes dos deps
      seq.push('step-health');
      seq.push('step-martial');
      for (var i = 0; i < numDeps; i++) {
        seq.push('step-dep');
        seq.push('step-health');
        seq.push('step-martial');
      }
    } else {
      // Guardian não treina; cada aluno tem dep + saúde + marcial
      for (var i = 0; i < numDeps; i++) {
        seq.push('step-dep');
        seq.push('step-health');
        seq.push('step-martial');
      }
    }

    // Turmas: holder treina (1 etapa) + cada dep/aluno
    var numClassSteps = (state.profile === PROFILE_HOLDER) ? (1 + numDeps) : numDeps;
    for (var j = 0; j < numClassSteps; j++) seq.push('step-classes');

    seq = seq.concat(TRAILING_STEPS);
    state.stepSequence = seq;

    // Garante array de deps com tamanho correto
    while (state.deps.length < numDeps) {
      state.deps.push({
        name: '', cpf: '', birthdate: '', sex: '', phone: '', email: '',
        password: '', pwConfirm: '', kinship: '', kinshipOther: '', classGroups: [],
        bloodType: '', allergies: '', injuries: '', emergencyContact: '',
        hasMartialArt: '', martialArt: '', martialArtGraduation: '',
        jiuJitsuBelt: '', jiuJitsuStripes: '0',
        martialArtStartedAt: '', martialArtLastGraduationAt: '', previousAcademy: '',
      });
    }
    state.deps.length = numDeps;

    // Garante array de classSelections com tamanho correto
    while (state.classSelections.length < numClassSteps) {
      state.classSelections.push({ ids: [] });
    }
    state.classSelections.length = numClassSteps;
  }

  function numDepsTotal() {
    return (state.profile === PROFILE_HOLDER)
      ? state.holderDepCount
      : state.guardianStudentCount;
  }

  function totalTrainingPersons() {
    if (state.profile === PROFILE_HOLDER) return 1 + state.deps.length;
    return state.deps.length;
  }

  // Planos elegíveis para este cadastro (regras de negócio de visibilidade)
  function getEligiblePlans() {
    var numPersons = totalTrainingPersons();
    return planCatalog.filter(function (p) {
      if (p.is_loyalty_plan) return false;          // exige 2 anos — nunca no cadastro inicial
      if (p.is_family_plan)  return numPersons >= 2; // família: mínimo 2 pessoas treinando
      return true;
    });
  }

  // Retorna índice 0-based do dependente dentro de state.deps para uma posição na sequência
  function depIndexAt(seqIdx) {
    var count = 0;
    for (var i = 0; i <= seqIdx; i++) {
      if (state.stepSequence[i] === 'step-dep') count++;
    }
    return count - 1;
  }

  // Retorna índice 0-based dentro de state.classSelections para uma posição na sequência
  function classPersonIndexAt(seqIdx) {
    var count = 0;
    for (var i = 0; i <= seqIdx; i++) {
      if (state.stepSequence[i] === 'step-classes') count++;
    }
    return count - 1;
  }

  // Retorna índice de pessoa (mesmo esquema que class) para step-health/step-martial
  function healthPersonIndexAt(seqIdx) {
    var count = 0;
    for (var i = 0; i <= seqIdx; i++) {
      if (state.stepSequence[i] === 'step-health') count++;
    }
    return count - 1;
  }

  function martialPersonIndexAt(seqIdx) {
    var count = 0;
    for (var i = 0; i <= seqIdx; i++) {
      if (state.stepSequence[i] === 'step-martial') count++;
    }
    return count - 1;
  }

  // person 0 com HOLDER = holder (não há dep array entry); com GUARDIAN = dep[0]
  function isHolderPerson(personIdx) {
    return state.profile === PROFILE_HOLDER && personIdx === 0;
  }

  // Retorna índice no state.deps para um personIdx
  function getDepIdxForPerson(personIdx) {
    return state.profile === PROFILE_HOLDER ? personIdx - 1 : personIdx;
  }

  // Retorna nome e dados da pessoa correspondente a um classPersonIdx
  function getPersonForClass(classPersonIdx) {
    if (state.profile === PROFILE_HOLDER) {
      if (classPersonIdx === 0) {
        return { name: getHidden('id_holder_name') || 'Você', sex: getHidden('id_holder_biological_sex'), birthdate: getHidden('id_holder_birthdate') };
      }
      var dep = state.deps[classPersonIdx - 1] || {};
      return { name: dep.name || ('Dependente ' + classPersonIdx), sex: dep.sex, birthdate: dep.birthdate };
    }
    var dep = state.deps[classPersonIdx] || {};
    return { name: dep.name || ('Aluno ' + (classPersonIdx + 1)), sex: dep.sex, birthdate: dep.birthdate };
  }

  // ── Progresso ─────────────────────────────────────────────────────────────────

  var elStepCurrent  = document.getElementById('wizard-step-current');
  var elStepTotal    = document.getElementById('wizard-step-total');
  var elProgressFill = document.getElementById('wizard-progress-fill');
  var elProgressBar  = document.querySelector('.wizard-progress-bar');

  function updateProgress() {
    var total   = state.stepSequence.length || 6;
    var current = state.stepIndex + 1;
    var pct     = (current / total * 100).toFixed(2) + '%';
    if (elStepCurrent)  elStepCurrent.textContent = current;
    if (elStepTotal)    elStepTotal.textContent    = total;
    if (elProgressFill) elProgressFill.style.width = pct;
    if (elProgressBar) {
      elProgressBar.setAttribute('aria-valuenow', current);
      elProgressBar.setAttribute('aria-valuemax',  total);
    }
  }

  // ── Navegação central ─────────────────────────────────────────────────────────

  function goTo(targetIdx) {
    var currentId = state.stepSequence[state.stepIndex];
    var targetId  = state.stepSequence[targetIdx];

    if (currentId !== targetId) {
      var currentEl = document.getElementById(currentId);
      if (currentEl) currentEl.hidden = true;
      var targetEl = document.getElementById(targetId);
      if (targetEl) targetEl.hidden = false;
    }

    state.stepIndex = targetIdx;
    updateProgress();
    onEnterStep(targetId, targetIdx);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function onEnterStep(stepId, seqIdx) {
    if (stepId === 'step-principal') onEnterPrincipal();
    if (stepId === 'step-dep')       onEnterDep(depIndexAt(seqIdx));
    if (stepId === 'step-health')    onEnterHealth(healthPersonIndexAt(seqIdx));
    if (stepId === 'step-martial')   onEnterMartial(martialPersonIndexAt(seqIdx));
    if (stepId === 'step-classes')   onEnterClasses(classPersonIndexAt(seqIdx));
    if (stepId === 'step-plan')      onEnterPlan();
    if (stepId === 'step-checkout')  onEnterCheckout();
  }

  // ── Elementos — Etapa de perfil ───────────────────────────────────────────────

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
  var elStep1Next       = document.getElementById('step-1-next');
  var elProfileInput    = document.getElementById('id_registration_profile');
  var elIncludeDepInput = document.getElementById('id_include_dependent');
  var elExtraDepInput   = document.getElementById('id_extra_dependents_payload');
  var elWizardBack      = document.getElementById('wizard-back');

  function syncHolderDeps() {
    var count = state.holderDepCount;
    elIncludeDepInput.value = count > 0 ? 'on' : '';
    var extras = [];
    for (var i = 0; i < Math.max(0, count - 1); i++) extras.push({});
    elExtraDepInput.value = JSON.stringify(extras);
  }

  function syncGuardianStudents() {
    var extras = [];
    for (var i = 0; i < state.guardianStudentCount - 1; i++) extras.push({});
    elExtraDepInput.value = JSON.stringify(extras);
    elIncludeDepInput.value = '';
  }

  function renderHolderDepCount() {
    var c = state.holderDepCount;
    if (elHolderDepVal) elHolderDepVal.textContent = c;
    if (elHolderDepDec) elHolderDepDec.disabled = (c <= 1);
    if (elHolderDepInc) elHolderDepInc.disabled = (c >= MAX_DEPENDENTS);
  }

  function renderGuardianStudentCount() {
    var c = state.guardianStudentCount;
    if (elStudentCountVal) elStudentCountVal.textContent = c;
    if (elStudentDec) elStudentDec.disabled = (c <= 1);
    if (elStudentInc) elStudentInc.disabled = (c >= MAX_DEPENDENTS);
  }

  function selectProfile(profile) {
    state.profile = profile;
    [elProfileHolder, elProfileGuardian].forEach(function (el) {
      el.setAttribute('aria-pressed', el.getAttribute('data-profile') === profile ? 'true' : 'false');
    });
    elHolderSub.hidden   = (profile !== PROFILE_HOLDER);
    elGuardianSub.hidden = (profile !== PROFILE_GUARDIAN);
    if (profile === PROFILE_HOLDER) {
      state.holderDepCount = 0;
      if (elHolderDepChk)    elHolderDepChk.checked  = false;
      if (elHolderCountArea) elHolderCountArea.hidden = true;
      renderHolderDepCount();
      syncHolderDeps();
    } else {
      state.guardianStudentCount = 1;
      renderGuardianStudentCount();
      syncGuardianStudents();
    }
    elProfileInput.value = profile;
    elStep1Next.disabled = false;
    elStep1Next.setAttribute('aria-disabled', 'false');
    buildStepSequence();
    updateProgress();
  }

  // ── Elementos — Etapa principal (step-2) ─────────────────────────────────────

  var s2Name          = document.getElementById('ui-s2-name');
  var s2NameError     = document.getElementById('ui-s2-name-error');
  var s2Cpf           = document.getElementById('ui-s2-cpf');
  var s2CpfError      = document.getElementById('ui-s2-cpf-error');
  var s2BirthdateWrap = document.getElementById('s2-birthdate-field');
  var s2Birthdate     = document.getElementById('ui-s2-birthdate');
  var s2BirthdateErr  = document.getElementById('ui-s2-birthdate-error');
  var s2Sex           = document.getElementById('ui-s2-sex');
  var s2SexError      = document.getElementById('ui-s2-sex-error');
  var s2Phone         = document.getElementById('ui-s2-phone');
  var s2Email         = document.getElementById('ui-s2-email');
  var s2EmailError    = document.getElementById('ui-s2-email-error');
  var s2Password      = document.getElementById('ui-s2-password');
  var s2PasswordErr   = document.getElementById('ui-s2-password-error');
  var s2PwConfirm     = document.getElementById('ui-s2-password-confirm');
  var s2PwConfirmErr  = document.getElementById('ui-s2-password-confirm-error');
  var s2Subtitle      = document.getElementById('s2-subtitle');
  var elStep2Next     = document.getElementById('step-2-next');

  function onEnterPrincipal() {
    var isHolder = (state.profile === PROFILE_HOLDER);
    if (s2BirthdateWrap) s2BirthdateWrap.hidden = !isHolder;
    if (s2Subtitle) s2Subtitle.textContent = isHolder
      ? 'Preencha suas informações de cadastro'
      : 'Seus dados como responsável pelo aluno';
    var prefix = isHolder ? 'holder' : 'guardian';
    var fields  = [
      [s2Name,      'id_' + prefix + '_name'],
      [s2Cpf,       'id_' + prefix + '_cpf'],
      [s2Sex,       'id_' + prefix + '_biological_sex'],
      [s2Phone,     'id_' + prefix + '_phone'],
      [s2Email,     'id_' + prefix + '_email'],
    ];
    fields.forEach(function (pair) {
      var v = getHidden(pair[1]);
      if (pair[0] && v) pair[0].value = v;
    });
    if (isHolder && s2Birthdate) {
      var bd = getHidden('id_holder_birthdate');
      if (bd) s2Birthdate.value = bd;
    }
  }

  function validatePrincipal() {
    var valid    = true;
    var isHolder = (state.profile === PROFILE_HOLDER);

    if (!s2Name.value.trim()) {
      showErr(s2Name, s2NameError, 'Campo obrigatório.'); valid = false;
    } else clearErr(s2Name, s2NameError);

    var cpfDigits = s2Cpf.value.replace(/\D/g, '');
    if (!cpfDigits) {
      showErr(s2Cpf, s2CpfError, 'Campo obrigatório.'); valid = false;
    } else if (cpfDigits.length !== 11) {
      showErr(s2Cpf, s2CpfError, 'CPF inválido.'); valid = false;
    } else clearErr(s2Cpf, s2CpfError);

    if (isHolder) {
      var bv = s2Birthdate.value.trim();
      if (!bv) {
        showErr(s2Birthdate, s2BirthdateErr, 'Campo obrigatório.'); valid = false;
      } else if (!/^\d{2}\/\d{2}\/\d{4}$/.test(bv)) {
        showErr(s2Birthdate, s2BirthdateErr, 'Use o formato DD/MM/AAAA.'); valid = false;
      } else clearErr(s2Birthdate, s2BirthdateErr);
    }

    if (!s2Sex.value) {
      showErr(s2Sex, s2SexError, 'Campo obrigatório.'); valid = false;
    } else clearErr(s2Sex, s2SexError);

    var ev = s2Email.value.trim();
    if (!ev) {
      showErr(s2Email, s2EmailError, 'Campo obrigatório.'); valid = false;
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(ev)) {
      showErr(s2Email, s2EmailError, 'E-mail inválido.'); valid = false;
    } else clearErr(s2Email, s2EmailError);

    if (!s2Password.value) {
      showErr(s2Password, s2PasswordErr, 'Campo obrigatório.'); valid = false;
    } else if (s2Password.value.length < 8) {
      showErr(s2Password, s2PasswordErr, 'Mínimo 8 caracteres.'); valid = false;
    } else clearErr(s2Password, s2PasswordErr);

    if (!s2PwConfirm.value) {
      showErr(s2PwConfirm, s2PwConfirmErr, 'Campo obrigatório.'); valid = false;
    } else if (s2PwConfirm.value !== s2Password.value) {
      showErr(s2PwConfirm, s2PwConfirmErr, 'As senhas não coincidem.'); valid = false;
    } else clearErr(s2PwConfirm, s2PwConfirmErr);

    return valid;
  }

  function collectPrincipal() {
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

  // ── Elementos — Etapa dependente (step-dep) ───────────────────────────────────

  var depBadge        = document.getElementById('dep-step-badge');
  var depTitle        = document.getElementById('dep-step-title');
  var depKinship      = document.getElementById('ui-dep-kinship');
  var depKinshipErr   = document.getElementById('ui-dep-kinship-error');
  var depKinshipOther     = document.getElementById('ui-dep-kinship-other');
  var depKinshipOtherErr  = document.getElementById('ui-dep-kinship-other-error');
  var depKinshipOtherWrap = document.getElementById('dep-kinship-other-field');
  var depName         = document.getElementById('ui-dep-name');
  var depNameErr      = document.getElementById('ui-dep-name-error');
  var depCpf          = document.getElementById('ui-dep-cpf');
  var depCpfErr       = document.getElementById('ui-dep-cpf-error');
  var depBirthdate    = document.getElementById('ui-dep-birthdate');
  var depBirthdateErr = document.getElementById('ui-dep-birthdate-error');
  var depSex          = document.getElementById('ui-dep-sex');
  var depSexErr       = document.getElementById('ui-dep-sex-error');
  var depPhone        = document.getElementById('ui-dep-phone');
  var depEmail        = document.getElementById('ui-dep-email');
  var depEmailErr     = document.getElementById('ui-dep-email-error');
  var depPassword     = document.getElementById('ui-dep-password');
  var depPasswordErr  = document.getElementById('ui-dep-password-error');
  var depPwConfirm    = document.getElementById('ui-dep-password-confirm');
  var depPwConfirmErr = document.getElementById('ui-dep-password-confirm-error');
  var elStepDepNext   = document.getElementById('step-dep-next');

  function toggleKinshipOther(val) {
    if (depKinshipOtherWrap) depKinshipOtherWrap.hidden = (val !== 'other');
  }

  function onEnterDep(depIdx) {
    var total = numDepsTotal();
    var label = (state.profile === PROFILE_HOLDER) ? 'Dependente' : 'Aluno';
    if (depBadge) depBadge.textContent = label + ' ' + (depIdx + 1) + ' de ' + total;
    if (depTitle) depTitle.textContent = 'Dados do ' + label.toLowerCase();

    var dep = state.deps[depIdx] || {};
    if (depKinship)      depKinship.value      = dep.kinship      || '';
    if (depKinshipOther) depKinshipOther.value  = dep.kinshipOther || '';
    if (depName)         depName.value          = dep.name         || '';
    if (depCpf)          depCpf.value           = dep.cpf          || '';
    if (depBirthdate)    depBirthdate.value      = dep.birthdate    || '';
    if (depSex)          depSex.value            = dep.sex          || '';
    if (depPhone)        depPhone.value          = dep.phone        || '';
    if (depEmail)        depEmail.value          = dep.email        || '';
    if (depPassword)     depPassword.value       = '';
    if (depPwConfirm)    depPwConfirm.value      = '';

    toggleKinshipOther(dep.kinship || '');
    clearDepErrors();
  }

  function clearDepErrors() {
    var pairs = [
      [depKinship, depKinshipErr], [depKinshipOther, depKinshipOtherErr],
      [depName, depNameErr], [depCpf, depCpfErr],
      [depBirthdate, depBirthdateErr], [depSex, depSexErr],
      [depEmail, depEmailErr], [depPassword, depPasswordErr],
      [depPwConfirm, depPwConfirmErr],
    ];
    pairs.forEach(function (p) { clearErr(p[0], p[1]); });
  }

  function readDepToState(depIdx) {
    if (depIdx < 0 || depIdx >= state.deps.length) return;
    var prev = state.deps[depIdx] || {};
    state.deps[depIdx] = Object.assign({}, prev, {
      name:         depName      ? depName.value.trim()           : '',
      cpf:          depCpf       ? depCpf.value                   : '',
      birthdate:    depBirthdate ? depBirthdate.value              : '',
      sex:          depSex       ? depSex.value                    : '',
      phone:        depPhone     ? depPhone.value                  : '',
      email:        depEmail     ? depEmail.value.trim()           : '',
      password:     depPassword  ? depPassword.value               : '',
      pwConfirm:    depPwConfirm ? depPwConfirm.value              : '',
      kinship:      depKinship   ? depKinship.value                : '',
      kinshipOther: depKinshipOther ? depKinshipOther.value.trim() : '',
    });
  }

  function validateDep() {
    var valid = true;

    if (!depKinship.value) {
      showErr(depKinship, depKinshipErr, 'Campo obrigatório.'); valid = false;
    } else clearErr(depKinship, depKinshipErr);

    if (depKinship.value === 'other') {
      if (!depKinshipOther.value.trim()) {
        showErr(depKinshipOther, depKinshipOtherErr, 'Informe o grau de parentesco.'); valid = false;
      } else clearErr(depKinshipOther, depKinshipOtherErr);
    }

    if (!depName.value.trim()) {
      showErr(depName, depNameErr, 'Campo obrigatório.'); valid = false;
    } else clearErr(depName, depNameErr);

    var cpfD = depCpf.value.replace(/\D/g, '');
    if (!cpfD) {
      showErr(depCpf, depCpfErr, 'Campo obrigatório.'); valid = false;
    } else if (cpfD.length !== 11) {
      showErr(depCpf, depCpfErr, 'CPF inválido.'); valid = false;
    } else clearErr(depCpf, depCpfErr);

    var bd = depBirthdate.value.trim();
    if (!bd) {
      showErr(depBirthdate, depBirthdateErr, 'Campo obrigatório.'); valid = false;
    } else if (!/^\d{2}\/\d{2}\/\d{4}$/.test(bd)) {
      showErr(depBirthdate, depBirthdateErr, 'Use o formato DD/MM/AAAA.'); valid = false;
    } else clearErr(depBirthdate, depBirthdateErr);

    if (!depSex.value) {
      showErr(depSex, depSexErr, 'Campo obrigatório.'); valid = false;
    } else clearErr(depSex, depSexErr);

    var em = depEmail.value.trim();
    if (em && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(em)) {
      showErr(depEmail, depEmailErr, 'E-mail inválido.'); valid = false;
    } else clearErr(depEmail, depEmailErr);

    if (!depPassword.value) {
      showErr(depPassword, depPasswordErr, 'Campo obrigatório.'); valid = false;
    } else if (depPassword.value.length < 8) {
      showErr(depPassword, depPasswordErr, 'Mínimo 8 caracteres.'); valid = false;
    } else clearErr(depPassword, depPasswordErr);

    if (!depPwConfirm.value) {
      showErr(depPwConfirm, depPwConfirmErr, 'Campo obrigatório.'); valid = false;
    } else if (depPwConfirm.value !== depPassword.value) {
      showErr(depPwConfirm, depPwConfirmErr, 'As senhas não coincidem.'); valid = false;
    } else clearErr(depPwConfirm, depPwConfirmErr);

    return valid;
  }

  // ── Sincroniza deps no form hidden ───────────────────────────────────────────

  function syncDepsToForm() {
    if (state.deps.length === 0) return;

    var isHolder = (state.profile === PROFILE_HOLDER);
    var prefix   = isHolder ? 'dependent' : 'student';
    var dep0     = state.deps[0];
    var dep0Groups = dep0.classGroups || [];

    setHidden('id_' + prefix + '_name',             dep0.name);
    setHidden('id_' + prefix + '_cpf',              dep0.cpf);
    setHidden('id_' + prefix + '_birthdate',        dep0.birthdate);
    setHidden('id_' + prefix + '_biological_sex',   dep0.sex);
    setHidden('id_' + prefix + '_phone',            dep0.phone);
    setHidden('id_' + prefix + '_email',            dep0.email);
    setHidden('id_' + prefix + '_password',         dep0.password);
    setHidden('id_' + prefix + '_password_confirm', dep0.pwConfirm);
    setHidden('id_' + prefix + '_kinship_type',     dep0.kinship);
    setHidden('id_' + prefix + '_kinship_other_label', dep0.kinshipOther);
    setHidden('id_' + prefix + '_blood_type',       dep0.bloodType || '');
    setHidden('id_' + prefix + '_allergies',        dep0.allergies || '');
    setHidden('id_' + prefix + '_injuries',         dep0.injuries || '');
    setHidden('id_' + prefix + '_emergency_contact', dep0.emergencyContact || '');
    var dep0HasMA = dep0.hasMartialArt === 'yes';
    setHidden('id_' + prefix + '_has_martial_art',                dep0HasMA ? 'yes' : '');
    setHidden('id_' + prefix + '_martial_art',                    dep0HasMA ? (dep0.martialArt || '') : '');
    setHidden('id_' + prefix + '_martial_art_graduation',         dep0HasMA ? (dep0.martialArtGraduation || '') : '');
    setHidden('id_' + prefix + '_jiu_jitsu_belt',                 dep0HasMA ? (dep0.jiuJitsuBelt || '') : '');
    setHidden('id_' + prefix + '_jiu_jitsu_stripes',              dep0HasMA ? (dep0.jiuJitsuStripes || '0') : '');
    setHidden('id_' + prefix + '_martial_art_started_at',         dep0HasMA ? (dep0.martialArtStartedAt || '') : '');
    setHidden('id_' + prefix + '_martial_art_last_graduation_at', dep0HasMA ? (dep0.martialArtLastGraduationAt || '') : '');
    setHidden('id_' + prefix + '_previous_academy',               dep0HasMA ? (dep0.previousAcademy || '') : '');
    _syncClassGroupInputs(prefix + '_class_groups', dep0Groups);

    var extras = state.deps.slice(1).map(function (d) {
      var hasMA = d.hasMartialArt === 'yes';
      return {
        full_name:                        d.name,
        cpf:                              d.cpf,
        birth_date:                       d.birthdate,
        biological_sex:                   d.sex,
        phone:                            d.phone,
        email:                            d.email,
        password:                         d.password,
        password_confirm:                 d.pwConfirm,
        kinship_type:                     d.kinship,
        kinship_other_label:              d.kinshipOther,
        class_groups:                     d.classGroups || [],
        blood_type:                       d.bloodType || '',
        allergies:                        d.allergies || '',
        previous_injuries:                d.injuries || '',
        emergency_contact:                d.emergencyContact || '',
        martial_art:                      hasMA ? (d.martialArt || '') : '',
        martial_art_graduation:           hasMA ? (d.martialArtGraduation || '') : '',
        jiu_jitsu_belt:                   hasMA ? (d.jiuJitsuBelt || '') : '',
        jiu_jitsu_stripes:                hasMA ? (parseInt(d.jiuJitsuStripes, 10) || 0) : null,
        martial_art_started_at:           hasMA ? (d.martialArtStartedAt || '') : '',
        martial_art_last_graduation_at:   hasMA ? (d.martialArtLastGraduationAt || '') : '',
        previous_academy:                 hasMA ? (d.previousAcademy || '') : '',
      };
    });
    elExtraDepInput.value = JSON.stringify(extras);
  }

  // ── Turmas — sincronização com form ──────────────────────────────────────────

  function _syncClassGroupInputs(fieldName, ids) {
    var form = document.getElementById('wizard-form');
    if (!form) return;
    // Remove inputs existentes com esse name
    var existing = form.querySelectorAll('input[name="' + fieldName + '"]');
    existing.forEach(function (el) { el.parentNode.removeChild(el); });
    // Cria um input por id selecionado
    ids.forEach(function (id) {
      var inp = document.createElement('input');
      inp.type = 'hidden';
      inp.name = fieldName;
      inp.value = id;
      form.appendChild(inp);
    });
  }

  function syncClassesToForm() {
    var isHolder = (state.profile === PROFILE_HOLDER);
    if (isHolder) {
      // classSelections[0] = turma do holder
      _syncClassGroupInputs('holder_class_groups', state.classSelections[0]?.ids || []);
      // classSelections[1..N] = turma dos deps (armazenado em state.deps[i-1].classGroups)
      for (var i = 1; i < state.classSelections.length; i++) {
        if (state.deps[i - 1]) state.deps[i - 1].classGroups = state.classSelections[i].ids || [];
      }
    } else {
      // guardian: classSelections[i] = turma do student[i]
      // student[0] → id_student_class_groups
      // student[1..N] → extra payload
      for (var j = 0; j < state.classSelections.length; j++) {
        if (state.deps[j]) state.deps[j].classGroups = state.classSelections[j].ids || [];
      }
    }
    syncDepsToForm();
  }

  // ── Turmas — elementos e lógica de etapa ─────────────────────────────────────

  // ── Elementos — Etapa de saúde (step-health) ─────────────────────────────────

  var healthBadge      = document.getElementById('health-step-badge');
  var healthTitle      = document.getElementById('health-step-title');
  var healthBloodType  = document.getElementById('ui-health-blood-type');
  var healthAllergies  = document.getElementById('ui-health-allergies');
  var healthInjuries   = document.getElementById('ui-health-injuries');
  var healthEmergency  = document.getElementById('ui-health-emergency');
  var elStepHealthNext = document.getElementById('step-health-next');

  function getHealthData() {
    return {
      bloodType:        healthBloodType ? healthBloodType.value : '',
      allergies:        healthAllergies ? healthAllergies.value.trim() : '',
      injuries:         healthInjuries  ? healthInjuries.value.trim()  : '',
      emergencyContact: healthEmergency ? healthEmergency.value.trim() : '',
    };
  }

  function onEnterHealth(personIdx) {
    var person = getPersonForClass(personIdx);
    var label  = person.name || (isHolderPerson(personIdx) ? 'Você' : 'Dependente');
    if (healthBadge) healthBadge.textContent = 'Saúde — ' + label;
    if (healthTitle) healthTitle.textContent  = 'Dados de saúde';

    var data;
    if (isHolderPerson(personIdx)) {
      data = {
        bloodType:        getHidden('id_holder_blood_type'),
        allergies:        getHidden('id_holder_allergies'),
        injuries:         getHidden('id_holder_injuries'),
        emergencyContact: getHidden('id_holder_emergency_contact'),
      };
    } else {
      var dep = state.deps[getDepIdxForPerson(personIdx)] || {};
      data = {
        bloodType: dep.bloodType || '', allergies: dep.allergies || '',
        injuries: dep.injuries || '', emergencyContact: dep.emergencyContact || '',
      };
    }
    if (healthBloodType) healthBloodType.value = data.bloodType;
    if (healthAllergies) healthAllergies.value = data.allergies;
    if (healthInjuries)  healthInjuries.value  = data.injuries;
    if (healthEmergency) healthEmergency.value  = data.emergencyContact;
  }

  function collectHealth(personIdx) {
    var data = getHealthData();
    if (isHolderPerson(personIdx)) {
      setHidden('id_holder_blood_type',        data.bloodType);
      setHidden('id_holder_allergies',         data.allergies);
      setHidden('id_holder_injuries',          data.injuries);
      setHidden('id_holder_emergency_contact', data.emergencyContact);
    } else {
      var di = getDepIdxForPerson(personIdx);
      if (di >= 0 && di < state.deps.length) {
        Object.assign(state.deps[di], data);
      }
    }
  }

  // ── Elementos — Etapa de artes marciais (step-martial) ───────────────────────

  var martialBadge           = document.getElementById('martial-step-badge');
  var martialTitle           = document.getElementById('martial-step-title');
  var martialHas             = document.getElementById('ui-martial-has');
  var martialHasErr          = document.getElementById('ui-martial-has-error');
  var martialDetailSection   = document.getElementById('martial-detail-section');
  var martialArtEl           = document.getElementById('ui-martial-art');
  var martialArtErr          = document.getElementById('ui-martial-art-error');
  var martialAcademy         = document.getElementById('ui-martial-academy');
  var martialStarted         = document.getElementById('ui-martial-started');
  var martialStartedErr      = document.getElementById('ui-martial-started-error');
  var martialGraduation      = document.getElementById('ui-martial-graduation');
  var martialOtherGradField  = document.getElementById('martial-other-grad-field');
  var martialJjSection       = document.getElementById('martial-jj-section');
  var martialJjBelt          = document.getElementById('ui-martial-jj-belt');
  var martialJjBeltErr       = document.getElementById('ui-martial-jj-belt-error');
  var martialJjStripes       = document.getElementById('ui-martial-jj-stripes');
  var martialJjLastGrad      = document.getElementById('ui-martial-jj-last-grad');
  var martialJjLastGradErr   = document.getElementById('ui-martial-jj-last-grad-error');
  var elStepMartialNext      = document.getElementById('step-martial-next');

  function toggleMartialDetail(show) {
    if (martialDetailSection) martialDetailSection.hidden = !show;
  }

  function toggleMartialJj(show) {
    if (martialJjSection)      martialJjSection.hidden      = !show;
    if (martialOtherGradField) martialOtherGradField.hidden = show;
  }

  function getMartialData() {
    var hasMA = martialHas ? martialHas.value : '';
    if (hasMA !== 'yes') {
      return { hasMartialArt: hasMA, martialArt: '', martialArtGraduation: '',
               jiuJitsuBelt: '', jiuJitsuStripes: '0',
               martialArtStartedAt: '', martialArtLastGraduationAt: '', previousAcademy: '' };
    }
    var art = martialArtEl ? martialArtEl.value : '';
    var isJj = art === 'jiu_jitsu';
    return {
      hasMartialArt:            'yes',
      martialArt:               art,
      martialArtGraduation:     (!isJj && martialGraduation) ? martialGraduation.value.trim() : '',
      jiuJitsuBelt:             isJj ? (martialJjBelt ? martialJjBelt.value : '') : '',
      jiuJitsuStripes:          isJj ? (martialJjStripes ? martialJjStripes.value : '0') : '0',
      martialArtStartedAt:      martialStarted ? martialStarted.value : '',
      martialArtLastGraduationAt: isJj ? (martialJjLastGrad ? martialJjLastGrad.value : '') : '',
      previousAcademy:          martialAcademy ? martialAcademy.value.trim() : '',
    };
  }

  function onEnterMartial(personIdx) {
    var person = getPersonForClass(personIdx);
    var label  = person.name || (isHolderPerson(personIdx) ? 'Você' : 'Dependente');
    if (martialBadge) martialBadge.textContent = 'Histórico esportivo — ' + label;

    var data;
    if (isHolderPerson(personIdx)) {
      data = {
        hasMartialArt:            getHidden('id_holder_has_martial_art'),
        martialArt:               getHidden('id_holder_martial_art'),
        martialArtGraduation:     getHidden('id_holder_martial_art_graduation'),
        jiuJitsuBelt:             getHidden('id_holder_jiu_jitsu_belt'),
        jiuJitsuStripes:          getHidden('id_holder_jiu_jitsu_stripes') || '0',
        martialArtStartedAt:      getHidden('id_holder_martial_art_started_at'),
        martialArtLastGraduationAt: getHidden('id_holder_martial_art_last_graduation_at'),
        previousAcademy:          getHidden('id_holder_previous_academy'),
      };
    } else {
      var dep = state.deps[getDepIdxForPerson(personIdx)] || {};
      data = {
        hasMartialArt:            dep.hasMartialArt || '',
        martialArt:               dep.martialArt || '',
        martialArtGraduation:     dep.martialArtGraduation || '',
        jiuJitsuBelt:             dep.jiuJitsuBelt || '',
        jiuJitsuStripes:          dep.jiuJitsuStripes || '0',
        martialArtStartedAt:      dep.martialArtStartedAt || '',
        martialArtLastGraduationAt: dep.martialArtLastGraduationAt || '',
        previousAcademy:          dep.previousAcademy || '',
      };
    }

    if (martialHas)       martialHas.value       = data.hasMartialArt;
    if (martialArtEl)     martialArtEl.value      = data.martialArt;
    if (martialAcademy)   martialAcademy.value    = data.previousAcademy;
    if (martialStarted)   martialStarted.value    = data.martialArtStartedAt;
    if (martialGraduation) martialGraduation.value = data.martialArtGraduation;
    if (martialJjBelt)    martialJjBelt.value     = data.jiuJitsuBelt;
    if (martialJjStripes) martialJjStripes.value  = data.jiuJitsuStripes;
    if (martialJjLastGrad) martialJjLastGrad.value = data.martialArtLastGraduationAt;

    var hasMA = data.hasMartialArt === 'yes';
    toggleMartialDetail(hasMA);
    toggleMartialJj(hasMA && data.martialArt === 'jiu_jitsu');

    // Limpa erros
    clearErr(martialHas, martialHasErr);
    clearErr(martialArtEl, martialArtErr);
    clearErr(martialJjBelt, martialJjBeltErr);
    clearErr(martialJjLastGrad, martialJjLastGradErr);
    clearErr(martialStarted, martialStartedErr);
  }

  function validateMartial() {
    var valid = true;
    if (!martialHas || !martialHas.value) {
      showErr(martialHas, martialHasErr, 'Campo obrigatório.'); valid = false;
    } else {
      clearErr(martialHas, martialHasErr);
    }
    if (martialHas && martialHas.value === 'yes') {
      if (!martialArtEl || !martialArtEl.value) {
        showErr(martialArtEl, martialArtErr, 'Selecione a modalidade.'); valid = false;
      } else {
        clearErr(martialArtEl, martialArtErr);
      }
      if (martialArtEl && martialArtEl.value === 'jiu_jitsu') {
        if (!martialJjBelt || !martialJjBelt.value) {
          showErr(martialJjBelt, martialJjBeltErr, 'Selecione sua faixa atual.'); valid = false;
        } else {
          clearErr(martialJjBelt, martialJjBeltErr);
        }
        if (martialStarted && martialStarted.value && !/^\d{2}\/\d{2}\/\d{4}$/.test(martialStarted.value)) {
          showErr(martialStarted, martialStartedErr, 'Use DD/MM/AAAA.'); valid = false;
        } else {
          clearErr(martialStarted, martialStartedErr);
        }
        if (martialJjLastGrad && martialJjLastGrad.value && !/^\d{2}\/\d{2}\/\d{4}$/.test(martialJjLastGrad.value)) {
          showErr(martialJjLastGrad, martialJjLastGradErr, 'Use DD/MM/AAAA.'); valid = false;
        } else {
          clearErr(martialJjLastGrad, martialJjLastGradErr);
        }
      }
    }
    return valid;
  }

  function collectMartial(personIdx) {
    var data = getMartialData();
    if (isHolderPerson(personIdx)) {
      setHidden('id_holder_has_martial_art',                data.hasMartialArt);
      setHidden('id_holder_martial_art',                    data.martialArt);
      setHidden('id_holder_martial_art_graduation',         data.martialArtGraduation);
      setHidden('id_holder_jiu_jitsu_belt',                 data.jiuJitsuBelt);
      setHidden('id_holder_jiu_jitsu_stripes',              data.jiuJitsuStripes);
      setHidden('id_holder_martial_art_started_at',         data.martialArtStartedAt);
      setHidden('id_holder_martial_art_last_graduation_at', data.martialArtLastGraduationAt);
      setHidden('id_holder_previous_academy',               data.previousAcademy);
    } else {
      var di = getDepIdxForPerson(personIdx);
      if (di >= 0 && di < state.deps.length) {
        Object.assign(state.deps[di], data);
      }
    }
  }

  // ── Elementos — Etapa de turma ─────────────────────────────────────────────

  var elClassCatalog    = document.getElementById('class-catalog-list');
  var elClassBadge      = document.getElementById('class-step-badge');
  var elClassTitle      = document.getElementById('class-step-title');
  var elClassSubtitle   = document.getElementById('class-step-subtitle');
  var elClassError      = document.getElementById('class-step-error');
  var elStepClassesNext = document.getElementById('step-classes-next');

  // ── Plano — catálogo e estado ─────────────────────────────────────────────────

  var planCatalog = (function () {
    try {
      var el = document.getElementById('reg-plan-catalog-json');
      return el ? JSON.parse(el.textContent) : [];
    } catch (e) { return []; }
  })();

  var CYCLE_ORDER  = ['monthly', 'quarterly', 'semiannual', 'annual'];
  var CYCLE_LABELS = { monthly: 'Mensal', quarterly: 'Trimestral', semiannual: 'Semestral', annual: 'Anual' };
  var METHOD_LABELS = { pix: 'PIX', credit_card: 'Cartão' };

  var planFilter    = { frequency: null, cycle: null, method: null };
  var selectedPlanId = null;

  function fmtPrice(val) {
    var n = parseFloat(val);
    return isNaN(n) ? 'R$ —' : 'R$ ' + n.toFixed(2).replace('.', ',');
  }

  function planFreqs() {
    var seen = {};
    getEligiblePlans().forEach(function (p) { seen[p.weekly_frequency] = true; });
    return Object.keys(seen).map(Number).sort(function (a, b) { return a - b; });
  }

  function planCycles() {
    var seen = {};
    getEligiblePlans().forEach(function (p) { seen[p.billing_cycle] = true; });
    return CYCLE_ORDER.filter(function (c) { return seen[c]; });
  }

  function planMethods() {
    var seen = {};
    getEligiblePlans().forEach(function (p) { seen[p.payment_method] = true; });
    return Object.keys(seen);
  }

  function getFilteredPlans() {
    return getEligiblePlans().filter(function (p) {
      if (planFilter.frequency !== null && p.weekly_frequency !== planFilter.frequency) return false;
      if (planFilter.cycle   && p.billing_cycle   !== planFilter.cycle)   return false;
      if (planFilter.method  && p.payment_method  !== planFilter.method)  return false;
      return true;
    });
  }

  function renderPlanFilters() {
    var area = document.getElementById('plan-filters-area');
    if (!area) return;

    var freqs   = planFreqs();
    var cycles  = planCycles();
    var methods = planMethods();

    var eligible = getEligiblePlans();
    if (eligible.length === 0) { area.innerHTML = ''; return; }

    // Auto-seleciona quando só há uma opção
    if (freqs.length === 1   && planFilter.frequency === null) planFilter.frequency = freqs[0];
    if (methods.length === 1 && planFilter.method   === null)  planFilter.method   = methods[0];

    var html = '';

    // Frequência
    if (freqs.length > 1) {
      html += '<div class="plan-filter-section"><p class="plan-filter-label">Frequência semanal</p><div class="plan-filter-row">';
      freqs.forEach(function (f) {
        var active = planFilter.frequency === f ? ' plan-filter-pill--active' : '';
        html += '<button type="button" class="plan-filter-pill' + active + '" data-filter="frequency" data-value="' + f + '">' + f + 'x por semana</button>';
      });
      html += '</div></div>';
    }

    // Ciclo
    if (cycles.length > 0) {
      html += '<div class="plan-filter-section"><p class="plan-filter-label">Período de cobrança</p><div class="plan-filter-row">';
      cycles.forEach(function (c) {
        var active  = planFilter.cycle === c ? ' plan-filter-pill--active' : '';
        var savings = (c === 'annual') ? '<span class="plan-filter-pill__badge">Melhor valor</span>' : (c === 'semiannual' ? '<span class="plan-filter-pill__badge">Economize</span>' : '');
        html += '<button type="button" class="plan-filter-pill' + active + '" data-filter="cycle" data-value="' + escHtml(c) + '">' + escHtml(CYCLE_LABELS[c] || c) + savings + '</button>';
      });
      html += '</div></div>';
    }

    // Método
    if (methods.length > 1) {
      html += '<div class="plan-filter-section"><p class="plan-filter-label">Forma de pagamento</p><div class="plan-filter-row">';
      methods.forEach(function (m) {
        var active = planFilter.method === m ? ' plan-filter-pill--active' : '';
        html += '<button type="button" class="plan-filter-pill' + active + '" data-filter="method" data-value="' + escHtml(m) + '">' + escHtml(METHOD_LABELS[m] || m) + '</button>';
      });
      html += '</div></div>';
    }

    area.innerHTML = html;
    area.querySelectorAll('.plan-filter-pill').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var key = btn.getAttribute('data-filter');
        var val = btn.getAttribute('data-value');
        if (key === 'frequency') planFilter.frequency = parseInt(val, 10);
        else if (key === 'cycle')   planFilter.cycle   = val;
        else if (key === 'method')  planFilter.method  = val;
        renderPlanFilters();
        renderPlanCards();
      });
    });
  }

  function renderPlanCards() {
    var area = document.getElementById('plan-cards-area');
    if (!area) return;

    var plans = getFilteredPlans();

    if (plans.length === 0) {
      var emptyMsg = planCatalog.length === 0
        ? 'Nenhum plano cadastrado ainda. Execute o seed de planos para continuar.'
        : getEligiblePlans().length === 0
          ? 'Nenhum plano disponível para o seu perfil de cadastro.'
          : 'Nenhum plano disponível para os filtros selecionados.';
      area.innerHTML = '<p class="plan-cards--empty">' + emptyMsg + '</p>';
      return;
    }

    var html = '<div class="plan-cards">';
    plans.forEach(function (plan) {
      var isSelected = plan.id === selectedPlanId;
      var price      = plan.payment_method === 'pix' ? plan.charge_pix : plan.charge_card;
      var tierLabel  = plan.name || plan.commercial_tier_label || plan.code;
      var isFeatured = /fidel|loyal/i.test(plan.code || '');

      html += '<button type="button" class="plan-card' + (isSelected ? ' plan-card--selected' : '') + '" data-plan-id="' + plan.id + '" aria-pressed="' + (isSelected ? 'true' : 'false') + '">';
      html += '<div class="plan-card__radio"><div class="plan-card__radio-dot"></div></div>';
      html += '<div class="plan-card__body">';

      // Cabeçalho
      html += '<div class="plan-card__header">';
      html += '<p class="plan-card__tier">' + escHtml(tierLabel) + '</p>';
      if (isFeatured) html += '<span class="plan-card__badge">Recomendado</span>';
      html += '</div>';

      // Preço
      html += '<div class="plan-card__price-wrap">';
      html += '<span class="plan-card__price">' + fmtPrice(price) + '</span>';
      html += '<span class="plan-card__price-cycle">/' + escHtml(plan.cycle || '') + '</span>';
      html += '</div>';

      // Parcelas
      if (plan.installment_count > 1 && plan.installment_label) {
        html += '<p class="plan-card__installment">' + escHtml(plan.installment_label) + '</p>';
      }

      // Frequência
      if (plan.weekly_frequency_label) {
        html += '<p class="plan-card__meta">' + escHtml(plan.weekly_frequency_label) + '</p>';
      }

      // Auth
      if (plan.requires_special_authorization) {
        html += '<p class="plan-card__auth-note">Requer autorização da academia</p>';
      }

      html += '</div></button>';
    });
    html += '</div>';
    area.innerHTML = html;

    area.querySelectorAll('.plan-card').forEach(function (card) {
      card.addEventListener('click', function () {
        selectPlan(parseInt(card.getAttribute('data-plan-id'), 10));
      });
    });
  }

  function selectPlan(planId) {
    selectedPlanId = planId;
    setHidden('id_selected_plan', planId);
    var plan = planCatalog.find(function (p) { return p.id === planId; });
    if (plan) {
      setHidden('id_checkout_action', plan.payment_method === 'pix' ? 'pix' : 'stripe');
    }
    renderPlanCards();
    var err = document.getElementById('plan-step-error');
    if (err) { err.hidden = true; err.textContent = ''; }
  }

  function validatePlan() {
    if (!selectedPlanId) {
      var err = document.getElementById('plan-step-error');
      if (err) { err.textContent = 'Selecione um plano para continuar.'; err.hidden = false; }
      return false;
    }
    return true;
  }

  function onEnterPlan() {
    if (!planFilter.cycle) {
      var cycles = planCycles();
      if (cycles.length) planFilter.cycle = cycles[0];
    }
    if (!planFilter.frequency) {
      var freqs = planFreqs();
      if (freqs.length) planFilter.frequency = freqs[0];
    }
    if (!planFilter.method) {
      var methods = planMethods();
      if (methods.length) planFilter.method = methods[0];
    }
    renderPlanFilters();
    renderPlanCards();
  }

  // ── Checkout — resumo e pagamento ─────────────────────────────────────────────

  function getSelectedPlan() {
    if (!selectedPlanId) return null;
    return planCatalog.find(function (p) { return p.id === selectedPlanId; }) || null;
  }

  function onEnterCheckout() {
    var summaryArea  = document.getElementById('checkout-summary-area');
    var actionsArea  = document.getElementById('checkout-actions-area');
    var plan         = getSelectedPlan();
    var isHolder     = state.profile === PROFILE_HOLDER;
    var numPersons   = isHolder ? (1 + state.deps.length) : state.deps.length;

    // ── Resumo ──
    var sumHtml = '<div class="checkout-summary">';

    if (plan) {
      var price = plan.payment_method === 'pix' ? plan.charge_pix : plan.charge_card;
      sumHtml += '<div class="checkout-summary__section">';
      sumHtml += '<p class="checkout-summary__label">Plano selecionado</p>';
      sumHtml += '<div class="checkout-summary__plan-row">';
      sumHtml += '<span class="checkout-summary__plan-name">' + escHtml(plan.commercial_tier_label || '') + '</span>';
      sumHtml += '<span class="checkout-summary__plan-price">' + fmtPrice(price) + ' <small>/' + escHtml(plan.cycle || '') + '</small></span>';
      sumHtml += '</div>';
      var metaParts = [];
      if (plan.payment_method_label) metaParts.push(plan.payment_method_label);
      if (plan.weekly_frequency_label) metaParts.push(plan.weekly_frequency_label);
      if (metaParts.length) sumHtml += '<p class="checkout-summary__plan-meta">' + escHtml(metaParts.join(' · ')) + '</p>';
      if (plan.installment_count > 1 && plan.installment_label) {
        sumHtml += '<p class="checkout-summary__plan-installment">' + escHtml(plan.installment_label) + '</p>';
      }
      sumHtml += '</div>';
    }

    if (numPersons > 0) {
      var personLabel = isHolder ? 'Você' : '';
      if (state.deps.length > 0) {
        var depWord = isHolder ? 'dependente' : 'aluno';
        if (isHolder) {
          personLabel = '1 titular + ' + state.deps.length + ' ' + (state.deps.length === 1 ? depWord : depWord + 's');
        } else {
          personLabel = state.deps.length + ' ' + (state.deps.length === 1 ? depWord : depWord + 's');
        }
      }
      sumHtml += '<div class="checkout-summary__section">';
      sumHtml += '<p class="checkout-summary__label">Matrículas</p>';
      sumHtml += '<p class="checkout-summary__value">' + escHtml(personLabel || (numPersons + ' pessoa(s)')) + '</p>';
      sumHtml += '</div>';
    }

    sumHtml += '</div>';
    if (summaryArea) summaryArea.innerHTML = sumHtml;

    // ── Ações ──
    if (!actionsArea) return;
    var actHtml = '';

    if (plan) {
      var isPix = plan.payment_method === 'pix';
      actHtml += '<button type="button" class="btn-checkout-pay" id="btn-pay-now">';
      actHtml += isPix
        ? '<svg class="btn-checkout-pay__icon" xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg> Pagar com PIX'
        : '<svg class="btn-checkout-pay__icon" xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg> Pagar com Cartão';
      actHtml += '</button>';
    }

    actHtml += '<button type="button" class="btn-checkout-later" id="btn-pay-later">Concluir e pagar depois</button>';
    actionsArea.innerHTML = actHtml;

    var btnNow = document.getElementById('btn-pay-now');
    if (btnNow) {
      btnNow.addEventListener('click', function () {
        var p = getSelectedPlan();
        setHidden('id_checkout_action', (p && p.payment_method === 'pix') ? 'pix' : 'stripe');
        document.getElementById('wizard-form').submit();
      });
    }

    var btnLater = document.getElementById('btn-pay-later');
    if (btnLater) {
      btnLater.addEventListener('click', function () {
        setHidden('id_checkout_action', 'pay_later');
        document.getElementById('wizard-form').submit();
      });
    }
  }

  // ── Catálogo de turmas (declarado após as funções de plano) ───────────────────

  var catalogGroups = (function () {
    try {
      var el = document.getElementById('reg-catalog-json');
      return el ? JSON.parse(el.textContent) : [];
    } catch (e) { return []; }
  })();

  var ibjjfCategories = (function () {
    try {
      var el = document.getElementById('reg-ibjjf-json');
      return el ? JSON.parse(el.textContent) : [];
    } catch (e) { return []; }
  })();

  var WEEKDAY_ABBREV = {
    'Segunda-feira': 'Seg', 'Terça-feira': 'Ter', 'Quarta-feira': 'Qua',
    'Quinta-feira': 'Qui', 'Sexta-feira': 'Sex', 'Sábado': 'Sáb', 'Domingo': 'Dom',
  };

  function calcAgeYears(birthdateStr) {
    if (!birthdateStr) return null;
    var parts = birthdateStr.split('/');
    if (parts.length !== 3) return null;
    var d = new Date(parseInt(parts[2]), parseInt(parts[1]) - 1, parseInt(parts[0]));
    if (isNaN(d.getTime())) return null;
    var today = new Date();
    var age = today.getFullYear() - d.getFullYear();
    if (today.getMonth() < d.getMonth() || (today.getMonth() === d.getMonth() && today.getDate() < d.getDate())) age--;
    return age;
  }

  function resolveAudience(birthdateStr) {
    var age = calcAgeYears(birthdateStr);
    if (age === null) return null;
    if (ibjjfCategories.length === 0) return age >= 16 ? 'adult' : (age >= 10 ? 'juvenile' : 'kids');
    var sorted = ibjjfCategories.slice().sort(function (a, b) { return a.minimum_age - b.minimum_age; });
    for (var i = 0; i < sorted.length; i++) {
      var cat = sorted[i];
      var maxOk = cat.maximum_age === null || cat.maximum_age === undefined || age <= cat.maximum_age;
      if (age >= cat.minimum_age && maxOk) return cat.audience;
    }
    return null;
  }

  function filterGroupsByPerson(groups, person) {
    var audience = resolveAudience(person.birthdate);
    if (!audience) return groups; // sem data de nascimento → exibe tudo
    var sex = person.sex;
    return groups.filter(function (g) {
      var ga = g.category_audience;
      if (audience === 'adult') {
        if (ga === 'adult') return true;
        if (ga === 'women' && sex === 'female') return true;
        return false;
      }
      if (audience === 'juvenile') return ga === 'juvenile' || ga === 'kids';
      if (audience === 'kids')     return ga === 'kids' || ga === 'juvenile';
      return ga === audience;
    });
  }

  function onEnterClasses(classPersonIdx) {
    var person = getPersonForClass(classPersonIdx);
    var numClassSteps = state.classSelections.length;
    var isHolder = (state.profile === PROFILE_HOLDER);

    if (elClassBadge) {
      if (numClassSteps === 1) {
        elClassBadge.textContent = isHolder ? 'Sua turma' : 'Turma do aluno';
      } else {
        var personLabel = isHolder
          ? (classPersonIdx === 0 ? 'Você' : 'Dependente ' + classPersonIdx)
          : 'Aluno ' + (classPersonIdx + 1);
        elClassBadge.textContent = 'Turma de ' + personLabel + ' (' + (classPersonIdx + 1) + ' de ' + numClassSteps + ')';
      }
    }

    if (elClassSubtitle) {
      elClassSubtitle.textContent = person.name
        ? 'Turma para ' + person.name
        : 'Selecione a turma que deseja frequentar';
    }

    if (elClassError) { elClassError.textContent = ''; elClassError.hidden = true; }

    var filteredGroups = filterGroupsByPerson(catalogGroups, person);
    var selectedIds = (state.classSelections[classPersonIdx] || { ids: [] }).ids;
    renderClassCatalog(filteredGroups, selectedIds, classPersonIdx);
  }

  function renderClassCatalog(groups, selectedIds, classPersonIdx) {
    if (!elClassCatalog) return;
    elClassCatalog.innerHTML = '';

    if (!groups || groups.length === 0) {
      var empty = document.createElement('p');
      empty.className = 'class-catalog--empty';
      empty.textContent = 'Nenhuma turma disponível para este perfil.';
      elClassCatalog.appendChild(empty);
      return;
    }

    groups.forEach(function (group) {
      var isSelected = selectedIds.indexOf(group.id) !== -1;
      var card = document.createElement('button');
      card.type = 'button';
      card.className = 'class-card' + (isSelected ? ' class-card--selected' : '');
      card.setAttribute('aria-pressed', isSelected ? 'true' : 'false');
      card.setAttribute('data-group-id', group.id);

      // Título
      var titleText = escHtml(group.category_name) +
        (group.display_name ? ' · ' + escHtml(group.display_name) : '');

      // Tabela de horários agrupada por dia usando compact_schedule_sections
      var scheduleHtml = '';
      var sections = group.compact_schedule_sections || [];
      if (sections.length) {
        var rows = sections.map(function (sec) {
          var abbrev = WEEKDAY_ABBREV[sec.weekday_label] || sec.weekday_label.substring(0, 3);
          var times = sec.entries.map(function (e) { return escHtml(e.time_label); }).join('  ·  ');
          return '<div class="class-card__day-row">' +
            '<span class="class-card__day-name">' + escHtml(abbrev) + '</span>' +
            '<span class="class-card__day-times">' + times + '</span>' +
            '</div>';
        }).join('');
        scheduleHtml = '<div class="class-card__divider"></div>' +
          '<div class="class-card__schedule-table">' + rows + '</div>';
      }

      card.innerHTML =
        '<div class="class-card__radio"><div class="class-card__radio-dot"></div></div>' +
        '<div class="class-card__body">' +
          '<p class="class-card__title">' + titleText + '</p>' +
          scheduleHtml +
        '</div>';

      card.addEventListener('click', function () {
        selectClassGroup(classPersonIdx, group.id);
      });

      elClassCatalog.appendChild(card);
    });
  }

  function escHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function selectClassGroup(classPersonIdx, groupId) {
    if (!state.classSelections[classPersonIdx]) return;
    // Seleção única: substitui o array
    state.classSelections[classPersonIdx].ids = [groupId];
    // Atualiza visual dos cards
    if (!elClassCatalog) return;
    elClassCatalog.querySelectorAll('.class-card').forEach(function (card) {
      var selected = card.getAttribute('data-group-id') === groupId;
      card.classList.toggle('class-card--selected', selected);
      card.setAttribute('aria-pressed', selected ? 'true' : 'false');
    });
    // Limpa erro ao selecionar
    if (elClassError) { elClassError.textContent = ''; elClassError.hidden = true; }
  }

  function validateClasses(classPersonIdx) {
    var sel = state.classSelections[classPersonIdx];
    if (!sel || sel.ids.length === 0) {
      if (elClassError) { elClassError.textContent = 'Selecione uma turma para continuar.'; elClassError.hidden = false; }
      return false;
    }
    return true;
  }

  // ── Eventos — Etapa de perfil ─────────────────────────────────────────────────

  if (elHolderDepChk) {
    elHolderDepChk.addEventListener('change', function () {
      var checked = elHolderDepChk.checked;
      elHolderCountArea.hidden = !checked;
      state.holderDepCount = checked ? 1 : 0;
      if (checked) renderHolderDepCount();
      syncHolderDeps();
      buildStepSequence();
      updateProgress();
    });
  }

  if (elHolderDepDec) {
    elHolderDepDec.addEventListener('click', function () {
      if (state.holderDepCount > 1) {
        state.holderDepCount--;
        renderHolderDepCount();
        syncHolderDeps();
        buildStepSequence();
        updateProgress();
      }
    });
  }

  if (elHolderDepInc) {
    elHolderDepInc.addEventListener('click', function () {
      if (state.holderDepCount < MAX_DEPENDENTS) {
        state.holderDepCount++;
        renderHolderDepCount();
        syncHolderDeps();
        buildStepSequence();
        updateProgress();
      }
    });
  }

  if (elStudentDec) {
    elStudentDec.addEventListener('click', function () {
      if (state.guardianStudentCount > 1) {
        state.guardianStudentCount--;
        renderGuardianStudentCount();
        syncGuardianStudents();
        buildStepSequence();
        updateProgress();
      }
    });
  }

  if (elStudentInc) {
    elStudentInc.addEventListener('click', function () {
      if (state.guardianStudentCount < MAX_DEPENDENTS) {
        state.guardianStudentCount++;
        renderGuardianStudentCount();
        syncGuardianStudents();
        buildStepSequence();
        updateProgress();
      }
    });
  }

  if (elProfileHolder)   elProfileHolder.addEventListener('click',   function () { selectProfile(PROFILE_HOLDER); });
  if (elProfileGuardian) elProfileGuardian.addEventListener('click', function () { selectProfile(PROFILE_GUARDIAN); });

  if (elStep1Next) {
    elStep1Next.addEventListener('click', function () {
      if (state.profile) goTo(1); // step-principal
    });
  }

  // ── Eventos — Etapa principal ─────────────────────────────────────────────────

  bindMask(s2Cpf,       maskCpf);
  bindMask(s2Phone,     maskPhone);
  bindMask(s2Birthdate, maskDate);
  setupPasswordToggle('ui-s2-password',         'ui-s2-pw-toggle');
  setupPasswordToggle('ui-s2-password-confirm', 'ui-s2-pwc-toggle');

  if (elStep2Next) {
    elStep2Next.addEventListener('click', function () {
      if (!validatePrincipal()) return;
      collectPrincipal();
      goTo(state.stepIndex + 1);
    });
  }

  // ── Eventos — Etapa dependente ────────────────────────────────────────────────

  if (depKinship) {
    depKinship.addEventListener('change', function () {
      toggleKinshipOther(depKinship.value);
    });
  }

  bindMask(depCpf,       maskCpf);
  bindMask(depPhone,     maskPhone);
  bindMask(depBirthdate, maskDate);
  setupPasswordToggle('ui-dep-password',         'ui-dep-pw-toggle');
  setupPasswordToggle('ui-dep-password-confirm', 'ui-dep-pwc-toggle');

  if (elStepDepNext) {
    elStepDepNext.addEventListener('click', function () {
      if (!validateDep()) return;
      var di = depIndexAt(state.stepIndex);
      readDepToState(di);
      syncDepsToForm();
      goTo(state.stepIndex + 1);
    });
  }

  // ── Eventos — Etapa de saúde ─────────────────────────────────────────────────

  if (elStepHealthNext) {
    elStepHealthNext.addEventListener('click', function () {
      var pi = healthPersonIndexAt(state.stepIndex);
      collectHealth(pi);
      goTo(state.stepIndex + 1);
    });
  }

  // ── Eventos — Etapa de artes marciais ────────────────────────────────────────

  if (martialHas) {
    martialHas.addEventListener('change', function () {
      toggleMartialDetail(martialHas.value === 'yes');
      if (martialHas.value !== 'yes') toggleMartialJj(false);
    });
  }

  if (martialArtEl) {
    martialArtEl.addEventListener('change', function () {
      toggleMartialJj(martialArtEl.value === 'jiu_jitsu');
    });
  }

  bindMask(martialStarted,    maskDate);
  bindMask(martialJjLastGrad, maskDate);

  if (elStepMartialNext) {
    elStepMartialNext.addEventListener('click', function () {
      if (!validateMartial()) return;
      var pi = martialPersonIndexAt(state.stepIndex);
      collectMartial(pi);
      goTo(state.stepIndex + 1);
    });
  }

  // ── Eventos — Plano ──────────────────────────────────────────────────────────

  var elStepPlanNext = document.getElementById('step-plan-next');
  if (elStepPlanNext) {
    elStepPlanNext.addEventListener('click', function () {
      if (!validatePlan()) return;
      goTo(state.stepIndex + 1);
    });
  }

  // ── Eventos — Etapa de turma ─────────────────────────────────────────────────

  if (elStepClassesNext) {
    elStepClassesNext.addEventListener('click', function () {
      var ci = classPersonIndexAt(state.stepIndex);
      if (!validateClasses(ci)) return;
      syncClassesToForm();
      goTo(state.stepIndex + 1);
    });
  }

  // ── Botão Voltar ──────────────────────────────────────────────────────────────

  if (elWizardBack) {
    elWizardBack.addEventListener('click', function (e) {
      if (state.stepIndex === 0) return; // deixa navegar para login
      e.preventDefault();
      var currentId = state.stepSequence[state.stepIndex];
      if (currentId === 'step-dep') {
        readDepToState(depIndexAt(state.stepIndex));
      } else if (currentId === 'step-health') {
        collectHealth(healthPersonIndexAt(state.stepIndex));
      } else if (currentId === 'step-martial') {
        collectMartial(martialPersonIndexAt(state.stepIndex));
      }
      goTo(state.stepIndex - 1);
    });
  }

  // ── Inicialização ─────────────────────────────────────────────────────────────

  var initialProfile = elProfileInput ? elProfileInput.value : '';
  if (initialProfile === PROFILE_HOLDER || initialProfile === PROFILE_GUARDIAN) {
    selectProfile(initialProfile);
    if (initialProfile === PROFILE_HOLDER && elIncludeDepInput && elIncludeDepInput.value) {
      if (elHolderDepChk) {
        elHolderDepChk.checked  = true;
        elHolderCountArea.hidden = false;
        state.holderDepCount = 1;
        try {
          var ex = JSON.parse(elExtraDepInput.value || '[]');
          state.holderDepCount = ex.length + 1;
        } catch (e) {}
        renderHolderDepCount();
        buildStepSequence();
      }
    }
  } else {
    buildStepSequence();
  }

  renderGuardianStudentCount();
  renderHolderDepCount();
  updateProgress();

})();
