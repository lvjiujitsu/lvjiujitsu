# PRD-097: Views de calendário órfãs sem rota

## Summary
Remover ou integrar classes legadas em `calendar_views.py` que não possuem entrada em `urls.py`, reduzindo superfície morta e confusão entre calendário unificado e admin calendar antigo.

## Demand type
Limpeza de código + governança.

## Current problem
- `AdminCalendarView`, `AdminToggleSessionView`, `AdminSpecialClassCreateView`, `AdminSpecialClassDeleteView` definidas com template `calendar/admin_calendar.html` inexistente.
- `CalendarView` unificada já atende `/cronograma/` para todos os perfis.
- Aliases `StudentScheduleView`, `InstructorCalendarView` mantidos sem uso em `urls.py`.
- Arquivo ~650 linhas dificulta manutenção.

## Goal
Uma superfície de calendário canônica (`CalendarView` + endpoints JSON existentes); código morto removido ou roteado com teste.

## Context Ledger
### Files read in full
- `system/views/calendar_views.py`
- `system/urls.py`
- `docs/prd/AUDIT-2026-06-30-master-findings.md`

### Adjacent files consulted
- `system/tests/test_calendar.py`
- Snapshot legado `calendar/admin_calendar.html` (referência apenas)

### Internet / official documentation
- N/A

### Context7 / MCPs / tools verified
- `rg` confirma ausência de rotas admin calendar.

### Limitations found
- Se alguma funcionalidade admin só existia nas views mortas, deve migrar para `CalendarView` antes de apagar.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
Auditoria 2026-06-30.

## Execution prompt
### Persona
Engenheiro de limpeza Django.

### Action
Inventariar imports; remover classes órfãs; garantir paridade funcional.

### Context
PRD-055 check-in e cronograma unificado.

### Constraints
- Não quebrar URLs registradas.
- Testes proporcionais.

### Acceptance criteria
- [ ] Nenhuma classe View em `calendar_views.py` sem rota ou uso testado.
- [ ] `rg AdminCalendarView` só histórico git ou zero no código ativo.
- [ ] `test_calendar` verde.
- [ ] Documentar na PRD se recurso admin foi consolidado em `CalendarView`.

### Expected evidence
- Diff + testes.

### Output format
PRD Evidence.

## Scope
- `calendar_views.py`
- `urls.py` se reencaminhamento necessário
- Testes

## Out of scope
- Novo template admin calendar separado.

## Impacted files
- `system/views/calendar_views.py`
- `system/tests/test_calendar.py`

## Risks and edge cases
- Import externo de alias em código não rastreado.

## Rules and constraints
- PRD-076 limpeza controlada.

## Plan
1. [x] `rg` imports de aliases.
2. [x] Migrar comportamento se gap (nenhum gap: `CalendarView` já cobria todos os perfis).
3. [x] Remover código morto.
4. [x] Testes.

## Test plan
### Tests to author
- `system/tests/test_lv_foundation_calendar.py::CalendarDeadCodeRemovedTestCase` confirma via `hasattr` que as 4 views foram removidas.

### Execution authorization
Local.

### Execution evidence
- `rg "AdminCalendarView|AdminToggleSessionView|AdminSpecialClassCreateView|AdminSpecialClassDeleteView" system/` retornava apenas o próprio `calendar_views.py` e o barrel `system/views/__init__.py` antes da remoção; nenhuma rota, template ou teste as referenciava.
- `.venv/Scripts/python.exe manage.py test system.tests.test_lv_foundation_calendar --verbosity 2` — 3 testes OK.
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 316 testes OK após a remoção (nenhuma regressão).
- `.venv/Scripts/python.exe manage.py check` — 0 problemas.

## Visual validation
Cronograma (`/calendar/`) validado no navegador interno durante a PRD-077 — sem qualquer dependência das views removidas.

## ORM validation
N/A.

## Quality validation
- `manage.py check` — OK.
- Suíte completa — OK.

## Evidence
- `AdminCalendarView` apontava para `template_name = "calendar/admin_calendar.html"`, que nunca existiu no repositório — confirma que a view nunca foi de fato executável.
- `AdminSpecialClassCreateView`/`AdminSpecialClassDeleteView` duplicavam exatamente a lógica de `InstructorSpecialClassCreateView`/`InstructorSpecialClassDeleteView`, que já cobrem administradores via override de capacidade.

## Implemented
- Removidas as 4 classes de `system/views/calendar_views.py` e suas entradas em `system/views/__init__.py` (imports e `__all__`).
- Limpos os imports agora não usados em `calendar_views.py`: `PersonTypeCode`, `Person`, `AdministrativeRequiredMixin`.

## Cleanup findings
- Nenhum resíduo. Arquivo `calendar_views.py` reduzido e sem símbolos órfãos remanescentes.

## Follow-up PRDs
- Nenhum.

## Deviations from plan
- Esta PRD foi implementada como parte do trabalho da PRD-077 (módulo Cronograma), não isoladamente — evidência registrada aqui para fechar o rastreamento.

## Pending
- Nenhum.

## Final status
Concluída.
