# PRD-109: Calendário administrativo quebra quando aulão cai em feriado

## Summary
`get_calendar_month_data()` monta o dicionário `holidays` como `{date: nome_do_feriado (string)}`, mas na montagem dos dados de aulão do dia (linha 1365) chama `_special_cancel_state(sc, holiday_name)` passando essa string — enquanto a função espera um objeto com atributo `.name` (é assim que os outros 4 call-sites da mesma função usam, passando o objeto `Holiday`). Quando um aulão cai num dia com feriado ativo cadastrado, a página quebra com `AttributeError: 'str' object has no attribute 'name'`.

## Demand type
Correção de bug (crash em runtime).

## Current problem
- `system/services/class_calendar.py:139-146` (`_special_cancel_state`): `if holiday: cancellation_reason = holiday.name` — espera um objeto `Holiday`.
- `system/services/class_calendar.py:1299-1300`: `holidays = {h.date: h.name for h in Holiday.objects.filter(...)}` — o dicionário guarda strings, não objetos.
- `system/services/class_calendar.py:1338`: `holiday_name = holidays.get(current_date, "")` — string.
- `system/services/class_calendar.py:1365`: `_special_cancel_state(sc, holiday_name)` — passa a string para o parâmetro que espera o objeto, ao contrário dos outros 4 usos da função (linhas 182, 270, 689, 773) que passam o objeto `Holiday` corretamente.
- Efeito: `CalendarView` (`system/views/calendar_views.py:66`, `context["calendar"] = get_calendar_month_data(...)`) quebra com 500 sempre que há um `SpecialClass` (aulão) numa data com `Holiday.is_active=True` cadastrado.

## Goal
Calendário administrativo renderiza normalmente mesmo com aulão marcado em dia de feriado, mostrando o feriado como motivo de cancelamento.

## Context Ledger
### Files read in full
- `system/services/class_calendar.py` (`_special_cancel_state` e os 5 call-sites; `get_calendar_month_data` completo)
- `system/views/calendar_views.py` (`CalendarView.get_context_data`, confirmando que é o único caminho de uso de `get_calendar_month_data`)

### Adjacent files consulted
- `system/tests/test_calendar.py` (`test_calendar_month_data_includes_specials`): confirmado que não cobre o caso aulão + feriado no mesmo dia — por isso o bug não foi pego antes.

### Limitations found
- Nenhuma.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
Autorizado pela solicitação atual ("finalize toda a implementação até não encontrar mais erros"). Único achado real de uma reauditoria do módulo Cronograma (demais aspectos investigados — CRUD de feriado, rotas órfãs — não apresentaram problema).

## Scope
- Corrigir a chamada na linha 1365 para passar o objeto `Holiday` (não a string), replicando o padrão dos outros 4 call-sites — isso exige que o dicionário `holidays` guarde o objeto, não só o nome, ou que se resolva o objeto separadamente.

## Out of scope
- CRUD de feriados (não há tela dedicada hoje; não há evidência de que seja um gap real — feriados são operação de baixa frequência, hoje via Django Admin, e não foi pedido/identificado como quebra).

## Impacted files
- `system/services/class_calendar.py`
- `system/tests/test_calendar.py`

## Risks and edge cases
- Preservar o comportamento de `is_holiday`/`holiday_name` (string) já usado no contexto do dia (linhas 1385-1386), que outras partes do template consomem — a correção deve resolver o objeto `Holiday` só para passar à função, sem quebrar os demais usos da string.

## Rules and constraints
- Nenhuma migration necessária (mudança de lógica pura em Python).

## Plan
- [x] Corrigir a passagem de argumento.
- [x] Teste focado cobrindo aulão + feriado no mesmo dia.
- [x] Suíte completa.

## Test plan
### Tests to author
- `get_calendar_month_data` não lança exceção e retorna `cancellation_reason` correto quando há aulão num dia de feriado ativo.

### Execution authorization
Autorizada localmente.

### Execution evidence
- `system/tests/test_calendar.py::SpecialClassServiceTestCase::test_calendar_month_data_does_not_crash_when_special_falls_on_holiday` (novo): antes da correção, este teste reproduzia o `AttributeError: 'str' object has no attribute 'name'`; após a correção, `get_calendar_month_data` retorna normalmente com `is_cancelled=True` e `cancellation_reason="Feriado Aulão Fundacao"`.
- `.venv/Scripts/python.exe manage.py test system.tests.test_calendar --verbosity 2` — 92 testes OK.
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 355 testes OK (suíte completa).
- `.venv/Scripts/python.exe manage.py check` — 0 problemas.

## Visual validation
Não aplicável a este fix pontual (cobertura por teste automatizado é suficiente para comprovar que o crash não ocorre mais); validação visual do calendário como um todo já foi feita em PRDs anteriores.

## ORM validation
`Holiday`/`SpecialClass` usados no teste focado.

## Quality validation
- `manage.py test system.tests.test_calendar` e suíte completa.
- `manage.py check`.

## Evidence
- Bug real confirmado por reprodução direta: o teste novo falhava com `AttributeError` antes da correção, comprovando o diagnóstico do agente de exploração (um dos poucos, nesta sessão, que não era falso positivo).

## Implemented
- `system/services/class_calendar.py`: `get_calendar_month_data` agora guarda o objeto `Holiday` no dicionário `holidays` (não a string), deriva `holiday_name` a partir dele, e passa o objeto (não a string) para `_special_cancel_state`, igual aos outros 4 call-sites da função.
- `system/tests/test_calendar.py`: 1 teste novo cobrindo aulão + feriado no mesmo dia.

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
