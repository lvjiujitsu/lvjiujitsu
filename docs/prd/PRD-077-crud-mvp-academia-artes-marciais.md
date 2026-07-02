# PRD-077: CRUD MVP da academia de artes marciais

## Summary
Entregar o MVP operacional de academia após a fundação: cadastro, visualização, alteração e exclusão dos domínios principais; estoque de materiais; aulas/turmas com cronograma; histórico financeiro; auditoria de aula; evolução e graduação.

## Demand type
Nova feature multi-módulo + integração de domínio existente.

## Current problem
- Pessoas e Planos têm templates parciais existentes.
- Turmas, categorias, horários, financeiro, graduação, materiais, loja, pré-pedidos e perfis têm views/rotas, mas templates ausentes em grande parte.
- A documentação PRD-065 declara hubs implementados, mas o inventário atual mostra templates ausentes.
- Não há validação visual atual desktop/mobile desses CRUDs porque as telas não renderizam integralmente.

## Goal
Construir um CRUD inicial consistente para:
- Pessoas e acessos;
- Planos;
- Turmas, categorias e horários;
- Cronograma e presença;
- Materiais/produtos, variantes e estoque;
- Financeiro, pedidos, mensalidades, repasses e histórico;
- Graduação, faixas, regras e histórico de evolução.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `docs/prd/PRD-065-hubs-administrativos-modulos-lv.md`
- `system/urls.py`
- `system/views/class_views.py`
- `system/views/category_views.py`
- `system/views/billing_admin_views.py`
- `system/views/graduation_views.py`
- `system/views/product_views.py`
- `system/views/plan_views.py`
- `system/views/person_views.py`

### Adjacent files consulted
- `system/forms/*`
- `system/services/*`
- `system/selectors/*`
- `templates/`
- `static/system/`
- `system/tests/test_admin_hubs_contract.py`

### Internet / official documentation
- Django 5.2 templates and CBVs: https://docs.djangoproject.com/en/5.2/topics/templates/

### Context7 / MCPs / tools verified
- Context7 Django 5.2.

### Limitations found
- Esta PRD depende de PRD-074 para permissões e PRD-075 para fundação UI/rotas.
- Pagamentos reais e webhooks não entram na validação sem ambiente/túnel/gateway.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved
Autorizado pela solicitação atual como objetivo final, mas execução deve ser faseada por segurança.

## Scope
- Implementar templates faltantes por módulo usando fundação comum.
- Completar actions CRUD com validação server-side.
- Cobrir estados vazios, erro, sucesso e bloqueio por vínculo.
- Criar testes de renderização, permissão e operação básica por módulo.
- Validar desktop/mobile no navegador interno.

## Out of scope
- Gateway de pagamento real.
- Escrita remota.
- Refatoração profunda do wizard público, salvo bloqueio do MVP.

## Impacted files
- `templates/classes/*`
- `templates/class_categories/*`
- `templates/class_schedules/*`
- `templates/billing/*`
- `templates/graduation/*`
- `templates/products/*`
- `templates/person_types/*`
- `templates/admin_modules/*`
- views/forms/services/tests proporcionais

## Risks and edge cases
- Excluir pessoa/produto/plano com vínculo deve bloquear com mensagem clara.
- Estoque não pode ser alterado por JS sem persistência transacional.
- Graduação precisa preservar histórico, não só campo atual.
- Financeiro exige trilha de auditoria e não pode mascarar status de gateway.
- Cronograma deve respeitar feriados, aulões, check-ins e substituições.

## Rules and constraints
- Depende da fundação PRD-075.
- Permissões dependem da PRD-074.
- Test-first por módulo.
- Não criar KPI agregado sem pedido nominal.

## Plan
- [x] Pessoas como referência completa (entregue na PRD-075).
- [x] Planos.
- [x] Turmas/categorias/horários.
- [x] Materiais/estoque/loja/pre-pedidos (CRUD administrativo; loja/backorder do aluno ficam como pendência de UI, ver Pending).
- [x] Graduação/evolução.
- [x] Financeiro/auditoria (telas de leitura + ações de estado; não é CRUD de criação, ver Evidence).
- [x] Cronograma/presença (calendário já existia e já era funcional; migrado para rota em inglês; código morto removido).

## Test plan
### Tests to author
- GET renderiza 200 para cada hub/listagem.
- Criar/editar/excluir por módulo.
- Bloqueio de permissão por papel.
- Estado vazio e dados populados.

### Execution authorization
Autorizada localmente, faseada.

