# PRD-050: Módulo administrativo de planos

## Resumo do que será implementado
Liberar o módulo de planos para visualização e gestão administrativa, conectando o atalho "Planos" da Home a telas server-rendered de listagem, detalhe, criação, edição e exclusão controlada de planos de assinatura.

## Tipo de demanda
Nova feature.

## Problema atual
O atalho "Planos" aparece na Home como link desabilitado, apesar de o projeto já possuir modelo, formulário parcial, serviços e views iniciais para `SubscriptionPlan`. Não há rotas registradas, templates do módulo, CSS próprio ou testes de acesso ao fluxo administrativo.

## Objetivo
Disponibilizar um módulo administrativo coerente com o padrão visual existente em `templates/people/`, respeitando `docs/UI-SCREEN-CONTRACT.md`, sem alterar schema e sem criar migrações.

## Context Ledger

### Arquivos lidos integralmente
- `AGENTS.md`
- `CLAUDE.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `system/models/plan.py`
- `system/forms/plan_forms.py`
- `system/services/plan_management.py`
- `system/views/plan_views.py`
- `system/urls.py`
- `templates/home/dashboard.html`
- `static/system/css/home/dashboard.css`
- `static/system/js/dashboard.js`
- `system/tests/test_home_dashboard.py`
- `system/views/person_views.py`
- `system/views/home_views.py`
- `templates/people/person_list.html`
- `templates/people/person_form.html`
- `templates/people/person_detail.html`
- `templates/people/person_confirm_delete.html`
- `static/system/css/people/people.css`
- `docs/prd/PRD-045-pessoas-listagem-detalhe.md`
- `docs/prd/PRD-028-crud-planos-precificacao-dinamica.md`
- `docs/prd/PRD-007-reformular-planos-precificacao-elegibilidade.md`
- `docs/prd/PRD-006-padronizar-tela-troca-plano.md`
- `docs/prd/PRD-019-troca-plano-padrao-plan-selector.md`
- `docs/prd/PRD-020-troca-plano-saldo-credito-refund.md`
- `docs/prd/PRD-035-seed-valores-planos-assinatura.md`
- `docs/prd/PRD-041-stripe-recorrente.md`
- `system/tests/test_plan_models.py`
- `system/tests/test_plan_eligibility.py`
- `system/tests/test_plan_change.py`
- `system/tests/test_forms.py`
- `system/admin.py`
- `system/models/__init__.py`
- `system/selectors/plan_eligibility.py`
- `system/services/registration_checkout.py`
- `system/signals.py`
- `static/initial_data/seed_system_initial_subscription_plans_values.json`
- `static/initial_data/seed_system_initial_subscription_plans_stripe.json`
- `system/management/commands/seed_system_initial_subscription_plans_values.py`
- `system/models/membership.py`
- `system/models/registration_order.py`
- `system/views/portal_mixins.py`

### Arquivos adjacentes consultados
- `docs/prd/`
- `templates/`
- `static/system/css/`
- `system/tests/`
- `system/migrations/`

### Internet / documentação oficial
- Django 4.1 — generic display views: `https://docs.djangoproject.com/en/4.1/ref/class-based-views/generic-display/`
- Django 4.1 — generic editing views: `https://docs.djangoproject.com/en/4.1/ref/class-based-views/generic-editing/`

### MCPs / ferramentas verificadas
- PowerShell — OK — `Get-Location`
- Python do projeto — OK — `.\.venv\Scripts\python.exe --version`
- Django test runner — OK — `.\.venv\Scripts\python.exe manage.py help test`
- Django checks — OK — `.\.venv\Scripts\python.exe manage.py check`
- Migrações existentes — OK — `.\.venv\Scripts\python.exe manage.py showmigrations`
- Context7 — limitado — tentativa de resolver documentação Django retornou token OAuth inválido

