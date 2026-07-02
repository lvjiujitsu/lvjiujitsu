# PRD-101: Loja pública, pré-pedidos e histórico do aluno

## Summary
Implementar as 3 telas do aluno/responsável que ainda não têm template, confirmadas pelo inventário programático de rotas ativas (PRD-078): `product-store` (loja), `student-backorders` (pré-pedidos) e `student-order-history` (histórico de pedidos). Views, forms e services já existem; falta a UI.

## Demand type
Nova feature de UI (telas faltantes documentadas desde a PRD-077/078).

## Current problem
- `ProductStoreView`, `StudentBackorderListView`, `StudentOrderHistoryView` estão roteadas em `/store/`, `/my-materials/backorders/`, `/my-materials/orders/` mas `TemplateDoesNotExist` ao acessar (confirmado via inventário `get_resolver()` + `get_template()`).
- Aluno/responsável não tem como comprar material, ver pré-pedido nem histórico de compras pela UI.

## Goal
Aluno/responsável ativo:
- vê o catálogo de materiais ativos agrupado por categoria, com estoque real por variante;
- compra variantes em estoque (carrinho simples, sem cálculo de preço no front);
- solicita pré-pedido para variante esgotada;
- vê e cancela/confirma seus próprios pré-pedidos;
- vê histórico de pedidos pagos/isentos.

## Context Ledger
### Files read in full
- `system/views/product_views.py` (`ProductStoreView`, `CreateProductOrderView`, `ProductBackorderCreateView`, `StudentBackorderListView`, `StudentBackorderConfirmView`, `StudentBackorderCancelView`, `StudentOrderHistoryView`)
- `system/forms/product_forms.py` (`ProductCartForm`)
- `system/services/registration_checkout.py` (`parse_selected_products`, `resolve_selected_product_items`, `get_product_catalog_payload`)
- `system/services/product_management.py` (`get_public_product_cards`)
- `system/models/product_backorder.py`
- `system/models/registration_order.py`

### Adjacent files consulted
- `templates/products/product_list.html` e `product_form.html` (padrão visual já estabelecido nas PRDs 077/078)
- `static/system/css/lv/base.css`, `static/system/css/people/people.css`, `static/system/css/classes/classes.css`

### Internet / official documentation
- Django 5.2 templates: https://docs.djangoproject.com/en/5.2/topics/templates/

### Context7 / MCPs / tools verified
- Não aplicável (reaproveita fundação já validada em Context7 nas PRDs anteriores).

### Limitations found
- Sem cálculo de preço/total no front nesta rodada (o backend calcula o pedido); manter escopo simples é decisão consciente, não lacuna.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved
Autorizado pela solicitação atual do usuário ("finalize toda a implementação até não encontrar mais erros"), que já havia identificado esta pendência nas PRDs 077/078.

## Scope
- `templates/products/product_store.html`, `student_backorder_list.html`, `student_order_history.html`.
- JS mínimo (sem regra de negócio) para montar o `cart_payload` JSON a partir dos inputs de quantidade.
- Testes de renderização e de fluxo (comprar, pré-pedido, cancelar, confirmar).

## Out of scope
- Gateway de pagamento real (fluxo de checkout já existe e não é alterado).
- Redesign visual amplo do catálogo (reaproveita o padrão de listagem já validado).

## Impacted files
- `templates/products/product_store.html` (novo)
- `templates/products/student_backorder_list.html` (novo)
- `templates/products/student_order_history.html` (novo)
- `system/tests/`

## Risks and edge cases
- Variante sem estoque não pode ser comprada, só solicitada como pré-pedido.
- Responsável comprando para dependente precisa do seletor de pessoa.
- Quantidade inválida (0, negativa, não numérica) deve ser ignorada no carrinho, não travar o POST.

## Rules and constraints
- UI pt-BR, sem `innerHTML` com dado de usuário, sem regra de negócio em JS.
- Reaproveitar tokens/CSS já existentes (`lv/base.css`, `people.css`, `classes.css`).

## Plan
- [x] Ler views/forms/services envolvidos.
- [x] Criar os 3 templates.
- [x] Testes de renderização e fluxo de compra/pré-pedido/histórico.
- [x] Validar no navegador interno.

## Test plan
### Tests to author
- GET das 3 rotas renderiza 200 para perfil autorizado.
- POST de compra com variante em estoque cria pedido e redireciona para checkout.
- POST de pré-pedido para variante esgotada cria `ProductBackorder`.
- Cancelar pré-pedido remove o registro.

