# PRD-107: Instrutor consegue aprovar check-in de aula regular já cancelada

## Summary
`approve_special_checkin` (aulão) valida `if checkin.special_class.is_cancelled: raise ValueError(...)` antes de aprovar presença, mas a função equivalente para turma regular, `approve_class_checkin`, não tem essa mesma validação — permitindo aprovar presença de uma aula que já foi marcada como cancelada.

## Demand type
Correção de bug (assimetria de validação entre dois caminhos análogos).

## Current problem
- `system/services/class_calendar.py:1250-1269` (`approve_class_checkin`): valida permissão (`instructor_group_ids`/substituto) e `checkin.is_approved`, mas não valida `checkin.session.is_cancelled` — aprova presença de aula cancelada silenciosamente.
- `system/services/class_calendar.py:1272-1289` (`approve_special_checkin`): valida a mesma coisa e, adicionalmente, `if checkin.special_class.is_cancelled: raise ValueError("Este aulão foi cancelado.")`.
- `system/views/calendar_views.py:511-516` (`InstructorApproveCheckinView.post`) e `:547-552` (`InstructorApproveSpecialCheckinView.post`): nenhuma das duas views captura `ValueError` vindo do service — só `ClassCheckin.DoesNotExist`/`SpecialClassCheckin.DoesNotExist` e `PermissionError`. Isso significa que, mesmo com a validação de `approve_special_checkin` já existente, hoje ela gera um **erro 500 não tratado** em vez de uma mensagem de erro limpa, pois o `ValueError` propaga sem ser capturado.
- `ClassSession` e `SpecialClass` (`system/models/calendar.py`) ambos expõem a property `is_cancelled`.

## Goal
`approve_class_checkin` recusa aprovar presença de uma sessão de aula já cancelada, com a mesma mensagem/padrão do caminho de aulão; e ambas as views retornam um erro JSON limpo (400) em vez de 500 quando a aula/aulão está cancelado.

## Context Ledger
### Files read in full
- `system/services/class_calendar.py` (`approve_class_checkin`, `approve_special_checkin`, funções de cancelamento de aula/aulão/self-checkin do instrutor)
- `system/models/calendar.py` (`ClassSession.is_cancelled`, `SpecialClass.is_cancelled`)

### Adjacent files consulted
- `system/views/calendar_views.py` (`InstructorApproveCheckinView`, `InstructorApproveSpecialCheckinView`)

### Limitations found
- Nenhuma.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
Autorizado pela solicitação atual ("finalize toda a implementação até não encontrar mais erros"). Achado confirmado por comparação direta de código entre os dois caminhos análogos (aula regular vs. aulão); demais hipóteses da mesma reauditoria (cancelamento de aula/aulão ou auto-checkin do instrutor não validarem check-ins já aprovados) foram deixadas de fora por serem decisões de produto debatíveis, não uma assimetria de código comprovada como esta.

## Scope
- Adicionar a mesma validação de `is_cancelled` em `approve_class_checkin`, espelhando `approve_special_checkin`.
- Adicionar `except ValueError` em `InstructorApproveCheckinView.post` e `InstructorApproveSpecialCheckinView.post`, retornando `JsonResponse({"error": str(e)}, status=400)`.

## Out of scope
- Validações de check-ins pendentes em `cancel_class_without_instructor`/`cancel_special_without_instructor`/auto-checkin do instrutor (comportamento atual pode ser intencional; não há evidência de regressão, só uma hipótese de risco — não abrir mudança sem confirmação de que é de fato indesejado).

## Impacted files
- `system/services/class_calendar.py`
- `system/tests/`

## Risks and edge cases
- Nenhum: a mudança só bloqueia um caminho que já deveria estar bloqueado, replicando um padrão já validado.

## Rules and constraints
- Mensagem de erro em pt-BR, mesmo padrão do aulão ("Esta aula foi cancelada.").

## Plan
- [x] Adicionar validação.
- [x] Teste focado.
- [x] Suíte completa.

## Test plan
### Tests to author
- Aprovar check-in de sessão cancelada levanta `ValueError` e não altera o status do check-in.

### Execution authorization
Autorizada localmente.

### Execution evidence
- `system/tests/test_calendar.py::CheckinApprovalServiceTestCase::test_approve_class_checkin_blocks_cancelled_session` (novo): aprovar check-in de sessão cancelada levanta `ValueError` e mantém status `PENDING`.
- `system/tests/test_calendar.py::InstructorApproveCheckinViewTestCase::test_approve_checkin_of_cancelled_session_returns_clean_400` (novo): a view retorna 400 com mensagem JSON limpa em vez de 500.
- `.venv/Scripts/python.exe manage.py test system.tests.test_calendar --verbosity 2` — 91 testes OK.
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 353 testes OK (suíte completa).
- `.venv/Scripts/python.exe manage.py check` — 0 problemas.

## Visual validation
Não aplicável (mudança de regra de negócio em service, sem UI nova; view já trata exceções de validação existentes do mesmo padrão).

## ORM validation
`ClassCheckin`/`ClassSession` usados no teste focado.

## Quality validation
- `manage.py test system.tests.test_lv_foundation_calendar` (ou teste novo) e suíte completa.
- `manage.py check`.

## Evidence
- Achado colateral relevante: `approve_special_checkin` já validava `is_cancelled` desde antes desta PRD, mas a `ValueError` levantada nunca era capturada por `InstructorApproveSpecialCheckinView` — ou seja, o caminho de aulão já tinha essa proteção "ativa" no código mas resultava em erro 500 para o usuário. A correção da view beneficia os dois caminhos.

## Implemented
- `system/services/class_calendar.py`: `approve_class_checkin` agora valida `checkin.session.is_cancelled` antes de aprovar, espelhando `approve_special_checkin`.
- `system/views/calendar_views.py`: `InstructorApproveCheckinView.post` e `InstructorApproveSpecialCheckinView.post` agora capturam `ValueError` e retornam `JsonResponse({"error": ...}, status=400)` em vez de deixar a exceção propagar como 500.
- `system/tests/test_calendar.py`: 2 testes novos (serviço + view).

## Cleanup findings
- Nenhum resíduo.

## Follow-up PRDs
- Nenhuma.

## Deviations from plan
_Nenhum até o momento._

## Pending
_Nenhuma até o momento._

## Final status
Concluída.
