# PRD-025: Redesign responsivo do sistema LV

## Resumo do que será implementado

Criar a base de especificacao para reimplementar, em etapas, a interface do sistema LV JIU JITSU em celulares e computadores, preservando todas as funcionalidades existentes, os temas claro e escuro e os contratos reais de permissao por tipo de pessoa.

Esta PRD nao autoriza ainda a troca visual de nenhuma tela. Ela cria a trilha de execucao para as proximas PRDs por tela ou modulo.

## Tipo de demanda

Alteracao arquitetural de UI, regeneracao documental e preparacao de refatoracao visual.

## Problema atual

As telas existem e cobrem varias rotinas do sistema, mas a experiencia visual esta inconsistente entre modulos, com uso misto de cards, tabelas, scripts inline, estilos inline, assets versionados manualmente e comportamentos diferentes entre templates autenticados e publicos.

O risco principal do redesign e melhorar aparencia removendo, escondendo ou quebrando funcionalidades operacionais ja existentes.

## Objetivo

Definir um contrato de UI para o sistema como academia de jiu jitsu, com padrao visual LV, responsividade, acessibilidade minima, comportamento por papel e regra de validacao obrigatoria antes de cada tela ser reimplementada.

## Context Ledger

### Arquivos lidos integralmente

- `AGENTS.md`
- `CLAUDE.md`
- `system/urls.py`
- `lvjiujitsu/urls.py`
- `templates/base.html`
- `system/views/portal_mixins.py`
- `system/views/home_views.py`
- `system/views/person_views.py`
- `system/constants.py`
- `system/forms/person_forms.py`
- `system/models/person.py`
- `system/selectors/person_selectors.py`
- `system/middleware.py`
- `system/context_processors.py`
- `templates/people/person_list.html`
- `templates/people/person_detail.html`
- `templates/people/person_form.html`
- `templates/home/admin/dashboard.html`
- `templates/home/administrative/dashboard.html`
- `templates/home/instructor/dashboard.html`
- `templates/home/student/dashboard.html`
- `system/views/class_views.py`
- `system/views/category_views.py`
- `system/views/plan_views.py`
- `system/views/product_views.py`
- `system/views/calendar_views.py`
- `system/views/graduation_views.py`
- `system/views/auth_views.py`
- `system/views/billing_admin_views.py`
- `system/views/payment_views.py`
- `system/views/plan_change_views.py`
- `system/views/asaas_views.py`

### Arquivos adjacentes consultados

- `templates/`
- `static/system/`
- `docs/prd/`
- `static/system/css/portal/portal.css`
- `static/system/css/portal/class-catalog.css`
- `static/system/css/portal/person-detail.css`
- `static/system/css/auth/login.css`
- `static/system/css/billing/billing.css`
- `static/system/css/shared/plan-selector.css`
- `templates/login/register.html`
- `templates/login/login_form.html`
- `templates/calendar/admin_calendar.html`
- `templates/calendar/instructor_calendar.html`
- `templates/calendar/student_schedule.html`
- `static/system/js/shared/theme-toggle.js`
- `static/system/js/shared/drawer-menu.js`
- `static/system/js/home/instructor-dashboard.js`
- `static/system/js/products/product-store.js`
- `static/system/js/billing/plan-change-selector.js`
- `static/system/js/auth/registration-wizard-clean.js`

### Internet / documentacao oficial

- MDN `prefers-color-scheme`: https://developer.mozilla.org/en-US/docs/Web/CSS/%40media/prefers-color-scheme
- MDN `color-scheme`: https://developer.mozilla.org/en-US/docs/Web/CSS/color-scheme
- MDN Container size and style queries: https://developer.mozilla.org/docs/Web/CSS/CSS_containment/Container_size_and_style_queries
- W3C WCAG 2.2: https://www.w3.org/TR/WCAG22/
- W3C Understanding Target Size Minimum: https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum

### MCPs / ferramentas verificadas

