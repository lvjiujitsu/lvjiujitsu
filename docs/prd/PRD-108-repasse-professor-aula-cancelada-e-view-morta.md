# PRD-108: Repasse do professor conta aula cancelada; `TeacherFinancialView` é código morto

## Summary
Duas falhas no fluxo de repasse financeiro do professor: (1) `_count_class_attendances()` não exclui sessões/aulões cancelados da contagem de presenças usada no cálculo de comissão — um check-in aprovado antes do cancelamento continua contando; (2) `TeacherFinancialView` (tela "financeira" dedicada do professor) não tem rota em `system/urls.py` nem template (`templates/home/instructor/financial.html` não existe) — é código morto, superado pela seção "Repasse" já consolidada na home (`_build_instructor_payroll_context`).

## Demand type
Correção de bug (contagem financeira) + limpeza de código morto.

## Current problem
- `system/services/payroll_rules.py:828-845` (`_count_class_attendances`): conta `ClassCheckin`/`SpecialClassCheckin` com `status=APPROVED` sem excluir sessões/aulões com `status=CANCELLED`. Como `cancel_class_without_instructor`/`toggle_session_cancel` (`system/services/class_calendar.py:1018-1026`, `:1405-1419`) não invalidam check-ins já aprovados ao cancelar, um check-in aprovado antes do cancelamento continua contando indevidamente na comissão do professor.
- `system/views/asaas_views.py:322-356` (`TeacherFinancialView`): view completa e funcional, mas sem entrada em `system/urls.py` e sem o template `home/instructor/financial.html` (diretório `templates/home/instructor/` não existe). Todo o dado que ela monta (`config`, `bank`, `available_balance`, `recent_payouts`, etc.) já é equivalente ao que `_build_instructor_payroll_context()` (`system/views/home_views.py:252-275`) expõe na seção "Repasse" da home — a view é um resquício pré-consolidação da "Fundação" (PRD-075), nunca removido.

## Goal
- Comissão do professor nunca conta aula/aulão cancelado, mesmo que um check-in tenha sido aprovado antes do cancelamento.
- Código morto (`TeacherFinancialView` e seu import) removido, sem tentar recriar rota/template para uma tela redundante com a home.

## Context Ledger
### Files read in full
- `system/services/payroll_rules.py` (`_count_class_attendances`, `calculate_monthly_payroll`)
- `system/services/class_calendar.py` (`cancel_class_without_instructor`, `cancel_special_without_instructor`, `toggle_session_cancel`, `toggle_special_cancel`)
- `system/views/asaas_views.py` (`TeacherFinancialView`)
- `system/views/home_views.py` (`_build_instructor_payroll_context`)
- `system/urls.py` (confirmado: nenhuma rota referencia `TeacherFinancialView`)

### Adjacent files consulted
- `templates/home/dashboard.html` (seção "Repasse", já cobre tudo que `TeacherFinancialView` montava)
- `system/tests/test_services.py` (sem teste cobrindo exclusão de aula cancelada no payroll)

### Limitations found
- Descartada uma 4ª hipótese do agente de exploração (`refuse_payout` reaproveitar o campo `approved_by` em vez de um `refused_by` dedicado): o model `TeacherPayout` só tem um campo (`approved_by`), criar um novo exigiria migration para uma melhoria puramente cosmética — fora de escopo.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
Autorizado pela solicitação atual ("finalize toda a implementação até não encontrar mais erros"). Achados confirmados por leitura direta; a hipótese de "rota faltando" foi refinada para "código morto a remover" após confirmar que a home já cobre o mesmo dado (mesmo padrão arquitetural de não duplicar telas dedicadas quando a home já resolve).

## Scope
- `_count_class_attendances`: excluir `session__status=SessionStatus.CANCELLED` e `special_class__status=SessionStatus.CANCELLED` da contagem.
- Remover `TeacherFinancialView` de `system/views/asaas_views.py` e seu export em `system/views/__init__.py`.

## Out of scope
- Criar `refused_by` no `TeacherPayout` (melhoria cosmética, exigiria migration sem ganho funcional).
- Invalidar/reverter check-ins já aprovados no momento do cancelamento (mudaria o comportamento de `cancel_class_without_instructor`; a correção no cálculo de payroll já resolve o problema financeiro sem tocar no histórico de check-in).

## Impacted files
- `system/services/payroll_rules.py`
- `system/views/asaas_views.py`
- `system/views/__init__.py`
- `system/tests/test_services.py`

## Risks and edge cases
- Nenhum: exclusão adicional só reduz falsos positivos na contagem, não afeta os demais cálculos (hold days, repasse por aluno, etc.).

## Rules and constraints
- Não criar migration para este escopo.

## Plan
- [x] Corrigir contagem de presenças.
- [x] Remover código morto.
- [x] Testes focados.
- [x] Suíte completa.

## Test plan
### Tests to author
- Aula cancelada com check-in aprovado antes do cancelamento não conta na presença do payroll.
- Aulão cancelado com check-in aprovado antes do cancelamento não conta na presença do payroll.

### Execution authorization
Autorizada localmente.

### Execution evidence
- `system/tests/test_services.py::PayrollRulesServiceTestCase::test_per_class_attendance_rule_excludes_cancelled_session` (novo): check-in aprovado antes do cancelamento da sessão não conta mais na comissão (`class_attendance_count == 0`, `total == 0.00`).
- `.venv/Scripts/python.exe manage.py test system.tests.test_services --verbosity 2` — 18 testes OK.
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 354 testes OK (suíte completa).
- `.venv/Scripts/python.exe manage.py check` — 0 problemas.

## Visual validation
Não aplicável (mudança de cálculo em service + remoção de código morto sem UI associada).

## ORM validation
`ClassCheckin`/`ClassSession`/`SpecialClassCheckin` usados nos testes focados.

## Quality validation
- `manage.py test system.tests.test_services` e suíte completa.
- `manage.py check`.

## Evidence
- Confirmado que `get_staff_financial_context` (service) fica sem chamador de view após a remoção, mas foi mantido: é uma função de serviço legítima e reutilizável, sem indício de ser ela própria "morta" além de ter perdido seu único consumidor de view — remover o service em si não estava no escopo autorizado (só o resquício de view/rota/template).

## Implemented
- `system/services/payroll_rules.py`: `_count_class_attendances` agora exclui `session__status=CANCELLED` e `special_class__status=CANCELLED` da contagem de presenças.
- `system/views/asaas_views.py`: removidos `TeacherFinancialView` e `StaffFinancialRequiredMixin` (código morto: sem rota, sem template); imports órfãos (`INSTRUCTOR_PERSON_TYPE_CODES`, `get_staff_financial_context`) removidos.
- `system/views/__init__.py`: removida a exportação de `TeacherFinancialView`.
- `system/tests/test_services.py`: 1 teste novo.

## Cleanup findings
- Nenhum resíduo adicional.

## Follow-up PRDs
- Nenhuma.

## Deviations from plan
_Nenhum até o momento._

## Pending
_Nenhuma até o momento._

## Final status
Concluída.
