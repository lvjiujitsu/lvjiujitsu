# PRD-009: Check-in com aprovação do professor + paridade de gestão de cronograma

## Resumo do que será implementado
Introduzir fluxo de aprovação no check-in: o aluno faz o check-in pelo painel e o registro fica em estado "Aguardando aprovação"; o professor da turma vê os check-ins pendentes no seu painel e confirma ou já visualiza como "Confirmado". Histórico de presença confirmada do aluno e do professor passa a considerar apenas check-ins aprovados.

**Expansão (2026-05-06):** dar paridade ao professor com o admin no cronograma — ele passa a cancelar/reativar sessões das turmas pelas quais é responsável, criar e remover aulões em qualquer dia/horário (sempre vinculando ele mesmo como teacher) e o admin passa a obrigatoriamente vincular um professor responsável ao criar aulão.

## Tipo de demanda
Nova feature com alteração de schema (check-in) + nova feature sem schema (gestão de cronograma do instrutor).

## Problema atual
- O painel do professor lista presentes mas não tem ação de aprovação.
- O check-in do aluno é gravado já como confirmado, sem mediação do professor.
- Não há distinção visual entre "aguardando aprovação" e "confirmado" no painel do aluno.
- O histórico de presença do aluno mistura check-ins de qualquer estado, sem garantia de aprovação real.

## Objetivo
- Aluno faz check-in → registro fica como `pending` (Aguardando aprovação).
- Professor da turma/aulão vê os check-ins do dia com botão **Aprovar** e os que já aprovou aparecem como confirmados.
- Painel do aluno exibe pill "Aguardando aprovação" enquanto não aprovado e "Confirmado" depois.
- Histórico de presença do aluno e do professor mostra apenas check-ins `approved`.

## Context Ledger
### Arquivos lidos integralmente
- `AGENTS.md`
- `CLAUDE.md`
- `docs/prd/PRD-008-ajustar-paineis-professor-aluno-checkin-historico.md`
- `system/models/calendar.py`
- `system/models/class_group.py`
- `system/models/__init__.py`
- `system/services/class_calendar.py`
- `system/views/calendar_views.py`
- `system/views/home_views.py`
- `system/views/portal_mixins.py`
- `system/views/__init__.py`
- `system/urls.py`
- `system/constants.py`
- `system/tests/test_calendar.py`
- `system/tests/test_views.py` (trechos relevantes do dashboard de professor/aluno)
- `templates/home/instructor/dashboard.html`
- `templates/home/student/dashboard.html`
- `static/system/css/portal/portal.css` (seção `today-class-*` e `attendance-history-*`)
- `system/admin.py` (registro de `ClassCheckin`)
- `clear_migrations.py`

### Arquivos adjacentes consultados
- `system/migrations/0001_initial.py`
- `feedback_migrations_policy.md` (memória)

### Internet / documentação oficial
- Não aplicável: comportamento interno ao domínio.

### MCPs / ferramentas verificadas
- `read`, `glob`, `grep` — ok
- `bash` — pendente para `manage.py test` e ciclo destrutivo
- browser/Playwright — pendente para validação visual

### Limitações encontradas
- Mudança requer alteração de schema → ciclo destrutivo autorizado pelo usuário em 2026-05-05.

## Prompt de execução
### Persona
Agente Django seguindo SDD + TDD + MVT, com camada de serviços para negócio.

### Ação
Adicionar status (pending/approved) em `ClassCheckin` e `SpecialClassCheckin`, criar serviços e views de aprovação, atualizar templates e testes.

### Contexto
O portal já tem check-in de aulas regulares e aulões. O dashboard do professor já lista presentes, mas sem ação. O fluxo precisa intermediar a confirmação para garantir que o histórico só contemple aulas realmente assistidas e validadas pelo responsável da turma.

### Restrições
- sem hardcode
- sem mascaramento de erro
- ciclo destrutivo autorizado para esta mudança
- leitura integral obrigatória
- validação obrigatória

### Critérios de aceite
- [ ] `ClassCheckin` e `SpecialClassCheckin` possuem `status`, `approved_at`, `approved_by` (verificável por teste de model).
- [ ] `perform_checkin` cria checkin como `pending` (verificável por teste).
- [ ] `approve_class_checkin(instructor, checkin_id)` exige que o instrutor pertença à turma; se sim, marca `approved` e preenche `approved_at`/`approved_by` (verificável por teste de service).
- [ ] `approve_special_checkin(instructor, checkin_id)` valida que o instrutor é o teacher do aulão (verificável por teste).
- [ ] Painel do professor exibe lista de check-ins do dia com badge de status e botão Aprovar para pendentes (verificável por teste de view + visual).
- [ ] Painel do aluno exibe pill "Aguardando aprovação" para pendentes e "Confirmado" para aprovados nas aulas do dia (verificável por teste de view + visual).
- [ ] Histórico de presença do aluno só inclui registros `approved` (verificável por teste).
- [ ] `manage.py test --verbosity 2` sem falhas.
- [ ] `manage.py check` sem erros.

### Evidências esperadas
- testes passando
- ciclo destrutivo executado com sucesso
- captura visual dos painéis após validação em navegador

### Formato de saída
Código + testes + evidências.

## Escopo

