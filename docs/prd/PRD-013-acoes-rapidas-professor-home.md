# PRD-013: Ações rápidas do professor na home

## Resumo do que será implementado
Adicionar ações rápidas no card "Aulas do dia" da home do professor para:
- cancelar ou reativar uma aula regular vinculada ao professor autenticado
- criar um aulão para o dia atual sem abrir a tela de cronograma

## Tipo de demanda
Nova feature de UI/fluxo.

## Problema atual
O professor precisa abrir "Gerir cronograma" para cancelar uma aula do dia ou criar um aulão. Isso adiciona navegação desnecessária em uma operação operacional e urgente.

## Objetivo
Permitir que o professor faça as ações mais frequentes do dia diretamente na home, preservando as permissões e os serviços já existentes do cronograma.

## Context Ledger
### Arquivos lidos integralmente
- `AGENTS.md`
- `CLAUDE.md`
- `lvjiujitsu/settings.py`
- `templates/home/instructor/dashboard.html`
- `templates/calendar/instructor_calendar.html`
- `templates/calendar/admin_calendar.html`
- `templates/base.html`
- `system/views/home_views.py`
- `system/views/calendar_views.py`
- `system/views/__init__.py`
- `system/urls.py`
- `system/services/class_calendar.py`
- `system/forms/class_forms.py`
- `system/models/calendar.py`
- `system/tests/test_calendar.py`
- `system/tests/test_views.py`
- `static/system/css/portal/portal.css`

### Arquivos adjacentes consultados
- `docs/prd/`
- `system/models/category.py`
- `system/models/class_catalog.py` via imports existentes
- `system/services/__init__.py` via testes existentes

### Internet / documentação oficial
- Não aplicável. A implementação reaproveita endpoints Django e JavaScript nativo já existentes no projeto.

### MCPs / ferramentas verificadas
- PowerShell — ok — leitura de arquivos e comandos locais.
- `.venv` — ok — Python 3.12.10.
- Django — ok — 4.1.13.
- Browser Use — limitado — `node_repl` retornou "No active Codex browser pane available".
- Playwright — ok — validação funcional desktop/mobile executada em `http://127.0.0.1:8000/home/instructor/`.

### Limitações encontradas
- O worktree já possui muitas alterações não relacionadas; esta entrega deve preservar esse estado.
- `rg` não foi usado porque falhou por permissão em execução anterior neste ambiente; inspeção feita com PowerShell.
- A suíte completa não ficou 100% verde por 3 erros fora deste fluxo: seed de regras de repasse e testes de payroll bloqueados por validação de data de nascimento.

## Prompt de execução
### Persona
Agente de desenvolvimento especialista em Django 4.1 seguindo SDD + TDD + MVT server-rendered.

### Ação
Implementar ações rápidas no card "Aulas do dia" da home do professor.

### Contexto
O projeto já possui:
- `InstructorToggleSessionView` para cancelar/reativar sessão de aula própria
- `InstructorSpecialClassCreateView` para criar aulão vinculado ao professor autenticado
- `get_today_classes_for_instructor` como fonte da listagem da home

### Restrições
- sem nova migração
- sem hardcode de duração/título; usar `settings`
- sem mascaramento de erro
- não criar regra de negócio em template
- preservar permissões server-side dos endpoints existentes
- validar em navegador

### Critérios de aceite
- [x] A home do professor deve exibir botão "Criar aulão" no card "Aulas do dia".
- [x] Ao clicar em "Criar aulão", deve abrir formulário compacto com data de hoje, título, horário, duração e observações.
- [x] Ao enviar o formulário, o aulão deve ser criado para o professor autenticado.
- [x] A aula regular vinculada ao professor deve exibir botão "Cancelar" quando ativa.
- [x] A aula regular cancelada deve exibir botão "Reativar".
- [x] Aula cancelada por feriado não deve expor "Reativar" como se fosse cancelamento manual.
- [x] As ações devem usar CSRF e endpoints autenticados existentes.
- [x] O JS deve ficar em arquivo estático separado e versionado no template.
- [x] `portal.css` versionado deve ser atualizado se houver alteração visual.

### Evidências esperadas
- teste automatizado de renderização da home com ações rápidas
- teste automatizado dos dados necessários no service da home
- `manage.py test --verbosity 2`
- `manage.py check`
- `manage.py collectstatic --noinput`
- `manage.py showmigrations`
- validação visual/funcional em navegador desktop e mobile
- console do navegador sem erro JS crítico

### Formato de saída
Código implementado + testes + evidências de validação.

## Escopo
- `system/services/class_calendar.py`
- `system/views/home_views.py`
- `templates/home/instructor/dashboard.html`
- `static/system/js/home/instructor-dashboard.js`
- `static/system/css/portal/portal.css`
- `templates/base.html`
- `system/tests/test_calendar.py`
- `docs/prd/PRD-013-acoes-rapidas-professor-home.md`

## Fora do escopo
- Alterar regras de calendário fora do dia atual.
- Criar edição/remover aulão pela home.
- Alterar CRUD de cronograma.
- Criar migrações.

## Arquivos impactados
- `system/services/class_calendar.py`
- `system/views/home_views.py`
- `templates/home/instructor/dashboard.html`
- `static/system/js/home/instructor-dashboard.js`
- `static/system/css/portal/portal.css`
- `templates/base.html`
- `system/tests/test_calendar.py`
- `docs/prd/PRD-013-acoes-rapidas-professor-home.md`

