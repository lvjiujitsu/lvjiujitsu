/**
 * Autofill de teste para o wizard de cadastro — use APENAS em ambiente de desenvolvimento.
 * Cole no console do Chrome com /register/ aberto.
 *
 * Uso:
 *   1. Abra http://127.0.0.1:8000/register/  (ou /register/recomecar/ para limpar estado)
 *   2. Cole este arquivo no console e execute
 *   3. O wizard preencherá automaticamente até o step-plan
 *   4. Selecione o plano desejado e clique em "Pagar"
 *
 * Perfis disponíveis: preencha a variável PROFILE antes de colar:
 *   "holder"   → Aluno Titular   (padrão)
 *   "guardian" → Responsável com aluno
 *
 * Dados usados: CPF 529.982.247-25 (CPF válido fictício para testes)
 */

(function () {
  'use strict';

  // ── Configuração ──────────────────────────────────────────────────────────
  var PROFILE = 'holder'; // "holder" | "guardian"
  var DATA = {
    holder: {
      name: 'Teste Autofill Aluno',
      cpf: '529.982.247-25',
      birthdate: '15/03/1990',
      sex: 'male',
      phone: '(62) 99999-0001',
      email: 'teste.aluno@dev.local',
      password: 'Teste@1234',
    },
    guardian: {
      name: 'Teste Autofill Responsável',
      cpf: '153.509.460-56',
      birthdate: '10/05/1980',
      sex: 'female',
      phone: '(62) 88888-0002',
      email: 'teste.responsavel@dev.local',
      password: 'Teste@1234',
      studentName: 'Filho Teste',
      studentCpf: '871.464.850-07',
      studentBirthdate: '20/07/2015',
      studentSex: 'male',
    },
  };

  // ── Utilitários ───────────────────────────────────────────────────────────
  function setField(id, val) {
    var el = document.getElementById(id);
    if (!el) { console.warn('[autofill] campo não encontrado:', id); return false; }
    var proto = el.tagName === 'SELECT' ? HTMLSelectElement.prototype : HTMLInputElement.prototype;
    var setter = Object.getOwnPropertyDescriptor(proto, 'value');
    if (setter && setter.set) setter.set.call(el, val);
    else el.value = val;
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
    el.dispatchEvent(new Event('blur', { bubbles: true }));
    return true;
  }

  function clickId(id) {
    var el = document.getElementById(id);
    if (!el) { console.warn('[autofill] botão não encontrado:', id); return false; }
    el.click();
    return true;
  }

  function sleep(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }

  // ── Fluxo principal ───────────────────────────────────────────────────────
  async function run() {
    console.log('[autofill] iniciando preenchimento do wizard — perfil:', PROFILE);

    // Step 1 — selecionar perfil
    var profileBtn = document.querySelector('button[data-profile="' + PROFILE + '"]');
    if (!profileBtn) { console.error('[autofill] botão de perfil não encontrado:', PROFILE); return; }
    profileBtn.click();
    await sleep(300);
    if (!clickId('step-1-next')) return;
    await sleep(600);

    var d = DATA[PROFILE];
    if (!d) { console.error('[autofill] dados não definidos para perfil:', PROFILE); return; }

    // Step 2 — dados pessoais do titular / responsável
    var prefix = PROFILE === 'guardian' ? 'guardian' : 'holder';
    setField('ui-s2-name', d.name);
    await sleep(200); // aguarda debounce de CPF
    setField('ui-s2-cpf', d.cpf);
    await sleep(600); // aguarda validação assíncrona de CPF
    setField('ui-s2-birthdate', d.birthdate);
    setField('ui-s2-sex', d.sex);
    setField('ui-s2-phone', d.phone);
    setField('ui-s2-email', d.email);
    setField('ui-s2-password', d.password);
    setField('ui-s2-password-confirm', d.password);

    if (PROFILE === 'guardian' && d.studentName) {
      // campos do aluno dependente
      setField('ui-s2-student-name', d.studentName);
      setField('ui-s2-student-cpf', d.studentCpf);
      setField('ui-s2-student-birthdate', d.studentBirthdate);
      setField('ui-s2-student-sex', d.studentSex);
    }

    await sleep(300);
    if (!clickId('step-2-next')) return;
    await sleep(600);

    // Step 3 — saúde (pular)
    if (!clickId('step-health-next')) return;
    await sleep(400);

    // Step 4 — artes marciais (pular)
    if (!clickId('step-martial-next')) return;
    await sleep(600);

    // Step 5 — turmas: selecionar primeiro cartão visível
    var classCards = Array.from(document.querySelectorAll('#step-classes button[type="button"]'));
    var visibleClass = classCards.find(function (b) { return b.offsetParent !== null && !b.id; });
    if (!visibleClass) {
      visibleClass = classCards.find(function (b) { return b.offsetParent !== null; });
    }
    if (visibleClass) {
      visibleClass.click();
      console.log('[autofill] turma selecionada:', visibleClass.textContent.trim().slice(0, 60));
    } else {
      console.warn('[autofill] nenhum cartão de turma encontrado — continue manualmente');
    }
    await sleep(300);
    if (!clickId('step-classes-next')) return;
    await sleep(600);

    // Step 6 — planos: mostrar disponíveis
    var planCards = Array.from(document.querySelectorAll('button[data-plan-id], button.plan-card'))
      .filter(function (b) { return b.offsetParent !== null; });
    if (planCards.length === 0) {
      // fallback: qualquer botão visível com texto "Individual" ou "Fidelidade"
      planCards = Array.from(document.querySelectorAll('button'))
        .filter(function (b) {
          return b.offsetParent !== null &&
            (b.textContent.includes('Individual') || b.textContent.includes('Fidelidade') || b.textContent.includes('Família'));
        });
    }

    console.log('[autofill] wizard preenchido! Planos disponíveis:');
    planCards.forEach(function (b, i) {
      console.log('  [' + i + ']', b.textContent.trim().slice(0, 80));
    });
    console.log('[autofill] clique no plano desejado e depois em "Pagar" para continuar.');
  }

  run().catch(function (err) { console.error('[autofill] erro:', err); });
})();
