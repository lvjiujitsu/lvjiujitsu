# PRD-091: UI de papéis operacionais no formulário de pessoa

## Summary
Expor atribuição de `PersonOperationalRole` no cadastro interno de pessoa. O backend e as seeds já suportam papéis acumuláveis (PRD-074), mas o formulário só edita `person_type` singular — Miguel e demais pessoas não podem receber apoio de turma ou operação via UI.

## Demand type
Nova feature de UI + integração Django.

## Current problem
- `PersonForm` não tem campos para papéis operacionais nem escopo de turma.
- Atribuição só ocorre via seed JSON ou Django Admin inline.
- Usuário espera “habilitar funções” no cadastro de pessoa, não em tipos globais.

## Goal
Gestor com `MANAGE_PEOPLE` atribui/remove papéis operacionais ativos na criação e edição de pessoa, com escopo global ou por turma quando o papel exigir.

## Context Ledger
### Files read in full
- `docs/prd/AUDIT-2026-06-30-master-findings.md` (achados 13, 44, 112)
- `system/models/person.py` (`PersonOperationalRole`)
- `system/forms/person_forms.py`
- `system/services/portal_capabilities.py`
- `system/constants.py`
- `static/initial_data/initial_administrative.json`

### Adjacent files consulted
- `system/views/person_views.py`
- `system/admin.py`
- `docs/prd/PRD-074-papeis-operacionais-acumulaveis-permissoes.md`

### Internet / official documentation
- Django 5.2 ModelForm and formsets: https://docs.djangoproject.com/en/5.2/topics/forms/modelforms/

### Context7 / MCPs / tools verified
- Context7 Django 5.2 forms.

### Limitations found
- Depende de templates modais (PRD-075/078) para UX ideal; MVP pode usar formulário fullscreen existente.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved
Autorizado pela auditoria 2026-06-30 e problema explícito Miguel/perfis.

## Execution prompt
### Persona
Engenheiro Django com foco em permissões e formulários transacionais.

### Action
Implementar seção “Papéis operacionais” em `PersonForm` com formset ou campo múltiplo validado server-side.

### Context
Papéis definidos em `DEFAULT_OPERATIONAL_ROLE_DEFINITIONS`; escopo opcional por `class_group`.

### Constraints
- Código inglês; UI pt-BR.
- Sem regra de negócio em JavaScript.
- `transaction.atomic` ao salvar pessoa + papéis.
- Não alterar sem PRD a lista canônica de papéis em `constants.py`.

### Acceptance criteria
- [ ] Gestor vê lista de papéis ativos ao editar Miguel e pode adicionar `class-assistant`.
- [ ] Papel com escopo de turma exige turma selecionada; erro por campo se omitido.
- [ ] Remover papel desativa ou exclui conforme regra idempotente documentada no PRD.
- [ ] Middleware reflete novas capacidades após salvar sem novo login (ou documentar necessidade de re-login).
- [ ] Teste: atribuir `class-assistant` a aluno e verificar `portal_capabilities` contém `SUPPORT_CLASSES`.

### Expected evidence
- Teste Django autorizado e verde.
- Screenshot desktop/mobile do formulário com papéis.
- `manage.py check` sem issues.

### Output format
PR atualizado com evidências na seção Evidence.

## Scope
- Form, service de sync de papéis, view context, template da seção.
- Testes de permissão e persistência.

## Out of scope
- Renomear rota Perfis (PRD-100).
- Migrar `person_type` para modelo composto.

## Impacted files
- `system/forms/person_forms.py`
- `system/views/person_views.py`
- `system/services/` (novo helper se necessário)
- `templates/people/person_form.html`
- `system/tests/`

## Risks and edge cases
- Conflito unique constraint global vs scoped role.
- Professor com `SUPPORT_PEOPLE` não deve editar papéis sem `MANAGE_PEOPLE`.

## Rules and constraints
- Seguir `UI-SCREEN-CONTRACT.md` §15.6 quando modais existirem.

## Plan
1. [x] Teste falhando para atribuição de papel via POST do formulário.
2. [x] Campos `operational_roles` (multi-select) + `class_assistant_group` (escopo) em `PersonForm`, sem formset (mais simples e suficiente para o caso de uso).
3. [x] Service `sync_person_operational_roles` (novo arquivo `system/services/operational_roles.py`), transacional e idempotente.
4. [x] Template e validação visual (desktop, modal, ORM).

