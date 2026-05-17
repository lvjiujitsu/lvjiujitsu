# PRD-028: Home e Pessoas em tela cheia

## Resumo do que será implementado
Recomeçar o padrão visual das homes e da home de Pessoas com tela cheia, módulos distintos, navegação lateral simples e redirecionamento claro da home principal para as homes funcionais, começando por Pessoas.

## Tipo de demanda
Refatoração de UI com regeneração documental.

## Problema atual
As telas reimplementadas ainda parecem blocos agrupados dentro de cartões, desperdiçam espaço em monitores diferentes e misturam resumo decorativo com ações reais. O menu lateral também fica pesado para navegar entre rotinas.

## Objetivo
- Usar a largura útil inteira da tela nas homes e em Pessoas.
- Exibir comandos diretos na home inicial dentro de blocos contextuais leves por domínio operacional.
- Simplificar o menu lateral com ícones, rótulos claros e links diretos por permissão.
- Preservar redirecionamento por perfil e todas as ações existentes.
- Manter tema claro/escuro e responsividade real em celular e desktop.

## Context Ledger
### Arquivos lidos integralmente
- `AGENTS.md`
- `CLAUDE.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `docs/prd/PRD-027-home-admin-redesign-responsivo.md`
- `system/constants.py`
- `system/forms/person_forms.py`
- `system/urls.py`
- `system/views/home_views.py`
- `system/views/person_views.py`
- `system/views/portal_mixins.py`
- `templates/base.html`
- `templates/home/admin/dashboard.html`
- `templates/home/instructor/dashboard.html`
- `templates/home/student/dashboard.html`
- `templates/people/person_list.html`
- `static/system/css/portal/portal.css`
- `static/system/css/portal/admin-dashboard.css`
- `static/system/css/portal/people.css`
- `static/system/js/shared/drawer-menu.js`
- `static/system/js/shared/people-list.js`
- `static/system/js/home/instructor-dashboard.js`
- `system/tests/test_views.py`

### Arquivos adjacentes consultados
- `docs/prd/`

### Internet / documentação oficial
- Não aplicável; mudança usa Django templates e CSS existentes.

### MCPs / ferramentas verificadas
- PowerShell — OK.
- Django test runner — OK.
- Browser/Playwright — OK.

### Limitações encontradas
- Sem criação de pastas.
- Sem migrações.
- Escopo desta etapa limitado a Home, menu lateral e home de Pessoas.
- A solicitação mencionou Figma; a skill `figma-generate-design` foi lida para guiar a composição, mas não há arquivo Figma alvo informado para mutação.

## Matriz funcional por perfil

### Administrador técnico
- Deve acessar a home `admin-home` após login técnico.
- Deve acessar Pessoas, Tipos, Planos, Categorias, Turmas, Horários, Cronograma administrativo, Estoque, Pré-pedidos, Panorama de graduação, Faixas, Regras, Histórico de graduação, Controle financeiro, Aprovações, Pagamentos pendentes, Folha de professores, Fila de pagamentos e Django Admin.
- Não deve ver a mesma ação duplicada na home inicial.

### Administrativo
- Deve acessar a home administrativa.
- Deve operar Pessoas, Estoque, Pré-pedidos, Cronograma, Planos, Controle financeiro e financeiro próprio quando aplicável.
- Não deve acessar a home técnica `admin-home`.

### Professor
- Deve acessar a home do professor.
- Deve ver aulas do dia, check-ins, criar aulão, gerir cronograma, visualizar alunos, cadastrar aluno, solicitar material e financeiro próprio.
- Em Pessoas, deve listar apenas alunos/dependentes permitidos e não deve receber Excluir.

### Aluno, responsável e dependente
- Devem acessar a home do aluno.
- Devem ver mensalidade, plano, loja, aulas do dia, check-in, histórico de presença e graduação.
- Responsável/dependente devem preservar o contexto financeiro vinculado pelo backend.

## Requisitos não funcionais
- A home inicial deve organizar comandos por proximidade funcional: Pessoas e acesso, Academia, Materiais, Graduação, Financeiro e Técnico.
- Os blocos devem orientar a navegação sem esconder ações, sem colapso e sem textos decorativos extensos.
- O menu lateral deve usar ícones simples, consistentes, com texto curto e alvo de toque confortável.
- A primeira tela em desktop deve aproveitar monitores largos sem criar colunas vazias.
- Em mobile, comandos devem virar lista/grade de uma coluna sem overflow horizontal.
- Em desktop, blocos e listagens operacionais devem usar comportamento horizontal: contexto à esquerda e comandos/registros à direita; em celular devem empilhar em sequência vertical.
- Tema claro/escuro deve usar tokens existentes.
- Ícones são decorativos e devem ter `aria-hidden="true"`.

## Prompt de execução
### Persona
Agente de desenvolvimento especialista em Django MVT seguindo SDD + TDD + CSS responsivo operacional.

### Ação
Reimplementar as superfícies de Home e Pessoas em tela cheia, preservando requisitos funcionais por perfil.

### Contexto
O portal LV JIU JITSU tem homes diferentes para administrador técnico, administrativo, professor e aluno/responsável/dependente. A home deve levar o usuário para módulos funcionais como Pessoas, Tatame, Financeiro, Materiais e Graduação sem transformar a tela em landing page.

### Restrições
- sem hardcode de regra de negócio
- sem migrações
- sem criar pastas
- sem remover funcionalidades
- CSS em `static/`
- templates em `templates/`
- validação visual obrigatória

### Critérios de aceite
- [ ] O menu lateral deve ter links diretos com ícones e sem árvore visual conturbada.
- [ ] A home técnica deve exibir comandos diretos para todos os módulos administrativos dentro de blocos contextuais.
- [ ] `Django Admin` deve aparecer uma única vez na home técnica.
- [ ] A home administrativa deve exibir Pessoas, Estoque, Pré-pedidos, Cronograma, Planos e Financeiro.
- [ ] A home do professor deve exibir aulas do dia, check-ins, cronograma, alunos, cadastro de aluno, loja e financeiro próprio.
- [ ] A home do aluno/responsável/dependente deve exibir mensalidade, graduação, loja, planos, aulas do dia, check-in e histórico.
- [ ] A home de Pessoas deve usar a largura inteira, manter KPIs funcionais, filtros, visualização em modal e ações conforme permissão.
- [ ] Desktop e mobile não podem ter overflow horizontal.
- [ ] Listagens de Pessoas, Tipos, Planos, Categorias, Turmas, Horários, Estoque e Faixas devem empilhar no mobile e alinhar em linhas horizontais no desktop.
- [ ] Telas financeiras e tabelas administrativas devem ocupar a largura útil e preservar rolagem horizontal apenas dentro da tabela quando necessário.
- [ ] Tema claro/escuro deve continuar funcional.

## Escopo
- `templates/base.html`
- `templates/home/admin/dashboard.html`
- `templates/home/instructor/dashboard.html`
- `templates/home/student/dashboard.html`
- `templates/people/person_list.html`
- `static/system/css/portal/workbench.css`
- `static/system/css/portal/portal.css`
- `system/tests/test_views.py`
- `docs/UI-SCREEN-CONTRACT.md`

## Fora do escopo
- Tela de edição de pessoa.
- Detalhe, exclusão e criação de pessoa.
- CRUDs de Tatame, Financeiro, Materiais e Graduação.
- Mudança de permissão ou rota.

## Arquivos impactados
- `docs/prd/PRD-028-home-e-pessoas-fullscreen.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `templates/base.html`
- `templates/home/admin/dashboard.html`
- `templates/home/instructor/dashboard.html`
- `templates/home/student/dashboard.html`
- `templates/people/person_list.html`
- `static/system/css/portal/workbench.css`
- `static/system/css/portal/portal.css`
- `system/tests/test_views.py`

