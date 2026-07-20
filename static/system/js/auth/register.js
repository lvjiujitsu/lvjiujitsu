(function () {
  'use strict';

  var Wz = window.LV && window.LV.Wizard;
  var DOM = window.LV && window.LV.DOM;
  if (!Wz || !DOM) {
    if (typeof console !== 'undefined' && console.error) {
      console.error('[LV register] wizard_shared.js e dom_utils.js são obrigatórios');
    }
    return;
  }

  var el = DOM.el;
  var clearChildren = DOM.clearChildren;

  function fillMarkup(node, html) {
    clearChildren(node);
    if (html) node.appendChild(DOM.parseMarkup(html));
  }

  function svgIcon(markup) {
    var frag = DOM.parseMarkup(markup);
    return frag.firstChild;
  }

  var wizardForm = document.getElementById('wizard-form');
  var wizardEndpoints = Wz.getFormEndpoints(wizardForm);
  var escHtml = Wz.escapeHtml;

  var PROFILE_HOLDER   = 'holder';
  var PROFILE_GUARDIAN = 'guardian';
  var PROFILE_TEACHER_REQUEST = 'teacher_request';
  var PROFILE_ADMINISTRATIVE_REQUEST = 'administrative_request';
  var OPERATIONAL_TYPE_CODES = {
    teacher_request: 'instructor',
    administrative_request: 'administrative-assistant',
  };
  var MAX_DEPENDENTS   = 5;

  var TRAILING_STEPS = ['step-plan', 'step-products', 'step-review'];

  var state = {
    profile:              null,
    holderDepCount:       0,
    guardianStudentCount: 1,
    stepSequence:         [],
    stepIndex:            0,
    deps:                 [],
    classSelections:      [],
    planSelections:       [],
    teacherProposedSchedule: null,
    teacherExistingClassSelections: [],
    eligibility: { fetchKey: null, planIds: null, pending: false },
  };

  var productCart = [];
  var configureProduct = null;
  var configureColor = null;
  var configureVariantId = null;
  var configureQty = 1;

  function maskCpf(value) {
    var d = value.replace(/\D/g, '').slice(0, 11);
    if (d.length <= 3) return d;
    if (d.length <= 6) return d.slice(0, 3) + '.' + d.slice(3);
    if (d.length <= 9) return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6);
    return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9);
  }

  function isValidCpf(digits) {
    if (digits.length !== 11 || /^(\d)\1+$/.test(digits)) return false;
    function checkDigit(d, len) {
      var s = 0;
      for (var i = 0; i < len; i++) s += parseInt(d[i]) * (len + 1 - i);
      var r = s % 11;
      return r < 2 ? 0 : 11 - r;
    }
    return parseInt(digits[9]) === checkDigit(digits, 9) &&
           parseInt(digits[10]) === checkDigit(digits, 10);
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

  function maskCep(value) {
    var d = value.replace(/\D/g, '').slice(0, 8);
    if (d.length <= 5) return d;
    return d.slice(0, 5) + '-' + d.slice(5);
  }

  function fetchCep(cep) {
    if (!s2Address || !s2AddressNeighborhood || !s2City) return;
    fetch('https://viacep.com.br/ws/' + cep + '/json/')
      .then(function (res) { return res.json(); })
      .then(function (data) {
        if (data.erro) return;
        if (data.logradouro && !s2Address.value.trim())
          s2Address.value = data.logradouro;
        if (data.bairro && !s2AddressNeighborhood.value.trim())
          s2AddressNeighborhood.value = data.bairro;
        if (data.localidade && !s2City.value.trim())
          s2City.value = data.localidade;
      })
      .catch(function (err) {
        Wz.warn('cep', 'Falha ao consultar CEP', err);
      });
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

  function isOperationalProfile(profile) {
    return profile === PROFILE_TEACHER_REQUEST || profile === PROFILE_ADMINISTRATIVE_REQUEST;
  }

  function isWizardRegistrationProfile(profile) {
    return profile === PROFILE_HOLDER || profile === PROFILE_GUARDIAN || isOperationalProfile(profile);
  }

  function getOperationalTypeCode(profile) {
    return OPERATIONAL_TYPE_CODES[profile] || '';
  }

  function buildStepSequence() {
    if (isOperationalProfile(state.profile)) {
      var operationalSeq = ['step-profile', 'step-principal', 'step-health', 'step-martial'];
      operationalSeq.push(
        state.profile === PROFILE_TEACHER_REQUEST
          ? 'step-teacher-schedule'
          : 'step-administrative-access'
      );
      operationalSeq.push('step-operational-finance');
      state.stepSequence = operationalSeq;
      state.deps.length = 0;
      state.classSelections.length = 0;
      state.planSelections.length = 0;
      return;
    }

    var numDeps = (state.profile === PROFILE_HOLDER)
      ? state.holderDepCount
      : state.guardianStudentCount;

    var seq = ['step-profile', 'step-principal'];

    if (state.profile === PROFILE_HOLDER) {

      seq.push('step-health');
      seq.push('step-martial');
      for (var i = 0; i < numDeps; i++) {
        seq.push('step-dep');
        seq.push('step-health');
        seq.push('step-martial');
      }
    } else {

      seq.push('step-health');
      seq.push('step-martial');
      for (var i = 0; i < numDeps; i++) {
        seq.push('step-dep');
        seq.push('step-health');
        seq.push('step-martial');
      }
    }

    var numClassSteps = (state.profile === PROFILE_HOLDER) ? (1 + numDeps) : numDeps;
    for (var j = 0; j < numClassSteps; j++) seq.push('step-classes');

    seq = seq.concat(TRAILING_STEPS);
    state.stepSequence = seq;

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

  function getEligiblePlans() {
    var numPersons = totalTrainingPersons();
    return planCatalog.filter(function (p) {
      if (p.is_loyalty_plan) return false;
      if (p.is_family_plan)  return numPersons >= 2;
      return true;
    });
  }

  function depIndexAt(seqIdx) {
    var count = 0;
    for (var i = 0; i <= seqIdx; i++) {
      if (state.stepSequence[i] === 'step-dep') count++;
    }
    return count - 1;
  }

  function classPersonIndexAt(seqIdx) {
    var count = 0;
    for (var i = 0; i <= seqIdx; i++) {
      if (state.stepSequence[i] === 'step-classes') count++;
    }
    return count - 1;
  }

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

  function isHolderPerson(personIdx) {
    return state.profile === PROFILE_HOLDER && personIdx === 0;
  }

  function isGuardianPrincipal(personIdx) {
    return state.profile === PROFILE_GUARDIAN && personIdx === 0;
  }

  function isOtherPrincipal(personIdx) {
    return isOperationalProfile(state.profile) && personIdx === 0;
  }

  function getDepIdxForPerson(personIdx) {
    return personIdx - 1;
  }

  function getPersonForClass(classPersonIdx) {
    if (isOperationalProfile(state.profile)) {
      return {
        name: getHidden('id_other_name') || 'Você',
        sex: getHidden('id_other_biological_sex'),
        birthdate: getHidden('id_other_birthdate'),
      };
    }
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

  function hideAllWizardSteps() {
    document.querySelectorAll('.wizard-step').forEach(function (el) {
      el.hidden = true;
    });
  }

  function showOnlyWizardStep(stepId) {
    hideAllWizardSteps();
    var targetEl = document.getElementById(stepId);
    if (targetEl) targetEl.hidden = false;
    return targetEl;
  }

  function normalizeIdList(values) {
    if (!values) return [];
    var rawValues = Array.isArray(values) ? values : [values];
    var result = [];
    rawValues.forEach(function (value) {
      var normalized = String(value || '').trim();
      if (normalized && result.indexOf(normalized) === -1) result.push(normalized);
    });
    return result;
  }

  function buildPendingDep(student) {
    return {
      name: student.full_name || '', cpf: '', birthdate: '', sex: '', phone: '', email: '',
      password: '', pwConfirm: '', kinship: '', kinshipOther: '',
      classGroups: normalizeIdList(student.class_group_ids),
      bloodType: '', allergies: '', injuries: '', emergencyContact: '',
      hasMartialArt: '', martialArt: '', martialArtGraduation: '',
      jiuJitsuBelt: '', jiuJitsuStripes: '0',
      martialArtStartedAt: '', martialArtLastGraduationAt: '', previousAcademy: '',
    };
  }

  function applyPendingClassSelections(students) {
    if (state.profile === PROFILE_HOLDER) {
      if (state.classSelections[0]) {
        state.classSelections[0].ids = normalizeIdList(pendingPersonData.class_group_ids);
      }
      students.forEach(function (student, index) {
        var selection = state.classSelections[index + 1];
        if (selection) selection.ids = normalizeIdList(student.class_group_ids);
      });
      return;
    }
    students.forEach(function (student, index) {
      var selection = state.classSelections[index];
      if (selection) selection.ids = normalizeIdList(student.class_group_ids);
    });
  }

  function rehydratePendingWizardState() {
    if (!pendingPersonData) return false;
    var students = Array.isArray(pendingPersonData.students) ? pendingPersonData.students : [];
    if (pendingPersonData.person_type_code === PROFILE_GUARDIAN) {
      state.profile = PROFILE_GUARDIAN;
      state.holderDepCount = 0;
      state.guardianStudentCount = Math.max(1, students.length || 1);
    } else {
      state.profile = PROFILE_HOLDER;
      state.holderDepCount = students.length;
      state.guardianStudentCount = 1;
    }
    state.deps = students.map(buildPendingDep);
    buildStepSequence();
    applyPendingClassSelections(students);
    return state.stepSequence.length > 0;
  }

  function goTo(targetIdx) {
    if (!state.stepSequence.length) buildStepSequence();
    if (targetIdx < 0 || targetIdx >= state.stepSequence.length) return;
    var targetId  = state.stepSequence[targetIdx];
    if (!showOnlyWizardStep(targetId)) return;

    state.stepIndex = targetIdx;
    updateProgress();
    onEnterStep(targetId, targetIdx);
    window.scrollTo({ top: 0, behavior: 'smooth' });
    saveWizardState();
  }

  function onEnterStep(stepId, seqIdx) {
    if (stepId === 'step-principal') onEnterPrincipal();
    if (stepId === 'step-dep')       onEnterDep(depIndexAt(seqIdx));
    if (stepId === 'step-health')    onEnterHealth(healthPersonIndexAt(seqIdx));
    if (stepId === 'step-martial')   onEnterMartial(martialPersonIndexAt(seqIdx));
    if (stepId === 'step-teacher-schedule') onEnterTeacherSchedule();
    if (stepId === 'step-administrative-access') onEnterAdministrativeAccess();
    if (stepId === 'step-operational-finance') onEnterOperationalFinance();
    if (stepId === 'step-classes')   onEnterClasses(classPersonIndexAt(seqIdx));
    if (stepId === 'step-plan')      onEnterPlan();
  }

  var elProfileHolder   = document.getElementById('profile-card-holder');
  var elProfileGuardian = document.getElementById('profile-card-guardian');
  var elProfileTeacherRequest = document.getElementById('profile-card-teacher-request');
  var elProfileAdministrativeRequest = document.getElementById('profile-card-administrative-request');
  var elProfileOptions  = document.querySelector('.profile-options');
  var elHolderSub       = document.getElementById('holder-suboption');
  var elHolderDepChk    = document.getElementById('include-dependent-checkbox');
  var elHolderCountArea = document.getElementById('holder-count-area');
  var elHolderDepVal    = document.getElementById('holder-dep-value');
  var elHolderDepDec    = document.getElementById('holder-dep-dec');
  var elHolderDepInc    = document.getElementById('holder-dep-inc');
  var elGuardianSub     = document.getElementById('guardian-suboption');
  var elTeacherRequestSub = document.getElementById('teacher-request-suboption');
  var elAdministrativeRequestSub = document.getElementById('administrative-request-suboption');
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
    [
      elProfileHolder,
      elProfileGuardian,
      elProfileTeacherRequest,
      elProfileAdministrativeRequest,
    ].forEach(function (el) {
      if (!el) return;
      el.setAttribute(
        'aria-pressed',
        el.getAttribute('data-profile') === profile ? 'true' : 'false'
      );
    });
    if (elHolderSub) elHolderSub.hidden = (profile !== PROFILE_HOLDER);
    if (elGuardianSub) elGuardianSub.hidden = (profile !== PROFILE_GUARDIAN);
    if (elTeacherRequestSub) {
      elTeacherRequestSub.hidden = (profile !== PROFILE_TEACHER_REQUEST);
    }
    if (elAdministrativeRequestSub) {
      elAdministrativeRequestSub.hidden = (profile !== PROFILE_ADMINISTRATIVE_REQUEST);
    }
    if (profile === PROFILE_HOLDER) {
      state.holderDepCount = 0;
      if (elHolderDepChk)    elHolderDepChk.checked  = false;
      if (elHolderCountArea) elHolderCountArea.hidden = true;
      renderHolderDepCount();
      syncHolderDeps();
    } else if (profile === PROFILE_GUARDIAN) {
      state.guardianStudentCount = 1;
      renderGuardianStudentCount();
      syncGuardianStudents();
    } else if (isOperationalProfile(profile)) {
      state.holderDepCount = 0;
      state.guardianStudentCount = 1;
      if (elIncludeDepInput) elIncludeDepInput.value = '';
      if (elExtraDepInput) elExtraDepInput.value = '[]';
      state.deps.length = 0;
      state.classSelections.length = 0;
      state.planSelections.length = 0;
      if (profile !== PROFILE_TEACHER_REQUEST) {
        state.teacherExistingClassSelections = [];
        state.teacherProposedSchedule = null;
      }
      syncOperationalProfileToHiddenFields(profile);
    } else {
      state.holderDepCount = 0;
      state.guardianStudentCount = 1;
      if (elIncludeDepInput) elIncludeDepInput.value = '';
      if (elExtraDepInput) elExtraDepInput.value = '[]';
      state.teacherExistingClassSelections = [];
      state.teacherProposedSchedule = null;
    }
    if (!isOperationalProfile(profile)) {
      elProfileInput.value = isWizardRegistrationProfile(profile) ? profile : '';
      setHidden('id_other_type_code', '');
    }
    elStep1Next.disabled = false;
    elStep1Next.setAttribute('aria-disabled', 'false');
    buildStepSequence();
    updateProgress();
    saveWizardState();
  }

  function getCheckedValue(name, fallback) {
    var checked = document.querySelector('input[name="' + name + '"]:checked');
    return checked ? checked.value : fallback;
  }

  function getCheckedValues(name) {
    return Array.prototype.slice.call(document.querySelectorAll('input[name="' + name + '"]:checked'))
      .map(function (input) { return input.value; })
      .filter(Boolean);
  }

  function syncOperationalProfileToHiddenFields(profile) {
    if (!isOperationalProfile(profile)) return;
    setHidden('id_registration_profile', 'other');
    setHidden('id_other_type_code', getOperationalTypeCode(profile));
    setHidden('id_include_dependent', '');
    setHidden('id_extra_dependents_payload', '[]');
  }

  var s2Name          = document.getElementById('ui-s2-name');
  var s2NameError     = document.getElementById('ui-s2-name-error');
  var s2Cpf           = document.getElementById('ui-s2-cpf');
  var s2CpfError      = document.getElementById('ui-s2-cpf-error');
  var s2CpfAvailability = { value: '', available: true, pending: false, error: '' };
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
  var s2PostalCode    = document.getElementById('ui-s2-postal-code');
  var s2Address       = document.getElementById('ui-s2-address');
  var s2AddressNumber = document.getElementById('ui-s2-address-number');
  var s2AddressComplement   = document.getElementById('ui-s2-address-complement');
  var s2AddressNeighborhood = document.getElementById('ui-s2-address-neighborhood');
  var s2City          = document.getElementById('ui-s2-city');
  var s2Subtitle      = document.getElementById('s2-subtitle');
  var elStep2Next     = document.getElementById('step-2-next');

  function getPrincipalPrefix() {
    if (state.profile === PROFILE_HOLDER) return 'holder';
    if (state.profile === PROFILE_GUARDIAN) return 'guardian';
    if (isOperationalProfile(state.profile)) return 'other';
    return 'holder';
  }

  function onEnterPrincipal() {
    var isHolder = (state.profile === PROFILE_HOLDER);
    var isGuardian = (state.profile === PROFILE_GUARDIAN);
    var isOperational = isOperationalProfile(state.profile);
    var requiresBirthdate = !isGuardian;
    if (s2BirthdateWrap) s2BirthdateWrap.hidden = !requiresBirthdate;
    if (s2Subtitle) {
      s2Subtitle.textContent = isHolder
        ? 'Preencha suas informações de cadastro'
        : (isOperational ? 'Dados pessoais do perfil solicitado' : 'Seus dados como responsável pelo aluno');
    }
    var prefix = getPrincipalPrefix();
    var fields  = [
      [s2Name,                  'id_' + prefix + '_name'],
      [s2Cpf,                   'id_' + prefix + '_cpf'],
      [s2Sex,                   'id_' + prefix + '_biological_sex'],
      [s2Phone,                 'id_' + prefix + '_phone'],
      [s2Email,                 'id_' + prefix + '_email'],
      [s2PostalCode,            'id_' + prefix + '_postal_code'],
      [s2Address,               'id_' + prefix + '_address'],
      [s2AddressNumber,         'id_' + prefix + '_address_number'],
      [s2AddressComplement,     'id_' + prefix + '_address_complement'],
      [s2AddressNeighborhood,   'id_' + prefix + '_address_neighborhood'],
      [s2City,                  'id_' + prefix + '_city'],
    ];
    fields.forEach(function (pair) {
      var v = getHidden(pair[1]);
      if (pair[0] && v) pair[0].value = v;
    });
    if (requiresBirthdate && s2Birthdate) {
      var bd = getHidden('id_' + prefix + '_birthdate');
      if (bd) s2Birthdate.value = bd;
    }
  }

  function validatePrincipal() {
    var valid    = true;
    var requiresBirthdate = (state.profile !== PROFILE_GUARDIAN);

    if (!s2Name.value.trim()) {
      showErr(s2Name, s2NameError, 'Campo obrigatório.'); valid = false;
    } else clearErr(s2Name, s2NameError);

    var cpfDigits = s2Cpf.value.replace(/\D/g, '');
    if (!cpfDigits) {
      showErr(s2Cpf, s2CpfError, 'Campo obrigatório.'); valid = false;
    } else if (!isValidCpf(cpfDigits)) {
      showErr(s2Cpf, s2CpfError, 'CPF inválido.'); valid = false;
    } else if (s2CpfAvailability.value === s2Cpf.value && s2CpfAvailability.available === false) {
      showErr(s2Cpf, s2CpfError, s2CpfAvailability.error || 'CPF já cadastrado no sistema.'); valid = false;
    } else clearErr(s2Cpf, s2CpfError);

    if (requiresBirthdate) {
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
    var prefix = getPrincipalPrefix();
    var requiresBirthdate = (state.profile !== PROFILE_GUARDIAN);
    setHidden('id_' + prefix + '_name',                 s2Name.value.trim());
    setHidden('id_' + prefix + '_cpf',                  s2Cpf.value);
    setHidden('id_' + prefix + '_biological_sex',       s2Sex.value);
    setHidden('id_' + prefix + '_phone',                s2Phone.value);
    setHidden('id_' + prefix + '_email',                s2Email.value.trim());
    setHidden('id_' + prefix + '_password',             s2Password.value);
    setHidden('id_' + prefix + '_password_confirm',     s2PwConfirm.value);
    if (s2PostalCode)            setHidden('id_' + prefix + '_postal_code',            s2PostalCode.value.trim());
    if (s2Address)               setHidden('id_' + prefix + '_address',                s2Address.value.trim());
    if (s2AddressNumber)         setHidden('id_' + prefix + '_address_number',         s2AddressNumber.value.trim());
    if (s2AddressComplement)     setHidden('id_' + prefix + '_address_complement',     s2AddressComplement.value.trim());
    if (s2AddressNeighborhood)   setHidden('id_' + prefix + '_address_neighborhood',   s2AddressNeighborhood.value.trim());
    if (s2City)                  setHidden('id_' + prefix + '_city',                   s2City.value.trim());
    if (requiresBirthdate) setHidden('id_' + prefix + '_birthdate', s2Birthdate.value);
    syncOperationalProfileToHiddenFields(state.profile);
  }

  function checkCpfAvailability(input, errorEl, stateRef) {
    if (!input) return;
    var cpf = input.value;
    var digits = cpf.replace(/\D/g, '');
    stateRef.value = cpf;
    stateRef.available = true;
    stateRef.error = '';
    if (digits.length !== 11) return;
    stateRef.pending = true;
    fetch('/register/check-cpf/?cpf=' + encodeURIComponent(cpf), {
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        if (stateRef.value !== cpf) return;
        stateRef.pending = false;
        stateRef.available = !!data.available;
        stateRef.error = data.error || '';
        if (!data.available) {
          showErr(input, errorEl, stateRef.error || 'CPF já cadastrado no sistema.');
        } else {
          clearErr(input, errorEl);
        }
      })
      .catch(function () {
        stateRef.pending = false;
      });
  }

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
    } else if (!isValidCpf(cpfD)) {
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

  function _syncClassGroupInputs(fieldName, ids) {
    var form = document.getElementById('wizard-form');
    if (!form) return;

    var existing = form.querySelectorAll('input[name="' + fieldName + '"]');
    existing.forEach(function (el) { el.parentNode.removeChild(el); });

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

      _syncClassGroupInputs('holder_class_groups', state.classSelections[0]?.ids || []);

      for (var i = 1; i < state.classSelections.length; i++) {
        if (state.deps[i - 1]) state.deps[i - 1].classGroups = state.classSelections[i].ids || [];
      }
    } else {

      for (var j = 0; j < state.classSelections.length; j++) {
        if (state.deps[j]) state.deps[j].classGroups = state.classSelections[j].ids || [];
      }
    }
    syncDepsToForm();
  }

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
    var label;
    if (isHolderPerson(personIdx)) {
      label = getHidden('id_holder_name') || 'Você';
    } else if (isGuardianPrincipal(personIdx)) {
      label = getHidden('id_guardian_name') || 'Responsável';
    } else if (isOtherPrincipal(personIdx)) {
      label = getHidden('id_other_name') || 'Você';
    } else {
      var p = getPersonForClass(personIdx);
      label = p.name || 'Dependente';
    }
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
    } else if (isGuardianPrincipal(personIdx)) {
      data = {
        bloodType:        getHidden('id_guardian_blood_type'),
        allergies:        getHidden('id_guardian_allergies'),
        injuries:         getHidden('id_guardian_injuries'),
        emergencyContact: getHidden('id_guardian_emergency_contact'),
      };
    } else if (isOtherPrincipal(personIdx)) {
      data = {
        bloodType:        getHidden('id_other_blood_type'),
        allergies:        getHidden('id_other_allergies'),
        injuries:         getHidden('id_other_injuries'),
        emergencyContact: getHidden('id_other_emergency_contact'),
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
    } else if (isGuardianPrincipal(personIdx)) {
      setHidden('id_guardian_blood_type',        data.bloodType);
      setHidden('id_guardian_allergies',         data.allergies);
      setHidden('id_guardian_injuries',          data.injuries);
      setHidden('id_guardian_emergency_contact', data.emergencyContact);
    } else if (isOtherPrincipal(personIdx)) {
      setHidden('id_other_blood_type',        data.bloodType);
      setHidden('id_other_allergies',         data.allergies);
      setHidden('id_other_injuries',          data.injuries);
      setHidden('id_other_emergency_contact', data.emergencyContact);
    } else {
      var di = getDepIdxForPerson(personIdx);
      if (di >= 0 && di < state.deps.length) {
        Object.assign(state.deps[di], data);
      }
    }
  }

  var martialBadge           = document.getElementById('martial-step-badge');
  var martialTitle           = document.getElementById('martial-step-title');
  var martialHas             = document.getElementById('ui-martial-has');
  var martialHasErr          = document.getElementById('ui-martial-has-error');
  var martialToggleNo        = document.getElementById('martial-toggle-no');
  var martialToggleYes       = document.getElementById('martial-toggle-yes');
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

  function _syncMartialHasPills(value) {
    if (martialToggleNo)  martialToggleNo.classList.toggle('martial-has-btn--active',  value !== 'yes');
    if (martialToggleYes) martialToggleYes.classList.toggle('martial-has-btn--active', value === 'yes');
  }

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
    var label;
    if (isHolderPerson(personIdx)) {
      label = getHidden('id_holder_name') || 'Você';
    } else if (isGuardianPrincipal(personIdx)) {
      label = getHidden('id_guardian_name') || 'Responsável';
    } else if (isOtherPrincipal(personIdx)) {
      label = getHidden('id_other_name') || 'Você';
    } else {
      var p = getPersonForClass(personIdx);
      label = p.name || 'Dependente';
    }
    if (martialBadge) martialBadge.textContent = 'Histórico esportivo — ' + label;

    var data;
    if (isHolderPerson(personIdx)) {
      data = {
        hasMartialArt:              getHidden('id_holder_has_martial_art'),
        martialArt:                 getHidden('id_holder_martial_art'),
        martialArtGraduation:       getHidden('id_holder_martial_art_graduation'),
        jiuJitsuBelt:               getHidden('id_holder_jiu_jitsu_belt'),
        jiuJitsuStripes:            getHidden('id_holder_jiu_jitsu_stripes') || '0',
        martialArtStartedAt:        getHidden('id_holder_martial_art_started_at'),
        martialArtLastGraduationAt: getHidden('id_holder_martial_art_last_graduation_at'),
        previousAcademy:            getHidden('id_holder_previous_academy'),
      };
    } else if (isGuardianPrincipal(personIdx)) {
      data = {
        hasMartialArt:              getHidden('id_guardian_has_martial_art'),
        martialArt:                 getHidden('id_guardian_martial_art'),
        martialArtGraduation:       getHidden('id_guardian_martial_art_graduation'),
        jiuJitsuBelt:               getHidden('id_guardian_jiu_jitsu_belt'),
        jiuJitsuStripes:            getHidden('id_guardian_jiu_jitsu_stripes') || '0',
        martialArtStartedAt:        getHidden('id_guardian_martial_art_started_at'),
        martialArtLastGraduationAt: getHidden('id_guardian_martial_art_last_graduation_at'),
        previousAcademy:            getHidden('id_guardian_previous_academy'),
      };
    } else if (isOtherPrincipal(personIdx)) {
      data = {
        hasMartialArt:              getHidden('id_other_has_martial_art'),
        martialArt:                 getHidden('id_other_martial_art'),
        martialArtGraduation:       getHidden('id_other_martial_art_graduation'),
        jiuJitsuBelt:               getHidden('id_other_jiu_jitsu_belt'),
        jiuJitsuStripes:            getHidden('id_other_jiu_jitsu_stripes') || '0',
        martialArtStartedAt:        getHidden('id_other_martial_art_started_at'),
        martialArtLastGraduationAt: getHidden('id_other_martial_art_last_graduation_at'),
        previousAcademy:            getHidden('id_other_previous_academy'),
      };
    } else {
      var dep = state.deps[getDepIdxForPerson(personIdx)] || {};
      data = {
        hasMartialArt:              dep.hasMartialArt || '',
        martialArt:                 dep.martialArt || '',
        martialArtGraduation:       dep.martialArtGraduation || '',
        jiuJitsuBelt:               dep.jiuJitsuBelt || '',
        jiuJitsuStripes:            dep.jiuJitsuStripes || '0',
        martialArtStartedAt:        dep.martialArtStartedAt || '',
        martialArtLastGraduationAt: dep.martialArtLastGraduationAt || '',
        previousAcademy:            dep.previousAcademy || '',
      };
    }

    var resolvedHas = data.hasMartialArt || 'no';
    if (martialHas)       martialHas.value       = resolvedHas;
    if (martialArtEl)     martialArtEl.value      = data.martialArt;
    if (martialAcademy)   martialAcademy.value    = data.previousAcademy;
    if (martialStarted)   martialStarted.value    = data.martialArtStartedAt;
    if (martialGraduation) martialGraduation.value = data.martialArtGraduation;
    if (martialJjBelt)    martialJjBelt.value     = data.jiuJitsuBelt;
    if (martialJjStripes) martialJjStripes.value  = data.jiuJitsuStripes;
    if (martialJjLastGrad) martialJjLastGrad.value = data.martialArtLastGraduationAt;

    var hasMA = resolvedHas === 'yes';
    _syncMartialHasPills(resolvedHas);
    toggleMartialDetail(hasMA);
    toggleMartialJj(hasMA && data.martialArt === 'jiu_jitsu');

    clearErr(martialHas, martialHasErr);
    clearErr(martialArtEl, martialArtErr);
    clearErr(martialJjBelt, martialJjBeltErr);
    clearErr(martialJjLastGrad, martialJjLastGradErr);
    clearErr(martialStarted, martialStartedErr);
  }

  function validateMartial() {
    var valid = true;

    clearErr(martialHas, martialHasErr);
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
    } else if (isGuardianPrincipal(personIdx)) {
      setHidden('id_guardian_has_martial_art',                data.hasMartialArt);
      setHidden('id_guardian_martial_art',                    data.martialArt);
      setHidden('id_guardian_martial_art_graduation',         data.martialArtGraduation);
      setHidden('id_guardian_jiu_jitsu_belt',                 data.jiuJitsuBelt);
      setHidden('id_guardian_jiu_jitsu_stripes',              data.jiuJitsuStripes);
      setHidden('id_guardian_martial_art_started_at',         data.martialArtStartedAt);
      setHidden('id_guardian_martial_art_last_graduation_at', data.martialArtLastGraduationAt);
      setHidden('id_guardian_previous_academy',               data.previousAcademy);
    } else if (isOtherPrincipal(personIdx)) {
      setHidden('id_other_has_martial_art',                data.hasMartialArt);
      setHidden('id_other_martial_art',                    data.martialArt);
      setHidden('id_other_martial_art_graduation',         data.martialArtGraduation);
      setHidden('id_other_jiu_jitsu_belt',                 data.jiuJitsuBelt);
      setHidden('id_other_jiu_jitsu_stripes',              data.jiuJitsuStripes);
      setHidden('id_other_martial_art_started_at',         data.martialArtStartedAt);
      setHidden('id_other_martial_art_last_graduation_at', data.martialArtLastGraduationAt);
      setHidden('id_other_previous_academy',               data.previousAcademy);
    } else {
      var di = getDepIdxForPerson(personIdx);
      if (di >= 0 && di < state.deps.length) {
        Object.assign(state.deps[di], data);
      }
    }
  }

  var elClassCatalog    = document.getElementById('class-catalog-list');
  var elClassBadge      = document.getElementById('class-step-badge');
  var elClassTitle      = document.getElementById('class-step-title');
  var elClassSubtitle   = document.getElementById('class-step-subtitle');
  var elClassError      = document.getElementById('class-step-error');
  var elStepClassesNext = document.getElementById('step-classes-next');

  var planCatalog = (function () {
    try {
      var el = document.getElementById('reg-plan-catalog-json');
      return el ? JSON.parse(el.textContent) : [];
    } catch (e) { return []; }
  })();

  var productCatalog = (function () {
    try {
      var el = document.getElementById('reg-product-catalog-json');
      return el ? JSON.parse(el.textContent) : [];
    } catch (e) { return []; }
  })();

  var regPostPlan = (function () {
    try {
      var el = document.getElementById('reg-post-plan-json');
      return el ? JSON.parse(el.textContent) : false;
    } catch (e) { return false; }
  })();

  var regPlanIsTrial = (function () {
    try {
      var el = document.getElementById('reg-plan-is-trial-json');
      return el ? JSON.parse(el.textContent) : false;
    } catch (e) { return false; }
  })();

  var regPostMaterials = (function () {
    try {
      var el = document.getElementById('reg-post-materials-json');
      return el ? JSON.parse(el.textContent) : false;
    } catch (e) { return false; }
  })();

  var regPostMaterialsSkipped = (function () {
    try {
      var el = document.getElementById('reg-post-materials-skipped-json');
      return el ? JSON.parse(el.textContent) : false;
    } catch (e) { return false; }
  })();

  var planOrderData = (function () {
    try {
      var el = document.getElementById('reg-plan-order-json');
      return el ? JSON.parse(el.textContent) : null;
    } catch (e) { return null; }
  })();

  var materialsOrderData = (function () {
    try {
      var el = document.getElementById('reg-materials-order-json');
      return el ? JSON.parse(el.textContent) : null;
    } catch (e) { return null; }
  })();

  var pendingPersonData = (function () {
    try {
      var el = document.getElementById('reg-pending-person-json');
      return el ? JSON.parse(el.textContent) : null;
    } catch (e) { return null; }
  })();

  var CYCLE_ORDER  = ['monthly', 'quarterly', 'semiannual', 'annual'];
  var CYCLE_LABELS = { monthly: 'Mensal', quarterly: 'Trimestral', semiannual: 'Semestral', annual: 'Anual' };
  var METHOD_LABELS = { pix: 'PIX', credit_card: 'Cartão' };
  var STATIC_URL = (window.STATIC_URL || '/static/');
  var PAYMENT_METHOD_ICONS = {
    pix: '<span class="payment-method-icons payment-method-icons--pix" aria-hidden="true">' +
      '<img class="payment-method-icon payment-method-icon--pix" src="' + STATIC_URL + 'system/img/icons/pix.svg" alt="">' +
      '</span>',
    credit_card: '<span class="payment-method-icons payment-method-icons--card" aria-hidden="true">' +
      '<img class="payment-method-icon payment-method-icon--brand" src="' + STATIC_URL + 'system/img/icons/mastercard.svg" alt="">' +
      '<img class="payment-method-icon payment-method-icon--brand" src="' + STATIC_URL + 'system/img/icons/visa.svg" alt="">' +
      '</span>',
  };

  var planFilter    = { frequency: null, cycle: null, method: null };
  var currentPlanPersonIndex = 0;

  function fmtPrice(val) {
    var n = parseFloat(val);
    return isNaN(n) ? 'R$ —' : 'R$ ' + n.toFixed(2).replace('.', ',');
  }

  function getTrainingPersonsForPlans() {
    var persons = [];
    if (state.profile === PROFILE_HOLDER) {
      persons.push({
        label: getHidden('id_holder_name') || 'Titular',
        birthdate: getHidden('id_holder_birthdate') || '',
        sex: getHidden('id_holder_biological_sex') || '',
      });
      state.deps.forEach(function (dep, idx) {
        persons.push({
          label: dep.name || ('Dependente ' + (idx + 1)),
          birthdate: dep.birthdate || '',
          sex: dep.sex || '',
        });
      });
      return persons;
    }
    state.deps.forEach(function (dep, idx) {
      persons.push({
        label: dep.name || ('Aluno ' + (idx + 1)),
        birthdate: dep.birthdate || '',
        sex: dep.sex || '',
      });
    });
    return persons;
  }

  function ensurePlanSelections() {
    var persons = getTrainingPersonsForPlans();
    while (state.planSelections.length < persons.length) {
      state.planSelections.push({ personIndex: state.planSelections.length, label: '', planId: null });
    }
    state.planSelections.length = persons.length;
    persons.forEach(function (person, index) {
      state.planSelections[index].personIndex = index;
      state.planSelections[index].label = person.label;
    });
    if (currentPlanPersonIndex >= persons.length) currentPlanPersonIndex = Math.max(0, persons.length - 1);
  }

  function getWizardCsrfToken() {
    return window.LV.getCsrfToken();
  }

  function buildEligibilityRequestPayload() {
    var payload = {
      registration_profile: state.profile,
      include_dependent: state.profile === PROFILE_HOLDER && state.holderDepCount > 0,
    };
    if (state.profile === PROFILE_HOLDER) {
      payload.holder_birthdate = getHidden('id_holder_birthdate') || '';
      payload.holder_class_groups = (state.classSelections[0] || { ids: [] }).ids;
      if (state.holderDepCount > 0) {
        var dep0 = state.deps[0] || {};
        payload.dependent_birthdate = dep0.birthdate || '';
        payload.dependent_class_groups = (state.classSelections[1] || { ids: [] }).ids;
      }
    } else if (state.profile === PROFILE_GUARDIAN) {
      var student0 = state.deps[0] || {};
      payload.student_birthdate = student0.birthdate || '';
      payload.student_class_groups = (state.classSelections[0] || { ids: [] }).ids;
    }
    return payload;
  }

  function refreshEligibilityFromServer(onUpdated) {
    if (isOperationalProfile(state.profile)) return;
    Wz.fetchEligibility({
      url: wizardEndpoints.eligibilityUrl,
      csrfToken: getWizardCsrfToken(),
      payload: buildEligibilityRequestPayload(),
      cache: state.eligibility,
      onUpdated: onUpdated,
    });
  }

  function getEligiblePlansForCurrentPerson() {
    var persons = getTrainingPersonsForPlans();
    var person = persons[currentPlanPersonIndex] || persons[0] || {};
    var audience = resolveAudience(person.birthdate);

    var serverKey = Wz.eligibilityFetchKey(buildEligibilityRequestPayload());
    var baseEligible;
    if (state.eligibility.planIds && state.eligibility.fetchKey === serverKey) {
      var idSet = {};
      state.eligibility.planIds.forEach(function (id) { idSet[id] = true; });
      baseEligible = getEligiblePlans().filter(function (p) { return idSet[p.id]; });
    } else {

      var sameAudienceCount = persons.filter(function (p) {
        var personAudience = resolveAudience(p.birthdate);
        if (audience === 'adult') return personAudience === 'adult';
        return personAudience === 'kids' || personAudience === 'juvenile';
      }).length;
      baseEligible = getEligiblePlans().filter(function (p) {
        if (!audience) return true;
        if (p.audience === 'adult' && audience !== 'adult') return false;
        if (p.audience === 'kids_juvenile' && audience !== 'kids' && audience !== 'juvenile') return false;
        if (p.is_family_plan) return sameAudienceCount >= 2;
        return true;
      });
      return baseEligible;
    }

    if (!audience) return baseEligible;
    return baseEligible.filter(function (p) {
      if (p.audience === 'adult') return audience === 'adult';
      if (p.audience === 'kids_juvenile') return audience === 'kids' || audience === 'juvenile';
      return true;
    });
  }

  function planFreqs() {
    var seen = {};
    getEligiblePlansForCurrentPerson().forEach(function (p) { seen[p.weekly_frequency] = true; });
    return Object.keys(seen).map(Number).sort(function (a, b) { return a - b; });
  }

  function planCycles() {
    var seen = {};
    getEligiblePlansForCurrentPerson().forEach(function (p) { seen[p.billing_cycle] = true; });
    return CYCLE_ORDER.filter(function (c) { return seen[c]; });
  }

  function planMethods() {
    var seen = {};
    getEligiblePlansForCurrentPerson().forEach(function (p) { seen[p.payment_method] = true; });
    return Object.keys(seen);
  }

  function getFilteredPlans() {
    var filtered = getEligiblePlansForCurrentPerson().filter(function (p) {
      if (planFilter.frequency !== null && p.weekly_frequency !== planFilter.frequency) return false;

      if (planFilter.cycle && p.billing_cycle !== planFilter.cycle) return false;
      if (planFilter.method && p.payment_method !== planFilter.method) return false;
      return true;
    });

    filtered.sort(function (a, b) {
      var aStripe = a.gateway_code === 'stripe_card' ? 1 : 0;
      var bStripe = b.gateway_code === 'stripe_card' ? 1 : 0;
      return aStripe - bStripe;
    });
    return filtered;
  }

  function renderPlanPersonTabs() {
    var area = document.getElementById('plan-person-tabs-area');
    if (!area) {
      var filters = document.getElementById('plan-filters-area');
      if (!filters || !filters.parentNode) return;
      area = document.createElement('div');
      area.id = 'plan-person-tabs-area';
      filters.parentNode.insertBefore(area, filters);
    }
    ensurePlanSelections();
    var persons = getTrainingPersonsForPlans();
    if (persons.length <= 1) {
      clearChildren(area);
      return;
    }
    var html = '<div class="plan-filter-section"><p class="plan-filter-label">Plano por aluno</p><div class="plan-filter-row">';
    persons.forEach(function (person, index) {
      var selected = state.planSelections[index] && state.planSelections[index].planId;
      html += '<button type="button" class="plan-filter-pill' + (index === currentPlanPersonIndex ? ' plan-filter-pill--active' : '') + '" data-plan-person="' + index + '">';
      html += escHtml(person.label);
      if (selected) html += '<span class="plan-filter-pill__badge">Selecionado</span>';
      html += '</button>';
    });
    html += '</div></div>';
    fillMarkup(area, html);
    area.querySelectorAll('[data-plan-person]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        currentPlanPersonIndex = parseInt(this.getAttribute('data-plan-person'), 10);
        planFilter.cycle = null;
        planFilter.frequency = null;
        renderPlanPersonTabs();
        onEnterPlan();
      });
    });
  }

  function renderPlanFilters() {
    var area = document.getElementById('plan-filters-area');
    if (!area) return;

    var freqs   = planFreqs();
    var cycles  = planCycles();
    var methods = planMethods();

    var eligible = getEligiblePlansForCurrentPerson();
    if (eligible.length === 0) { clearChildren(area); return; }

    if (freqs.length === 1   && planFilter.frequency === null) planFilter.frequency = freqs[0];
    if (methods.length === 1 && planFilter.method   === null)  planFilter.method   = methods[0];

    var html = '';

    if (freqs.length > 1) {
      html += '<div class="plan-filter-section"><p class="plan-filter-label">Frequência semanal</p><div class="plan-filter-row">';
      freqs.forEach(function (f) {
        var active = planFilter.frequency === f ? ' plan-filter-pill--active' : '';
        html += '<button type="button" class="plan-filter-pill' + active + '" data-filter="frequency" data-value="' + f + '">' + f + 'x por semana</button>';
      });
      html += '</div></div>';
    }

    if (cycles.length > 0) {
      html += '<div class="plan-filter-section"><p class="plan-filter-label">Período de cobrança</p><div class="plan-filter-row">';
      cycles.forEach(function (c) {
        var active  = planFilter.cycle === c ? ' plan-filter-pill--active' : '';
        var savings = (c === 'annual') ? '<span class="plan-filter-pill__badge">Melhor valor</span>' : (c === 'semiannual' ? '<span class="plan-filter-pill__badge">Economize</span>' : '');
        html += '<button type="button" class="plan-filter-pill' + active + '" data-filter="cycle" data-value="' + escHtml(c) + '">' + escHtml(CYCLE_LABELS[c] || c) + savings + '</button>';
      });
      html += '</div></div>';
    }

    if (methods.length > 1) {
      html += '<div class="plan-filter-section"><p class="plan-filter-label">Forma de pagamento</p><div class="plan-filter-row">';
      methods.forEach(function (m) {
        var active = planFilter.method === m ? ' plan-filter-pill--active' : '';
        var icon = PAYMENT_METHOD_ICONS[m] || '';
        html += '<button type="button" class="plan-filter-pill plan-filter-pill--payment' + active + '" data-filter="method" data-value="' + escHtml(m) + '">' + icon + '<span>' + escHtml(METHOD_LABELS[m] || m) + '</span></button>';
      });
      html += '</div></div>';
    }

    fillMarkup(area, html);
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
          ? 'Nenhum plano disponível para esta pessoa.'
          : 'Nenhum plano disponível para os filtros selecionados.';
      area.textContent = '';
      var emptyP = document.createElement('p');
      emptyP.className = 'plan-cards--empty';
      emptyP.textContent = emptyMsg;
      area.appendChild(emptyP);
      return;
    }

    var html = '<div class="plan-cards">';
    plans.forEach(function (plan) {
      var currentSelection = state.planSelections[currentPlanPersonIndex] || {};
      var isSelected = plan.id === currentSelection.planId;
      var price      = plan.payment_method === 'pix' ? plan.charge_pix : plan.charge_card;
      var isStripe   = plan.gateway_code === 'stripe_card';
      var tierLabel  = plan.commercial_tier_label || plan.name || plan.code;
      var isFeatured = /fidel|loyal/i.test(plan.code || '');
      var cycleLabel = isStripe ? 'mês' : (plan.cycle || '');

      html += '<button type="button" class="plan-card' + (isSelected ? ' plan-card--selected' : '') + '" data-plan-id="' + plan.id + '" aria-pressed="' + (isSelected ? 'true' : 'false') + '">';
      html += '<div class="plan-card__radio"><div class="plan-card__radio-dot"></div></div>';
      html += '<div class="plan-card__body">';

      html += '<div class="plan-card__header">';
      html += '<p class="plan-card__tier">' + escHtml(tierLabel) + '</p>';
      if (isStripe)        html += '<span class="plan-card__badge plan-card__badge--stripe">Recorrente</span>';
      else if (isFeatured) html += '<span class="plan-card__badge">Recomendado</span>';
      html += '</div>';

      html += '<div class="plan-card__price-wrap">';
      html += '<span class="plan-card__price">' + fmtPrice(price) + '</span>';
      html += '<span class="plan-card__price-cycle">/' + escHtml(cycleLabel) + '</span>';
      html += '</div>';

      if (!isStripe && plan.installment_count > 1 && plan.installment_label) {
        html += '<p class="plan-card__installment">' + escHtml(plan.installment_label) + '</p>';
      }

      if (plan.weekly_frequency_label) {
        html += '<p class="plan-card__meta">' + escHtml(plan.weekly_frequency_label) + '</p>';
      }

      if (plan.requires_special_authorization) {
        html += '<p class="plan-card__auth-note">Requer autorização da academia</p>';
      }

      html += '</div></button>';
    });
    html += '</div>';
    fillMarkup(area, html);

    area.querySelectorAll('.plan-card').forEach(function (card) {
      card.addEventListener('click', function () {
        selectPlan(card.getAttribute('data-plan-id'));
      });
    });
  }

  function resolvePlanCheckoutAction(plan) {
    if (!plan) return 'asaas_card';
    if (plan.payment_method === 'pix') return 'pix';
    if (plan.gateway_code === 'stripe_card') return 'stripe_card';
    return 'asaas_card';
  }

  function updateStripeUiForPlan(plan) {
    var isStripe = plan && plan.gateway_code === 'stripe_card';
    var notice = document.getElementById('stripe-commitment-notice');
    var couponArea = document.getElementById('coupon-area');
    if (notice) notice.hidden = !isStripe;
    if (couponArea) couponArea.hidden = isStripe;
  }

  function selectPlan(planId) {
    ensurePlanSelections();
    if (state.planSelections[currentPlanPersonIndex]) {
      state.planSelections[currentPlanPersonIndex].planId = planId;
    }
    syncSelectedPlansPayload();
    setHidden('id_selected_plan', planId);
    var plan = planCatalog.find(function (p) { return p.id === planId; });
    if (plan) {
      setHidden('id_checkout_action', resolvePlanCheckoutAction(plan));
      updateStripeUiForPlan(plan);
    }
    renderPlanPersonTabs();
    renderPlanCards();
    var err = document.getElementById('plan-step-error');
    if (err) { err.hidden = true; err.textContent = ''; }
    saveWizardState();
  }

  function validatePlan() {
    ensurePlanSelections();
    var missing = state.planSelections.some(function (entry) { return !entry.planId; });
    if (missing) {
      var err = document.getElementById('plan-step-error');
      if (err) { err.textContent = 'Selecione um plano para cada aluno antes de pagar.'; err.hidden = false; }
      return false;
    }
    var methods = {};
    state.planSelections.forEach(function (entry) {
      var plan = planCatalog.find(function (p) { return p.id === entry.planId; });
      if (plan) methods[plan.payment_method] = true;
    });
    if (Object.keys(methods).length > 1) {
      var methodErr = document.getElementById('plan-step-error');
      if (methodErr) {
        methodErr.textContent = 'Para pagar todos agora, selecione planos com a mesma forma de pagamento. O período pode ser diferente por aluno.';
        methodErr.hidden = false;
      }
      return false;
    }
    syncSelectedPlansPayload();
    return true;
  }

  function syncSelectedPlansPayload() {
    var payload = state.planSelections.map(function (entry) {
      return {
        person_index: entry.personIndex,
        label: entry.label,
        plan_id: entry.planId
      };
    });
    setHidden('id_selected_plans_payload', JSON.stringify(payload));
    if (payload.length && payload[0].plan_id) {
      setHidden('id_selected_plan', payload[0].plan_id);
    }
  }

  function onEnterPlan() {
    if (planAlreadyPaid) { showPlanPaidMode(); return; }
    ensurePlanSelections();
    renderPlanPersonTabs();
    var cycles = planCycles();
    if (planFilter.cycle !== null && cycles.indexOf(planFilter.cycle) === -1) planFilter.cycle = null;
    if (!planFilter.cycle && cycles.length) planFilter.cycle = cycles[0];

    var freqs = planFreqs();
    if (planFilter.frequency !== null && freqs.indexOf(planFilter.frequency) === -1) planFilter.frequency = null;
    if (!planFilter.frequency && freqs.length) planFilter.frequency = freqs[0];

    var methods = planMethods();
    if (planFilter.method !== null && methods.indexOf(planFilter.method) === -1) planFilter.method = null;
    if (!planFilter.method && methods.length) planFilter.method = methods[0];
    renderPlanFilters();
    renderPlanCards();

    var currentSelection = state.planSelections[currentPlanPersonIndex] || {};
    var currentPlan = currentSelection.planId
      ? planCatalog.find(function (p) { return p.id === currentSelection.planId; }) || null
      : null;
    updateStripeUiForPlan(currentPlan);

    refreshEligibilityFromServer(function () {
      if (state.stepSequence[state.stepIndex] !== 'step-plan') return;
      renderPlanFilters();
      renderPlanCards();
    });
  }

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

  var WEEKDAY_LABELS = {
    monday: 'Segunda-feira',
    tuesday: 'Terça-feira',
    wednesday: 'Quarta-feira',
    thursday: 'Quinta-feira',
    friday: 'Sexta-feira',
    saturday: 'Sábado',
    sunday: 'Domingo',
  };

  var STYLE_LABELS = {
    kimono: 'Kimono',
    no_gi: 'No-Gi',
    mixed: 'Misto',
  };

  var teacherExistingField = document.getElementById('teacher-existing-schedule-field');
  var teacherExistingClassList = document.getElementById('teacher-existing-class-list');
  var teacherExistingError = document.getElementById('teacher-existing-class-error');
  var teacherProposedField = document.getElementById('teacher-proposed-schedule-field');
  var teacherProposedSummary = document.getElementById('teacher-proposed-schedule-summary');
  var teacherProposedError = document.getElementById('teacher-proposed-schedule-error');
  var elStepTeacherScheduleNext = document.getElementById('step-teacher-schedule-next');
  var adminRoleError = document.getElementById('admin-role-error');
  var elStepAdministrativeAccessNext = document.getElementById('step-administrative-access-next');
  var operationalPayoutMethodField = document.getElementById('operational-payout-method-field');
  var operationalMoneyFields = document.getElementById('operational-money-fields');
  var operationalFixedAmountField = document.getElementById('operational-fixed-amount-field');
  var operationalStudentPercentageField = document.getElementById('operational-student-percentage-field');
  var operationalFixedAmount = document.getElementById('ui-operational-fixed-amount');
  var operationalStudentPercentage = document.getElementById('ui-operational-student-percentage');
  var operationalFinanceError = document.getElementById('operational-finance-error');
  var operationalFinanceNote = document.getElementById('operational-finance-note');
  var operationalPixFields = document.getElementById('operational-pix-fields');
  var operationalBankFields = document.getElementById('operational-bank-fields');
  var operationalPixKeyType = document.getElementById('ui-operational-pix-key-type');
  var operationalPixKey = document.getElementById('ui-operational-pix-key');
  var operationalBankDetails = document.getElementById('ui-operational-bank-details');
  var elStepOperationalFinanceNext = document.getElementById('step-operational-finance-next');
  var teacherScheduleModal = document.getElementById('teacher-schedule-modal');
  var teacherOpenScheduleModal = document.getElementById('teacher-open-schedule-modal');
  var teacherCancelScheduleModal = document.getElementById('teacher-cancel-schedule-modal');
  var teacherSaveScheduleModal = document.getElementById('teacher-save-schedule-modal');
  var teacherScheduleModalError = document.getElementById('teacher-schedule-modal-error');
  var teacherScheduleCategory = document.getElementById('ui-teacher-schedule-category');
  var teacherScheduleName = document.getElementById('ui-teacher-schedule-name');
  var teacherScheduleStyle = document.getElementById('ui-teacher-schedule-style');
  var teacherScheduleStart = document.getElementById('ui-teacher-schedule-start');
  var teacherScheduleDuration = document.getElementById('ui-teacher-schedule-duration');
  var teacherScheduleCapacity = document.getElementById('ui-teacher-schedule-capacity');
  var teacherScheduleJustification = document.getElementById('ui-teacher-schedule-justification');

  function getTeacherMode() {
    return getCheckedValue('teacher-assignment-mode', 'propose');
  }

  function buildClassGroupScheduleLabel(group) {
    var schedules = Array.isArray(group.schedules) ? group.schedules : [];
    var scheduleLabel = schedules.map(function (schedule) {
      return (schedule.weekday_display || schedule.weekday || '') + ' ' + (schedule.start_time || '');
    }).filter(Boolean).join(', ');
    return group.category_name + ' · ' + group.display_name + (scheduleLabel ? ' · ' + scheduleLabel : '');
  }

  function buildTeacherExistingClassPayload(group) {
    var teacherNames = Array.isArray(group.teacher_names) ? group.teacher_names : [];
    if (!teacherNames.length && group.teacher_name) teacherNames = [group.teacher_name];
    var schedules = Array.isArray(group.schedules) ? group.schedules : [];
    var classGroupId = group.class_group_id || group.id;
    return {
      id: classGroupId,
      class_group_id: classGroupId,
      label: buildClassGroupScheduleLabel(group),
      category_name: group.category_name || '',
      display_name: group.display_name || '',
      teacher_names: teacherNames,
      teacher_label: teacherNames.length ? teacherNames.join(', ') : 'Sem professor vinculado',
      schedules: schedules,
      approval_scope: teacherNames.length ? 'admin_and_current_teacher' : 'admin_only',
    };
  }

  function renderTeacherExistingClassList() {
    if (!teacherExistingClassList) return;
    clearChildren(teacherExistingClassList);
    if (!catalogGroups.length) {
      teacherExistingClassList.appendChild(el('p', {
        className: 'teacher-class-list__empty',
        text: 'Nenhuma turma ativa disponível. Crie uma proposta de horário.',
      }));
      return;
    }

    catalogGroups.forEach(function (group) {
      var payload = buildTeacherExistingClassPayload(group);
      var selected = state.teacherExistingClassSelections.some(function (item) {
        return String(item.class_group_id || item.id) === String(group.class_group_id || group.id);
      });
      var input = el('input', {
        attrs: {
          type: 'checkbox',
          name: 'teacher-existing-class-group',
          value: String(group.class_group_id || group.id),
        },
      });
      input.checked = selected;
      var currentTeacherLabel = payload.teacher_names.length
        ? 'Professor atual: ' + payload.teacher_label
        : 'Sem professor vinculado';
      var reviewLabel = payload.teacher_names.length
        ? 'Aprovação: gestão e professor atual'
        : 'Aprovação: gestão';
      var card = el('label', {
        className: 'teacher-class-card' + (selected ? ' teacher-class-card--selected' : ''),
      }, [
        input,
        el('span', { className: 'teacher-class-card__body' }, [
          el('strong', { text: payload.category_name + (payload.display_name ? ' · ' + payload.display_name : '') }),
          el('small', { text: payload.label }),
          el('small', { text: currentTeacherLabel }),
          el('small', { text: reviewLabel }),
        ]),
      ]);
      input.addEventListener('change', function () {
        toggleTeacherExistingClassSelection(group, input.checked);
      });
      teacherExistingClassList.appendChild(card);
    });
  }

  function toggleTeacherExistingClassSelection(group, checked) {
    state.teacherExistingClassSelections = state.teacherExistingClassSelections.filter(function (item) {
      return String(item.id) !== String(group.id);
    });
    if (checked) {
      state.teacherExistingClassSelections.push(buildTeacherExistingClassPayload(group));
    }
    clearErr(null, teacherExistingError);
    renderTeacherExistingClassList();
    syncTeacherScheduleToHiddenFields();
    saveWizardState();
  }

  function populateTeacherScheduleCategories() {
    if (!teacherScheduleCategory) return;
    var current = teacherScheduleCategory.value;
    var seen = {};
    var categoryOptions = [{ value: '', label: 'Selecione' }];
    catalogGroups.forEach(function (group) {
      if (!group.category_id || seen[group.category_id]) return;
      seen[group.category_id] = true;
      categoryOptions.push({
        value: String(group.category_id),
        label: group.category_name || ('Categoria ' + group.category_id),
      });
    });
    DOM.setSelectOptions(teacherScheduleCategory, categoryOptions);
    teacherScheduleCategory.value = current;
  }

  function updateTeacherScheduleMode() {
    var mode = getTeacherMode();
    if (teacherExistingField) teacherExistingField.hidden = mode !== 'existing';
    if (teacherProposedField) teacherProposedField.hidden = mode !== 'propose';
    clearErr(null, teacherExistingError);
    clearErr(null, teacherProposedError);
  }

  function onEnterTeacherSchedule() {
    renderTeacherExistingClassList();
    populateTeacherScheduleCategories();
    updateTeacherScheduleMode();
    syncOperationalProfileToHiddenFields(state.profile);
  }

  function validateTeacherSchedule() {
    if (getTeacherMode() === 'existing') {
      if (!state.teacherExistingClassSelections.length) {
        showErr(null, teacherExistingError, 'Selecione ao menos uma turma ativa ou crie uma proposta.');
        return false;
      }
      clearErr(null, teacherExistingError);
      return true;
    }
    if (!state.teacherProposedSchedule) {
      showErr(null, teacherProposedError, 'Crie o horário proposto antes de avançar.');
      return false;
    }
    clearErr(null, teacherProposedError);
    return true;
  }

  function syncTeacherScheduleToHiddenFields() {
    var mode = getTeacherMode();
    setHidden('id_teacher_assignment_mode', mode);
    setHidden(
      'id_teacher_existing_class_group',
      mode === 'existing' && state.teacherExistingClassSelections.length
        ? String(state.teacherExistingClassSelections[0].id)
        : ''
    );
    setHidden(
      'id_teacher_existing_class_groups_payload',
      mode === 'existing' ? JSON.stringify(state.teacherExistingClassSelections) : ''
    );
    setHidden(
      'id_teacher_proposed_schedule_payload',
      mode === 'propose' && state.teacherProposedSchedule
        ? JSON.stringify(state.teacherProposedSchedule)
        : ''
    );
  }

  function clearScheduleModalError() {
    clearErr(null, teacherScheduleModalError);
  }

  function readTeacherScheduleModalData() {
    var selectedWeekdays = getCheckedValues('teacher-schedule-weekdays');
    var selectedWeekdayLabels = selectedWeekdays.map(function (weekday) {
      return WEEKDAY_LABELS[weekday] || weekday;
    });
    return {
      category_id: teacherScheduleCategory ? teacherScheduleCategory.value : '',
      category_label: teacherScheduleCategory && teacherScheduleCategory.selectedOptions[0]
        ? teacherScheduleCategory.selectedOptions[0].textContent
        : '',
      display_name: teacherScheduleName ? teacherScheduleName.value.trim() : '',
      weekdays: selectedWeekdays,
      weekdays_label: selectedWeekdayLabels.join(', '),
      training_style: teacherScheduleStyle ? teacherScheduleStyle.value : '',
      training_style_label: teacherScheduleStyle ? (STYLE_LABELS[teacherScheduleStyle.value] || teacherScheduleStyle.value) : '',
      start_time: teacherScheduleStart ? teacherScheduleStart.value : '',
      duration_minutes: teacherScheduleDuration ? teacherScheduleDuration.value : '',
      default_capacity: teacherScheduleCapacity ? teacherScheduleCapacity.value : '',
      justification: teacherScheduleJustification ? teacherScheduleJustification.value.trim() : '',
    };
  }

  function validateTeacherScheduleModal(data) {
    if (!data.category_id || !data.display_name || !data.weekdays.length || !data.start_time) {
      showErr(null, teacherScheduleModalError, 'Informe categoria, nome, dias da semana e horário de início.');
      return false;
    }
    clearScheduleModalError();
    return true;
  }

  function renderTeacherProposedScheduleSummary() {
    if (!teacherProposedSummary) return;
    var data = state.teacherProposedSchedule;
    if (!data) {
      teacherProposedSummary.textContent = 'Nenhum horário proposto.';
      return;
    }
    teacherProposedSummary.textContent = [
      data.category_label,
      data.display_name,
      data.weekdays_label,
      data.start_time,
      data.training_style_label,
    ].filter(Boolean).join(' · ');
  }

  function openTeacherScheduleModal() {
    populateTeacherScheduleCategories();
    clearScheduleModalError();
    if (teacherScheduleModal && typeof teacherScheduleModal.showModal === 'function') {
      teacherScheduleModal.showModal();
    }
  }

  function saveTeacherScheduleModal() {
    var data = readTeacherScheduleModalData();
    if (!validateTeacherScheduleModal(data)) return;
    state.teacherProposedSchedule = data;
    renderTeacherProposedScheduleSummary();
    syncTeacherScheduleToHiddenFields();
    if (teacherScheduleModal) teacherScheduleModal.close();
    saveWizardState();
  }

  function onEnterAdministrativeAccess() {
    clearErr(null, adminRoleError);
    syncOperationalProfileToHiddenFields(state.profile);
  }

  function validateAdministrativeAccess() {
    var roles = getCheckedValues('admin-role');
    if (!roles.length) {
      showErr(null, adminRoleError, 'Selecione ao menos uma área administrativa.');
      return false;
    }
    clearErr(null, adminRoleError);
    return true;
  }

  function syncAdministrativeAccessToHiddenFields() {
    setHidden('id_operational_requested_roles_payload', JSON.stringify(getCheckedValues('admin-role')));
  }

  function getOperationalFinancialArrangement() {
    return getCheckedValue('operational-financial-arrangement', 'pays_monthly');
  }

  function isPaidOperationalArrangement(arrangement) {
    return ['paid_fixed', 'paid_per_student', 'paid_mixed'].indexOf(arrangement) !== -1;
  }

  function setRadioValue(name, value) {
    document.querySelectorAll('input[name="' + name + '"]').forEach(function (input) {
      input.checked = input.value === value;
    });
  }

  function updateOperationalFinanceFields() {
    var arrangement = getOperationalFinancialArrangement();
    var paid = isPaidOperationalArrangement(arrangement);
    var needsFixed = arrangement === 'paid_fixed' || arrangement === 'paid_mixed';
    var needsPercentage = arrangement === 'paid_per_student' || arrangement === 'paid_mixed';

    if (!paid) setRadioValue('operational-payout-method', 'none');
    if (operationalPayoutMethodField) operationalPayoutMethodField.hidden = !paid;
    if (operationalMoneyFields) operationalMoneyFields.hidden = !paid;
    if (operationalFixedAmountField) operationalFixedAmountField.hidden = !needsFixed;
    if (operationalStudentPercentageField) operationalStudentPercentageField.hidden = !needsPercentage;

    var method = paid ? getCheckedValue('operational-payout-method', 'none') : 'none';
    if (operationalPixFields) operationalPixFields.hidden = !paid || method !== 'pix';
    if (operationalBankFields) operationalBankFields.hidden = !paid || method !== 'bank';

    if (operationalFinanceNote) {
      var note = '';
      if (arrangement === 'barter') {
        note = 'Permuta representa abatimento de plano e não registra dados de recebimento.';
      } else if (arrangement === 'pays_monthly') {
        note = 'Este perfil segue como pagante. Quando também treinar, o plano será tratado no cadastro de aluno.';
      } else if (arrangement === 'volunteer') {
        note = 'Sem mensalidade e sem repasse financeiro.';
      } else if (paid) {
        note = 'Recebimentos ficam pendentes de aprovação da gestão antes de qualquer repasse.';
      }
      operationalFinanceNote.textContent = note;
      operationalFinanceNote.hidden = !note;
    }
    clearErr(null, operationalFinanceError);
    syncOperationalFinanceToHiddenFields();
  }

  function onEnterOperationalFinance() {
    updateOperationalFinanceFields();
    syncOperationalProfileToHiddenFields(state.profile);
  }

  function validatePositiveDecimalInput(input) {
    if (!input) return false;
    var normalized = input.value.trim().replace(',', '.');
    if (!normalized) return false;
    var value = Number(normalized);
    return Number.isFinite(value) && value > 0;
  }

  function validateOperationalFinance() {
    var arrangement = getOperationalFinancialArrangement();
    var paid = isPaidOperationalArrangement(arrangement);
    if (!paid) {
      clearErr(null, operationalFinanceError);
      return true;
    }
    if ((arrangement === 'paid_fixed' || arrangement === 'paid_mixed') && !validatePositiveDecimalInput(operationalFixedAmount)) {
      showErr(null, operationalFinanceError, 'Informe o valor fixo combinado.');
      return false;
    }
    if ((arrangement === 'paid_per_student' || arrangement === 'paid_mixed') && !validatePositiveDecimalInput(operationalStudentPercentage)) {
      showErr(null, operationalFinanceError, 'Informe o percentual por aluno.');
      return false;
    }
    var payoutMethod = getCheckedValue('operational-payout-method', 'none');
    if (payoutMethod === 'none') {
      showErr(null, operationalFinanceError, 'Selecione PIX ou conta bancária para recebimento.');
      return false;
    }
    if (payoutMethod === 'pix') {
      if (!operationalPixKeyType || !operationalPixKeyType.value || !operationalPixKey || !operationalPixKey.value.trim()) {
        showErr(null, operationalFinanceError, 'Informe tipo e chave PIX.');
        return false;
      }
    }
    if (payoutMethod === 'bank') {
      if (!operationalBankDetails || !operationalBankDetails.value.trim()) {
        showErr(null, operationalFinanceError, 'Informe os dados bancários.');
        return false;
      }
    }
    clearErr(null, operationalFinanceError);
    return true;
  }

  function syncOperationalFinanceToHiddenFields() {
    var arrangement = getOperationalFinancialArrangement();
    var payoutMethod = isPaidOperationalArrangement(arrangement)
      ? getCheckedValue('operational-payout-method', 'none')
      : 'none';
    var legacyPaymentCondition = arrangement === 'pays_monthly'
      ? 'pay_monthly'
      : (arrangement === 'barter' ? 'barter' : 'no_monthly_fee');
    var legacyCompensation = arrangement === 'barter'
      ? 'barter'
      : (isPaidOperationalArrangement(arrangement) ? payoutMethod : 'none');
    setHidden('id_operational_training_intent', getCheckedValue('admin-training-intent', 'none'));
    setHidden('id_operational_financial_arrangement', arrangement);
    setHidden('id_operational_payment_condition', legacyPaymentCondition);
    setHidden('id_operational_compensation_preference', legacyCompensation);
    setHidden('id_operational_payout_method', payoutMethod);
    setHidden('id_operational_pix_key_type', payoutMethod === 'pix' && operationalPixKeyType ? operationalPixKeyType.value : '');
    setHidden('id_operational_pix_key', payoutMethod === 'pix' && operationalPixKey ? operationalPixKey.value.trim() : '');
    setHidden('id_operational_bank_details', payoutMethod === 'bank' && operationalBankDetails ? operationalBankDetails.value.trim() : '');
    setHidden(
      'id_operational_fixed_amount',
      (arrangement === 'paid_fixed' || arrangement === 'paid_mixed') && operationalFixedAmount
        ? operationalFixedAmount.value.trim()
        : ''
    );
    setHidden(
      'id_operational_student_percentage',
      (arrangement === 'paid_per_student' || arrangement === 'paid_mixed') && operationalStudentPercentage
        ? operationalStudentPercentage.value.trim()
        : ''
    );
  }

  function submitOperationalRegistration() {
    syncOperationalProfileToHiddenFields(state.profile);
    syncOperationalFinanceToHiddenFields();
    if (state.profile === PROFILE_TEACHER_REQUEST) syncTeacherScheduleToHiddenFields();
    if (state.profile === PROFILE_ADMINISTRATIVE_REQUEST) syncAdministrativeAccessToHiddenFields();
    setHidden('id_selected_plan', '');
    setHidden('id_selected_plans_payload', '[]');
    setHidden('id_checkout_action', 'pay_later');
    clearWizardState();
    var form = document.getElementById('wizard-form');
    if (form && form.requestSubmit) {
      form.requestSubmit();
    } else if (form) {
      form.submit();
    }
  }

  function resolveAudience(birthdateStr) {
    return Wz.resolveAudience(birthdateStr, ibjjfCategories);
  }

  function filterGroupsByPerson(groups, person) {
    var audience = resolveAudience(person.birthdate);
    if (!audience) return groups;
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
      var subtitleBase = person.name
        ? 'Turma para ' + person.name
        : 'Selecione a turma que deseja frequentar';
      elClassSubtitle.textContent = subtitleBase + ' — você pode escolher mais de uma.';
    }

    if (elClassError) { elClassError.textContent = ''; elClassError.hidden = true; }

    var filteredGroups = filterGroupsByPerson(catalogGroups, person);
    var selectedIds = (state.classSelections[classPersonIdx] || { ids: [] }).ids;
    renderClassCatalog(filteredGroups, selectedIds, classPersonIdx);
  }

  function renderClassCatalog(groups, selectedIds, classPersonIdx) {
    if (!elClassCatalog) return;
    clearChildren(elClassCatalog);

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

      var titleText = (group.category_name || '') +
        (group.display_name ? ' · ' + group.display_name : '');

      var bodyChildren = [
        el('p', { className: 'class-card__title', text: titleText }),
      ];
      var sections = group.compact_schedule_sections || [];
      if (sections.length) {
        var scheduleTable = el('div', { className: 'class-card__schedule-table' });
        sections.forEach(function (sec) {
          var abbrev = WEEKDAY_ABBREV[sec.weekday_label] || sec.weekday_label.substring(0, 3);
          var times = sec.entries.map(function (e) { return e.time_label; }).join('  ·  ');
          scheduleTable.appendChild(el('div', { className: 'class-card__day-row' }, [
            el('span', { className: 'class-card__day-name', text: abbrev }),
            el('span', { className: 'class-card__day-times', text: times }),
          ]));
        });
        bodyChildren.unshift(el('div', { className: 'class-card__divider' }));
        bodyChildren.push(scheduleTable);
      }

      card.appendChild(el('div', { className: 'class-card__radio' }, [
        el('div', { className: 'class-card__radio-dot' }),
      ]));
      card.appendChild(el('div', { className: 'class-card__body' }, bodyChildren));

      card.addEventListener('click', function () {
        selectClassGroup(classPersonIdx, group.id);
      });

      elClassCatalog.appendChild(card);
    });
  }

  function selectClassGroup(classPersonIdx, groupId) {
    var selection = state.classSelections[classPersonIdx];
    if (!selection) return;

    var index = selection.ids.indexOf(groupId);
    if (index === -1) {
      selection.ids.push(groupId);
    } else {
      selection.ids.splice(index, 1);
    }

    if (!elClassCatalog) return;
    elClassCatalog.querySelectorAll('.class-card').forEach(function (card) {
      var selected = selection.ids.indexOf(card.getAttribute('data-group-id')) !== -1;
      card.classList.toggle('class-card--selected', selected);
      card.setAttribute('aria-pressed', selected ? 'true' : 'false');
    });

    if (elClassError && selection.ids.length > 0) { elClassError.textContent = ''; elClassError.hidden = true; }
  }

  function validateClasses(classPersonIdx) {
    var sel = state.classSelections[classPersonIdx];
    if (!sel || sel.ids.length === 0) {
      if (elClassError) { elClassError.textContent = 'Selecione ao menos uma turma para continuar.'; elClassError.hidden = false; }
      return false;
    }
    return true;
  }

  if (elHolderDepChk) {
    elHolderDepChk.addEventListener('change', function () {
      var checked = elHolderDepChk.checked;
      elHolderCountArea.hidden = !checked;
      state.holderDepCount = checked ? 1 : 0;
      if (checked) renderHolderDepCount();
      syncHolderDeps();
      buildStepSequence();
      updateProgress();
      saveWizardState();
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
        saveWizardState();
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
        saveWizardState();
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
        saveWizardState();
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
        saveWizardState();
      }
    });
  }

  if (elProfileOptions) {
    elProfileOptions.addEventListener('click', function (event) {
      var card = event.target.closest('.profile-card[data-profile]');
      if (!card || !elProfileOptions.contains(card)) return;
      selectProfile(card.getAttribute('data-profile'));
    });
  }

  if (elStep1Next) {
    elStep1Next.addEventListener('click', function () {
      if (!state.profile) return;
      goTo(1);
    });
  }

  bindMask(s2Cpf,       maskCpf);
  if (s2Cpf) {
    s2Cpf.addEventListener('input', function () {
      checkCpfAvailability(s2Cpf, s2CpfError, s2CpfAvailability);
    });
  }
  bindMask(s2Phone,     maskPhone);
  bindMask(s2Birthdate, maskDate);
  bindMask(s2PostalCode, maskCep);
  setupPasswordToggle('ui-s2-password',         'ui-s2-pw-toggle');
  setupPasswordToggle('ui-s2-password-confirm', 'ui-s2-pwc-toggle');

  if (s2PostalCode) {
    s2PostalCode.addEventListener('input', function () {
      var digits = s2PostalCode.value.replace(/\D/g, '');
      if (digits.length === 8) fetchCep(digits);
    });
  }

  if (elStep2Next) {
    elStep2Next.addEventListener('click', function () {
      if (!validatePrincipal()) return;
      collectPrincipal();
      goTo(state.stepIndex + 1);
    });
  }

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

  if (elStepHealthNext) {
    elStepHealthNext.addEventListener('click', function () {
      var pi = healthPersonIndexAt(state.stepIndex);
      collectHealth(pi);
      goTo(state.stepIndex + 1);
    });
  }

  function _setMartialHas(value) {
    if (martialHas) martialHas.value = value;
    _syncMartialHasPills(value);
    toggleMartialDetail(value === 'yes');
    if (value !== 'yes') toggleMartialJj(false);
    if (martialHasErr) { martialHasErr.hidden = true; martialHasErr.textContent = ''; }
  }

  if (martialToggleNo)  martialToggleNo.addEventListener('click',  function () { _setMartialHas('no'); });
  if (martialToggleYes) martialToggleYes.addEventListener('click', function () { _setMartialHas('yes'); });

  if (martialHas) {
    martialHas.addEventListener('change', function () {
      _syncMartialHasPills(martialHas.value);
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

  document.querySelectorAll('input[name="teacher-assignment-mode"]').forEach(function (input) {
    input.addEventListener('change', updateTeacherScheduleMode);
  });
  if (teacherOpenScheduleModal) teacherOpenScheduleModal.addEventListener('click', openTeacherScheduleModal);
  if (teacherCancelScheduleModal) {
    teacherCancelScheduleModal.addEventListener('click', function () {
      if (teacherScheduleModal) teacherScheduleModal.close();
    });
  }
  if (teacherSaveScheduleModal) teacherSaveScheduleModal.addEventListener('click', saveTeacherScheduleModal);
  if (elStepTeacherScheduleNext) {
    elStepTeacherScheduleNext.addEventListener('click', function () {
      if (!validateTeacherSchedule()) return;
      syncTeacherScheduleToHiddenFields();
      goTo(state.stepIndex + 1);
    });
  }

  document.querySelectorAll('input[name="admin-role"]').forEach(function (input) {
    input.addEventListener('change', function () {
      syncAdministrativeAccessToHiddenFields();
      clearErr(null, adminRoleError);
    });
  });
  if (elStepAdministrativeAccessNext) {
    elStepAdministrativeAccessNext.addEventListener('click', function () {
      if (!validateAdministrativeAccess()) return;
      syncAdministrativeAccessToHiddenFields();
      goTo(state.stepIndex + 1);
    });
  }

  document.querySelectorAll('input[name="operational-payout-method"]').forEach(function (input) {
    input.addEventListener('change', updateOperationalFinanceFields);
  });
  document.querySelectorAll('input[name="operational-financial-arrangement"]').forEach(function (input) {
    input.addEventListener('change', updateOperationalFinanceFields);
  });
  [operationalFixedAmount, operationalStudentPercentage, operationalPixKeyType, operationalPixKey, operationalBankDetails].forEach(function (input) {
    if (!input) return;
    input.addEventListener('input', syncOperationalFinanceToHiddenFields);
    input.addEventListener('change', syncOperationalFinanceToHiddenFields);
  });
  if (elStepOperationalFinanceNext) {
    elStepOperationalFinanceNext.addEventListener('click', function () {
      if (!validateOperationalFinance()) return;
      syncOperationalFinanceToHiddenFields();
      submitOperationalRegistration();
    });
  }

  var planAlreadyPaid = false;

  var elStepPlanNext = document.getElementById('step-plan-next');
  if (elStepPlanNext) {
    elStepPlanNext.addEventListener('click', function () {
      if (planAlreadyPaid) return;
      if (!validatePlan()) return;
      var firstPlan = planCatalog.find(function (p) { return p.id === state.planSelections[0].planId; });
      setHidden('id_checkout_action', firstPlan ? resolvePlanCheckoutAction(firstPlan) : 'asaas_card');
      document.getElementById('wizard-form').submit();
    });
  }

  var elBtnTrialClass = document.getElementById('btn-trial-class');
  if (elBtnTrialClass) {
    elBtnTrialClass.addEventListener('click', function () {
      showPostPaymentMode('step-products');
      bindProductsSection();
    });
  }

  (function bindCoupon() {
    var elCouponInput  = document.getElementById('coupon-code-input');
    var elCouponBtn    = document.getElementById('coupon-apply-btn');
    var elCouponMsg    = document.getElementById('coupon-message');
    var elCouponHidden = document.getElementById('id_coupon_code');

    if (!elCouponBtn || !elCouponInput) return;

    elCouponBtn.addEventListener('click', function () {
      var code = (elCouponInput.value || '').trim();
      if (!code) {
        if (elCouponMsg) { elCouponMsg.textContent = 'Informe o código do cupom.'; elCouponMsg.className = 'coupon-msg coupon-msg--error'; elCouponMsg.hidden = false; }
        return;
      }

      var total = state.planSelections.reduce(function (acc, sel) {
        var p = planCatalog.find(function (p) { return p.id === sel.planId; });
        return p ? acc + parseFloat(p.price || 0) : acc;
      }, 0);

      var body = new URLSearchParams();
      body.append('coupon_code', code);
      body.append('total', total.toFixed(2));
      body.append('csrfmiddlewaretoken', (document.querySelector('[name=csrfmiddlewaretoken]') || {}).value || '');

      elCouponBtn.disabled = true;
      fetch(wizardEndpoints.validateCouponUrl, { method: 'POST', body: body })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (data.valid) {
            if (elCouponHidden) elCouponHidden.value = data.coupon_code;
            if (elCouponMsg) { elCouponMsg.textContent = data.message + ' Novo total: R$ ' + parseFloat(data.discounted_total).toFixed(2).replace('.', ','); elCouponMsg.className = 'coupon-msg coupon-msg--ok'; elCouponMsg.hidden = false; }
            elCouponBtn.textContent = 'Aplicado';
            elCouponInput.disabled = true;
            elCouponBtn.disabled = true;
          } else {
            if (elCouponMsg) { elCouponMsg.textContent = data.message; elCouponMsg.className = 'coupon-msg coupon-msg--error'; elCouponMsg.hidden = false; }
            elCouponBtn.disabled = false;
          }
        })
        .catch(function (err) {
          Wz.warn('coupon', 'Falha ao validar cupom', err);
          if (elCouponMsg) { elCouponMsg.textContent = 'Erro ao validar cupom. Tente novamente.'; elCouponMsg.className = 'coupon-msg coupon-msg--error'; elCouponMsg.hidden = false; }
          elCouponBtn.disabled = false;
        });
    });
  }());

  if (elStepClassesNext) {
    elStepClassesNext.addEventListener('click', function () {
      var ci = classPersonIndexAt(state.stepIndex);
      if (!validateClasses(ci)) return;
      syncClassesToForm();
      goTo(state.stepIndex + 1);
    });
  }

  if (elWizardBack) {
    elWizardBack.addEventListener('click', function (e) {
      var visibleStep = document.querySelector('.wizard-step:not([hidden])');
      var visibleId = visibleStep ? visibleStep.id : null;

      if (visibleId === 'step-review') {
        e.preventDefault();
        showPostPaymentMode('step-products');
        bindProductsSection();
        return;
      }

      if (visibleId === 'step-products') {
        e.preventDefault();
        showPlanPaidMode();
        return;
      }

      if (state.stepIndex === 0) return;
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

  var CHECK_ICON_MARKUP = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';

  function renderConfirmationSummary(containerId) {
    var container = document.getElementById(containerId);
    if (!container) return;

    var panel = el('div', { className: 'reg-confirm-panel' });
    panel.appendChild(el('div', { className: 'reg-confirm-panel__heading', text: 'Resumo do cadastro' }));
    var firstRow = true;

    function addRow(label, value, meta) {
      if (!value) return;
      if (!firstRow) panel.appendChild(el('div', { className: 'reg-confirm-panel__divider' }));
      firstRow = false;

      var icon = el('span', { className: 'reg-confirm-panel__icon reg-confirm-panel__icon--ok', attrs: { 'aria-hidden': 'true' } });
      icon.appendChild(svgIcon(CHECK_ICON_MARKUP));

      var infoChildren = [
        el('p', { className: 'reg-confirm-panel__label', text: label }),
        el('p', { className: 'reg-confirm-panel__value', text: value }),
      ];
      if (meta) infoChildren.push(el('p', { className: 'reg-confirm-panel__meta', text: meta }));
      var info = el('div', { className: 'reg-confirm-panel__info' }, infoChildren);

      panel.appendChild(el('div', { className: 'reg-confirm-panel__row' }, [icon, info]));
    }

    if (pendingPersonData) {
      addRow('Nome', pendingPersonData.full_name, null);
      addRow('E-mail', pendingPersonData.email, null);
      addRow('Telefone', pendingPersonData.phone, null);
      addRow('Turma', pendingPersonData.class_group_name, null);
    }

    if (planOrderData && planOrderData.plan_name) {
      var planMeta = planOrderData.plan_price
        ? 'R$ ' + parseFloat(planOrderData.plan_price).toFixed(2).replace('.', ',') + ' confirmado'
        : null;
      addRow('Plano contratado', planOrderData.plan_name, planMeta);
    }

    clearChildren(container);
    container.appendChild(panel);
  }

  function showPostPaymentMode(stepId) {
    if (!rehydratePendingWizardState() && !state.stepSequence.length) buildStepSequence();
    var wizForm = document.getElementById('wizard-form');
    if (wizForm) wizForm.hidden = true;
    showOnlyWizardStep(stepId);

    var idx = state.stepSequence.indexOf(stepId);
    if (idx < 0) {
      var fallbackStep = (stepId === 'step-plan-confirmed') ? 'step-plan' : 'step-plan';
      idx = state.stepSequence.indexOf(fallbackStep);
    }
    if (idx >= 0) {
      state.stepIndex = idx;
      updateProgress();
    }
  }

  function fmtCurrency(value) {
    var n = parseFloat(value) || 0;
    return 'R$ ' + n.toFixed(2).replace('.', ',').replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  }

  function buildProductsPayload() {
    return JSON.stringify(productCart.map(function (item) {
      return { variant_id: item.variantId, quantity: item.qty };
    }));
  }

  function submitProductsForm(action) {
    var form = document.getElementById('products-payment-form');
    var payloadInput = document.getElementById('products-payload-hidden');
    var actionInput = document.getElementById('products-checkout-action-hidden');
    if (!form || !payloadInput || !actionInput) return;
    payloadInput.value = buildProductsPayload();
    actionInput.value = action;
    form.submit();
  }

  function showProductsSubview(name) {
    var catalog = document.getElementById('products-subview-catalog');
    var configure = document.getElementById('products-subview-configure');
    var cart = document.getElementById('products-subview-cart');
    if (catalog) catalog.hidden = (name !== 'catalog');
    if (configure) configure.hidden = (name !== 'configure');
    if (cart) cart.hidden = (name !== 'cart');
  }

  function getCartTotal() {
    return productCart.reduce(function (sum, item) { return sum + item.unitPrice * item.qty; }, 0);
  }

  function getCartCount() {
    return productCart.reduce(function (sum, item) { return sum + item.qty; }, 0);
  }

  function renderProductsCatalog() {
    var area = document.getElementById('products-catalog-area');
    var viewCartBtn = document.getElementById('products-btn-view-cart');
    if (!area) return;

    if (!productCatalog.length) {
      area.textContent = '';
      var emptyProducts = document.createElement('p');
      emptyProducts.className = 'wizard-step__subtitle';
      emptyProducts.style.textAlign = 'center';
      emptyProducts.style.padding = '2rem 0';
      emptyProducts.textContent = 'Nenhum produto disponível no momento.';
      area.appendChild(emptyProducts);
      if (viewCartBtn) viewCartBtn.hidden = true;
      return;
    }

    var html = '';
    productCatalog.forEach(function (product) {
      var hasStock = product.total_stock > 0;
      var inCart = false;
      for (var i = 0; i < productCart.length; i++) {
        if (productCart[i].productId === product.id) { inCart = true; break; }
      }

      html += '<div class="prod-card' + (hasStock ? '' : ' prod-card--unavailable') + '">';
      html += '<div class="prod-card__body">';
      html += '<div class="prod-card__header">';
      html += '<p class="prod-card__name">' + escHtml(product.name) + '</p>';
      if (inCart) html += '<span class="prod-card__badge prod-card__badge--cart">✓ No carrinho</span>';
      html += '</div>';
      html += '<p class="prod-card__category">' + escHtml(product.category) + '</p>';
      if (product.description) {
        html += '<p class="prod-card__desc">' + escHtml(product.description) + '</p>';
      }
      html += '<div class="prod-card__price-row">';
      html += '<span class="prod-card__price">' + fmtCurrency(product.price) + '</span>';
      if (!hasStock) {
        html += '<span class="prod-card__stock-badge prod-card__stock-badge--out">Sem estoque</span>';
      } else {
        html += '<span class="prod-card__stock-badge">' + product.total_stock + ' un.</span>';
      }
      html += '</div>';
      if (hasStock) {
        html += '<div class="prod-card__footer">';
        html += '<button type="button" class="prod-card__add-btn" data-product-id="' + product.id + '">' + (inCart ? 'Alterar seleção' : 'Adicionar') + '</button>';
        html += '</div>';
      }
      html += '</div>';
      html += '</div>';
    });
    fillMarkup(area, html);

    area.querySelectorAll('.prod-card__add-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var pid = parseInt(this.getAttribute('data-product-id'), 10);
        var product = null;
        for (var i = 0; i < productCatalog.length; i++) {
          if (productCatalog[i].id === pid) { product = productCatalog[i]; break; }
        }
        if (product) startConfigureProduct(product);
      });
    });

    var cartCount = getCartCount();
    if (viewCartBtn) {
      viewCartBtn.hidden = cartCount === 0;
      if (cartCount > 0) {
        DOM.setButtonTextWithSvg(
          viewCartBtn,
          'Ver carrinho (' + cartCount + ' item' + (cartCount !== 1 ? 'ns' : '') + ')',
          ARROW_SVG
        );
      }
    }
  }

  function getUniqueColors(product) {
    var seen = {};
    var colors = [];
    product.variants.forEach(function (v) {
      if (v.color && !seen[v.color]) { seen[v.color] = true; colors.push(v.color); }
    });
    return colors;
  }

  function getVariantsForColor(product, color) {
    if (!color) return product.variants;
    return product.variants.filter(function (v) { return v.color === color; });
  }

  function startConfigureProduct(product) {
    configureProduct = product;
    configureColor = null;
    configureVariantId = null;
    configureQty = 1;

    for (var i = 0; i < productCart.length; i++) {
      if (productCart[i].productId === product.id) {
        configureVariantId = productCart[i].variantId;
        configureColor = productCart[i].variantColor || null;
        configureQty = productCart[i].qty;
        break;
      }
    }

    if (configureColor === null) {
      var uniqueColors = getUniqueColors(product);
      if (uniqueColors.length === 1) configureColor = uniqueColors[0];
    }

    renderProductsConfigure();
    showProductsSubview('configure');
  }

  function renderProductsConfigure() {
    var area = document.getElementById('products-configure-area');
    if (!area || !configureProduct) return;

    var product = configureProduct;
    var uniqueColors = getUniqueColors(product);
    var showColorPicker = uniqueColors.length > 1;

    if (!configureColor && uniqueColors.length === 1) configureColor = uniqueColors[0];

    var variantsForColor = getVariantsForColor(product, configureColor);
    var uniqueSizes = [];
    var seenSizes = {};
    variantsForColor.forEach(function (v) {
      if (v.size && !seenSizes[v.size]) { seenSizes[v.size] = true; uniqueSizes.push(v.size); }
    });
    var showSizePicker = uniqueSizes.length > 0;

    if (!configureVariantId && !showColorPicker && !showSizePicker && product.variants.length > 0) {
      for (var k = 0; k < product.variants.length; k++) {
        if (product.variants[k].is_in_stock) { configureVariantId = product.variants[k].id; break; }
      }
    }

    if (!configureVariantId && variantsForColor.length === 1 && !showSizePicker) {
      if (variantsForColor[0].is_in_stock) configureVariantId = variantsForColor[0].id;
    }

    var html = '';

    if (showColorPicker) {
      html += '<div class="prod-configure__section">';
      html += '<p class="prod-configure__section-label">Cor</p>';
      html += '<div class="color-pills">';
      uniqueColors.forEach(function (color) {
        var isSelected = color === configureColor;
        var hasStock = product.variants.some(function (v) { return v.color === color && v.is_in_stock; });
        html += '<button type="button" class="color-pill' +
          (isSelected ? ' color-pill--selected' : '') +
          (!hasStock ? ' color-pill--disabled' : '') +
          '" data-color="' + escHtml(color) + '">' + escHtml(color) + '</button>';
      });
      html += '</div>';
      html += '</div>';
    }

    if (showSizePicker && (configureColor !== null || !showColorPicker)) {
      html += '<div class="prod-configure__section">';
      html += '<p class="prod-configure__section-label">Tamanho</p>';
      html += '<div class="size-pills">';
      variantsForColor.forEach(function (v) {
        if (!v.size) return;
        var isSelected = v.id === configureVariantId;
        var stockText = v.is_in_stock ? v.stock_quantity + ' un.' : 'Esgotado';
        html += '<button type="button" class="size-pill' +
          (isSelected ? ' size-pill--selected' : '') +
          (!v.is_in_stock ? ' size-pill--disabled' : '') +
          '" data-variant-id="' + v.id + '">';
        html += '<span class="size-pill__size">' + escHtml(v.size) + '</span>';
        html += '<span class="size-pill__stock">' + escHtml(stockText) + '</span>';
        html += '</button>';
      });
      html += '</div>';
      html += '</div>';
    }

    var selectedVariant = null;
    for (var i = 0; i < product.variants.length; i++) {
      if (product.variants[i].id === configureVariantId) { selectedVariant = product.variants[i]; break; }
    }
    var maxQty = selectedVariant ? Math.min(selectedVariant.stock_quantity, 10) : 1;
    configureQty = Math.max(1, Math.min(configureQty, maxQty));
    var stepperDisabled = !configureVariantId;

    html += '<div class="prod-configure__section">';
    html += '<div class="configure-qty-row">';
    html += '<span class="configure-qty-label">Quantidade</span>';
    html += '<div class="configure-qty-stepper">';
    html += '<button type="button" class="configure-qty-stepper__btn" id="cfg-qty-dec" aria-label="Diminuir"' +
      (configureQty <= 1 || stepperDisabled ? ' disabled' : '') + '>−</button>';
    html += '<span class="configure-qty-stepper__value" id="cfg-qty-val">' + configureQty + '</span>';
    html += '<button type="button" class="configure-qty-stepper__btn" id="cfg-qty-inc" aria-label="Aumentar"' +
      (configureQty >= maxQty || stepperDisabled ? ' disabled' : '') + '>+</button>';
    html += '</div>';
    html += '</div>';
    if (selectedVariant) {
      html += '<p class="prod-configure__stock-hint">' + selectedVariant.stock_quantity + ' unidade' +
        (selectedVariant.stock_quantity !== 1 ? 's' : '') + ' disponível' +
        (selectedVariant.stock_quantity !== 1 ? 'is' : '') + '</p>';
    }
    html += '</div>';

    fillMarkup(area, html);

    area.querySelectorAll('.color-pill[data-color]').forEach(function (pill) {
      pill.addEventListener('click', function () {
        configureColor = this.getAttribute('data-color');
        configureVariantId = null;
        configureQty = 1;
        renderProductsConfigure();
      });
    });

    area.querySelectorAll('.size-pill[data-variant-id]').forEach(function (pill) {
      pill.addEventListener('click', function () {
        configureVariantId = parseInt(this.getAttribute('data-variant-id'), 10);
        configureQty = 1;
        renderProductsConfigure();
      });
    });

    var dec = document.getElementById('cfg-qty-dec');
    var inc = document.getElementById('cfg-qty-inc');
    var valEl = document.getElementById('cfg-qty-val');

    function refreshStepper() {
      if (valEl) valEl.textContent = configureQty;
      if (dec) dec.disabled = configureQty <= 1 || !configureVariantId;
      if (inc) inc.disabled = configureQty >= maxQty || !configureVariantId;
    }
    if (dec) dec.addEventListener('click', function () { if (configureQty > 1) { configureQty--; refreshStepper(); } });
    if (inc) inc.addEventListener('click', function () { if (configureQty < maxQty) { configureQty++; refreshStepper(); } });

    var addBtn = document.getElementById('products-btn-add-to-cart');
    if (addBtn) addBtn.disabled = !configureVariantId;
  }

  function renderProductsCart() {
    var area = document.getElementById('products-cart-area');
    if (!area) return;

    if (!productCart.length) {
      area.textContent = '';
      var emptyCart = document.createElement('p');
      emptyCart.className = 'wizard-step__subtitle';
      emptyCart.style.textAlign = 'center';
      emptyCart.style.padding = '1.5rem 0';
      emptyCart.textContent = 'Carrinho vazio.';
      area.appendChild(emptyCart);
      return;
    }

    var html = '<div class="cart-item-list">';
    productCart.forEach(function (item) {
      html += '<div class="cart-item">';
      html += '<div class="cart-item__info">';
      html += '<p class="cart-item__name">' + escHtml(item.productName) + '</p>';
      html += '<p class="cart-item__meta">' + escHtml(item.variantLabel) + ' · Qtd: ' + item.qty + '</p>';
      html += '</div>';
      html += '<span class="cart-item__subtotal">' + fmtCurrency(item.unitPrice * item.qty) + '</span>';
      html += '<button type="button" class="cart-item__remove" data-variant-id="' + item.variantId + '" aria-label="Remover">×</button>';
      html += '</div>';
    });
    html += '</div>';
    html += '<div class="cart-total-row"><span>Total</span><strong>' + fmtCurrency(getCartTotal()) + '</strong></div>';

    fillMarkup(area, html);

    area.querySelectorAll('.cart-item__remove').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var vid = parseInt(this.getAttribute('data-variant-id'), 10);
        productCart = productCart.filter(function (c) { return c.variantId !== vid; });
        if (!productCart.length) {
          showProductsSubview('catalog');
          renderProductsCatalog();
        } else {
          renderProductsCart();
        }
      });
    });
  }

  function bindProductsSection() {
    renderProductsCatalog();

    var viewCartBtn = document.getElementById('products-btn-view-cart');
    var skipCatalogBtn = document.getElementById('products-btn-skip-catalog');
    var backCatalogBtn = document.getElementById('products-btn-back-catalog');
    var cancelCfgBtn = document.getElementById('products-btn-cancel-configure');
    var addToCartBtn = document.getElementById('products-btn-add-to-cart');
    var backToCatalogBtn = document.getElementById('products-btn-back-to-catalog');
    var payCardBtn = document.getElementById('products-btn-pay-card');
    var payPixBtn = document.getElementById('products-btn-pay-pix');
    var skipCartBtn = document.getElementById('products-btn-skip-cart');

    if (viewCartBtn) viewCartBtn.addEventListener('click', function () {
      renderProductsCart();
      showProductsSubview('cart');
    });

    if (skipCatalogBtn) skipCatalogBtn.addEventListener('click', function () {
      submitProductsForm('pay_later');
    });

    if (backCatalogBtn) backCatalogBtn.addEventListener('click', function () {
      showProductsSubview('catalog');
      renderProductsCatalog();
    });

    if (cancelCfgBtn) cancelCfgBtn.addEventListener('click', function () {
      showProductsSubview('catalog');
      renderProductsCatalog();
    });

    if (addToCartBtn) addToCartBtn.addEventListener('click', function () {
      if (!configureProduct || !configureVariantId) return;
      var variant = null;
      for (var i = 0; i < configureProduct.variants.length; i++) {
        if (configureProduct.variants[i].id === configureVariantId) { variant = configureProduct.variants[i]; break; }
      }
      var labelParts = [];
      if (variant && variant.color) labelParts.push(variant.color);
      if (variant && variant.size) labelParts.push(variant.size);
      var variantLabel = labelParts.length ? labelParts.join(' · ') : 'Padrão';
      var unitPrice = parseFloat(configureProduct.price) || 0;
      var newItem = {
        variantId: configureVariantId,
        variantLabel: variantLabel,
        variantColor: variant ? (variant.color || '') : '',
        variantSize: variant ? (variant.size || '') : '',
        productId: configureProduct.id,
        productName: configureProduct.name,
        qty: configureQty,
        unitPrice: unitPrice
      };
      var replaced = false;
      for (var j = 0; j < productCart.length; j++) {
        if (productCart[j].productId === configureProduct.id) {
          productCart[j] = newItem;
          replaced = true;
          break;
        }
      }
      if (!replaced) productCart.push(newItem);
      showProductsSubview('catalog');
      renderProductsCatalog();
    });

    if (backToCatalogBtn) backToCatalogBtn.addEventListener('click', function () {
      showProductsSubview('catalog');
      renderProductsCatalog();
    });

    if (payCardBtn) payCardBtn.addEventListener('click', function () { submitProductsForm('asaas_card'); });
    if (payPixBtn) payPixBtn.addEventListener('click', function () { submitProductsForm('pix'); });
    if (skipCartBtn) skipCartBtn.addEventListener('click', function () { submitProductsForm('pay_later'); });
  }

  function renderReview() {
    var area = document.getElementById('review-summary-area');
    if (!area) return;
    var blocks = [];

    if (pendingPersonData) {
      var isGuardian = pendingPersonData.person_type_code === 'guardian';
      var mainChildren = [
        el('p', { className: 'order-review-block__label', text: isGuardian ? 'Responsável' : 'Aluno' }),
        el('p', { className: 'order-review-block__name', text: pendingPersonData.full_name }),
      ];
      if (pendingPersonData.email) {
        mainChildren.push(el('p', { className: 'order-review-block__meta', text: pendingPersonData.email }));
      }
      blocks.push(el('div', { className: 'order-review-block' }, mainChildren));

      var students = pendingPersonData.students || [];
      var planTotal = parseFloat((planOrderData && planOrderData.total) || 0);
      var perStudent = students.length > 0 ? planTotal / students.length : planTotal;
      students.forEach(function (s, idx) {
        var studentChildren = [
          el('p', { className: 'order-review-block__label', text: 'Aluno ' + (idx + 1) }),
          el('p', { className: 'order-review-block__name', text: s.full_name }),
        ];
        if (s.class_group_name) {
          studentChildren.push(el('p', { className: 'order-review-block__meta', text: 'Turma: ' + s.class_group_name }));
        }
        if (planOrderData && planOrderData.plan_name) {
          studentChildren.push(el('p', { className: 'order-review-block__meta', text: 'Plano: ' + planOrderData.plan_name }));
        }
        if (perStudent > 0) {
          studentChildren.push(el('p', { className: 'order-review-block__amount', text: 'R$ ' + perStudent.toFixed(2).replace('.', ',') }));
        }
        blocks.push(el('div', { className: 'order-review-block' }, studentChildren));
      });

      if (!isGuardian && pendingPersonData.class_group_name) {
        blocks.push(el('div', { className: 'order-review-block' }, [
          el('p', { className: 'order-review-block__label', text: 'Turma' }),
          el('p', { className: 'order-review-block__name', text: pendingPersonData.class_group_name }),
        ]));
      }
    }

    if (planOrderData && planOrderData.plan_name) {
      blocks.push(el('div', { className: 'order-review-block' }, [
        el('p', { className: 'order-review-block__label', text: 'Plano contratado' }),
        el('p', { className: 'order-review-block__name', text: planOrderData.plan_name || 'Plano' }),
        el('p', { className: 'order-review-block__amount', text: 'Total: R$ ' + (parseFloat(planOrderData.total || 0).toFixed(2).replace('.', ',')) }),
      ]));
    }

    if (materialsOrderData && materialsOrderData.items && materialsOrderData.items.length > 0) {
      var materialsChildren = [el('p', { className: 'order-review-block__label', text: 'Materiais' })];
      materialsOrderData.items.forEach(function (item) {
        materialsChildren.push(el('div', { className: 'order-review-item' }, [
          el('span', { text: item.name + ' × ' + item.quantity }),
          el('span', { text: 'R$ ' + (parseFloat(item.subtotal || 0).toFixed(2).replace('.', ',')) }),
        ]));
      });
      materialsChildren.push(el('p', {
        className: 'order-review-block__amount',
        attrs: { style: 'margin-top:.5rem' },
        text: 'Total materiais: R$ ' + (parseFloat(materialsOrderData.total || 0).toFixed(2).replace('.', ',')),
      }));
      blocks.push(el('div', { className: 'order-review-block' }, materialsChildren));
    } else {
      blocks.push(el('div', { className: 'order-review-block' }, [
        el('p', { className: 'order-review-block__label', text: 'Materiais' }),
        el('p', {
          className: 'order-review-block__name',
          attrs: { style: 'color:var(--muted);font-weight:400' },
          text: 'Nenhum material selecionado',
        }),
      ]));
    }

    clearChildren(area);
    blocks.forEach(function (block) { area.appendChild(block); });
  }

  var CHECK_CIRCLE = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>';
  var ARROW_SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>';
  var ARROW_SVG_BTN = '<svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>';

  function renderPlanConfirmed() {
    var summaryArea = document.getElementById('plan-confirmed-summary-area');
    var actionsArea = document.getElementById('plan-confirmed-actions-area');

    var html = '<div class="checkout-confirmed-banner">';
    html += '<span class="checkout-confirmed-banner__icon" aria-hidden="true">' + CHECK_CIRCLE + '</span>';
    html += '<span class="checkout-confirmed-banner__text">Pagamento confirmado</span>';
    html += '</div>';

    if (planOrderData) {
      html += '<div class="checkout-summary"><div class="checkout-summary__section">';
      html += '<p class="checkout-summary__label">Plano contratado</p>';
      if (planOrderData.plan_name) {
        html += '<p class="checkout-summary__value">' + escHtml(planOrderData.plan_name) + '</p>';
      }
      if (planOrderData.total) {
        html += '<p class="checkout-summary__plan-meta">Total: R$ ' + parseFloat(planOrderData.total).toFixed(2).replace('.', ',') + '</p>';
      }
      html += '</div></div>';
    }

    if (summaryArea) fillMarkup(summaryArea, html);

    if (actionsArea) {
      clearChildren(actionsArea);
      var continueBtn = el('button', {
        className: 'btn-checkout-pay',
        attrs: { type: 'button', id: 'btn-plan-confirmed-continue' },
      });
      DOM.setButtonTextWithSvg(continueBtn, ' Continuar para materiais', ARROW_SVG_BTN, { svgFirst: true });
      actionsArea.appendChild(continueBtn);
      var btn = document.getElementById('btn-plan-confirmed-continue');
      if (btn) {
        btn.addEventListener('click', function () {
          var planConfEl = document.getElementById('step-plan-confirmed');
          if (planConfEl) planConfEl.hidden = true;
          showPostPaymentMode('step-products');
          bindProductsSection();
        });
      }
    }
  }

  function renderMaterialsConfirmed() {
    var confirmArea = document.getElementById('products-confirm-area');
    var subCatalog = document.getElementById('products-subview-catalog');
    var subConfigure = document.getElementById('products-subview-configure');
    var subCart = document.getElementById('products-subview-cart');
    if (subCatalog)   subCatalog.hidden   = true;
    if (subConfigure) subConfigure.hidden = true;
    if (subCart)      subCart.hidden      = true;

    var html = '<div class="checkout-confirmed-banner">';
    html += '<span class="checkout-confirmed-banner__icon" aria-hidden="true">' + CHECK_CIRCLE + '</span>';
    html += '<span class="checkout-confirmed-banner__text">Materiais confirmados</span>';
    html += '</div>';

    if (materialsOrderData && materialsOrderData.items && materialsOrderData.items.length > 0) {
      html += '<div class="checkout-summary"><div class="checkout-summary__section">';
      html += '<p class="checkout-summary__label">Materiais adquiridos</p>';
      materialsOrderData.items.forEach(function (item) {
        html += '<div class="order-review-item"><span>' + escHtml(item.name) + ' × ' + item.quantity + '</span>';
        html += '<span>R$ ' + parseFloat(item.subtotal || 0).toFixed(2).replace('.', ',') + '</span></div>';
      });
      html += '<p class="checkout-summary__plan-meta" style="margin-top:.5rem">Total: R$ ' + parseFloat(materialsOrderData.total || 0).toFixed(2).replace('.', ',') + '</p>';
      html += '</div></div>';
    }

    html += '<div class="checkout-actions" style="margin-top:1rem">';
    html += '<button type="button" class="btn-checkout-pay" id="btn-materials-confirmed-continue">';
    html += ARROW_SVG_BTN;
    html += ' Continuar para o resumo</button></div>';

    if (confirmArea) fillMarkup(confirmArea, html);

    var btn = document.getElementById('btn-materials-confirmed-continue');
    if (btn) {
      btn.addEventListener('click', function () {
        var productsEl = document.getElementById('step-products');
        if (productsEl) productsEl.hidden = true;
        showPostPaymentMode('step-review');
        renderReview();
      });
    }
  }

  function showPlanPaidMode() {
    planAlreadyPaid = true;
    if (!rehydratePendingWizardState() && !state.stepSequence.length) buildStepSequence();
    showOnlyWizardStep('step-plan');

    var planIdx = state.stepSequence.indexOf('step-plan');
    if (planIdx >= 0) {
      state.stepIndex = planIdx;
      updateProgress();
    }

    var filtersArea = document.getElementById('plan-filters-area');
    var cardsArea   = document.getElementById('plan-cards-area');

    var html;
    if (regPlanIsTrial) {
      html = '<div class="checkout-confirmed-banner checkout-confirmed-banner--trial">';
      html += '<span class="checkout-confirmed-banner__icon" aria-hidden="true">' + CHECK_CIRCLE + '</span>';
      html += '<span class="checkout-confirmed-banner__text">Aula experimental liberada!</span>';
      html += '</div>';
      html += '<div class="checkout-summary"><div class="checkout-summary__section">';
      html += '<p class="checkout-summary__label">Aula experimental</p>';
      html += '<p class="checkout-summary__value">Você tem 1 aula experimental liberada.</p>';
      html += '<p class="checkout-summary__plan-meta">Finalize o cadastro e compareça à academia para aproveitar.</p>';
      html += '</div></div>';
    } else {
      html = '<div class="checkout-confirmed-banner">';
      html += '<span class="checkout-confirmed-banner__icon" aria-hidden="true">' + CHECK_CIRCLE + '</span>';
      html += '<span class="checkout-confirmed-banner__text">Pagamento confirmado</span>';
      html += '</div>';
      if (planOrderData) {
        html += '<div class="checkout-summary"><div class="checkout-summary__section">';
        html += '<p class="checkout-summary__label">Plano contratado</p>';
        if (planOrderData.plan_name) {
          html += '<p class="checkout-summary__value">' + escHtml(planOrderData.plan_name) + '</p>';
        }
        if (planOrderData.total) {
          html += '<p class="checkout-summary__plan-meta">Total: R$ ' + parseFloat(planOrderData.total).toFixed(2).replace('.', ',') + '</p>';
        }
        html += '</div></div>';
      }
    }

    if (filtersArea) fillMarkup(filtersArea, html);
    if (cardsArea)   clearChildren(cardsArea);

    var trialBtnEl = document.getElementById('btn-trial-class');
    if (trialBtnEl) trialBtnEl.hidden = true;
    var couponAreaEl = document.getElementById('coupon-area');
    if (couponAreaEl) couponAreaEl.hidden = true;
    var stripeNoticeEl = document.getElementById('stripe-commitment-notice');
    if (stripeNoticeEl) stripeNoticeEl.hidden = true;

    var nextBtn = document.getElementById('step-plan-next');
    if (nextBtn) {
      DOM.setButtonTextWithSvg(nextBtn, ' Continuar para materiais', ARROW_SVG, { svgFirst: true });
      nextBtn.disabled = false;
      nextBtn.onclick  = function (e) {
        e.stopImmediatePropagation();
        showPostPaymentMode('step-products');
        bindProductsSection();
      };
    }

    var existingReset = document.getElementById('plan-paid-reset-link');
    if (existingReset) existingReset.remove();

    var wizFormPaid = document.getElementById('wizard-form');
    if (wizFormPaid) wizFormPaid.hidden = false;

    var sysMsgs = document.querySelector('.wizard-system-messages');
    if (sysMsgs && !sysMsgs.hidden) {
      setTimeout(function () {
        sysMsgs.style.transition = 'opacity 0.4s';
        sysMsgs.style.opacity = '0';
        setTimeout(function () { sysMsgs.hidden = true; }, 400);
      }, 5000);
    }
  }

  var WIZARD_STORAGE_KEY = 'lv-wiz-v1';
  var _wizardRestoring   = false;

  function _collectHiddenFields() {
    var result = {};
    var form = document.getElementById('wizard-form');
    if (!form) return result;
    form.querySelectorAll('input[type="hidden"]').forEach(function (inp) {
      if (!inp.name || inp.name === 'csrfmiddlewaretoken') return;
      if (!result[inp.name]) result[inp.name] = [];
      result[inp.name].push(inp.value);
    });
    return result;
  }

  function saveWizardState() {
    if (_wizardRestoring) return;
    try {
      sessionStorage.setItem(WIZARD_STORAGE_KEY, JSON.stringify({
        v: 1,
        stepIndex: state.stepIndex,
        profile: state.profile,
        holderDepCount: state.holderDepCount,
        guardianStudentCount: state.guardianStudentCount,
        deps: state.deps,
        classSelections: state.classSelections,
        planSelections: state.planSelections,
        teacherProposedSchedule: state.teacherProposedSchedule,
        teacherExistingClassSelections: state.teacherExistingClassSelections,
        fields: _collectHiddenFields(),
      }));
    } catch (e) {
      Wz.warn('storage', 'Falha ao salvar estado do wizard em sessionStorage', e);
    }
  }

  function clearWizardState() {
    try {
      sessionStorage.removeItem(WIZARD_STORAGE_KEY);
    } catch (e) {
      Wz.warn('storage', 'Falha ao limpar estado do wizard em sessionStorage', e);
    }
  }

  function _applyHiddenFields(form, savedFields) {
    Object.keys(savedFields).forEach(function (name) {
      var vals = savedFields[name];
      var existing = Array.prototype.slice.call(
        form.querySelectorAll('input[type="hidden"][name="' + name + '"]')
      );
      if (existing.length === 1 && vals.length === 1) {
        existing[0].value = vals[0];
        return;
      }

      var staticInps  = existing.filter(function (el) { return !!el.id; });
      var dynamicInps = existing.filter(function (el) { return !el.id; });
      dynamicInps.forEach(function (el) { el.parentNode.removeChild(el); });
      var offset = 0;
      if (staticInps.length > 0 && vals.length > 0) {
        staticInps[0].value = vals[0];
        offset = 1;
      }
      for (var i = offset; i < vals.length; i++) {
        var inp = document.createElement('input');
        inp.type  = 'hidden';
        inp.name  = name;
        inp.value = vals[i];
        form.appendChild(inp);
      }
    });
  }

  function readHiddenValuesByName(fieldName) {
    var form = document.getElementById('wizard-form');
    if (!form) return [];
    var values = [];
    form.querySelectorAll('input[name="' + fieldName + '"]').forEach(function (el) {
      if (el.value) values.push(el.value);
    });
    return normalizeIdList(values);
  }

  function readExtraDependentsFromForm() {
    try {
      var parsed = JSON.parse(elExtraDepInput.value || '[]');
      return Array.isArray(parsed) ? parsed : [];
    } catch (e) {
      Wz.warn('form', 'Falha ao ler extra_dependents_payload', e);
      return [];
    }
  }

  function applyInitialProfileCounts(profile, extraDependents) {
    if (profile === PROFILE_HOLDER) {
      var hasDependents = !!(elIncludeDepInput && elIncludeDepInput.value);
      state.holderDepCount = hasDependents ? extraDependents.length + 1 : 0;
      if (elHolderDepChk) elHolderDepChk.checked = hasDependents;
      if (elHolderCountArea) elHolderCountArea.hidden = !hasDependents;
      renderHolderDepCount();
      return;
    }
    state.guardianStudentCount = Math.max(1, extraDependents.length + 1);
    renderGuardianStudentCount();
  }

  function rehydrateInitialClassSelections(profile, extraDependents) {
    if (profile === PROFILE_HOLDER) {
      if (state.classSelections[0]) {
        state.classSelections[0].ids = readHiddenValuesByName('holder_class_groups');
      }
      if (state.classSelections[1]) {
        var dependentIds = readHiddenValuesByName('dependent_class_groups');
        state.classSelections[1].ids = dependentIds;
        if (state.deps[0]) state.deps[0].classGroups = dependentIds;
      }
      extraDependents.forEach(function (dependent, index) {
        var selection = state.classSelections[index + 2];
        var ids = normalizeIdList(dependent.class_groups);
        if (selection) selection.ids = ids;
        if (state.deps[index + 1]) state.deps[index + 1].classGroups = ids;
      });
      return;
    }
    if (state.classSelections[0]) {
      var studentIds = readHiddenValuesByName('student_class_groups');
      state.classSelections[0].ids = studentIds;
      if (state.deps[0]) state.deps[0].classGroups = studentIds;
    }
    extraDependents.forEach(function (student, index) {
      var selection = state.classSelections[index + 1];
      var ids = normalizeIdList(student.class_groups);
      if (selection) selection.ids = ids;
      if (state.deps[index + 1]) state.deps[index + 1].classGroups = ids;
    });
  }

  function rehydrateInitialWizardStateFromForm(profile) {
    var extraDependents = readExtraDependentsFromForm();
    applyInitialProfileCounts(profile, extraDependents);
    buildStepSequence();
    rehydrateInitialClassSelections(profile, extraDependents);
    saveWizardState();
  }

  function tryRestoreWizard() {
    try {
      var raw = sessionStorage.getItem(WIZARD_STORAGE_KEY);
      if (!raw) return false;
      var saved = JSON.parse(raw);
      if (!saved || saved.v !== 1 || !saved.profile) return false;

      _wizardRestoring = true;

      var form = document.getElementById('wizard-form');
      if (form && saved.fields) _applyHiddenFields(form, saved.fields);

      state.deps              = saved.deps              || [];
      state.classSelections   = saved.classSelections   || [];
      state.planSelections    = saved.planSelections     || [];
      state.teacherProposedSchedule = saved.teacherProposedSchedule || null;
      state.teacherExistingClassSelections = saved.teacherExistingClassSelections || [];
      state.holderDepCount    = saved.holderDepCount     || 0;
      state.guardianStudentCount = saved.guardianStudentCount || 1;

      selectProfile(saved.profile);

      state.holderDepCount       = saved.holderDepCount     || 0;
      state.guardianStudentCount = saved.guardianStudentCount || 1;
      state.deps                 = saved.deps              || [];
      state.classSelections      = saved.classSelections   || [];
      state.planSelections       = saved.planSelections    || [];
      state.teacherProposedSchedule = saved.teacherProposedSchedule || null;
      state.teacherExistingClassSelections = saved.teacherExistingClassSelections || [];

      if (saved.profile === PROFILE_HOLDER && state.holderDepCount > 0) {
        if (elHolderDepChk)    { elHolderDepChk.checked   = true; }
        if (elHolderCountArea) { elHolderCountArea.hidden  = false; }
        renderHolderDepCount();
        syncHolderDeps();
      }
      if (saved.profile === PROFILE_GUARDIAN) {
        renderGuardianStudentCount();
        syncGuardianStudents();
      }

      buildStepSequence();

      _wizardRestoring = false;

      var targetIdx = Math.min(saved.stepIndex || 0, state.stepSequence.length - 1);
      goTo(targetIdx);
      return true;
    } catch (e) {
      _wizardRestoring = false;
      Wz.warn('storage', 'Falha ao restaurar estado do wizard', e);
      return false;
    }
  }

  if (regPostMaterialsSkipped) {
    clearWizardState();
    showPostPaymentMode('step-review');
    renderReview();
  } else if (regPostMaterials) {
    clearWizardState();
    showPostPaymentMode('step-products');
    renderMaterialsConfirmed();
  } else if (regPostPlan) {
    clearWizardState();
    showPlanPaidMode();
  } else {
    var queryProfile = '';
    try {
      queryProfile = new URLSearchParams(window.location.search).get('profile') || '';
    } catch (e) {
      Wz.warn('url', 'Falha ao ler profile da query string', e);
      queryProfile = '';
    }
    if (isOperationalProfile(queryProfile)) {
      clearWizardState();
      selectProfile(queryProfile);
      renderGuardianStudentCount();
      renderHolderDepCount();
      updateProgress();
    } else {
      var _restored = tryRestoreWizard();
      if (!_restored) {
        var initialProfile = elProfileInput ? elProfileInput.value : '';
        if (initialProfile === PROFILE_HOLDER || initialProfile === PROFILE_GUARDIAN) {
          var initialIncludeDependent = elIncludeDepInput ? elIncludeDepInput.value : '';
          var initialExtraDependents = elExtraDepInput ? elExtraDepInput.value : '[]';
          selectProfile(initialProfile);
          if (elIncludeDepInput) elIncludeDepInput.value = initialIncludeDependent;
          if (elExtraDepInput) elExtraDepInput.value = initialExtraDependents;
          rehydrateInitialWizardStateFromForm(initialProfile);
        } else {
          buildStepSequence();
        }
        renderGuardianStudentCount();
        renderHolderDepCount();
        updateProgress();
      }
    }
  }

})();
