# PRD-014: Painel administrativo como pessoa do portal

## Resumo do que será implementado
Reorganizar o acesso de administrativo, professor e master no portal. O master tecnico continua com painel proprio. A pessoa administrativa passa a usar a mesma experiencia operacional do professor, com uma area administrativa mais abaixo. O professor ganha uma area operacional limitada para materiais, cadastro/consulta de alunos e agenda propria. A loja passa a permitir pedido ou pre-pedido para a propria pessoa ou para um aluno selecionado quando o usuario autenticado for professor ou administrativo.

## Tipo de demanda
Nova feature + correcao de fluxo/permissoes + ajuste de UI autenticada.

## Problema atual
A pessoa administrativa tem uma home separada e puramente administrativa, apesar de ser uma pessoa do portal. O painel master e o painel administrativo ficam conceitualmente proximos demais. A loja e os pre-pedidos estao limitados aos tipos de aluno, impedindo professor ou administrativo de solicitar material. O professor tambem nao possui atalhos operacionais para apoiar venda/solicitacao de material, cadastro e consulta de alunos.

## Objetivo
- Manter somente o master tecnico com painel diferente.
- Fazer a home do administrativo ter a mesma base da home do professor, acrescentando uma area administrativa abaixo.
- Expor ao professor apenas a area operacional coerente com aula, materiais e atendimento ao aluno.
- Permitir que professor/administrativo solicitem material para si ou para aluno selecionado sem nova migracao.
- Permitir que professor cadastre e visualize alunos, sem liberar edicao/exclusao/financeiro administrativo.

## Context Ledger
### Arquivos lidos integralmente
- `AGENTS.md`
- `CLAUDE.md`
- `.cursor/rules/anti-hallucination.mdc`
- `.cursor/rules/clean-code.mdc`
- `.cursor/rules/django-architecture.mdc`
- `.cursor/rules/environment.mdc`
- `.cursor/rules/language.mdc`
- `.cursor/rules/prd.mdc`
- `.cursor/rules/protocol.mdc`
- `.cursor/rules/security.mdc`
- `.cursor/rules/templates-static.mdc`
- `.cursor/rules/testing.mdc`
- `.cursor/rules/validation.mdc`
- `system/constants.py`
- `system/middleware.py`
- `system/services/portal_auth.py`
- `system/views/portal_mixins.py`
- `system/views/home_views.py`
- `system/urls.py`
- `system/models/person.py`
- `system/views/__init__.py`
- `system/views/product_views.py`
- `system/views/calendar_views.py`
- `system/views/person_views.py`
- `system/views/class_views.py`
- `system/views/billing_admin_views.py`
- `system/forms/person_forms.py`
- `system/forms/product_forms.py`
- `system/context_processors.py`
- `system/selectors/person_selectors.py`
- `system/selectors/__init__.py`
- `system/selectors/product_backorders.py`
- `system/models/product.py`
- `system/models/product_backorder.py`
- `system/models/registration_order.py`
- `system/services/product_backorders.py`
- `system/services/registration_checkout.py`
- `system/services/class_calendar.py`
- `system/views/payment_views.py`
- `templates/base.html`
- `templates/home/admin/dashboard.html`
- `templates/home/administrative/dashboard.html`
- `templates/home/instructor/dashboard.html`
- `templates/products/product_store.html`
- `templates/products/student_backorder_list.html`
- `templates/billing/admin_backorder_queue.html`
- `templates/people/person_list.html`
- `templates/people/person_form.html`
- `templates/people/person_detail.html`
- `templates/calendar/instructor_calendar.html`
- `templates/calendar/admin_calendar.html`
- `static/system/js/home/admin-dashboard.js`
- `static/system/js/products/product-store.js`
- `static/system/css/portal/portal.css`
- `system/tests/test_product_views.py`
- `system/tests/test_views.py`
- `system/tests/test_calendar.py`

### Arquivos adjacentes consultados
- `docs/prd/PRD-008-ajustar-paineis-professor-aluno-checkin-historico.md`
- `docs/prd/PRD-009-loja-portal-prepedido-historico.md`
- `docs/prd/PRD-012-modulo-financeiro-repasses.md`
- `docs/prd/PRD-013-acoes-rapidas-professor-home.md`

### Internet / documentação oficial
- Nao aplicavel. A entrega reaproveita Django CBVs, templates e services ja existentes sem biblioteca nova.

