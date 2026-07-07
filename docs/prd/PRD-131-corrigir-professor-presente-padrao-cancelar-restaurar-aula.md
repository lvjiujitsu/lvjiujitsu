# PRD-131: Corrigir professor presente por padrão ao cancelar/restaurar aula

## Summary
Corrige uma regressão latente no gating de check-in do aluno (PRD-094): cancelar e depois restaurar uma aula do dia — sem que o professor jamais tenha se declarado ausente — deixa a sessão travada em "professor não confirmado" (`instructor_present=False`) para sempre, bloqueando o check-in de **todos** os alunos matriculados naquela turma, mesmo que o professor titular vá dar a aula normalmente. Regra de negócio esperada pelo usuário: toda turma está ativa/com professor presente por padrão todos os dias; só fica pendente de confirmação quando o professor **explicitamente** cancela sua própria presença ou indica um substituto.

## Demand type
Correção de regressão de regra de negócio (reportada pelo usuário via captura de tela: dois alunos recém-cadastrados, matriculados na mesma turma/horário, viam estados diferentes de check-in em momentos diferentes — investigação em par com o usuário identificou a causa raiz).

## Current problem
- `system/services/class_calendar.py::toggle_session_cancel` (usada tanto por `InstructorToggleSessionView`, o toggle da página de calendário, quanto por `cancel_class_without_instructor`, o botão "Cancelar aula" do dashboard) cria a `ClassSession` do dia via `ClassSession.objects.get_or_create(schedule=.., date=.., defaults={"status": SessionStatus.SCHEDULED})` — **sem** `instructor_present=True` nos defaults.
- Isso difere do padrão já usado em `register_instructor_self_checkin` (`_session_creation_defaults()`, que inclui `instructor_present=True`).
- Resultado: se a **primeira** ação tocando a sessão do dia for um cancelamento (calendário ou "Cancelar aula"), sem que o professor tenha antes se declarado ausente (`cancel_instructor_self_checkin`) ou indicado substituto (`assign_session_substitute`), a sessão nasce com `instructor_present=False` (default do campo do model). Cancelar não expõe o problema (aula cancelada não mostra o gate de check-in), mas **restaurar** (`toggle_session_cancel` de novo, voltando `status=SCHEDULED`) não reseta `instructor_present` — a aula volta a aparecer como normal, mas com o professor marcado como "não confirmado", bloqueando check-in de todos os alunos até alguém confirmar presença manualmente.
- Reproduzido nesta sessão: dois alunos novos (Beatriz e Carlos), matriculados nas mesmas duas turmas de hoje, viram estados diferentes de check-in em momentos diferentes — não por diferença entre eles, mas porque, entre uma captura de tela e outra, as duas `ClassSession` do dia foram criadas (provavelmente via cancelar/restaurar no calendário) com `instructor_present=False`, travando o check-in retroativamente para os dois.
- Validado ao vivo: login como Beatriz, no estado atual, mostra o mesmo bloqueio que Carlos — confirma que não é bug de cadastro/matrícula, é o `toggle_session_cancel`.

## Goal
Toda turma nasce com o professor titular assumido como presente por padrão, todos os dias — sem exigir nenhuma ação prévia. O check-in do aluno só deve ficar bloqueado (mensagem "Solicite ao professor...") quando o professor **explicitamente** declarar ausência (`cancel_instructor_self_checkin`) ou quando um substituto for indicado e ainda não tiver confirmado (`assign_session_substitute`). Cancelar e restaurar uma aula, isoladamente, nunca deve travar o check-in dos alunos.

