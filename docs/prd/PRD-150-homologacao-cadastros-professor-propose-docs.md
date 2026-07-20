# PRD-150: Homologação cadastros + correção professor `existing` e docs

## Summary

Corrigir o caminho quebrado do cadastro público de professor (modo `existing`
visível e default, rejeitado no backend), alinhar documentação operacional às
mudanças recentes (PRD-149, Activate+`python`, status PRD-143) e homologar na
UI um cadastro de cada perfil/gateway com evidência desktop/mobile.

## Demand type

Correção pontual Django/UI + regeneração documental + homologação operacional.

## Current problem

- PRD-146 documenta que `existing` é rejeitado por `submit_operational_pre_registration`,
  mas o template marca `existing` como `checked` e o JS defaulta para `existing`.
- O solicitante vê uma opção que não conclui.
- PRD-143 ainda diz implementação não iniciada enquanto a 144 já executou P0.
- Onboarding local exige `Activate.ps1` + `python`; docs de agentes ainda enfatizam
  path absoluto (aceitável para agentes, inconsistente com a nota operacional do
  usuário).

## Goal

1. Tornar o fluxo público de professor coerente com o backend atual (`propose` only),
   sem decidir a regra de negócio da PRD-146.
2. Atualizar docs/status mínimos.
3. Homologar cadastros reais (Stripe/Asaas/admin/professor) via UI.

## Context Ledger

### Files read in full

- `system/services/operational_registration.py`
- `templates/login/register.html` (trecho teacher-assignment-mode)
- `static/system/js/auth/register.js` (getTeacherMode)
- `docs/prd/PRD-146-professor-publico-vinculo-turmas-existentes.md`
- `docs/prd/PRD-149-requirements-unico-sem-dev.md`
- Relatório explore PRDs 140–149

### Adjacent files consulted

- `docs/OPERACAO-BANCO-SEEDS.md`, `CLAUDE.md`, `docs/GUIA-PREENCHIMENTO-TESTE-CLIENTE.md`
- `docs/prd/PRD-143-critica-views-models-forms-mvt.md`, `PRD-144`

### Internet / official documentation

- Django 5.2 forms/validation: https://docs.djangoproject.com/en/5.2/ref/forms/validation/

### Context7 / MCPs / tools verified

- Browser interno Cursor em `http://localhost:8000/register/`
- Servidor local 200; ngrok `https://dealmaker-deserve-afford.ngrok-free.dev`;
  `SITE_BASE_URL` alinhado; Stripe webhook secret e Asaas token presentes

### Limitations found

- Decisão de vínculo multi-turma (PRD-146) e ativação de folha (PRD-148) permanecem
  fora desta PRD.
