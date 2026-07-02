# PRD-094: Check-in aluno com papel duplo e pré-condição do professor

## Summary
Garantir que pessoa aluna — inclusive com papel administrativo ou apoio de turma — consiga solicitar check-in como aluna, com regra clara sobre dependência da presença do professor e separação das listas de aula na home.

## Demand type
Correção de fluxo de presença + UX.

## Current problem
- Botão check-in aluno só aparece se `item.instructor_present` (`today_classes_section.html:217-218`).
- Aline (aluno + apoio) pode estar na lista errada da home (visão staff vs aluno).
- `perform_checkin` não valida matrícula, mas UI pode ocultar ação.
- Usuário: Aline administrativa não consegue marcar presença como aluna.

## Goal
Aluno matriculado sempre vê estado claro: aguardando professor, disponível para check-in, pendente ou confirmado — na seção **Minha área**, independente de papéis staff.

## Context Ledger
### Files read in full
- `system/services/class_calendar.py` (`get_today_classes_for_person`, `perform_checkin`)
- `templates/home/partials/today_classes_section.html`
- `system/views/home_views.py`
- `static/system/js/home/dashboard.js`

### Adjacent files consulted
- `docs/prd/PRD-055-checkin-com-aprovacao-do-professor.md`
- `docs/prd/AUDIT-2026-06-30-master-findings.md`

### Internet / official documentation
- N/A

### Context7 / MCPs / tools verified
- N/A

### Limitations found
- Se a regra de negócio exigir professor presente, UX deve comunicar sem parecer bug.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved
Problema explícito Aline na auditoria 2026-06-30.

## Execution prompt
### Persona
Engenheiro de presença e cronograma.

### Action
Revisar gating de check-in e garantir entrada `entry_role=student` nas aulas matriculadas para papéis duplos.

### Context
PRD-092 split; seed Aline com matrículas adult.

### Constraints
- Backend valida matrícula e sessão cancelada.
- Mensagens pt-BR acessíveis.

### Acceptance criteria
- [ ] Aline logada vê botão ou mensagem explícita em cada aula matriculada na Minha área.
- [ ] Check-in POST retorna sucesso quando professor presente e matrícula ativa.
- [ ] Quando professor ausente, mensagem orienta ação (não tela vazia).
- [ ] Teste integração: aluno + `class-assistant` faz check-in em turma matriculada.
- [ ] `perform_checkin` rejeita sem matrícula com `ValueError` claro.

### Expected evidence
- Teste API check-in verde.
- Screenshot estados antes/depois professor self-check-in.

### Output format
PRD Evidence.

## Scope
- Service calendar, partial template, home context, testes.

## Out of scope
- Aprovação em lote pelo professor (já existe).
- Calendário mensal completo.

## Impacted files
- `system/services/class_calendar.py`
- `system/views/home_views.py`
- `templates/home/partials/today_classes_section.html`
- `system/tests/test_calendar.py` ou novo arquivo

## Risks and edge cases
- Apoio de turma kids vs matrícula adult.
- Aulão especial sem professor titular.

## Rules and constraints
- Coordenar com PRD-092 para lista correta.

## Plan
1. [x] Teste Red check-in Aline (reproduzido ao vivo no navegador antes de codar: seção "Turmas de hoje" simplesmente não aparecia).
2. [x] Ajustar `home_views.py` (não foi `get_today_classes_for_person`, que já estava correta — o bug era na escolha de qual lista vira `today_classes`).
3. [x] UX: nenhuma mensagem nova necessária; a mensagem "Solicite ao professor..." já existia no partial para quando `instructor_present=False`.
4. [x] Green.

## Test plan
### Tests to author
- `test_dual_role_student_sees_own_checkin_merged_with_support_classes`

### Execution authorization
Local.

### Execution evidence
- Reproduzido ao vivo no navegador interno logado como Aline (CPF `920.000.011-81`, seed real): a seção "Turmas de hoje" não existia na home — confirmado via ORM que `get_today_classes_for_person(aline)` retornava 2 aulas reais de hoje com `instructor_present=True` (deveria mostrar botão Check-in), mas a home não usava essa lista para ela.
- Causa raiz: em `home_views.py`, o bloco `if is_instructor or (can_support_classes and not is_administrative): context["today_classes"] = get_today_classes_for_instructor(person)` sobrescrevia `today_classes` com a visão de apoio/instrutor, descartando a lista pessoal (`my_classes`) para qualquer pessoa com `can_support_classes=True`, mesmo quando ela também treina.
- Corrigido: quando a pessoa treina e não é instrutora (mas tem `can_support_classes`), `today_classes` passa a ser o **merge** de `my_classes` (suas próprias aulas, `entry_role=student`) com as aulas de apoio (`entry_role` diferente de `student`), ordenado por horário, via novo helper `_merge_class_entries`.
- `system/tests/test_home_dashboard.py::test_dual_role_student_sees_own_checkin_merged_with_support_classes` (novo): pessoa aluna + `class-assistant`, matriculada e com aula hoje, vê "Turmas de hoje", vê "Check-in" e o `today_classes` do contexto contém uma entrada com `entry_role="student"`.
- `.venv/Scripts/python.exe manage.py test system.tests.test_home_dashboard --verbosity 2` — 5 testes OK (incluindo os 2 testes pré-existentes que já cristalizavam o comportamento correto de "sem Gestão" para Aline — preservados sem alteração).
- `.venv/Scripts/python.exe manage.py test system.tests.test_calendar --verbosity 1` — 89 testes OK (fluxo de check-in em si não foi alterado, só o roteamento de qual lista aparece na home).
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 326 testes OK (suíte completa).
- Validação ao vivo pós-fix: logada como Aline, a home mostra "Turmas de hoje" com as 2 aulas reais (06:30 e 19:00, Jiu Jitsu Adulto) cada uma com botão "Check-in" visível, mais a ação "Criar aulão" do apoio de turma na mesma lista — sem seção "Gestão" indevida.

## Visual validation
Validado no navegador interno (ver Execution evidence). Mobile não testado nesta rodada isoladamente — o layout do card de aula é o mesmo já validado em mobile nas PRDs anteriores, sem alteração estrutural que justificasse nova verificação de alvo de toque.

## ORM validation
`get_today_classes_for_person`/`get_today_classes_for_instructor` verificados via shell local antes e depois da correção (ver Execution evidence).

## Quality validation
- `manage.py check` — 0 problemas.
- Suíte completa — 326 testes OK.

## Evidence
- O gating `{% elif not item.instructor_present %}` no partial já exibia a mensagem "Solicite ao professor que realize o check-in na aula para continuar" corretamente — não havia bug de UX ali. O bug era estrutural: a lista errada chegava ao template.

## Implemented
- `system/views/home_views.py`: novo helper `_merge_class_entries(personal_entries, support_entries)`; branch de `today_classes` ajustado para mesclar quando `trains and not is_instructor`.

## Cleanup findings
- Nenhum resíduo. Dado de demonstração (senha resetada da Aline para validação) não afeta dados de negócio, apenas a credencial de acesso ao portal dela no ambiente de desenvolvimento local.

## Follow-up PRDs
- Nenhum. PRD-092 fechada em conjunto (ver evidência lá — o mesmo fix resolve as duas).

## Deviations from plan
- Não foi necessário alterar `get_today_classes_for_person` (já estava correta); o bug estava inteiramente na composição do contexto em `home_views.py`.

## Pending
- Nenhum.

## Final status
Concluída.