## Context Ledger
### Files read in full
- `system/services/class_calendar.py` (todas as funções de presença/sessão: `_student_instructor_present`, `_instructor_presence_state`, `_session_creation_defaults`, `register_instructor_self_checkin`, `cancel_instructor_self_checkin`, `assign_session_substitute`, `toggle_session_cancel`, `cancel_class_without_instructor`, `perform_checkin`)
- `system/models/calendar.py` (`ClassSession`, `SpecialClass` — `instructor_present` default `False` no model)
- `system/views/calendar_views.py` (`InstructorToggleSessionView`, `InstructorCancelClassTodayView`)
- `templates/home/partials/today_classes_list.html` (gate `{% elif not item.instructor_present %}` → mensagem "Solicite ao professor...")
- `docs/prd/PRD-094-checkin-aluno-papel-duplo-precondicao-professor.md` (origem do gate, confirma o comportamento "sem sessão = presente por padrão")
- `system/tests/test_calendar.py` (testes existentes de toggle/cancelamento/substituto — nenhum fixa o valor de `instructor_present` após um cancelar+restaurar feito **sem** declaração prévia de ausência, confirmando que a lacuna não tinha cobertura)

### Adjacent files consulted
- `system/services/class_calendar.py::create_special_class` (aulão sempre nasce com `instructor_present=True` — não tem o mesmo problema, confirma que o padrão correto já é usado em outro lugar do próprio arquivo)

### Limitations found
- N/A — investigação de causa raiz concluída via ORM/shell ao vivo, sem necessidade de documentação externa (é regra de negócio interna, não integração de terceiros).

## Required skills
`lv-task-intake`, `lv-prd`, `lv-django-delivery`, `lv-cleanup-audit`

## Understanding approved
Usuário confirmou a regra de negócio diretamente: "é previsto que as turmas estejam sempre ativas todos os dias apenas se o professor não for dar a aula ele cancela sua presença... é pré-entendido que ele irá dar a aula para não precisar ficar tendo que realizar o check-in todo dia. Só se ele não for, ele cancela a aula ou indica outro professor." E pediu explicitamente: "reavalie em um novo PRD o fluxo completo e testes."

## Scope
- `system/services/class_calendar.py::toggle_session_cancel`: trocar `defaults={"status": SessionStatus.SCHEDULED}` por `defaults=_session_creation_defaults()` no `get_or_create`, alinhando com o mesmo padrão já usado em `register_instructor_self_checkin`.
- Novos testes cobrindo exatamente o cenário relatado: cancelar uma aula que nunca teve declaração de ausência do professor, restaurar, e confirmar que `instructor_present` permanece/volta a `True` (check-in liberado) — tanto via `toggle_session_cancel`/`cancel_class_without_instructor` diretamente quanto via `get_today_classes_for_person` (visão do aluno).
- Confirmar (teste de não-regressão) que o caminho onde o professor **explicitamente** se declara ausente antes de cancelar (`cancel_instructor_self_checkin` → `cancel_class_without_instructor` → restaurar) continua exigindo confirmação manual após restaurar (comportamento correto e já coberto por `test_today_classes_exposes_can_uncancel_class_after_instructor_cancel`).

## Out of scope
- Qualquer mudança em `assign_session_substitute`/`cancel_instructor_self_checkin` (já corretos — criam a sessão com `instructor_present=False` de forma deliberada, refletindo uma declaração explícita).
- Qualquer mudança em `SpecialClass`/aulão (já nasce com `instructor_present=True` via `create_special_class`).
- Criação de rotina/cron para pré-gerar `ClassSession` todos os dias — o modelo "lazy" (sessão só existe quando algo a toca) permanece, apenas o valor default na criação muda.

## Rules and constraints
- Sem migration de schema (campo `instructor_present` já existe, só muda o valor default usado na criação via este fluxo específico).
- Preservar 100% dos testes existentes de `test_calendar.py` sem regressão.
- TDD: teste Red antes do fix.