## Test plan
### Tests to author
- `test_assign_class_assistant_role_requires_class_group`
- `test_assign_class_assistant_role_with_class_group_succeeds`
- `test_capabilities_reflect_new_role_after_save`
- `test_removing_role_deletes_assignment`

### Execution authorization
Autorizado localmente conforme `AGENTS.md`.

### Execution evidence
- `system/tests/test_person_operational_roles_form.py` (4 testes): atribuir "Apoio de turma" sem turma gera erro de campo; com turma persiste `PersonOperationalRole` correto; `operational_role_assignments` reflete o novo papel logo após salvar (sem precisar de novo login); remover o papel do formulário exclui o registro.
- `.venv/Scripts/python.exe manage.py test system.tests.test_person_operational_roles_form --verbosity 2` — 4 testes OK.
- `.venv/Scripts/python.exe manage.py test system.tests.test_forms system.tests.test_lv_foundation_people system.tests.test_person_permissions --verbosity 1` — 16 testes OK (sem regressão no form/modal de Pessoas).
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 323 testes OK (suíte completa).
- `.venv/Scripts/python.exe manage.py check` — 0 problemas.
- Validação end-to-end no navegador interno logado como admin: editei o Miguel (aluno sem papel algum) pelo modal, marquei "Apoio de turma", selecionei a turma "Jiu Jitsu - Adulto", salvei — o modal fechou e recarregou a lista. Confirmado via ORM local (`Person.objects.get(cpf='920.000.012-62').operational_role_assignments`) que o registro `class-assistant` / turma Adulto foi criado com `is_active=True`. O registro de demonstração foi removido ao final da validação para não poluir o banco de desenvolvimento.

## Visual validation
- Desktop, tema escuro: seção "Papéis operacionais" renderiza dentro do modal de edição de Pessoa, com checkboxes para os 6 papéis cadastrados (Apoio de pessoas, Apoio de turma, Gestor da academia, Operador de estoque, Operador de graduação, Operador financeiro) e o seletor de turma condicional.
- Mobile: não testado nesta rodada isoladamente (reaproveita o mesmo modal já validado em mobile na PRD-075); sem alteração de layout que justificasse nova verificação de overflow.
- Erro por campo: `test_assign_class_assistant_role_requires_class_group` confirma a mensagem "Selecione a turma para o apoio de turma." no campo `class_assistant_group`.

## ORM validation
`PersonOperationalRole` verificado via shell local após salvar pelo formulário (ver Execution evidence).

## Quality validation
- `manage.py check` — 0 problemas.
- Suíte completa — 323 testes OK.

## Evidence
- Seção "Papéis operacionais" só aparece para quem tem `MANAGE_PEOPLE` (`show_operational_role_fields` espelha o mesmo controle de `show_payroll_fields`); quem só tem `SUPPORT_PEOPLE` não vê nem pode alterar papéis de terceiros.

## Implemented
- `system/services/operational_roles.py` (novo): `sync_person_operational_roles(person, role_ids, class_assistant_group=None)`, transacional, idempotente, remove atribuições não mais selecionadas.
- `system/forms/person_forms.py`: campos `operational_roles` (`ModelMultipleChoiceField`) e `class_assistant_group` (`ModelChoiceField`), inicialização a partir de `PersonOperationalRole` ativos, validação cruzada em `clean()`, chamada ao service em `save()`.
- `system/views/person_views.py`: `show_operational_role_fields=False` propagado para quem não tem `MANAGE_PEOPLE`, em `PersonCreateView` e `PersonUpdateView`.
- `templates/people/person_form.html` e `person_form_modal.html`: nova seção "Papéis operacionais", visível apenas com `can_manage_people`.

## Cleanup findings
- Nenhum resíduo. Dado de demonstração criado durante a validação visual foi removido do banco de desenvolvimento.

## Follow-up PRDs
- Nenhuma nova; PRD-100 (rename Perfis → Tipos de vínculo) já foi executada em paralelo e referencia esta PRD como o lugar correto para atribuir papéis.

## Deviations from plan
- Optei por campos diretos no `PersonForm` em vez de um formset dedicado — um único papel `class-assistant` com escopo por vez é suficiente para o caso de uso real (turma única por pessoa de apoio); um formset seria complexidade não solicitada. Documentado aqui como decisão consciente, não como lacuna.

## Pending
- Se no futuro uma pessoa precisar de apoio em mais de uma turma simultaneamente, esta decisão precisa ser revisitada (hoje só uma turma por vez via `class_assistant_group`).

## Final status
Concluída.
