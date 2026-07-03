# PRD-122: Desfazer check-in pendente do aluno

## Summary
Permitir que o aluno desfaça um check-in feito por engano enquanto a presença ainda estiver pendente de aprovação do professor.

## Demand type
Django MVT + UI da home do aluno.

## Current problem
Na home, após o aluno clicar em `Check-in`, o card troca para `Aguardando aprovação` e não oferece ação para desfazer. Isso cria uma presença pendente incorreta quando o clique foi acidental.

## Goal
Adicionar cancelamento de check-in próprio pendente para aula regular e aulão, mantendo bloqueio para presença aprovada.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/PRD-STANDARD.md`
- `docs/UI-SCREEN-CONTRACT.md`

### Adjacent files consulted
- `system/services/class_calendar.py`
- `system/views/calendar_views.py`
- `system/urls.py`
- `system/views/__init__.py`
- `system/tests/test_calendar.py`
- `templates/home/dashboard.html`
- `templates/home/partials/today_classes_section.html`
- `static/system/js/home/dashboard.js`
- `static/system/css/home/dashboard.css`
- `system/services/trial_access.py`
- `system/models/trial_access.py`

### Internet / official documentation
- Django 5.2 official documentation via Context7: class-based views, `JsonResponse`, test client JSON POST and session-based tests.

### Context7 / MCPs / tools verified
- Context7 Django docs resolved as `/websites/djangoproject_en_5_2`.
- Browser interno disponível para validação em `http://127.0.0.1:8000/home/`.

### Limitations found
- Não existe vínculo persistido entre um check-in e a concessão de aula experimental consumida; restaurar trial ao desfazer exige modelagem adicional e fica fora deste patch.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`
- `browser:control-in-app-browser`

## Understanding approved
A solicitação atual do usuário autoriza a correção: “corrija por que a tela nao e possivel desfazer o checking as vezes o aluno pode ter clicado sem querer”.

## Execution prompt
### Persona
Agente Django/UI do LV JIU JITSU.

### Action
Implementar cancelamento de check-in pendente pelo próprio aluno na home.

### Context
O check-in do aluno cria `ClassCheckin` ou `SpecialClassCheckin` com status `PENDING`. Professores aprovam depois. O aluno precisa desfazer apenas enquanto estiver pendente.

### Constraints
- Backend decide permissão e estado.
- Não permitir cancelar presença aprovada.
- Não editar `staticfiles/`.
- Não usar `innerHTML` com dado de usuário.
- UI em pt-BR.

### Acceptance criteria
- [x] Aula regular pendente exibe ação de desfazer ao lado do status.
- [x] Aulão pendente exibe a mesma ação.
- [x] Cancelar remove apenas o check-in pendente do aluno logado.
- [x] Presença aprovada retorna erro e permanece intacta.
- [x] Ausência de check-in retorna resposta limpa sem erro 500.
- [x] UI volta a permitir `Check-in` após cancelamento bem-sucedido.
- [x] Teste focado cobre serviço e endpoint.
- [ ] Navegador interno valida o fluxo real.

### Expected evidence
- `python manage.py test system.tests.test_calendar...`
- `python manage.py check`
- Navegador interno: antes/depois do botão `Desfazer`.

### Output format
Fechamento curto com implementado, evidências, limitações e status.

## Scope
- Serviço de cancelamento pendente para aula regular e aulão.
- Views JSON autenticadas para o aluno.
- URLs canônicas.
- Dados expostos pelo selector da home.
- Template, CSS e JS da home.
- Testes focados.

## Out of scope
- Cancelamento de presença já aprovada.
- Edição de histórico aprovado.
- Restauração de aula experimental consumida.
- Mudança no fluxo de aprovação do professor.

## Impacted files
- `docs/prd/README.md`
- `docs/prd/PRD-122-desfazer-checkin-pendente-aluno.md`
- `system/services/class_calendar.py`
- `system/views/calendar_views.py`
- `system/views/__init__.py`
- `system/urls.py`
- `system/tests/test_calendar.py`
- `templates/home/dashboard.html`
- `templates/home/partials/today_classes_section.html`
- `static/system/js/home/dashboard.js`
- `static/system/css/home/dashboard.css`

## Risks and edge cases
- Check-in aprovado não pode ser removido pelo aluno.
- Endpoint não deve aceitar cancelar check-in de outra pessoa.
- Se a sessão ainda não existir, a resposta deve ser limpa.
- Duplo clique em desfazer deve ser idempotente.

## Rules and constraints
- `PENDING` é cancelável.
- `APPROVED` é imutável para o aluno.
- Aula cancelada não altera a regra de cancelamento de presença pendente.

## Plan
- [x] Criar testes focados.
- [x] Implementar serviço transacional.
- [x] Implementar views e URLs.
- [x] Expor flags no selector.
- [x] Ajustar UI e JS.
- [x] Validar testes e renderização no navegador interno.

## Test plan
### Tests to author
- Serviço cancela `ClassCheckin` pendente.
- Serviço bloqueia `ClassCheckin` aprovado.
- Serviço cancela `SpecialClassCheckin` pendente.
- View de aula regular retorna sucesso.
- View de presença aprovada retorna erro 400.
- Home renderiza `js-cancel-checkin` para pendente.

### Execution authorization
Autorizada pela solicitação operacional atual.

### Execution evidence
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_calendar` -> OK, 100 testes.
- `.\.venv\Scripts\python.exe manage.py check` -> OK, sem issues.
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_home_dependents_section system.tests.test_calendar` -> OK, 111 testes.

## Visual validation
- Navegador interno em `http://127.0.0.1:8000/home/`: a linha confirmada não mostrou `Desfazer`; duas linhas pendentes mostraram `Aguardando aprovação Desfazer`.
- Clique real de cancelamento no navegador interno não foi concluído nesta rodada porque a interação visual foi interrompida/lenta após validação do modal de conta; backend e renderização estão cobertos por testes.

## ORM validation
- Testes de serviço confirmam remoção de `ClassCheckin` e `SpecialClassCheckin` pendentes e bloqueio de presença aprovada.

## Quality validation
- `manage.py check`: OK.
- `system.tests.test_calendar`: OK.
- Suíte proporcional `test_home_dependents_section` + `test_calendar`: OK.

## Evidence
- Serviços `cancel_student_checkin` e `cancel_student_special_class_checkin` removem apenas presença pendente do aluno logado.
- Views JSON retornam sucesso para pendente e erro 400 para aprovada.
- Template renderiza `js-cancel-checkin` somente quando o check-in está pendente e cancelável.

## Implemented
- Botão `Desfazer` para check-ins pendentes em aulas regulares e aulões.
- Endpoints `aulas/checkin/cancelar/` e `aulas/aulao/checkin/cancelar/`.
- Atualização JS da linha para retornar ao estado de `Check-in` após sucesso.
- Testes de serviço, view e renderização.

## Cleanup findings
- Restauração de aula experimental consumida continua fora do escopo e permanece como follow-up.

## Follow-up PRDs
- Restauração rastreável de aula experimental consumida ao desfazer check-in pendente.

## Deviations from plan
Nenhuma até agora.

## Pending
- Clique real de cancelamento no navegador interno ainda deve ser repetido em uma rodada visual dedicada.

## Final status
Concluída com limitação visual.