## Test plan
### Tests to author
- `test_cancel_class_without_instructor_declaration_keeps_instructor_present_after_restore`: sem nenhuma declaração prévia de ausência, cancela e restaura uma aula — `instructor_present` deve ser `True` após restaurar.
- `test_toggle_session_cancel_creates_session_with_instructor_present_true_by_default`: `toggle_session_cancel` chamado diretamente numa turma sem sessão prévia — a sessão criada nasce com `instructor_present=True` (mesmo estando cancelada nesse momento).
- `test_student_checkin_available_after_cancel_restore_without_absence_declaration`: visão do aluno (`get_today_classes_for_person`) mostra `instructor_present=True` (botão Check-in) após esse ciclo cancelar/restaurar sem declaração prévia.
- Não-regressão: `test_today_classes_exposes_can_uncancel_class_after_instructor_cancel` (já existente) continua OK sem alteração — confirma que declaração explícita de ausência ainda exige reconfirmação após restaurar.

### Execution authorization
Local.

## Plan
1. [x] Escrever os 3 testes novos (Red).
2. [x] Ajustar `toggle_session_cancel` para usar `_session_creation_defaults()`.
3. [x] Rodar os novos testes (Green) e a suíte completa de `test_calendar.py` (não-regressão).
4. [x] `manage.py check`.
5. [x] Validar ao vivo no navegador interno logando como Beatriz (conta real já criada), conferindo que o check-in volta a aparecer.

## Implemented
- `system/services/class_calendar.py::toggle_session_cancel`: `get_or_create` agora usa `defaults=_session_creation_defaults()` (`instructor_present=True`, `instructor_checked_in_at=now()`) em vez de `defaults={"status": SessionStatus.SCHEDULED}` — alinhado com o mesmo padrão já usado em `register_instructor_self_checkin`.
- `system/services/class_calendar.py::cancel_class_without_instructor`: as duas guardas (`instructor_present` e `substitute_teacher_id`) passam a considerar `not session.is_cancelled` — evita bloquear a **restauração** de uma aula cancelada (guarda existia para impedir cancelar uma aula com o professor já confirmado/substituto indicado, não para impedir restaurar). Sem essa correção, o fix do item anterior fazia a restauração falhar com "Cancele a confirmação antes de cancelar a aula." mesmo sem nenhuma confirmação pendente.
- `system/tests/test_calendar.py` (`InstructorSelfCheckinServiceTestCase`): 3 testes novos — `test_toggle_session_cancel_creates_session_with_instructor_present_true_by_default`, `test_cancel_class_without_instructor_declaration_keeps_instructor_present_after_restore`, `test_student_checkin_available_after_cancel_restore_without_absence_declaration`.
- Dados reais corrigidos via ORM: as duas `ClassSession` de hoje (schedule 2 e 10, criadas antes do fix com `instructor_present=False`) tiveram o valor corrigido para `True` — refletindo o que a criação já teria feito com o fix aplicado, sem exigir ação manual do professor.

## Evidence
- Teste Red confirmado antes do fix: os 3 testes novos falhavam (`AssertionError: False is not true`), reproduzindo exatamente o bug relatado.
- Após o fix: `manage.py test system.tests.test_calendar --verbosity 2` → **103 testes, OK** (100 pré-existentes + 3 novos, nenhuma regressão).
- `manage.py check` → limpo.
- Validação ao vivo no navegador interno: login como Beatriz Aluna Stripe (CPF `529.982.247-25`) — antes do fix mostrava "Solicite ao professor..." nas duas turmas de hoje; após corrigir os dados existentes (refletindo o novo default) e reiniciar o servidor de preview para carregar o código novo, a mesma conta volta a mostrar o botão "Check-in" normalmente nas duas turmas.
- `manage.py test` (suíte completa) → **554 testes, OK**. `manage.py check` → limpo. Nenhuma regressão em nenhuma outra área do sistema.

## Cleanup findings
Nenhum resíduo. A correção foi cirúrgica (2 linhas de comportamento em `toggle_session_cancel`/`cancel_class_without_instructor`), sem introduzir campo novo, migration ou configuração.

## Final status
Concluída e validada — testes automatizados (103, suíte de calendário + suíte completa) e validação visual ao vivo.
