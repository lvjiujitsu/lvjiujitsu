# PRD-099: Permissão de edição de pessoa para apoio

## Summary
Alinhar `PersonUpdateView` (e exclusão se aplicável) às capacidades reais: quem tem `SUPPORT_PEOPLE` e pode criar aluno deve poder editar fichas de alunos/dependentes, enquanto `MANAGE_PEOPLE` mantém edição ampla.

## Demand type
Correção de permissões.

## Current problem
- `PersonCreateView` usa `PeopleSupportRequiredMixin` (`SUPPORT_PEOPLE`).
- `PersonUpdateView` usa `AdministrativeRequiredMixin` (`MANAGE_ACADEMY`).
- Professor fica bloqueado ao editar aluno que acabou de cadastrar.
- Contribui para “cadastro de pessoa disfuncional” reportado pelo usuário.

## Goal
Matriz coerente create/read/update/delete por capability documentada e testada.

## Context Ledger
### Files read in full
- `system/views/person_views.py`
- `system/views/portal_mixins.py`
- `docs/prd/PRD-014-painel-administrativo-como-pessoa.md`
- `docs/prd/AUDIT-2026-06-30-master-findings.md` (achado 15)

### Adjacent files consulted
- `system/tests/test_person_delete.py`
- `docs/prd/PRD-074-papeis-operacionais-acumulaveis-permissoes.md`

### Internet / official documentation
- Django 5.2 access mixins: https://docs.djangoproject.com/en/5.2/topics/auth/default/#the-permissionrequiredmixin-mixin

### Context7 / MCPs / tools verified
- Context7 Django 5.2.

### Limitations found
- Edição de campos sensíveis (payroll, tipo administrativo) deve permanecer restrita.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
Auditoria 2026-06-30.

## Execution prompt
### Persona
Engenheiro de autorização.

### Action
Substituir mixin de update por verificação granular no dispatch/get_queryset.

### Context
PRD-014 prometia professor cadastrar e visualizar alunos sem financeiro admin.

### Constraints
- Campos payroll e `person_type` administrativo só com `MANAGE_PEOPLE`.
- CSRF e validação server-side.

### Acceptance criteria
- [ ] Instrutor com `SUPPORT_PEOPLE` edita aluno existente (nome, turmas).
- [ ] Instrutor não edita pessoa administrativa nem campos payroll.
- [ ] Gestor com `MANAGE_PEOPLE` edita todos os campos atuais.
- [ ] Testes de permissão 302 vs 200.
- [ ] `PersonDeleteView` permanece restrito a gestão (documentado).

### Expected evidence
- Testes verdes.

### Output format
PRD Evidence.

## Scope
- `person_views.py`
- Testes em `system/tests/`

## Out of scope
- Novos campos no formulário.

## Impacted files
- `system/views/person_views.py`
- `system/tests/test_forms.py` ou novo `test_person_permissions.py`

## Risks and edge cases
- Instrutor alterar plano/financeiro via campos ocultos — bloquear no form.

## Rules and constraints
- Não enfraquecer `MANAGE_ACADEMY` para módulos financeiros.

## Plan
1. [x] Teste instrutor update aluno Red.
2. [x] Trocar `AdministrativeRequiredMixin` por `PeopleSupportRequiredMixin` em `PersonUpdateView` (mesma capability do Create).
3. [x] Restringir queryset (exclui administrativo/professor) e campos do form (`person_type_codes`, `show_payroll_fields=False`) para quem não tem `MANAGE_PEOPLE`, espelhando `PersonCreateView`.
4. [x] Green.

## Test plan
### Tests to author
- `test_support_people_can_update_student`
- `test_support_people_cannot_update_administrative_person`
- `test_support_people_form_hides_payroll_fields`

### Execution authorization
Local.

### Execution evidence
- `system/tests/test_person_permissions.py` (3 testes): instrutor com papel `people-support` (só `SUPPORT_PEOPLE`) consegue abrir a edição de um aluno (200); a mesma pessoa tenta editar um administrativo e recebe 404 (queryset já exclui); o formulário não mostra "Repasse do professor" e `form.show_payroll_fields` é `False`.
- `.venv/Scripts/python.exe manage.py test system.tests.test_person_permissions --verbosity 2` — 3 testes OK.
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 319 testes OK (suíte completa, sem regressão).
- `.venv/Scripts/python.exe manage.py check` — 0 problemas.

## Visual validation
Não aplicável nesta rodada (mudança é de permissão/queryset, reaproveita o template/modal já existente e validado nas PRDs 075/077).

## ORM validation
N/A — coberto pelos testes de permissão acima.

## Quality validation
- `manage.py check` — 0 problemas.
- Suíte completa — 319 testes OK.

## Evidence
- Antes: `PersonUpdateView(AdministrativeRequiredMixin, ...)` exigia `MANAGE_ACADEMY`, bloqueando qualquer pessoa com apenas `SUPPORT_PEOPLE` (ex.: papel operacional `people-support`, ou instrutor que cadastrou o aluno) de editar a ficha que acabou de criar.
- `PersonCreateView` já usava `PeopleSupportRequiredMixin` e já restringia `person_type_codes`/`show_payroll_fields` para quem não gerencia — o Update não replicava essa mesma matriz, causando a assimetria create-sim/update-não relatada pelo usuário.

## Implemented
- `system/views/person_views.py`: `PersonUpdateView` trocou `AdministrativeRequiredMixin` por `PeopleSupportRequiredMixin`; `get_queryset` filtra por `CLASS_ENROLLMENT_PERSON_TYPE_CODES` quando `not _can_manage_people`; novo `get_form_kwargs` replica a restrição de `PersonCreateView` (sem payroll, sem trocar para tipo administrativo/professor).
- `PersonDeleteView` permanece com `AdministrativeRequiredMixin` (`MANAGE_ACADEMY`), conforme decisão explícita de manter exclusão restrita à gestão.

## Cleanup findings
- Nenhum resíduo. Nenhuma duplicação de lógica: `PersonUpdateView` agora espelha exatamente o padrão já usado por `PersonCreateView`.

## Follow-up PRDs
- Nenhum.

## Deviations from plan
- Nenhum desvio funcional.

## Pending
- Nenhum.

## Final status
Concluída.
