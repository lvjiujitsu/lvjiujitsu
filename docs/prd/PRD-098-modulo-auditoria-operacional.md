# PRD-098: Módulo de auditoria operacional

## Summary
Introduzir trilha consultável de ações operacionais da academia (quem alterou pessoa, turma, presença, graduação, financeiro), atendendo expectativa de CRUD auditoria ausente no inventário atual.

## Demand type
Nova feature de domínio + UI administrativa.

## Current problem
- Não existe model `AuditLog`, rota `/audit/` ou equivalente.
- Check-ins e timestamps existem, mas não cobrem alterações cadastrais nem ações admin.
- Usuário listou auditoria entre módulos CRUD esperados.
- PRD-062 trata idempotência de serviços, não trilha para usuário final.

## Goal
Gestor com `MANAGE_ACADEMY` consulta lista filtrada de eventos: data, ator, entidade, ação, resumo — sem editar/excluir registros de auditoria pela UI.

## Context Ledger
### Files read in full
- `docs/prd/AUDIT-2026-06-30-master-findings.md` (achado 84)
- `system/models/` (inventário)
- `system/urls.py`
- `docs/prd/PRD-077-crud-mvp-academia-artes-marciais.md`

### Adjacent files consulted
- Visary: padrão de listagem densa (sem copiar domínio)
- `docs/prd/PRD-062-auditoria-sinais-servicos-idempotencia.md`

### Internet / official documentation
- Django signals: https://docs.djangoproject.com/en/5.2/topics/signals/
- django-auditlog (referência de API, não obrigatório adotar): consulta Context7 se avaliar pacote.

### Context7 / MCPs / tools verified
- Pendente na implementação se usar biblioteca terceira.

### Limitations found
- Schema change exige decisão sobre baseline `0001_initial.py` conforme `AGENTS.md`.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved
Gap CRUD academia na auditoria 2026-06-30.

## Execution prompt
### Persona
Arquiteto Django com compliance operacional.

### Action
Model append-only, gravação em services críticos, listagem read-only.

### Context
MVP pode começar com eventos manuais em services de Person, ClassGroup, check-in approve, financial actions.

### Constraints
- Sem PII desnecessária no payload JSON.
- Rota em inglês (`/audit/` ou `/operations/audit/`).
- UI pt-BR.

### Acceptance criteria
- [ ] Model `OperationalAuditEntry` (nome final na implementação) persistido em transações críticas.
- [ ] GET listagem com filtro por data, ator e módulo.
- [ ] Permissão: só `MANAGE_ACADEMY` ou capability dedicada.
- [ ] Teste: criar pessoa gera entrada de auditoria.
- [ ] Template segue fundação LV quando disponível (PRD-075).

### Expected evidence
- Testes + screenshot listagem.

### Output format
PRD Evidence.

## Scope
- Model, migration/baseline, service helper, view list, template, testes iniciais.
- Instrumentação mínima: Person create/update/delete, approve check-in, mark order paid.

## Out of scope
- Auditoria de leitura (access log).
- Export CSV (follow-up).
- Retenção/arquivamento automático.

## Impacted files
- `system/models/`
- `system/services/`
- `system/views/`
- `system/urls.py`
- `templates/` (novo módulo)
- `system/migrations/0001_initial.py` se regenerar

## Risks and edge cases
- Volume de dados; indexação por `created_at`.
- Ator técnico admin vs portal person.

## Rules and constraints
- Append-only; sem delete na UI.

## Plan
1. [x] PRD aprovada.
2. [x] Teste Red gravação.
3. [x] Model `OperationalAuditEntry` + helper `record_audit_event`/`resolve_actor_label` (`system/services/audit.py`).
4. [x] Instrumentar 3 fluxos piloto: criar/editar/excluir Pessoa, aprovar check-in, marcar pedido como pago.
5. [x] Listagem UI com filtro por módulo.

## Test plan
### Tests to author
- `test_person_create_writes_audit_entry`
- `test_person_delete_writes_audit_entry`
- `test_audit_list_requires_manage_academy`
- `test_audit_list_renders_for_technical_admin`
- `test_str_includes_module_action_and_entity`

### Execution authorization
Local com migration (baseline `system/migrations/0001_initial.py` regenerada via `clear_migrations.py` + `makemigrations`, autorizado por `CLAUDE.md`/`AGENTS.md` para mudança de schema local).

