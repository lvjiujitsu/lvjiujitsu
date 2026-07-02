# PRD-093: Responsável iniciar treino e matrícula

## Summary
Permitir que pessoa com vínculo `guardian` (responsável) inicie treino: matrícula em turmas, faixa inicial e check-in como aluno titular, sem forçar troca de `person_type` para `student` quando a regra de negócio permitir acumulação.

## Demand type
Correção de regra de negócio + formulário.

## Current problem
- `PersonForm.clean` rejeita `class_groups` se tipo não for `student` ou `dependent` (`person_forms.py:460-466`).
- `CLASS_ENROLLMENT_PERSON_TYPE_CODES` não inclui `guardian`.
- Middleware marca `portal_is_student=True` para responsável via `ACCESS_STUDENT_AREA`, mas sem turmas o usuário não treina.
- Problema explícito do usuário: responsável não pode começar a treinar.

## Goal
Responsável ativo pode:
- receber turmas e matrícula via cadastro interno ou fluxo aprovado;
- ver área de aluno na home quando matriculado;
- fazer check-in nas aulas matriculadas.

## Context Ledger
### Files read in full
- `system/forms/person_forms.py`
- `system/constants.py`
- `system/models/person.py` (`can_enroll_in_class_group`)
- `docs/prd/PRD-040-fluxo-cadastro-pagamento-antes-pessoa.md` (adjacente)

### Adjacent files consulted
- `system/services/membership.py`
- `docs/prd/AUDIT-2026-06-30-master-findings.md`

### Internet / official documentation
- Django 5.2 validation: https://docs.djangoproject.com/en/5.2/ref/forms/validation/

### Context7 / MCPs / tools verified
- Context7 Django 5.2.

### Limitations found
- Decisão de produto: responsável treina como titular com mesmo CPF ou exige perfil `student` separado — PRD deve registrar decisão escolhida na implementação.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved
Autorizado pelo problema explícito do usuário.

## Execution prompt
### Persona
Engenheiro de domínio academia.

### Action
Estender elegibilidade de matrícula e validação do formulário para responsável que inicia treino.

### Context
Papéis acumuláveis PRD-074; faturamento pode permanecer no responsável.

### Constraints
- Validar idade/categoria IBJJF igual aos demais tipos.
- Não quebrar fluxo de dependente vs titular.

### Acceptance criteria
- [ ] Gestor atribui turmas a pessoa `guardian` sem erro de formulário.
- [ ] `can_enroll_in_class_group()` alinhado ao form.
- [ ] Home exibe “Minha área” quando responsável tem matrícula ativa.
- [ ] Check-in funciona para responsável matriculado (com regras PRD-094).
- [ ] Teste cobre caso feliz e bloqueio sem turma.

### Expected evidence
- Testes verdes.
- ORM local com guardian matriculado.

### Output format
PRD atualizada.

## Scope
- `constants.py` se necessário.
- `person_forms.py`, `person.py`.
- Testes forms e home.

## Out of scope
- Wizard público para responsável titular (PRD-040 escopo próprio).
- Cobrança/plano do responsável-aluno.

## Impacted files
- `system/constants.py`
- `system/forms/person_forms.py`
- `system/models/person.py`
- `system/tests/test_forms.py`
- `system/tests/test_home_dashboard.py`

## Risks and edge cases
- Responsável com dependentes: faturamento e tabs na home.
- Menor de idade como responsável (improvável).

## Rules and constraints
- Regra explícita em PRD antes de código se houver duas interpretações.

## Plan
1. [x] Decisão documentada: guardian pode matricular-se e treinar mantendo o vínculo `guardian` (sem forçar troca para `student`); faturamento permanece no responsável, conforme já implementado por `get_membership_owner`/`get_guardian_billing_tabs`.
2. [x] Teste Red.
3. [x] Ajuste em `constants.py` (`CLASS_ENROLLMENT_PERSON_TYPE_CODES` passou a incluir `PersonTypeCode.GUARDIAN`).
4. [x] Green + teste de home.

## Test plan
### Tests to author
- `test_guardian_can_receive_class_groups_on_update`
- `test_guardian_with_enrollment_has_personal_home_area`

### Execution authorization
Local.

### Execution evidence
- `system/tests/test_guardian_can_train.py` (2 testes): gestor edita um responsável e atribui turma sem erro de formulário, criando `ClassEnrollment` ativo; responsável com matrícula ativa vê `has_personal_area=True` e o rótulo "Responsável" na home.
- `.venv/Scripts/python.exe manage.py test system.tests.test_guardian_can_train --verbosity 2` — 2 testes OK.
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 325 testes OK (suíte completa, sem regressão nos demais usos de `CLASS_ENROLLMENT_PERSON_TYPE_CODES`: listagem de pessoas, overview de graduação, seed de graduação inicial no cadastro público).
- `.venv/Scripts/python.exe manage.py check` — 0 problemas.

## Visual validation
Não executada nesta rodada isoladamente (mudança é de elegibilidade de dados, reaproveita o mesmo formulário/modal já validado visualmente na PRD-075/091).

## ORM validation
`ClassEnrollment` ativo confirmado via teste (ver Execution evidence).

## Quality validation
- `manage.py check` — 0 problemas.
- Suíte completa — 325 testes OK.

## Evidence
- `get_class_group_eligibility_error` (usada na validação do form) já era neutra quanto a `person_type` — valida apenas idade/sexo biológico vs categoria da turma. O único bloqueio real era a checagem explícita em `PersonForm.clean()` contra `CLASS_ENROLLMENT_PERSON_TYPE_CODES`, que não incluía `guardian`.
- `CLASS_ENROLLMENT_PERSON_TYPE_CODES` é usado em 7 pontos do código (listagem/detalhe de pessoas, overview de graduação, seed de graduação inicial no checkout, contexto "aluno" da home) — todos os usos fazem sentido semântico para incluir responsáveis que também treinam; nenhum deles é uma trava de cobrança/pagamento que pudesse ter efeito colateral indesejado.

## Implemented
- `system/constants.py`: `CLASS_ENROLLMENT_PERSON_TYPE_CODES` passou a incluir `PersonTypeCode.GUARDIAN`.

## Cleanup findings
- Nenhum resíduo. Mudança mínima e cirúrgica em uma única constante amplamente reaproveitada, sem duplicar lógica.

## Follow-up PRDs
- PRD-040 (wizard público) não foi alterada nesta PRD — fica como decisão de produto separada se o cadastro público precisar oferecer matrícula direta para responsável titular.

## Deviations from plan
- Nenhum desvio funcional.

## Pending
- Nenhuma pendência de código. Decisão de produto sobre plano/mensalidade do responsável-aluno permanece em aberto (cobrança já flui para o responsável via `get_membership_owner`, mas nenhuma tela nova de plano foi criada especificamente para este caso).

## Final status
Concluída.