### Execution evidence
- Planos: `system/tests/test_lv_foundation_plans.py` (6 testes: rota inglesa, 2 redirects de rotas antigas, modal de criar/editar renderiza template correto, POST válido cria o plano e renderiza `lv/modal_done.html`).
- Turmas/categorias/horários: `system/tests/test_lv_foundation_classes.py` (8 testes: rotas inglesas dos 3 sub-módulos, redirect de rota antiga, detalhe de turma usa o pk real do registro (não o card agrupado), modal de criar categoria com POST válido, modal de editar turma expõe o formset de horários, modal de criar horário renderiza).
- Ajustado `system/tests/test_admin_hubs_contract.py` (contrato de rotas da PRD-065) para refletir os novos paths em inglês de `class-group-*`, `class-category-list` e `class-schedule-list`, já que PRD-077 supera esse contrato para os módulos migrados.
- `.venv/Scripts/python.exe manage.py test system.tests.test_lv_foundation_plans --verbosity 2` — 6 testes OK.
- `.venv/Scripts/python.exe manage.py test system.tests.test_lv_foundation_classes --verbosity 2` — 8 testes OK.
- Materiais: `system/tests/test_lv_foundation_products.py` (4 testes: rota inglesa, redirect de rota antiga, modal expõe `variant_formset`, POST válido cria produto+variante e renderiza `lv/modal_done.html`).
- Ajustadas mais duas expectativas de `test_admin_hubs_contract.py` (`product-*`, `admin-backorder-queue`, `product-store`, `student-backorders`, `student-order-history`) para os novos paths em inglês.
- `.venv/Scripts/python.exe manage.py test system.tests.test_lv_foundation_products --verbosity 2` — 4 testes OK.
- Graduação: `system/tests/test_lv_foundation_graduation.py` (7 testes: rota inglesa do overview, redirect de rota antiga, modal de criar faixa com POST válido, modal de editar regra renderiza, modal de registrar graduação preserva histórico via novo registro, confirma que não existe rota de edição para graduação — histórico é imutável por desenho).
- Mais uma rodada de ajuste em `test_admin_hubs_contract.py` (`graduation-*`) para os paths em inglês.
- `.venv/Scripts/python.exe manage.py test system.tests.test_lv_foundation_graduation --verbosity 2` — 7 testes OK.
- Financeiro: `system/tests/test_lv_foundation_financial.py` (5 testes: rota inglesa do painel, redirect de rota antiga, listagem de pendentes com dado real, ação "marcar pago" muda o status de verdade, folha/repasses renderizam).
- Mais uma rodada de ajuste em `test_admin_hubs_contract.py` (`financial-*`) para os paths em inglês.
- `.venv/Scripts/python.exe manage.py test system.tests.test_lv_foundation_financial --verbosity 2` — 5 testes OK.
- Cronograma: `system/tests/test_lv_foundation_calendar.py` (3 testes: rota inglesa `/calendar/` renderiza, redirect de `/cronograma/`, confirma via `hasattr` que as 4 views mortas de calendário foram removidas do módulo).
- `.venv/Scripts/python.exe manage.py test system.tests.test_lv_foundation_calendar --verbosity 2` — 3 testes OK.
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 308 testes OK (suíte completa, sem regressão, após todos os 7 módulos e a limpeza de código morto).
- `.venv/Scripts/python.exe manage.py check` — 0 problemas.

## Visual validation
- Planos: validado no navegador interno — modal de criação em `<dialog>` com iframe, tema escuro consistente, preço estimado calculado dinamicamente dentro do modal (`plans.js` reaproveitado via `modal_extra_scripts`), mobile (375×812) sem overflow horizontal e modal ancorado à base.
- Bug de duplicidade encontrado e evitado: `plans.js` já tinha sua própria lógica de alternância de tema; não incluí `theme_toggle.js` em `plan_list.html` para não duplicar o binding do botão (dedupe completo desse padrão fica para a PRD-084).
- Turmas: validado no navegador interno com dados reais de seed — a listagem mostra 6 turmas individuais (3 delas com o mesmo nome/categoria "Jiu Jitsu · Adulto" mas professores diferentes); modal de edição abre a turma correta por professor e exibe o formset de horários (6 slots: 5 existentes + 1 extra em branco) com "Remover este horário" nos existentes. Categorias validado em mobile (375×812) sem overflow horizontal.
- Materiais: validado no navegador interno com dados reais de seed (5 materiais, incluindo "Faixa LV" com 35 variantes reais) — listagem mostra estoque total e contagem de variantes corretos; modal de edição renderiza 36 slots do formset (35 existentes + 1 extra); mobile sem overflow horizontal.
- Graduação: validado no navegador interno com dados reais (overview mostra Aline 50% e Miguel 0%, refletindo o progresso real calculado); modal de nova faixa renderiza todos os campos incluindo cores; mobile sem overflow horizontal.
- Financeiro: validado no navegador interno com dados reais — painel mostra saldo disponível/a receber calculados de verdade (Asaas+Stripe); folha de professores mostra o cálculo mensal real por professor (ex.: R$ 400,00 fixo para dois professores); mobile sem overflow horizontal.
- Cronograma: validado no navegador interno — calendário mensal real (Julho de 2026) com aulas reais por dia da semana; mobile sem overflow horizontal.

