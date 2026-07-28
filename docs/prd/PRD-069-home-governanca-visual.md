# PRD-069: Home do LV com governanca visual madura

## Summary
Recriar somente a Home autenticada do LV JIU JITSU, usando governanca visual madura e preservando apenas a regra LV necessaria para autenticacao, permissao e fluxo de Pessoas.

## Demand type
UI + Django MVT, sem schema novo e sem reabrir modulos fora do escopo.

## Current problem
A PRD-068 deixou o projeto apenas com login e assets vinculados. O codigo Python do LV ainda possui `HomeView`, rotas e testes historicos da home, mas `templates/home/dashboard.html` e os assets `static/system/css/home/dashboard.css` e `static/system/js/home/dashboard.js` nao existem mais.

## Goal
Implementar uma Home unica em `/home/`, limpa e seca, com estilo e governanca maduros, e conteudo e regras de permissao do LV.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `docs/PRD-STANDARD.md`
- `docs/OPERACAO-BANCO-SEEDS.md`
- `system/management/commands/create_admin_superuser.py`
- `system/urls.py`
- `system/views/home_views.py`
- `system/views/portal_mixins.py`
- `system/views/auth_views.py`
- `system/middleware.py`
- `system/services/portal_auth.py`
- `system/forms/auth_forms.py`
- `system/models/person.py`
- `system/constants.py`
- `system/runtime_config.py`
- `system/context_processors.py`
- `lvjiujitsu/settings.py`
- `system/tests/test_home_dashboard.py`
- `system/tests/test_admin_hubs_contract.py`

### Adjacent files consulted
- `system/tests/test_commands.py`

### Internet / official documentation
- Django 5.2 official docs via Context7: custom management commands, class-based views, templates and login mixins.

### Context7 / MCPs / tools verified
- Context7 `/websites/djangoproject_en_5_2`
- Browser interno ja validado para o login LV em PRD-068.

### Limitations found
- Resolvido pela PRD-070: `system/migrations/0001_initial.py` foi gerada, aplicada no SQLite local e validada.
- Banco local recebeu somente as seeds necessarias para o fluxo objetivo: admin, tipos de pessoa, faixas e 5 pessoas de amostra.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-ui-delivery`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
Aprovado pelo usuario na mensagem "Implemente".

## Execution prompt
### Persona
Engenheiro Django MVT senior, pragmatico, com governanca visual madura.

### Action
Recriar somente a Home LV com o primeiro modulo operacional: Pessoas.

### Context
O LV deve seguir o estilo estrutural de referencia, mas nao portar dominio externo. O conteudo da home deve refletir academia: pessoas, acesso tecnico/admin, alunos recentes e estado vazio.

### Constraints
- Nao executar seeds amplas ou importacoes legadas fora do fluxo objetivo.
- Nao reintroduzir Pessoas completo, CRUD modal, base global ampla ou outros modulos.
- Nao criar KPIs agregados nao solicitados.
- Nao adicionar links mortos, `href="#"` ou atalhos desabilitados.
- Nao editar `staticfiles/`.

### Acceptance criteria
- `/home/` renderiza para admin tecnico autenticado.
- Home carrega tema claro/escuro com `lv-theme`.
- Home usa shell proprio minimo, com topbar.
- Acesso rapido mostra somente links permitidos e existentes nesta etapa: `Pessoas` e `Django Admin`.
- Pessoas recentes aparecem quando houver dados.
- Estado vazio aparece quando nao houver pessoas.
- Mobile nao tem overflow horizontal.
- Console sem erro critico.

### Expected evidence
- `manage.py check`
- `node --check static/system/js/home/dashboard.js`
- Browser interno para rota real disponivel.
- Browser interno autenticado em `http://localhost:8000/home/`.

### Output format
Fechamento em pt-BR com implementado, evidencias, nao validado, pendencias e status.

## Scope
- `templates/home/dashboard.html`
- `templates/home/partials/_dashboard_chevron.html`
- `static/system/css/home/dashboard.css`
- `static/system/js/home/dashboard.js`
- Ajuste minimo em `HomeView`, somente se necessario para contexto da home.
- Teste focado de contrato da home, se precisar ajustar ao comportamento minimo.

## Out of scope
- Importar massa legada de pessoas.
- Implementar Pessoas, turmas, financeiro, graduacao, materiais, planos ou CRUD modal.
- Recriar `templates/lv/base.html` amplo.
- Importar dominio externo.

## Impacted files
- A criar: `templates/home/dashboard.html`
- A criar: `templates/home/partials/_dashboard_chevron.html`
- A criar: `static/system/css/home/dashboard.css`
- A criar: `static/system/js/home/dashboard.js`
- A avaliar: `system/views/home_views.py`
- A avaliar: `system/tests/test_home_dashboard.py`

## Risks and edge cases
- Banco sem tabelas impede validacao real da home via browser.
- Criar shell amplo agora pode reintroduzir arquivos fora do modulo home.
- Links para modulos ainda nao recriados quebrariam a estrategia progressiva.
- Tecnico admin nao possui `portal_person`; a home precisa funcionar sem pessoa.

## Rules and constraints
- Interface em pt-BR.
- Codigo e identificadores em ingles.
- Tokens CSS por tema.
- Sem CSS/JS inline de comportamento.
- Sem regra de negocio em template ou JS.

## Visual hierarchy
- Topbar: logo LV, tema, sair.
- Header: data, saudacao, contexto operacional.
- Secao 1: Acesso rapido, com grupos definidos.
- Secao 2: Pessoas recentes, com lista densa e faixa/grau quando existir.
- Estado vazio: painel simples com acao para Pessoas.

## Wireframe
### Regiao: Topbar
- Logo LV a esquerda.
- Botao tema e sair a direita.