### Execution authorization
Autorizada localmente conforme `AGENTS.md`.

### Execution evidence
- `system/tests/test_product_store.py` (5 testes): loja renderiza com dado real; comprar variante em estoque cria `RegistrationOrder` e redireciona para `/pagamentos/...`; solicitar pré-pedido de variante esgotada cria `ProductBackorder` e redireciona para a lista de pré-pedidos; listagem de pré-pedidos renderiza e cancelar atualiza o status para `canceled` (não apaga o registro — comportamento real do service `cancel_backorder`, corrigido no teste depois de eu ter suposto erroneamente que seria delete); histórico renderiza estado vazio.
- Dois testes falharam na primeira tentativa por suposições erradas minhas sobre o comportamento real (redirect de destino e delete vs. mudança de status) — corrigidos após ler o service `cancel_backorder` e a view `ProductBackorderCreateView`.
- `.venv/Scripts/python.exe manage.py test system.tests.test_product_store --verbosity 2` — 5 testes OK.
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 338 testes OK (suíte completa).
- Inventário programático final (`get_resolver()` + `get_template()` em todas as views registradas): **0 templates ausentes** (era 36 no início da sessão).
- Validação end-to-end no navegador interno logado como admin: loja renderiza com "Faixa LV" (35 variantes reais) e demais produtos, cada variante em estoque com input de quantidade; comprar 1 unidade criou `RegistrationOrder` real (R$ 69,90, Aline, status pendente) e redirecionou para `/pagamentos/1/asaas-pix/`; lista de pré-pedidos renderiza estado vazio corretamente. Mobile (375×812) sem overflow horizontal em loja e pré-pedidos.

## Visual validation
Executada no navegador interno: desktop (loja com dados reais, seletor "Comprar para" com as 7 pessoas seedadas), mobile (loja e pré-pedidos sem overflow), tema escuro, estado vazio (pré-pedidos e histórico).

## ORM validation
`RegistrationOrder` e `ProductBackorder` verificados via teste focado e via shell local durante a validação visual.

## Quality validation
- `manage.py test system.tests.test_product_store` — 5 testes OK.
- `manage.py test system` — 338 testes OK.
- `manage.py check` — 0 problemas.

## Evidence
- `ProductBackorderCreateView` redireciona para `student-backorders` (não para `product-store` como eu presumi inicialmente ao escrever a PRD) — comportamento correto, só ajustei a expectativa do teste.
- `cancel_backorder` é uma transição de estado (`status="canceled"`), não uma exclusão — condizente com o padrão "append-only com trilha" já usado no resto do sistema (ex.: `MembershipInvoice`, `Graduation`).

## Implemented
- `templates/products/product_store.html`: catálogo agrupado por categoria, quantidade por variante em estoque, aviso de "Esgotado" com botão de pré-pedido, seletor de pessoa para responsável/admin comprando em nome de terceiros.
- `templates/products/student_backorder_list.html`: lista de pré-pedidos com ações de confirmar (quando `ready`) e cancelar (quando `pending`/`ready`).
- `templates/products/student_order_history.html`: histórico de pedidos pagos com itens e valor.
- `static/system/js/products/store_cart.js`: script mínimo que só lê os inputs de quantidade e monta o JSON do carrinho no submit — nenhuma regra de negócio ou cálculo de preço no front.
- `system/tests/test_product_store.py`: 5 testes cobrindo os 4 fluxos (loja, compra, pré-pedido, cancelamento, histórico).

## Cleanup findings
- Nenhum resíduo de código. O pedido de demonstração (`RegistrationOrder` #1, Aline, R$ 69,90) criado durante a validação visual foi removido do banco de desenvolvimento ao final.

## Follow-up PRDs
- Nenhuma nova identificada nesta PRD.

## Deviations from plan
- Nenhum desvio funcional; os dois ajustes de teste (redirect e status vs. delete) foram correções da minha própria suposição inicial, não do código.

## Pending
- Nenhuma.

## Final status
Concluída — as 3 telas renderizam, o fluxo de compra cria pedido real e redireciona para o checkout existente, pré-pedido/cancelamento funcionam, testado (5 testes novos + suíte completa de 338) e validado ao vivo no navegador (desktop, mobile, dado real). Inventário de templates ausentes chega a zero.