## Riscos e edge cases
- Aula regular sem `ClassSession` ainda precisa ser cancelável; o endpoint cria a sessão ao cancelar.
- Aula cancelada por feriado não deve ser reativada pela home.
- Professor auxiliar vinculado via `ClassInstructorAssignment` deve continuar autorizado.
- Erros de permissão devem continuar bloqueados no backend.
- Se criar aulão com horário inválido, o formulário deve mostrar erro sem mascarar.

## Regras e restrições
- SDD antes de código
- TDD para implementação
- sem hardcode
- sem mascaramento de erro
- sem migrações
- leitura integral obrigatória
- validação obrigatória

## Plano
- [x] 1. Contexto e leitura integral
- [x] 2. Contratos e modelagem
- [x] 3. Testes (Red)
- [x] 4. Implementação (Green)
- [x] 5. Refatoração (Refactor)
- [x] 6. Validação completa
- [x] 7. Limpeza final
- [x] 8. Atualização documental

## Validação visual
### Desktop
Playwright em viewport 1366x900:
- login com professor temporário
- home abriu em `/home/instructor/`
- botão "Criar aulão" visível
- formulário recolhível abriu
- aulão criado pela home
- botões "Cancelar" e "Reativar" visíveis conforme estado
- console sem erros críticos

### Mobile
Playwright em viewport 390x844:
- botão "Criar aulão" visível
- painel recolhível abriu
- `scrollWidth` menor que `innerWidth`, sem overflow horizontal
- console sem erros críticos

### Console do navegador
Sem entradas `error` ou `pageerror` nas validações Playwright.

### Terminal
Servidor local respondeu `200` em `http://127.0.0.1:8000/home/instructor/`.

## Validação ORM
### Banco
Sem alteração de schema. Nenhuma migração criada.

### Shell checks
Dados temporários de validação criados e removidos via ORM:
- `Person.cpf='920.000.800-01'`
- `ClassGroup.code='codex-home-actions-group'`
- `ClassCategory.code='codex-home-actions'`
- `SpecialClass` vinculada ao professor temporário

Cleanup confirmou `False False False False` para existência residual.

### Integridade do fluxo
Criação de aulão usa `InstructorSpecialClassCreateView`, que vincula `teacher` ao professor autenticado.
Cancelamento/reativação usa `InstructorToggleSessionView`, preservando `assert_instructor_owns_schedule`.

## Validação de qualidade
### Sem hardcode
Título e duração padrão do aulão vêm de `settings.SPECIAL_CLASS_DEFAULT_TITLE` e `settings.SPECIAL_CLASS_DEFAULT_DURATION_MINUTES`.

### Sem estruturas condicionais quebradiças
Template decide apenas exposição de ações com flags vindas do service (`is_special`, `is_holiday_cancelled`, `is_cancelled`).

### Sem `except: pass`
Não introduzido.

### Sem mascaramento de erro
JS exibe erro retornado pelo backend quando a resposta não é `ok`; endpoints continuam retornando status HTTP explícito.

### Sem comentários e docstrings desnecessários
Não foram adicionados comentários/docstrings no código da feature.

## Evidências
- `manage.py test system.tests.test_calendar.CheckinApprovalServiceTestCase.test_today_classes_for_instructor_exposes_quick_action_identifiers --verbosity 2` — passou.
- `manage.py test system.tests.test_calendar.InstructorHomeQuickActionsViewTestCase.test_instructor_dashboard_exposes_quick_schedule_actions --verbosity 2` — passou.
- `manage.py test system.tests.test_calendar --verbosity 2` — 46 testes, passou.
- `manage.py check` — sem issues.
- `node --check static/system/js/home/instructor-dashboard.js` — passou.
- `manage.py showmigrations` — migrations aplicadas até `system.0001_initial`.
- `git diff --check` — sem erro de whitespace; apenas avisos de LF/CRLF do Windows.
- `manage.py collectstatic --noinput` — 3 arquivos copiados, 161 inalterados.
- `manage.py test --verbosity 2` — 298 testes executados, 295 ok, 3 erros fora do fluxo.

## Implementado
- `get_today_classes_for_instructor` passou a expor `schedule_id`, `session_date`, `is_holiday_cancelled` e `special_id`.
- Home do professor recebeu botão "Criar aulão" e formulário recolhível no card "Aulas do dia".
- Aulas regulares ativas exibem "Cancelar"; aulas canceladas manualmente exibem "Reativar".
- Aulas canceladas por feriado não exibem ação de reativação.
- JS inline da home foi substituído por `static/system/js/home/instructor-dashboard.js`.
- CSS do painel rápido e botões foi adicionado em `portal.css`, com versionamento atualizado em `base.html`.
- Teste de service e teste de renderização da home foram adicionados em `system/tests/test_calendar.py`.

## Desvios do plano
- O arquivo JS ficou em `static/system/js/home/instructor-dashboard.js`, seguindo a pasta existente de scripts de home, em vez de `static/system/js/portal/instructor-home.js`.
- A validação visual usou Playwright MCP porque Browser Use não encontrou um painel ativo no Codex.
- A suíte completa falhou por 3 erros de payroll/seed fora do fluxo alterado.

## Pendências
- Corrigir os 3 erros globais fora deste escopo se a meta for suíte completa 100% verde:
  - `test_seed_class_catalog_creates_default_payroll_rules`
  - `test_calculates_fixed_monthly_plus_student_percentage_rules`
  - `test_calculates_per_class_attendance_rule`