### MCPs / ferramentas verificadas
- PowerShell — OK — leitura de arquivos e comandos locais.
- `.venv` — OK — `.\.venv\Scripts\python.exe --version` retornou Python 3.12.10.
- Django — OK — `.\.venv\Scripts\python.exe -m django --version` retornou 4.1.13.
- `manage.py check` — OK — sem issues no preflight.
- `manage.py showmigrations` — OK — `system` segue somente com `0001_initial`.
- Browser/Playwright — OK — navegador embutido em `http://localhost:8000` com console inspecionado nas telas alteradas.

### Limitações encontradas
- `rg` existe, mas falhou com `Acesso negado`; descoberta foi feita com `Get-ChildItem` e `Select-String`.
- O worktree ja possui muitas alteracoes nao relacionadas; a entrega deve preservar esse estado.
- `templates/home/instructor/dashboard.html` referencia `static/system/js/home/instructor-dashboard.js`, mas o arquivo fonte ainda nao existe. A validacao visual exigira corrigir isso dentro do escopo da tela do professor/administrativo.

## Prompt de execução
### Persona
Agente de desenvolvimento especialista em Django 4.1 seguindo SDD + TDD + MVT com services/selectors.

### Ação
Implementar o ajuste de homes, permissoes e fluxo de materiais descrito abaixo.

### Contexto
O projeto tem tres homes autenticadas: master tecnico (`home/admin`), administrativo (`home/administrative`) e professor (`home/instructor`). O middleware ja separa `portal_is_technical_admin`, `portal_is_administrative`, `portal_is_instructor` e `portal_is_student`. A loja usa `RegistrationOrder` para pedidos avulsos e `ProductBackorder` para pre-pedidos.

### Restrições
- sem nova migracao
- sem hardcode de regra variavel
- sem mascaramento de erro
- sem liberar funcoes financeiras/estoque administrativas ao professor
- professor pode cadastrar/listar/visualizar alunos, mas nao editar/excluir pessoas nem gerenciar tipos
- administrative pode continuar acessando estoque, cronograma, financeiro e cadastros administrativos
- master tecnico continua sendo gestor administrativo, nao uma pessoa do portal
- leitura integral obrigatoria
- validacao obrigatoria

### Critérios de aceite
- [ ] Login tecnico/staff redireciona para `admin-home` e renderiza "Painel master".
- [ ] Pessoa administrativa nao acessa `admin-home`; o painel master fica restrito ao tecnico.
- [ ] Pessoa administrativa acessa `administrative-home` com layout base do professor, contendo "Aulas do dia" e area administrativa abaixo.
- [ ] Home administrativa mantem atalhos para Pessoas, Materiais/Estoque, Cronograma, Planos e Financeiro na area administrativa.
- [ ] Professor ve area operacional abaixo da home com materiais, cadastro/lista de alunos e cronograma.
- [ ] Professor consegue abrir a loja de materiais.
- [ ] Administrativo consegue abrir a loja de materiais como pessoa do portal.
- [ ] Loja exibe selecao de destinatario para professor/administrativo: propria pessoa + alunos/dependentes ativos.
- [ ] POST de compra de material por professor/administrativo pode gerar `RegistrationOrder` para aluno selecionado.
- [ ] POST de pre-pedido por professor/administrativo pode gerar `ProductBackorder` para aluno selecionado.
- [ ] Professor consegue listar e visualizar alunos.
- [ ] Professor consegue abrir cadastro de nova pessoa limitado a aluno/dependente.
- [ ] Professor nao consegue editar/excluir pessoas, gerenciar tipos, controlar estoque ou abrir financeiro administrativo.
- [ ] `manage.py test --verbosity 2` passa.
- [ ] `manage.py check` passa.
- [ ] `collectstatic --noinput` passa se static for alterado.
- [ ] Validacao em navegador desktop/mobile sem erro JS critico nem 404 relevante de asset alterado.

### Evidências esperadas
- Testes Red falhando antes da implementacao.
- Testes Green passando depois.
- `manage.py check`, `showmigrations` e `collectstatic` sem falha.
- Navegador abrindo homes de professor e administrativo, loja e fluxo de selecao de destinatario.
- Console do navegador sem erro critico.

### Formato de saída
Codigo implementado + testes + evidencias de validacao.

