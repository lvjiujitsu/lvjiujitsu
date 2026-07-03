# PRD-116: Home do aluno com permissoes, cronograma modal e fidelidade

## Summary
Corrigir a home do aluno para que aluno comum nao tenha acao de criar aulão, o cronograma abra em modal na propria home, presencas aprovadas possam ser exibidas como exemplo local e planos recorrentes Stripe fiquem bloqueados para troca/cancelamento ate a data de liberacao da carencia.

## Demand type
Correcao de UI/UX + regra Django de permissao/cobranca + carga local de dados de demonstracao.

## Current problem
- A home renderiza `instructor_toolbar="full"` quando `today_classes` existe, mesmo para aluno comum, expondo "Criar aulão".
- A acao "Cronograma" e um link para outra pagina, mas o comportamento esperado e popup/modal.
- O aluno recem-cadastrado nao possui historico de presencas aprovadas para demonstracao.
- A trava de troca de plano depende apenas de `Membership.stripe_subscription_id`; no fluxo real de Stripe, a mensalidade ativa pode estar em plano recorrente sem esse campo persistido.
- A tela exibe "Trocar plano" apesar do aceite da carencia/fidelidade do plano recorrente.

## Goal
- Normalizar a toolbar de turmas de hoje por permissao real.
- Manter aluno comum sem "Criar aulão" no DOM da home.
- Abrir cronograma em modal com conteudo embutido, sem trocar a URL da home.
- Centralizar a regra de bloqueio de plano recorrente para UI e endpoint POST.
- Mostrar mensagem com a data de liberacao para troca/cancelamento.
- Inserir presencas aprovadas ficticias no banco local para o aluno de validacao.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/PRD-STANDARD.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `templates/home/dashboard.html`
- `templates/home/partials/today_classes_section.html`
- `templates/calendar/calendar.html`
- `static/system/js/home/dashboard.js`
- `static/system/css/home/dashboard.css`
- `system/views/home_views.py`
- `system/views/calendar_views.py`
- `system/views/plan_change_views.py`
- `system/services/plan_change.py`
- `system/services/membership.py`
- `system/models/membership.py`
- `system/models/plan.py`
- `system/tests/test_home_dashboard.py`
- `system/tests/test_plan_change_views.py`

### Adjacent files consulted
- `system/tests/test_membership_actions_ui.py`
- `system/tests/test_plan_commercial.py`
- `docs/prd/README.md`

### Internet / official documentation
- Django 5.2 authentication and view protection via Context7: `https://docs.djangoproject.com/en/5.2/topics/auth/default/`
- Conclusao: permissoes devem ser aplicadas no backend/view e a UI nao pode ser a unica barreira.