### Aprovação de check-in
- `system/models/calendar.py` — adicionar `CheckinStatus`, campos `status`, `approved_at`, `approved_by` em `ClassCheckin` e `SpecialClassCheckin`.
- `system/services/class_calendar.py` — `perform_checkin` cria pending; novos `approve_class_checkin` e `approve_special_checkin`; `get_today_classes_for_instructor` expõe IDs/status de check-ins; `get_student_checkin_history` filtra approved; `get_today_classes_for_person` expõe status do próprio check-in.
- `system/views/calendar_views.py` — novas views `InstructorApproveCheckinView` e `InstructorApproveSpecialCheckinView`.
- `system/urls.py` — rotas `instructor-approve-checkin` e `instructor-approve-special-checkin`.
- `templates/home/instructor/dashboard.html` — listar presentes com badge e botão Aprovar.
- `templates/home/student/dashboard.html` — pill "Aguardando aprovação"/"Confirmado" no card e filtro do histórico.
- `static/system/css/portal/portal.css` — pills, lista de check-ins do professor, botão Aprovar; bumpar `?v=`.
- `system/admin.py` — incluir novos campos no `ClassCheckinAdmin`.

### Gestão de cronograma do instrutor (expansão)
- `system/services/class_calendar.py` — `assert_instructor_owns_schedule(person, schedule_id)`, `assert_instructor_owns_special(person, special_id)`.
- `system/views/calendar_views.py` — `InstructorCalendarView`, `InstructorToggleSessionView`, `InstructorSpecialClassCreateView` (força `teacher=person`), `InstructorSpecialClassDeleteView`.
- `system/views/calendar_views.py` — `AdminCalendarView` passa `instructors` no contexto; `_get_instructor_choices` helper.
- `system/urls.py` — rotas `instructor-calendar`, `instructor-calendar-month`, `instructor-toggle-session`, `instructor-special-class-create`, `instructor-special-class-delete`.
- `templates/calendar/instructor_calendar.html` — clone funcional do admin com endpoints próprios e gating de botões por propriedade do schedule/aulão.
- `templates/calendar/admin_calendar.html` — campo obrigatório `teacher` no modal e payload.
- `templates/home/instructor/dashboard.html` — link "Gerir cronograma" passa a apontar para `instructor-calendar`.

### Testes
- `system/tests/test_calendar.py` — cobrir novo status/services de aprovação + helpers de ownership.
- `system/tests/test_views.py` — atualizar testes existentes e adicionar cenários de aprovação, cronograma do instrutor (loads, toggle, special create/delete) e admin (teacher obrigatório no aulão).

## Fora do escopo
- Notificação ao aluno após aprovação.
- Histórico de aprovações com auditoria detalhada além de `approved_at`/`approved_by`.
- Workflow de "rejeição" (apenas pending → approved nesta entrega).
- Fluxo administrativo (apenas portal de instrutor).

## Arquivos impactados
Vide seção "Escopo".

## Riscos e edge cases
- Check-ins criados antes da migração: como ciclo destrutivo recria o banco, não há legado.
- Instrutor que não é `main_teacher` mas é `ClassInstructorAssignment`: deve poder aprovar — usar `_get_instructor_class_group_ids`.
- Aulão sem teacher (FK nullable): aprovação só liberada para o teacher do aulão; sem teacher, ninguém pode aprovar — comportamento explícito.
- Aprovar duas vezes: idempotente, não muda nada se já estiver `approved`.

## Regras e restrições
- SDD antes de código
- TDD ao introduzir comportamento novo
- sem hardcode
- sem mascaramento de erro
- ciclo destrutivo autorizado
- leitura integral obrigatória
- validação obrigatória

## Plano
- [x] 1. Contexto e leitura integral
- [x] 2. Modelo (`status`, `approved_at`, `approved_by`)
- [x] 3. Services (perform_checkin pending + approve_*)
- [x] 4. Views/URLs de aprovação
- [x] 5. Templates (professor + aluno)
- [x] 6. CSS + bump `?v=`
- [x] 7. Testes de aprovação (atualizar + novos)
- [x] 8. Helpers de ownership do instrutor (services)
- [x] 9. Views/URLs do cronograma do instrutor
- [x] 10. Template `instructor_calendar.html` + link no dashboard
- [x] 11. Modal admin com `teacher` obrigatório
- [x] 12. Testes da expansão (cronograma do instrutor + admin teacher)
- [x] 13. `manage.py check` (0 issues)
- [ ] 14. Ciclo destrutivo + seeds (pendente — autorizado pelo usuário, bloqueado pelo hook local)
- [ ] 15. `manage.py test --verbosity 2`
- [ ] 16. Validação visual em navegador
- [ ] 17. Limpeza final + atualização do PRD

## Validação visual
### Desktop
- Painel do professor: card de aula do dia mostra lista de presentes com pill `Pendente` + botão Aprovar; após aprovar, vira `Confirmado`.
- Painel do aluno: card de aula do dia mostra pill `Aguardando aprovação` após check-in; vira `Confirmado` após aprovação.

### Mobile
- Cards e pills devem se manter legíveis e com toque adequado.

### Console do navegador
- Sem erros JS críticos.

### Terminal
- Sem stack trace ao abrir os dashboards e ao aprovar.

## Validação ORM
### Banco
- Schema regenerado pelo ciclo destrutivo após edição dos modelos.

### Shell checks
- Verificar `ClassCheckin.objects.values_list("status", flat=True)` pós-migração.

### Integridade do fluxo
- Check-in cria como pending; service muda para approved; histórico só lista approved.

## Validação de qualidade
### Sem hardcode
Status e textos vêm de `TextChoices`/templates.

### Sem estruturas condicionais quebradiças
Guard clauses; serviços validam autorização e idempotência.

### Sem `except: pass`
Erros de não autorização são `PermissionError` explícitos.

### Sem mascaramento de erro
Views retornam JSON com código de status apropriado e mensagem clara.

### Sem comentários e docstrings desnecessários
Manter código autoexplicativo.

## Evidências
(preencher após execução)

## Implementado
(preencher ao final)

## Desvios do plano
(preencher ao final)

## Pendências
(preencher ao final)
