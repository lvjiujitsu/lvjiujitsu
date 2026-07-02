# PRD-110: Elegibilidade de graduação conta aula/aulão cancelado

## Summary
Mesmo padrão de bug corrigido na PRD-108 (repasse do professor), agora no cálculo de elegibilidade de graduação: `count_approved_classes_in_window()` conta `ClassCheckin`/`SpecialClassCheckin` com `status=APPROVED` sem excluir sessões/aulões com `status=CANCELLED`. Um check-in aprovado antes do cancelamento da aula continua contando para a janela de aulas exigidas para graduar.

## Demand type
Correção de bug (contagem incorreta), mesma causa raiz da PRD-108.

## Current problem
- `system/services/graduation.py:21-40` (`count_approved_classes_in_window`): não exclui `session__status=CANCELLED` nem `special_class__status=CANCELLED` das contagens.
- Mesma causa raiz documentada na PRD-108: `cancel_class_without_instructor`/`toggle_session_cancel` não invalidam check-ins já aprovados ao cancelar a sessão.

## Goal
Contagem de aulas para elegibilidade de graduação nunca inclui aula/aulão cancelado.

## Context Ledger
### Files read in full
- `system/services/graduation.py` (`count_approved_classes_in_window`, `compute_graduation_progress`, `get_graduation_history`, `get_current_graduation`)
- `system/services/payroll_rules.py` (`_count_class_attendances`, já corrigida na PRD-108 — usada como referência do padrão de correção)

### Adjacent files consulted
- `system/tests/test_graduation.py` (confirmado: nenhum teste cobre sessão cancelada na janela de contagem)

### Limitations found
- Nenhuma.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
Autorizado pela solicitação atual ("finalize toda a implementação até não encontrar mais erros"). Achado confirmado por leitura direta e comparação com a correção já aplicada na PRD-108 para o mesmo padrão de bug.

## Scope
- Adicionar `.exclude(session__status=SessionStatus.CANCELLED)` e `.exclude(special_class__status=SessionStatus.CANCELLED)` em `count_approved_classes_in_window`.

## Out of scope
- Qualquer outra mudança no módulo de graduação (views, templates e regras de faixa já foram confirmados corretos pela reauditoria).

## Impacted files
- `system/services/graduation.py`
- `system/tests/test_graduation.py`

## Risks and edge cases
- Nenhum: exclusão adicional só reduz falsos positivos na contagem.

## Rules and constraints
- Sem migration.

## Plan
- [x] Corrigir contagem.
- [x] Teste focado.
- [x] Suíte completa.

## Test plan
### Tests to author
- Aula cancelada com check-in aprovado antes do cancelamento não conta na janela de elegibilidade de graduação.

### Execution authorization
Autorizada localmente.

### Execution evidence
- `system/tests/test_graduation.py::GraduationServiceTestCase::test_count_approved_classes_excludes_cancelled_session` (novo): check-in aprovado antes do cancelamento da sessão não conta mais na janela (`0` em vez de `1`).
- `.venv/Scripts/python.exe manage.py test system.tests.test_graduation --verbosity 2` — 17 testes OK.
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 356 testes OK (suíte completa).
- `.venv/Scripts/python.exe manage.py check` — 0 problemas.

## Visual validation
Não aplicável (mudança de cálculo em service, sem UI nova).

## ORM validation
`ClassCheckin`/`ClassSession` usados no teste focado.

## Quality validation
- `manage.py test system.tests.test_graduation` e suíte completa.
- `manage.py check`.

## Evidence
- Mesmo padrão de bug e mesma correção da PRD-108 (repasse), agora aplicada em `count_approved_classes_in_window`.

## Implemented
- `system/services/graduation.py`: import de `SessionStatus`; `count_approved_classes_in_window` agora exclui `session__status=CANCELLED` e `special_class__status=CANCELLED`.
- `system/tests/test_graduation.py`: 1 teste novo.

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