## Escopo
- Ajustar constantes de roles para apoio operacional e material.
- Ajustar `AdminHomeView`, `AdministrativeHomeView`, `InstructorHomeView` e contexto compartilhado.
- Reaproveitar template do professor para administrativo com area administrativa condicional.
- Adicionar area operacional do professor.
- Ajustar permissoes de loja/pre-pedido/historico para pessoas do portal que podem solicitar material.
- Adicionar selector para destinatarios de material.
- Permitir que pedido/pre-pedido seja criado para aluno selecionado quando autorizado.
- Ajustar permissoes de listagem/detalhe/criacao de pessoas para professor com restricao de tipo.
- Corrigir JS estatico da home do professor para os controles ja renderizados.
- Atualizar testes de views/produtos.

## Fora do escopo
- Novo schema para representante/vendedor do pedido.
- Relatorio de comissao por venda feita pelo professor.
- Edicao/exclusao de alunos pelo professor.
- Controle de estoque por professor.
- Mudancas no fluxo de pagamento externo alem de manter autorizacao por pedido criado na sessao.
- Notificacao por e-mail.

## Arquivos impactados
- `docs/prd/PRD-014-painel-administrativo-como-pessoa.md`
- `system/constants.py`
- `system/selectors/person_selectors.py`
- `system/selectors/__init__.py`
- `system/views/home_views.py`
- `system/views/calendar_views.py`
- `system/views/person_views.py`
- `system/views/product_views.py`
- `templates/base.html`
- `templates/home/instructor/dashboard.html`
- `templates/home/administrative/dashboard.html`
- `templates/products/product_store.html`
- `templates/people/person_list.html`
- `templates/people/person_form.html`
- `templates/people/person_detail.html`
- `static/system/js/home/instructor-dashboard.js`
- `system/tests/test_views.py`
- `system/tests/test_product_views.py`
- `system/tests/test_calendar.py`

## Riscos e edge cases
- Pessoa administrativa sem turmas deve ver a mesma base do professor com estado vazio em "Aulas do dia".
- Administrativo atribuido como apoio de aula deve poder usar as mesmas acoes de aula, respeitando ownership do service.
- Professor nao pode usar links escondidos como unica barreira de permissao; views precisam bloquear server-side.
- Pedido de material para aluno selecionado deve autorizar o checkout via sessao para nao expor pedido de terceiro sem contexto.
- Pre-pedido duplicado para o aluno selecionado deve continuar idempotente pelo service existente.
- Master tecnico sem `portal_person` nao deve ser tratado como comprador de material.

## Regras e restrições
- SDD antes de codigo
- TDD para implementacao
- sem hardcode
- sem mascaramento de erro
- sem migracoes
- leitura integral obrigatoria
- validacao obrigatoria

## Plano
- [x] 1. Contexto e leitura integral
- [x] 2. Contratos e modelagem
- [x] 3. Testes (Red)
- [x] 4. Implementacao (Green)
- [x] 5. Refatoracao (Refactor)
- [x] 6. Validacao completa
- [x] 7. Limpeza final
- [x] 8. Atualizacao documental

## Validação visual
### Desktop
Navegador embutido recarregado em `http://localhost:8000/home/administrative/` e Playwright headless em viewport `1366x900`.

- `Painel administrativo`: 1 ocorrencia.
- `Aulas do dia`: 1 ocorrencia.
- `Área administrativa`: presente.
- `Controle de estoque`: presente.
- `Cronograma`: presente.
- `http://127.0.0.1:8000/home/admin/` com administrativo retornou `403`, mantendo o master separado.
- Console da pagina: sem erros.

### Mobile
Navegador embutido em viewport estreita e Playwright headless em viewport mobile `390x844` validaram:

- `http://localhost:8000/home/instructor/` com `Apoio operacional`, `Solicitar material`, `Cadastrar aluno`, `Visualizar alunos` e `Cronograma`.
- `Controle financeiro` nao aparece para professor.
- `http://localhost:8000/store/` exibe `Solicitar para` com seletor de destinatario.
- O seletor aceitou trocar de `Layon Quirino · Professor` para `Aluno PIX Pago Masculino · Aluno`.
- Playwright mobile encontrou 10 opcoes no seletor de destinatario.

### Console do navegador
Sem erros JS criticos nas telas:

- `home/administrative/`
- `home/instructor/`
- `store/`
- `people/`
- `people/create/`
- `home/admin/` retornando 403 para administrativo
- `products/`
- `admin-calendar/`
- Playwright desktop registrou `Failed to load resource: 403 (Forbidden)` apenas na navegacao intencional para `/home/admin/` com administrativo. Sem erro JS critico nas rotas validas.

### Terminal
`read_thread_terminal` nao encontrou sessao de terminal anexada ao thread. A rota local respondeu por HTTP em `127.0.0.1:8000` com status 200.

## Validação ORM
### Banco
Sem alteracao de schema e sem migracao nova.

### Shell checks
- `PortalAccount` com CPF `900.000.000-07`: `Administrativo Teste`, tipo `administrative-assistant`, ativo.
- Professores ativos encontrados no seed: `Layon Quirino`, `Vinicius Antonio`, `Lauro Viana`, `Andre Oliveira`, `Vanessa Ferro`.
- Alunos ativos encontrados para selecao de material, incluindo `Aluno PIX Pago Masculino`.

### Integridade do fluxo
- Administrativo entra em `home/administrative/` e nao entra em `home/admin/` (`403 Forbidden`).
- Professor entra em `home/instructor/`, acessa `store/`, `people/` e `people/create/`.
- Cadastro aberto por professor limita `person_type` a `Aluno` e `Dependente`.
- Lista de pessoas do professor nao renderiza `Editar`, `Excluir` nem bloco financeiro.

## Validação de qualidade
### Sem hardcode
OK. Regras de roles foram centralizadas em constantes e selectors.

### Sem estruturas condicionais quebradiças
OK. Permissoes server-side foram concentradas em mixins/selectors e flags de contexto.

### Sem `except: pass`
OK. Nenhum `except: pass` introduzido.

### Sem mascaramento de erro
OK. Destinatario invalido de material retorna mensagem explicita e redirect seguro.

### Sem comentários e docstrings desnecessários
OK. O codigo novo foi mantido sem comentarios narrativos.

## Evidências
- Red: testes focados falharam antes da implementacao para home administrativa, bloqueio do master, area operacional do professor e loja de materiais por professor/administrativo.
- Green focado: `manage.py test system.tests.test_views.PortalViewTestCase.test_administrative_portal_account_dashboard_exposes_shortcuts ... --verbosity 2` com 4 testes OK.
- Green focado: `manage.py test system.tests.test_product_views.ProductViewTestCase.test_instructor_product_store_exposes_student_recipient_choices ... --verbosity 2` com 4 testes OK.
- Suite completa: `manage.py test --verbosity 2` executou 305 testes em 42.854s com OK.
- `manage.py check`: sem issues.
- `manage.py showmigrations system`: `system` segue apenas com `0001_initial` aplicada.
- `manage.py collectstatic --noinput`: concluido, 0 arquivos copiados e 165 inalterados na rodada final.
- Browser: validacao funcional real nas homes, loja, lista/cadastro de pessoas, estoque e cronograma.
- Playwright headless: desktop `1366x900` para administrativo/master bloqueado e mobile `390x844` para professor/loja.

## Implementado
- `AdminHomeView` passou a exigir sessao tecnica/master.
- `AdministrativeHomeView` reutiliza a base de dashboard do professor e renderiza area administrativa abaixo.
- `InstructorHomeView` ganhou area operacional limitada.
- Loja de materiais permite professor/administrativo selecionar destinatario ativo.
- Checkout e pre-pedido gravam o pedido para o aluno/dependente selecionado quando autorizado.
- Professor pode listar, visualizar e abrir cadastro de aluno/dependente, sem editar/excluir/financeiro administrativo.
- Rotas de cronograma do professor aceitam equipe de aula autorizada.
- `static/system/js/home/instructor-dashboard.js` foi criado para o script ja referenciado pelo template.

## Desvios do plano
- Durante a validacao manual foi tentada a URL incorreta `/calendar/admin/`; a rota real do sistema e `/admin-calendar/`, validada em seguida sem erro.
- A primeira rodada Playwright headless dentro do sandbox falhou com `WinError 5`; foi reexecutada fora do sandbox com aprovacao. A primeira selecao por `label` do `<option>` falhou por normalizacao de espacos; foi revalidada por `value` real do option.
- O worktree ja continha muitas alteracoes nao relacionadas; elas foram preservadas.

## Pendências
- Nenhuma pendencia funcional conhecida neste escopo.