## Riscos e edge cases
- Perder link funcional ao simplificar o menu.
- Esconder ações em mobile.
- Tornar módulos visualmente iguais demais e perder escaneabilidade.
- Quebrar JS de check-in por mover containers.

## Plano
- [x] 1. Atualizar contrato e testes.
- [x] 2. Implementar menu lateral simples com ícones.
- [x] 3. Implementar home técnica em blocos contextuais.
- [x] 4. Reestruturar CSS full-screen compartilhado.
- [x] 5. Reestruturar home de Pessoas.
- [x] 6. Validar testes, check, collectstatic e browser.

## Validação visual
### Desktop
OK. Browser/Playwright em `http://localhost:8000/home/admin/`:
- viewport 1440x1000: `workbench-context-grid` com 4 colunas, 6 blocos contextuais, 19 comandos, sem overflow horizontal;
- viewport 2327x1411: `workbench-context-grid` com 6 colunas, 6 blocos contextuais, 19 comandos, sem overflow horizontal;
- validação posterior em 1440x1000 confirmou blocos da home com 2 colunas internas por bloco: contexto à esquerda e comandos à direita;
- validação posterior cobriu Pessoas, Tipos, Planos, Categorias, Turmas, Horários, Cronograma, Estoque, Pré-pedidos, Panorama, Faixas, Regras, Histórico, Controle financeiro, Aprovações, Pagamentos pendentes, Folha de professores e Fila de pagamentos sem overflow horizontal;
- `Django Admin` aparece uma vez na home;
- drawer sem `details`, `summary` ou `.drawer-group`;
- 23 ícones no drawer;
- sem overflow horizontal.