### Limitações encontradas
- O projeto possui worktree sujo antes desta mudança; alterações não relacionadas não devem ser revertidas.
- `CLAUDE.md` restringe criação de novas pastas, mas `PRD-045` já registra precedente para criar pastas de templates/static quando views existentes apontam para um módulo ainda sem arquivos.
- Não haverá mudança de schema; portanto, não haverá migração, `makemigrations` ou `migrate`.

## Prompt de execução

### Persona
Agente de desenvolvimento especialista em Django MVT seguindo SDD, TDD e server-rendered UI.

### Ação
Implementar o módulo administrativo de planos seguindo a spec abaixo.

### Contexto
O sistema já possui `SubscriptionPlan` como entidade central para mensalidades, troca de plano, cadastro público, pagamento recorrente e seeds de valores. O módulo administrativo deve expor esse cadastro para equipe autorizada sem quebrar os fluxos existentes.

### Restrições
- sem hardcode de segredo, domínio, token ou regra variável
- sem mascaramento de erro
- sem migrações
- sem `makemigrations`
- sem `migrate`
- leitura integral obrigatória
- validação obrigatória
- textos visíveis em pt-BR
- identificadores técnicos em inglês
- CSS/JS separados por módulo
- não editar `staticfiles/`

### Critérios de aceite
- [ ] O atalho "Planos" da Home deve abrir o módulo em `/planos/` para administrador técnico (verificável por teste e navegador).
- [ ] Usuário não autenticado deve ser redirecionado ao login ao acessar `/planos/` (verificável por teste).
- [ ] A listagem deve exibir planos existentes com nome, código, público, frequência, ciclo, método de pagamento, status e preço (verificável por teste e inspeção visual).
- [ ] A listagem deve permitir filtrar por busca textual, público, frequência, ciclo, gateway e status (verificável por teste).
- [ ] O detalhe deve exibir dados comerciais, precificação, gateway, Stripe e uso do plano (verificável por teste e inspeção visual).
- [ ] O formulário deve expor campos administrativos necessários para criar/editar plano sem alterar schema (verificável por teste).
- [ ] Exclusão de plano vinculado a `Membership` deve falhar de forma explícita, preservar o plano e orientar desativação (verificável por teste).
- [ ] Hierarquia visual: título em peso 700, rótulos em 500, hints em `--muted` (verificável: inspeção visual).
- [ ] Proximidade: campos do mesmo grupo com gap <= 12px; grupos separados por divisor ou gap >= 20px (verificável: inspeção visual).
- [ ] Affordance: ação primária com fundo `--brand-red`; filtros e badges com estados distintos (verificável: inspeção visual).
- [ ] Estado disabled com opacity 0.45 e cursor `not-allowed` quando houver ação indisponível (verificável: inspeção visual).
- [ ] Feedback de erro por campo abaixo do campo em `--danger` (verificável: submissão inválida).
- [ ] Máquina de estado: listagem vazia, listagem com dados, formulário inválido e exclusão bloqueada têm representação visual distinta (verificável: teste + inspeção).

### Evidências esperadas
- testes focados passando
- `manage.py test --verbosity 2` passando
- `manage.py check` passando
- `manage.py collectstatic --noinput` passando, se houver novo estático
- console do navegador sem erro JS crítico
- terminal do servidor sem stack trace
- inspeção visual desktop e mobile

### Formato de saída
Código implementado + testes + evidências de validação.

## Escopo
- Registrar rotas administrativas de planos no namespace `system`.
- Liberar o quick-link "Planos" da Home.
- Expandir o formulário de planos para campos comerciais, de precificação e gateway já existentes no modelo.
- Criar filtro server-side para a listagem.
- Criar templates `plans/` seguindo o padrão visual de `people/`.
- Criar CSS/JS próprio em `static/system/css/plans/` e `static/system/js/plans/`.
- Adicionar testes de views, formulário e Home.
- Validar UI no navegador.

## Fora do escopo
- Alterar o modelo `SubscriptionPlan`.
- Criar ou regenerar migrações.
- Criar integração nova com gateway.
- Sincronizar produtos/preços no Stripe.
- Alterar o wizard público de cadastro.
- Alterar regra de elegibilidade de planos.
- Implementar permissões granulares novas.