- `figma-use` skill: carregada e lida. Status: disponivel. Teste executado: leitura de `SKILL.md`. `use_figma` nao foi chamado porque nao ha URL de arquivo Figma alvo nesta etapa.
- PowerShell: disponivel. Teste executado: comandos de leitura e `git status --short`.
- Python do projeto: disponivel. Teste executado: `.\.venv\Scripts\python.exe --version` retornou Python 3.12.10.
- Django check: disponivel. Teste executado: `.\.venv\Scripts\python.exe manage.py check` retornou 0 problemas.

### Limitacoes encontradas

- A etapa atual nao valida visualmente telas em navegador porque ainda nao altera UI.
- O arquivo de referencia visual `LOGO_LV.pdf` esta fora do workspace em `C:\Users\whsf\Downloads\LOGO_LV.pdf`; foi verificada a existencia do arquivo, mas a identidade visual principal usada nesta PRD veio da imagem PNG fornecida e dos assets ja existentes em `static/system/img/`.
- Existem ocorrencias atuais de JavaScript inline, estilos inline e `innerHTML` em templates/scripts. Isso sera tratado como divida de UI/seguranca a resolver por PRD de tela, sem impedir a criacao deste contrato.

## Prompt de execucao

### Persona

Agente de desenvolvimento especialista em Django server-rendered, UI responsiva, SDD, TDD e validacao visual com navegador.

### Acao

Reimplementar cada tela do sistema LV JIU JITSU seguindo o contrato `docs/UI-SCREEN-CONTRACT.md`, criando uma PRD especifica por tela ou modulo antes de qualquer alteracao visual.

### Contexto

O sistema e um monolito Django que opera o portal publico e areas autenticadas de uma academia de jiu jitsu. A interface deve refletir a identidade LV: tatame, disciplina, cultura marcial, preto/cinza/branco com vermelho como acento, mantendo tema claro e escuro.

### Restricoes

- sem criar novas pastas
- sem editar `staticfiles/`
- sem migracoes
- sem hardcode de segredo ou regra variavel
- sem remover funcionalidade existente
- sem esconder funcionalidade critica por responsividade
- sem JS/CSS inline novo, salvo JSON de dados em `<script type="application/json">`
- sem alterar regra de negocio em template ou JavaScript
- leitura integral obrigatoria da tela antes de altera-la
- validacao visual obrigatoria em desktop e mobile antes de concluir qualquer tela

### Criterios de aceite

- [ ] Cada etapa de redesign deve possuir PRD propria ou subsecao de PRD aprovada, com escopo de tela/modulo claro.
- [ ] Cada tela alterada deve preservar links, forms, permissoes, mensagens, estados vazios, estados de erro e acoes POST existentes.
- [ ] Tema claro e escuro devem permanecer disponiveis em toda tela alterada.
- [ ] Em celular, informacoes criticas devem aparecer em fluxo vertical com rolagem clara, sem sumir.
- [ ] Em desktop, informacoes devem usar largura, grade e densidade adequadas ao fluxo operacional.
- [ ] Tabelas operacionais devem ser substituidas por cards responsivos ou receber tratamento de overflow legivel, sem perder colunas criticas.
- [ ] A tela de pessoas deve diferenciar comportamento visivel de Aluno, Dependente, Responsavel, Professor, Administrativo e Admin tecnico conforme contratos reais de permissao.
- [ ] Todo asset CSS/JS versionado com `?v=` deve ter a versao atualizada quando alterado.
- [ ] O redesign deve passar por `manage.py check`, testes aplicaveis, `collectstatic --noinput` quando houver static, e validacao visual com browser/Playwright.

### Evidencias esperadas

- PRD da tela/modulo atualizada
- testes passando
- `manage.py check` sem problemas
- `collectstatic --noinput` sem erro quando houver estatico
- navegador desktop e mobile sem erro critico no console
- terminal do servidor sem stack trace
- screenshots ou relato objetivo das telas validadas

### Formato de saida

Codigo implementado + testes + evidencias de validacao + pendencias reais.

## Escopo

- Criar contrato documental de UI e responsividade em `docs/UI-SCREEN-CONTRACT.md`.
- Atualizar `CLAUDE.md` para declarar esse contrato como fonte de verdade local de redesign.
- Registrar no PRD o inventario inicial das areas e o protocolo de execucao por etapa.