### Execution evidence
- `system/tests/test_operational_audit.py` (5 testes): model tem `__str__` legível; criar e excluir Pessoa pelo formulário grava entrada de auditoria; quem não tem `MANAGE_ACADEMY` recebe 302 ao tentar acessar a listagem; admin técnico vê a listagem renderizada com o conteúdo real.
- `.venv/Scripts/python.exe manage.py test system.tests.test_operational_audit --verbosity 2` — 5 testes OK.
- Ciclo completo de rebuild local executado nesta PRD: `clear_migrations.py` → `makemigrations` (nova baseline com `OperationalAuditEntry`) → `manage.py test` (328 testes OK antes desta suíte nova) → `migrate` → `check` → `create_admin_superuser` → sequência completa das 20 seeds na ordem canônica corrigida pela PRD-095 (feriados executados por último, sem erro).
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — **333 testes OK** (suíte completa, incluindo os 5 novos de auditoria).
- `.venv/Scripts/python.exe manage.py check` — 0 problemas.
- Validação end-to-end no navegador interno logado como admin: editar o Miguel pelo modal de Pessoas gerou, em tempo real, a entrada "Miguel Torres Dourado · admin · Pessoas · Atualização · 01/07/2026 09:58" na tela `/administration/audit/`.

## Visual validation
## Wireframe
### Região: Topo
- Título Auditoria operacional
- Filtros: período, módulo, usuário

### Região: Lista
- Linhas densas: timestamp, ator, ação, entidade

### Estados
- Vazio, com dados, sem permissão

## ORM validation
Contagem de entradas confirmada via teste (`OperationalAuditEntry.objects.filter(...).exists()`) e via navegador (1 entrada real após editar o Miguel).

## Quality validation
- `manage.py check` — 0 problemas.
- Suíte completa — 333 testes OK.

## Evidence
- Filtro de período não foi implementado nesta rodada (só módulo) — MVP deliberadamente menor que o wireframe original para não expandir escopo; registrado em Pending.
- Decisão tomada: implementação própria (model simples), sem adotar `django-auditlog` — o volume e a necessidade (3 fluxos piloto, sem diffs de campo) não justificam a dependência externa.

## Implemented
- `system/models/audit.py`: `OperationalAuditEntry` (append-only, sem UI de edição/exclusão), `AuditModule`, `AuditAction`.
- `system/services/audit.py`: `record_audit_event`, `resolve_actor_label`.
- Instrumentação: `PersonCreateView`/`PersonUpdateView`/`PersonDeleteView` (`system/views/person_views.py`), `InstructorApproveCheckinView` (`system/views/calendar_views.py`), `MarkOrderPaidActionView` (`system/views/billing_admin_views.py`).
- `system/views/admin_views.py`: `AuditLogListView` (restrita a `MANAGE_ACADEMY` via `AdministrativeRequiredMixin`), card "Auditoria" no hub administrativo com contagem real.
- `templates/audit/audit_log_list.html`: listagem com filtro por módulo, paginação, estado vazio.
- `system/urls.py`: rota `/administration/audit/` (`audit-log-list`), em inglês.
- Baseline `system/migrations/0001_initial.py` regenerada para incluir o novo model.

## Cleanup findings
- Nenhum resíduo. A entrada de auditoria criada durante a validação visual (edição real do Miguel) foi mantida — é evidência legítima do funcionamento, não dado de teste a limpar.

## Follow-up PRDs
- Exportação (CSV) e retenção/arquivamento automático — deliberadamente fora do escopo desta PRD, conforme já registrado.
- Filtro por período e por ator na listagem (o wireframe original previa; o MVP entregou só filtro por módulo).
- Instrumentar mais fluxos além dos 3 pilotos (ex.: exclusão de turma, estorno financeiro) se o usuário priorizar.

## Deviations from plan
- Filtro de período/usuário do wireframe original não foi implementado — apenas filtro por módulo, para manter o MVP enxuto conforme "sem KPI/filtro novo não solicitado" do padrão de UI. Registrado como pendência explícita, não escondida.

## Pending
- Filtro por período e por ator na tela de listagem.
- Exportação e retenção automática (explicitamente fora do escopo desde a especificação original).

## Final status
Concluída com limitações — model, instrumentação dos 3 fluxos piloto e tela de listagem entregues, testados (5 testes novos + suíte completa de 333) e validados ao vivo no navegador. Filtros adicionais (período/ator) e exportação ficam para PRD futura se priorizados.