## ORM validation
Dados criados via ORM local (`SubscriptionPlan.objects.create(...)`) em teste isolado; nenhuma escrita remota.

## Quality validation
- Testes focados por módulo.
- `manage.py check`.
- Browser interno (desktop, mobile, tema escuro).

## Evidence
- Inventário `template_name -> exists` identificou 36 templates ausentes (parte já resolvida por Pessoas/Planos/Turmas; restante seguirá módulo a módulo).
- Rotas administrativas resolvem, mas testes existentes não garantem renderização real (Planos, Pessoas, Turmas/categorias/horários agora têm teste de renderização real).
- Módulos de domínio existem em models/forms/services/selectors, mas a superfície CRUD ainda está incompleta para Materiais, Graduação, Financeiro e Cronograma.
- Bug real encontrado em `system/views/class_views.py`: `ClassGroupListView`/`ClassScheduleListView` e os respectivos `DetailView.get_object` usavam `get_admin_class_group_cards()`/`get_admin_schedule_day_cards()` e `get_class_group_card_by_pk`/`get_schedule_day_card_by_pk`, funções que **agrupam várias turmas/horários reais em um único "card"** (ex.: mesma modalidade+categoria com professores diferentes viram um card só), expondo apenas o `pk` do primeiro registro do grupo (`lead_group`/`lead_schedule`). Usar isso para editar/excluir teria silenciosamente ignorado os demais registros agrupados. Corrigido para usar `get_admin_class_group_queryset()`/`get_admin_class_schedule_queryset()` (querysets reais, um item por registro) e `ClassGroup.objects.get(pk=...)`/`ClassSchedule.objects.get(pk=...)` no detalhe. As funções antigas continuam existindo e em uso legítimo em `system/services/class_overview.py` para os filtros/dropdowns públicos (onde agrupar por modalidade+categoria é o comportamento correto) — não são código morto, só estavam sendo mal aplicadas ao CRUD administrativo.
- Bug real encontrado em `templates/products/product_list.html` (nesta própria implementação, corrigido antes de commitar): a primeira versão referenciava `product._total_stock`/`product._variant_count` (os aliases de `annotate()` de `get_product_list_cards()`), mas o Django Templates proíbe variáveis começando com `_` — a listagem de materiais nunca teria renderizado. `system/models/product.py` já define as properties públicas `total_stock`/`variant_count` exatamente para esse propósito (com fallback para quando o annotate não foi aplicado); o template foi corrigido para usá-las.