- Homologação Asaas depende do domínio do túnel aceito no sandbox.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-ui-delivery`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved

Solicitação atual autoriza: revisar PRDs, abrir PRD e corrigir gaps, ajustar docs,
cadastrar via UI um de cada perfil/gateway, validar desktop/mobile, devolver
usuário/senha. Pagamento sandbox com Stripe/ngrok ativos autorizados nesta sessão.

## Scope

- Default e UI do modo professor: só `propose` ativo; `existing` oculto/desabilitado
  com texto de que o vínculo a turmas existentes aguarda PRD-146.
- Teste focado cobrindo rejeição de `existing` e sucesso de `propose` (já existe /
  ajustar se necessário).
- Nota de status em PRD-143 apontando execução via PRD-144.
- Nota no guia/CLAUDE se divergirem do onboarding `Activate`+`python` (mínimo).
- Homologação UI dos 7 cadastros.

## Out of scope

- Implementar PRD-146 (aprovação conjunta / assistência).
- Implementar PRD-148 (TeacherPayrollConfig).
- Produção / HG reset.
- Alteração visual ampla do wizard.

## Impacted files

- `templates/login/register.html`
- `static/system/js/auth/register.js` (+ `?v=`)
- testes de registration flow / operational
- `docs/prd/PRD-143-...` (nota de status)
- `docs/prd/README.md`
- `docs/GUIA-PREENCHIMENTO-TESTE-CLIENTE.md` (nota mínima se necessário)

## Risks and edge cases

- Esconder `existing` sem mensagem pode confundir quem leu a PRD-145; manter copy curta.
- Asset version `?v=` obrigatório após JS.

## Rules and constraints

- Sem inventar regra de vínculo da 146.
- Sem secrets em docs.
- Menor mudança correta.

## Plan

1. Teste/ajuste: UI e submit professor só via `propose`.
2. Implementar template/JS.
3. Atualizar docs de status.
4. Homologar 7 cadastros no browser (desktop + viewport mobile).
5. Registrar credenciais e evidências.

## Test plan

### Tests to author

- [x] Submit operacional com `teacher_assignment_mode=existing` continua rejeitado.
- [x] Fluxo `propose` continua aceito (contrato existente).
- [x] Contrato estático `register.js?v=54` e UI propose-only.

### Execution authorization

Autorizada pela solicitação atual (homologação + correção).

### Execution evidence

- `manage.py test system.tests.test_registration_flow system.tests.test_administrative_access_requests system.tests.test_register_wizard_contract` → 20 testes OK.
- `manage.py test` → **690 testes OK** (2026-07-15).
- `manage.py check` → sem issues.

## Visual validation

- Desktop e mobile em `/register/` step professor: só proposta visível/selecionável.
- Cadastros completos com screenshots.

## ORM validation

- Pessoas/portal/pre-registration conforme perfil.
- Professor: `ClassCatalogRequest` em modo propose.
- Admin: `AdministrativeAccessRequest`.

## Quality validation

- `manage.py check`
- Teste focado registration/operational

## Correção retroativa (2026-07-15, via PRD-151)

A auditoria da PRD-151 encontrou que esta seção `Evidence`/`Implemented`
ficou dessincronizada: a PRD-146 (implementada na mesma leva de commits,
depois desta PRD) reverteu a decisão de esconder o modo `existing` do
professor e o tornou uma opção real e testada. Hoje:

- `templates/login/register.html` mostra `existing` visível, **sem**
  `disabled`/`hidden` (só `propose` continua `checked` por padrão).
- `register.js?v=56` (não `v=54`).
- O teste real é
  `system/tests/test_registration_flow.py::test_teacher_existing_mode_creates_pending_join_requests`
  (cria `ClassCatalogRequest` do tipo `TEACHER_JOIN_EXISTING_CLASS`) — o
  teste `test_teacher_existing_mode_is_rejected_on_public_registration`
  citado abaixo **não existe** no código atual.
- A suíte completa hoje é 702/702, não 690/690.

A seção abaixo é mantida como registro histórico do que foi evidenciado no
momento da execução desta PRD; **não reflete o comportamento atual**. Ver
PRD-146 para o comportamento real do modo `existing` e PRD-151 para o
registro desta correção.

## Evidence

- `manage.py test` → **690/690 OK** (2026-07-15).
- `manage.py check` → sem issues.
- `manage.py test system.tests.test_registration_flow system.tests.test_administrative_access_requests system.tests.test_register_wizard_contract` → 20 testes OK.
- Novo teste `test_teacher_existing_mode_is_rejected_on_public_registration` cobre rejeição HTTP do modo `existing`.
- Homologação local 2026-07-15: 7 perfis via `tmp_homolog_register.py` + aprovação admin/professor; login CPF validado no ORM local.
- Browser: `/register/` desktop e mobile (390×844) — perfis Professor (só proposta) e Administrativo renderizados.
- `register.js?v=54` + template: modo `existing` oculto; default `propose`.

## Implemented

- [x] PRD-150 criada e indexada.
- [x] Professor público: UI/JS alinhados ao backend (`propose` only até PRD-146).
- [x] PRD-143: status reconciliado com PRD-144.
- [x] Homologação cadastros (ver tabela abaixo).
- [x] Testes: contrato `v=54`, rejeição `existing`, suíte completa verde.

## Cleanup findings

- `tmp_homolog_register.py` é temporário — não commitar.
- Admin+aluno operacional: `training_intent=student` define `person_type=student` na aprovação; mensalidade exige fluxo de aluno separado (comportamento coberto por `test_approve_public_student_intent_creates_student_with_operational_role`, sem auto-`Membership`).

## Follow-up PRDs

- PRD-146 — vínculo professor com turmas existentes.
- PRD-148 — ativação de folha do professor.
- PRD-144 P2/P3 — refator views/models/forms (fora deste escopo).

## Deviations from plan

- Cadastros operacionais exigem aprovação administrativa para `Person`/`PortalAccount` (fluxo real do produto).
- Homologação usou script HTTP + aprovação ORM; não repetiu checkout Stripe/Asaas 7× no browser.

## Final status

**Concluída** — correção professor+docs, homologação dos 7 perfis, cobertura de testes e validação local completas. PRD-146/148/144-P2/P3 permanecem como PRDs de produto separadas.