## Fora do escopo

- Reimplementar telas nesta etapa.
- Alterar CSS/JS de producao nesta etapa.
- Criar novas pastas.
- Alterar modelos, migrations, services ou regras de negocio.
- Criar ou modificar arquivo Figma sem URL alvo e sem etapa propria.

## Arquivos impactados

- `docs/prd/PRD-025-redesign-ui-responsivo-lv.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `CLAUDE.md`
- `AGENTS.md` somente se for necessario reforco generico de fonte de verdade, sem regra especifica do projeto.

## Riscos e edge cases

- Redesign visual ocultar acoes administrativas ou financeiras em mobile.
- Tela de pessoas tratar todos os tipos de pessoa como aluno e esconder informacoes de professor ou administrativo.
- Cards substituirem tabelas removendo colunas de auditoria.
- Tema escuro ficar legivel e tema claro ficar sem identidade LV, ou o inverso.
- Uso de vermelho virar acento dominante e comprometer contraste.
- JavaScript inline existente continuar dificultando validacao e manutencao.
- Mudanca visual em asset versionado nao atualizar query string.

## Regras e restricoes

- SDD antes de codigo.
- TDD para implementacao.
- Sem hardcode.
- Sem mascaramento de erro.
- Sem migracoes por padrao.
- Leitura integral obrigatoria.
- Validacao obrigatoria.
- Nenhuma funcionalidade pode ser removida, escondida ou substituida por texto explicativo.
- A identidade visual deve usar a linguagem LV sem transformar o sistema interno em landing page.

## Plano

- [x] 1. Contexto e leitura integral
- [x] 2. Contratos e modelagem
- [ ] 3. Testes (Red)
- [ ] 4. Implementacao (Green)
- [ ] 5. Refatoracao (Refactor)
- [ ] 6. Validacao completa
- [ ] 7. Limpeza final
- [ ] 8. Atualizacao documental

## Validação visual

### Desktop

Nao aplicavel nesta etapa documental.

### Mobile

Nao aplicavel nesta etapa documental.

### Console do navegador

Nao aplicavel nesta etapa documental.

### Terminal

`manage.py check` executado antes da edicao documental e retornou sem problemas.

## Validação ORM

### Banco

Nao aplicavel nesta etapa.

### Shell checks

Nao aplicavel nesta etapa.

### Integridade do fluxo

Fluxos foram mapeados por rotas, views, templates e constantes de permissao. Nenhum fluxo foi alterado nesta etapa.

## Validação de qualidade

### Sem hardcode

Documentacao nao introduz hardcode operacional.

### Sem estruturas condicionais quebradicas

Nao aplicavel a codigo de producao nesta etapa.

### Sem `except: pass`

Nao foi introduzido codigo Python.

### Sem mascaramento de erro

Nao foi introduzido tratamento de erro.

### Sem comentarios e docstrings desnecessarios

Nao aplicavel.

## Evidências

- `.\.venv\Scripts\python.exe --version` -> Python 3.12.10.
- `.\.venv\Scripts\python.exe manage.py check` -> System check identified no issues.
- `docs/prd/` ja existia; nenhuma pasta nova foi criada.
- Arquivo visual enviado verificado em `C:\Users\whsf\Downloads\ChatGPT Image 8 de mai. de 2026, 22_03_06 (3).png`.
- Logo PDF enviado verificado em `C:\Users\whsf\Downloads\LOGO_LV.pdf`.

## Implementado

- PRD macro do redesign responsivo.
- Contrato documental de UI e comportamento por tela.
- Referencia do contrato no `CLAUDE.md`.

## Desvios do plano

- Nenhum desvio nesta etapa.

## Pendências

- Criar PRD especifica para a primeira tela a ser reimplementada.
- Validar visualmente a tela real antes e depois de cada alteracao.
- Extrair scripts inline e estilos inline existentes quando a tela correspondente entrar no escopo.
- Definir se a primeira tela sera `people/person_list.html`, `people/person_detail.html` ou `people/person_form.html`.