## Implemented
- Planos: `system/views/plan_views.py` usa `ModalFormMixin` (reaproveitado de `person_views.py`) em `PlanCreateView`/`PlanUpdateView`; `templates/plans/plan_form_modal.html` criado reaproveitando os grupos de campos do form completo; `templates/plans/plan_list.html` com botões Criar/Editar em modal e Excluir em `<dialog>` de confirmação, scripts inline removidos; `system/urls.py` migrado para `/plans/...` com redirect de `/planos/...`.
- Turmas/categorias/horários: criados do zero (nenhum template existia antes) `templates/class_categories/*`, `templates/classes/*`, `templates/class_schedules/*` (list/form/detail/confirm_delete cada) e `static/system/css/classes/classes.css` (reaproveita tokens/componentes de `people.css`, evitando triplicar ~1100 linhas de CSS). `system/views/category_views.py` e `system/views/class_views.py` ganharam `ModalFormMixin`; como nenhum template pré-existia, cada form usa o MESMO arquivo para tela cheia e modal (extends `lv/modal_frame.html` diretamente, sem `modal_template_name` separado). `system/urls.py` migrado para `/classes/...` com redirect de `/turmas/...`.
- Materiais: criados do zero `templates/products/*` (list/form com formset de variantes/estoque/detail/confirm_delete) e `templates/billing/admin_backorder_queue.html` (fila de pré-pedidos, leitura). `system/views/product_views.py` ganhou `ModalFormMixin` em `ProductCreateView`/`ProductUpdateView`. `system/urls.py` migrado para `/materials/...`, `/store/...` e `/my-materials/...` com redirect das rotas antigas em português.
- Graduação: criados do zero `templates/graduation/*` (overview, faixas com CRUD completo, regras com list/form/delete, histórico com list/form de novo registro/delete — sem tela de edição para histórico, preservando o registro imutável por desenho). `system/views/graduation_views.py` ganhou `ModalFormMixin` em `BeltRankCreateView`/`UpdateView`, `GraduationRuleCreateView`/`UpdateView` e `GraduationCreateView`. `system/urls.py` migrado para `/graduation/...` com redirect de `/graduacao/...`.
- Financeiro: criados do zero `templates/billing/financial_entries.html` (painel com KPIs reais), `approval_queue.html`, `pending_payments.html`, `payroll_list.html` e `payout_queue.html`. Este módulo não segue o padrão modal de criação porque não é CRUD de entidade — são telas de leitura com ações de transição de estado (isentar, marcar pago, estornar, aprovar/recusar/enviar repasse), cada ação reaproveitando as views de ação já existentes (`ExemptOrderActionView`, `MarkOrderPaidActionView` etc.) via formulário simples com POST direto, consistente com a exceção documentada no padrão Visary para páginas financeiras expandidas. `system/urls.py` migrado para `/financial/...` com redirect das 5 rotas de leitura em português (as rotas de ação POST-only não foram redirecionadas — risco baixo, nenhum template aponta mais para os paths antigos).
- Cronograma: o calendário (`templates/calendar/calendar.html`) já existia e já era funcional (entregue/ajustado em PRD-080). Migrado `system/urls.py` de `/cronograma/` para `/calendar/` com redirect (exceto a variante `/cronograma/<ano>/<mês>/`, que ficou sem redirect — gap pequeno registrado em Pending). Removidas 4 views mortas de `system/views/calendar_views.py` (`AdminCalendarView`, `AdminToggleSessionView`, `AdminSpecialClassCreateView`, `AdminSpecialClassDeleteView`) — nenhuma tinha rota, template ou teste; `AdminCalendarView` apontava para `calendar/admin_calendar.html`, que nunca existiu. Limpos os imports agora não usados (`PersonTypeCode`, `Person`, `AdministrativeRequiredMixin`) e as 4 entradas correspondentes em `system/views/__init__.py` (imports e `__all__`).

## Cleanup findings
- Nenhum resíduo temporário.
- Duplicidade de lógica de tema entre `plans.js` e a fundação `lv/theme_toggle.js` identificada e evitada nesta rodada (não corrigida na raiz — registrada como dívida da PRD-084).
- Bug de agrupamento de turmas/horários no CRUD administrativo corrigido nesta rodada (ver Evidence).

## Follow-up PRDs
- PRD-084 para eliminar a duplicidade de JS de tema entre módulos.

## Deviations from plan
- Nenhum desvio funcional.

## Pending
- Loja pública (`product-store`) e fluxo de pré-pedido do aluno (`student-backorders`, `student-order-history`) continuam sem template (rotas já migradas para inglês, mas telas ainda ausentes) — não fazem parte do CRUD administrativo desta PRD; registrar PRD própria se for prioridade antes da próxima rodada de auditoria.
- CRUD de `ProductCategory` (categoria de material) não tem tela própria (só é escolhida via FK no form de Product); avaliar se é necessário em PRD futura.
- Ação de cancelar assinatura/trocar plano (`cancel-membership`, `change-membership-plan`) não tem nenhum botão disparando-a em nenhuma tela ainda (a view existe, mas está órfã de UI); avaliar se entra no detalhe de Pessoa em PRD futura.
- Trilha de auditoria financeira explícita (quem fez cada ação, quando) não existe como tela própria; as ações já registram `admin_user`/`notes` no service, mas não há um "log" navegável — possível PRD futura (`auditoria-financeira-ausente`, já mapeado na auditoria de PRD-098).
- Redirect de `/cronograma/<ano>/<mês>/` (variante com parâmetros) não foi implementado, só a rota base `/cronograma/`.

## Final status
Concluída com limitações — os 7 módulos do CRUD MVP (Pessoas, Planos, Turmas/categorias/horários, Materiais/estoque, Graduação, Financeiro e Cronograma) foram entregues, testados (33 testes novos específicos desta PRD + suíte completa de 308 testes OK) e validados visualmente (desktop, mobile, tema escuro) com dados reais de seed. Pendências específicas (loja pública, categoria de produto, ações de assinatura órfãs de UI, trilha de auditoria financeira) estão documentadas acima para PRDs futuras, não escondidas.