### Limitations found
- Nao existe campo dedicado de termino de fidelidade/carencia no modelo `Membership` ou `SubscriptionPlan`; nesta entrega a data operacional exibida usa `current_period_end`.
- A home do aluno nao tem fluxo de cancelamento proprio hoje; a mensagem cita troca/cancelamento porque e a regra de negocio solicitada, mas a acao visivel corrigida e a troca de plano.
- A criacao de aulão ja possui protecao no endpoint operacional; a falha observada e de toolbar/template para aluno.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-ui-delivery`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
Autorizado pela solicitacao atual: corrigir, inserir dados ficticios locais e validar a tela.

## Design proposal
- Objetivo: manter a home do aluno como painel pessoal, sem acoes operacionais de professor.
- Hierarquia:
  - Secao "Turmas de hoje": titulo a esquerda; acoes compactas a direita.
  - Aluno comum: Historico quando houver presencas + Cronograma.
  - Operacional/professor: Historico + Criar aulão + Cronograma.
  - Modal de cronograma: cabecalho "Cronograma", botao fechar e iframe interno com calendario em modo embutido.
  - Mensalidade expandida: dados atuais, vigencia e aviso de bloqueio quando o plano recorrente esta em carencia.
- Estados:
  - Cronograma fechado/aberto/carregado.
  - Plano desbloqueado mostra "Trocar plano".
  - Plano bloqueado esconde "Trocar plano" e mostra aviso com data.
  - Desktop e mobile mantem acoes sem overflow.

## Acceptance criteria
- [x] Aluno comum autenticado em `/home/` nao ve "Criar aulão".
- [x] Professor/operacional preserva a acao "Criar aulão" quando autorizado.
- [x] A acao "Cronograma" em `/home/` e um botao/modal e nao um link de navegacao direta.
- [x] Clicar em "Cronograma" abre popup sem alterar a URL da home.
- [x] O calendario embutido nao renderiza topbar duplicada.
- [x] Plano recorrente Stripe com `gateway_code="stripe_card"` fica bloqueado mesmo sem `stripe_subscription_id`.
- [x] Endpoint de troca de plano rejeita plano recorrente bloqueado com mensagem pt-BR.
- [x] Home mostra a data de liberacao para troca/cancelamento quando bloqueado.
- [x] Banco local contem presencas aprovadas ficticias do aluno de validacao.
- [x] Validacao no navegador interno cobre desktop/mobile, console sem erros e o fluxo de modal.

## Expected evidence
- Testes focados de home e troca de plano.
- `python manage.py check`.
- Validacao visual no navegador interno em desktop e mobile.
- ORM local confirmando presencas aprovadas ficticias.

## Scope
- `templates/home/dashboard.html`
- `templates/home/partials/today_classes_section.html`
- `templates/calendar/calendar.html`
- `static/system/js/home/dashboard.js`
- `static/system/css/home/dashboard.css`
- `system/views/home_views.py`
- `system/views/calendar_views.py`
- `system/views/plan_change_views.py`
- `system/services/plan_change.py`
- `system/tests/test_home_dashboard.py`
- `system/tests/test_plan_change_views.py`
- Carga local do banco para aluno de teste.

## Out of scope
- Criar campo novo de contrato/fidelidade no schema.
- Redesenhar todo o financeiro ou checkout Stripe.
- Criar fluxo de cancelamento self-service.
- Mudar o cadastro novamente.

## Executed evidence
- Red esperado: `python manage.py test system.tests.test_home_dashboard.HomeDashboardContractTestCase.test_student_with_today_class_does_not_receive_instructor_toolbar system.tests.test_plan_change_views.PlanChangeSelectViewTestCase.test_stripe_gateway_membership_is_rejected_without_subscription_id system.tests.test_plan_change_views.HomeDashboardPlanChangeContextTestCase.test_home_locks_stripe_gateway_plan_without_subscription_id`: 3 testes, falhou antes do codigo por toolbar ausente e Stripe gateway sem bloqueio.
- Red esperado adicional: `python manage.py test system.tests.test_calendar.CalendarServiceTestCase.test_calendar_embedded_mode_is_same_origin_and_hides_topbar`: falhou com `X-Frame-Options: DENY`.
- `node --check static/system/js/home/dashboard.js`: OK.
- `python manage.py check`: OK, sem issues.
- `python manage.py test system.tests.test_home_dashboard system.tests.test_plan_change_views system.tests.test_calendar system.tests.test_lv_foundation_calendar`: 111 testes, OK.
- ORM local: criadas/confirmadas 8 presencas aprovadas para `Aluno Stripe Codex`, `schedule_ids=[3, 4]`.
- Navegador interno desktop em `/home/`: `dashboard.css?v=18`, `dashboard.js?v=12`, `createButtons=0`, texto "Criar aulão" ausente, `calendarButtons=1`, links diretos para `/calendar/` ausentes.
- Navegador interno desktop: aviso exibido `Troca e cancelamento liberados em 02/08/2026, após a carência da assinatura recorrente.`, botao `Trocar plano` ausente.
- Navegador interno desktop: modal de cronograma abriu sem alterar `http://127.0.0.1:8000/home/`; iframe com `calendar-board=1`, `topbar=0`, titulo `Cronograma`, mes `Julho 2026`.
- Navegador interno desktop: historico de presencas abriu com 8 itens aprovados, 6 visiveis na primeira pagina.
- Navegador interno mobile 390x844: sem overflow horizontal, `createButtons=0`, `calendarButtons=1`, `historyButtons=1`, botao `Trocar plano` ausente e aviso de carencia visivel.
- Navegador interno mobile 390x844: modal de cronograma abriu com largura 390, sem overflow, titulo `Cronograma` e `topbar=0`.
- Console do navegador interno: sem erros.

## Cleanup / follow-up
- Removido o comportamento de link direto do cronograma na home.
- Regra de bloqueio foi centralizada em `system.services.plan_change`.
- Debito fora do escopo registrado em `PRD-117-fidelidade-contratual-planos-recorrentes.md`: campo contratual dedicado para data/fim de carencia ou fidelidade.