### Mobile
OK. Browser em 390x900:
- `workbench-context-grid` com 1 coluna;
- 19 comandos diretos;
- sem overflow horizontal.

### Console do navegador
Sem erro crítico observado durante a validação de navegação e inspeção DOM.

### Terminal
OK.

## Evidências
- Red inicial:
  - `test_master_dashboard_uses_grouped_responsive_layout` falhou por ausência de `workbench.css` e `workbench-shell`.
  - `test_dashboards_and_people_home_use_fullscreen_workbench_contract` falhou por ausência de `workbench-shell`.
- Green:
  - `manage.py test system.tests.test_views.PortalViewTestCase.test_master_dashboard_shows_all_shortcuts_without_toggle system.tests.test_views.PortalViewTestCase.test_master_dashboard_uses_contextual_command_blocks system.tests.test_class_portal_views.ClassPortalViewTestCase.test_admin_home_exposes_class_crud_shortcuts --verbosity 2` — OK.
  - `manage.py test system.tests.test_views.PortalViewTestCase.test_master_dashboard_uses_contextual_command_blocks system.tests.test_class_portal_views.ClassPortalViewTestCase.test_admin_home_exposes_class_crud_shortcuts --verbosity 2` — OK apos ajuste de altura natural dos blocos.
  - `manage.py test system.tests.test_views --verbosity 2` — 78 testes OK.
  - `manage.py test --verbosity 2` — 269 testes OK.
  - `manage.py test --verbosity 2` — 275 testes OK apos ajustes de planos e padronizacao horizontal.
  - `manage.py check` — OK.
  - `manage.py collectstatic --noinput` — OK.

## Implementado
- Menu lateral com ícones SVG compartilhados e links diretos.
- Removidos agrupadores colapsáveis do drawer.
- Home master com 6 blocos contextuais e 19 comandos diretos.
- Removida duplicidade de `Django Admin` na home master.
- CSS `workbench.css` ajustado para grade responsiva de comandos.
- CSS compartilhado ajustado para listas e telas operacionais horizontais no desktop e verticais no mobile.
- Contrato de UI atualizado com regra de home em blocos contextuais e menu iconográfico.

## Desvios do plano
O primeiro desenho removeu totalmente a proximidade por domínio e deixou os comandos soltos. A correção posterior adotou blocos contextuais leves, mantendo todas as ações visíveis.

## Pendências
Homes administrativa, professor, aluno e Pessoas seguem carregando `workbench.css`, mas a remodelagem visual profunda sem agrupamentos foi aplicada nesta correção apenas na home master e no menu lateral, conforme anotação atual do usuário.