### Regiao: Header
- Eyebrow: dia e data.
- Titulo: `Ola, <nome>`.

### Regiao: Acesso rapido
- Grupo `Operacao`.
- Link `Pessoas`.
- Link `Django Admin` somente para tecnico.

### Regiao: Pessoas recentes
- Lista `summary-list`.
- Cada item: status/tipo a esquerda, nome e CPF/turma no centro, badge de faixa/grau se existir.
- Estado vazio com texto objetivo e link para Pessoas.

## State machine
### Tema
- `light` -> clique -> `dark`
- `dark` -> clique -> `light`
- Persistencia em `localStorage["lv-theme"]`

### Secoes recolhiveis
- `expanded` -> clique -> `collapsed`
- `collapsed` -> clique -> `expanded`
- Persistencia em `localStorage["lv-home-sections"]`

### Lista de pessoas
- `empty`: sem pessoas recentes.
- `populated`: renderiza ate seis pessoas recentes vindas de `HomeView`.

## Plan
1. Aprovar proposta visual.
2. Criar template, partial, CSS e JS da home.
3. Ajustar contexto minimo da view se necessario.
4. Escrever/ajustar contrato automatizado e executar teste proporcional.
5. Validar com checks.
6. Validar no browser autenticado.
7. Auditar limpeza.

## Test plan
### Tests available
- `system/tests/test_home_dashboard.py`
- `system/tests/test_admin_hubs_contract.py`

### Execution authorization
Autorizacao atualizada pela PRD-070: testes locais, migrations, seeds e admin autorizados para entrega operacional.

### Execution evidence
- `manage.py test system.tests.test_home_dashboard system.tests.test_admin_hubs_contract --verbosity 2`: 3 testes OK.
- `manage.py test --verbosity 2`: 226 testes executados; 9 erros legados por templates fora do escopo progressivo removidos anteriormente.

## Visual validation
Validacao visual autenticada concluida no navegador interno em `http://localhost:8000/home/`.

- Desktop claro: `test_screenshots/prd-070-home-validation/desktop-light.png`
- Desktop escuro: `test_screenshots/prd-070-home-validation/desktop-dark.png`
- Mobile claro: `test_screenshots/prd-070-home-validation/mobile-light.png`
- Mobile escuro: `test_screenshots/prd-070-home-validation/mobile-dark.png`
- Console: sem erros.
- Overflow horizontal: ausente em desktop e mobile.
- Conteudo validado: `Ola, admin`, quick links `Pessoas` e `Django Admin`, lista de pessoas recentes e badge `Branca · 4º`.

## ORM validation
Banco local validado com 1 usuario, 1 superusuario, 5 tipos de pessoa, 5 pessoas, 13 faixas e 1 turma. Nao houve importacao ampla.

## Quality validation
- `py_compile system/views/home_views.py`: sucesso.
- `manage.py check`: sucesso, 0 issues.
- `node --check static/system/js/home/dashboard.js`: sucesso.
- `get_template('home/dashboard.html')`: `TEMPLATE_OK`.
- Busca por residuos em Home/CSS/JS/View: sem `href="#"`, `quick-link--disabled`, `innerHTML`, `Planos`, `Turmas`, `Financeiro`, `Graduacao`, `Materiais` ou `Perfis e acessos`.
- `git diff --check`: sem erro, apenas aviso local de conversao LF/CRLF em `system/views/home_views.py`.
- `manage.py check`: 0 issues apos migrate/seeds.
- `manage.py showmigrations system`: `[X] 0001_initial`.

## Evidence
- `manage.py help create_admin_superuser`: comando disponivel.
- `py_compile` de comando admin, home views, urls e mixins: sucesso.
- `manage.py check`: sem issues.
- `manage.py showmigrations --plan`: migrations built-in pendentes; app `system` ausente.
- Settings `ADMIN_SUPERUSER_USERNAME`, `ADMIN_SUPERUSER_EMAIL` e `ADMIN_SUPERUSER_PASSWORD`: configurados.
- PRD-070 removeu o bloqueio local, gerou/aplicou `system.0001_initial`, executou seeds objetivas e validou a Home autenticada no browser.

## Implemented
- `templates/home/dashboard.html`: shell proprio minimo, topbar LV, alternancia de tema, logout, header e seções de Acesso rapido/Pessoas recentes.
- `templates/home/partials/_dashboard_chevron.html`: icone reutilizado nos toggles de seção.
- `static/system/css/home/dashboard.css`: tokens claro/escuro, layout responsivo, links operacionais, lista de pessoas e badge visual de faixa/grau.
- `static/system/js/home/dashboard.js`: tema persistido em `lv-theme`, seções recolhiveis persistidas em `lv-home-sections`, fechamento de mensagens sem `innerHTML`.
- `system/views/home_views.py`: removido contexto antigo de aulas, graduacao, financeiro, trial e folha; mantido somente auth, data, nome, permissao de Pessoas e pessoas recentes.

## Cleanup findings
- Removidos imports e consultas de modulos fora da Home/Pessoas no `HomeView`.
- Home nao possui links mortos ou atalhos desabilitados.
- Acesso a pessoas recentes fica condicionado a tecnico admin ou perfis de suporte de Pessoas.
- Arquivos criados ficam restritos a `templates/home/` e `static/system/{css,js}/home/`.

## Follow-up PRDs
PRD-070 executou o ciclo operacional local. Falhas da suite completa fora do escopo progressivo ficam registradas na PRD-070 como achado de alinhamento legado.

## Deviations from plan
- A validacao autenticada foi concluida depois da revisao de governanca da PRD-070.

## Pending
- Alinhar testes legados de modulos removidos ao escopo progressivo, se a suite completa precisar ficar verde antes da recriacao desses modulos.

## Final status
Concluida.