## Arquivos impactados
- `docs/prd/PRD-050-modulo-planos-admin.md`
- `system/forms/plan_forms.py`
- `system/services/plan_management.py`
- `system/views/plan_views.py`
- `system/urls.py`
- `templates/home/dashboard.html`
- `templates/plans/plan_list.html`
- `templates/plans/plan_detail.html`
- `templates/plans/plan_form.html`
- `templates/plans/plan_confirm_delete.html`
- `static/system/css/plans/plans.css`
- `static/system/js/plans/plans.js`
- `system/tests/test_plan_views.py`
- `system/tests/test_forms.py`
- `system/tests/test_home_dashboard.py`

## Riscos e edge cases
- Planos vinculados a assinaturas não podem ser excluídos por causa de `PROTECT`.
- Campos de gateway e Stripe são usados por fluxos de pagamento; a UI deve expor dados sem inventar sincronização.
- O cálculo de preço no model usa `base_monthly_net_price`; o formulário não deve ocultar o preço manual quando esse campo estiver vazio.
- A listagem pode conter muitos planos; a primeira entrega usa filtros server-side e ordenação previsível, sem paginação porque o catálogo esperado é pequeno.
- O padrão atual de templates possui scripts inline de tema; esta implementação deve preferir JS de módulo para novas interações.

## Regras e restrições
- SDD antes de código
- TDD para implementação
- sem hardcode
- sem mascaramento de erro
- sem migrações
- leitura integral obrigatória
- validação obrigatória

## Hierarquia Visual

- Padrão de leitura: F Pattern
- Título de tela: peso 700-800, token `--text`
- Seções/grupos: peso 600, token `--text`
- Campos/rótulos: peso 500, token `--text`
- Help text/hints: peso 400, token `--muted`
- Ação primária: `--brand-red`, peso 600
- Ação secundária: borda `--border`, peso 500

## Wireframe

### Região: Topo
- Eyebrow: Administração
- Título: Planos
- Ação primária: Novo plano, alinhada à direita
- Ação secundária: Voltar para Home

### Região: Conteúdo principal
- Grupo A: Indicadores — total, ativos, inativos, família, especiais e gateways
- Grupo B: Filtros — busca, público, frequência, ciclo, gateway e status
- Grupo C: Lista — cards/tabela responsiva com dados principais e ação "Detalhe"

### Região: Detalhe
- Cabeçalho com nome, código, status e ações
- Grupo A: Comercial
- Grupo B: Precificação
- Grupo C: Gateway e Stripe
- Grupo D: Uso do plano

### Região: Formulário
- Grupo A: Identificação
- Grupo B: Segmentação
- Grupo C: Precificação
- Grupo D: Gateway
- Grupo E: Exibição
- Ações: Cancelar (secundário), Salvar plano (primário)

### Estados da tela
- Carregando: renderização server-side sem estado intermediário visual específico
- Vazio: painel com mensagem "Nenhum plano encontrado"
- Com dados: lista de planos agrupada em cards responsivos
- Erro: mensagens globais e erros por campo em `--danger`

## Máquinas de estado

### Listagem de planos
- Estados: vazia, com dados, filtrada sem resultado
- Transições: request inicial -> queryset -> render vazio | render com dados
- Representação visual: painel vazio com ícone/texto ou lista com cards e contadores

### Formulário de plano
- Estados: inicial, inválido, salvando, salvo
- Transições: GET -> preenchimento -> POST inválido | POST válido -> redirect
- Representação visual: campos agrupados; erros por campo; mensagem de sucesso após redirect

### Exclusão de plano
- Estados: disponível, bloqueada por vínculos, concluída
- Transições: GET confirmação -> POST -> delete | ProtectedError
- Representação visual: alerta de risco; bloqueio com orientação para desativar quando houver uso

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
Validar `/home/`, `/planos/`, detalhe, formulário e exclusão em viewport desktop.

### Mobile
Validar os mesmos fluxos em viewport mobile, com foco em filtros, cards, botões e ausência de sobreposição.

### Console do navegador
Verificar ausência de erro JS crítico.

### Terminal
Verificar ausência de stack trace no servidor Django.

## Validação ORM

### Banco
Usar dados criados em teste; não executar migração.

### Shell checks
Não previsto para esta mudança sem schema.

### Integridade do fluxo
Confirmar que planos vinculados a `Membership` não são removidos.

## Validação de qualidade

### Sem hardcode
Filtros, rotas e URLs devem usar Django forms, `reverse`/`url` e choices do modelo.

### Sem estruturas condicionais quebradiças
Views devem delegar filtros e estatísticas para serviços auxiliares.

### Sem `except: pass`
Erros de exclusão protegida devem ser tratados explicitamente.

### Sem mascaramento de erro
`ProtectedError` deve gerar mensagem clara e manter o objeto.

### Sem comentários e docstrings desnecessários
Comentários só serão adicionados se houver decisão arquitetural não inferível.

## Evidências
- Red: `.\.venv\Scripts\python.exe manage.py test system.tests.test_plan_views system.tests.test_forms.PlanFormLayoutContractTestCase system.tests.test_home_dashboard.HomeDashboardTestCase.test_technical_admin_home_does_not_render_dead_staff_links --verbosity 2 --keepdb` falhou inicialmente por rotas `plan-*` inexistentes e ausência de agrupamentos em `PlanForm`.
- Green focado: o mesmo comando passou com 8 testes.
- Validação técnica: `.\.venv\Scripts\python.exe manage.py check` passou sem issues.
- Validação final após ajuste de estilo: `.\.venv\Scripts\python.exe manage.py check` e testes focados de planos/formulário passaram.
- Migrações em leitura: `.\.venv\Scripts\python.exe manage.py showmigrations system` mostrou apenas `[X] 0001_initial`.
- Estáticos: `.\.venv\Scripts\python.exe manage.py collectstatic --noinput` processou os novos assets de planos.
- Suíte completa: `.\.venv\Scripts\python.exe manage.py test --verbosity 2 --keepdb` passou com 207 testes.
- Browser DOM: login técnico, Home e link "Planos" validado em `http://127.0.0.1:8000/home/`; `/planos/` validado com KPIs, filtros, listagem e link de detalhe.
- Validação visual Playwright: desktop e mobile capturados em `C:\Users\whsf\AppData\Local\Temp\lvj-plans-validation\`.
- Console do navegador: sem erros críticos (`console_errors: []`, `page_errors: []`).
- Limpeza: usuário temporário `codex_plan_validation` e sessões associadas removidos.

## Implementado
- Rotas administrativas de planos em `/planos/`, `/planos/novo/`, `/planos/<pk>/`, `/planos/<pk>/editar/` e `/planos/<pk>/excluir/`.
- Atalho "Planos" liberado na Home.
- `PlanForm` expandido com campos de identificação, segmentação, precificação e gateway.
- `PlanListFilterForm` criado com busca, público, frequência, ciclo, meio de pagamento, gateway e status.
- Serviço de listagem com filtros server-side e estatísticas de planos.
- Tratamento explícito de `ProtectedError` na exclusão de planos vinculados a assinaturas.
- Templates administrativos de listagem, detalhe, formulário e confirmação de exclusão.
- CSS/JS próprios do módulo de planos.
- Testes de views, filtro, formulário, Home e exclusão protegida.

## Desvios do plano
- O Browser embutido validou navegação e DOM, mas a captura de screenshot por CDP excedeu timeout. A validação visual foi concluída com Playwright headless no mesmo servidor local.
- O teste antigo da Home foi ajustado para aceitar asset hasheado após `collectstatic`, validando `system/js/dashboard` em vez de `system/js/dashboard.js`.

## Pendências
- Nenhuma pendência funcional identificada nesta entrega.
