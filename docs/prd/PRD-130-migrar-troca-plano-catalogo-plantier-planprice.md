# PRD-130: Migrar troca de plano (upgrade/downgrade) para o catálogo PlanTier/PlanPrice

## Summary
Corrige mais uma regressão da mesma família das PRD-128/129: o botão "Trocar plano" desapareceu da home do cliente porque `build_plan_catalog`/`get_eligible_plans` (`system/services/plan_change.py`/`system/selectors/plan_eligibility.py`) só leem `SubscriptionPlan`, e as linhas não-veteranas desse modelo foram inativadas pela PRD-127. Qualquer cliente com `Membership.plan_price` (modelo novo) ou mesmo `Membership.plan` legado não-veterano vê um catálogo de troca vazio.

## Demand type
Correção de regressão (reportada pelo usuário: "trocar plano não está acessível, sumiu da tela do cliente").

## Current problem
- `get_eligible_plans` (`plan_eligibility.py`) consulta só `SubscriptionPlan.objects.filter(is_active=True)`; após a PRD-127, isso só retorna variantes Veterano.
- `build_plan_catalog` exclui `gateway_code="stripe_card"` e o plano atual, mas parte de um catálogo já vazio para não-veteranos — resultado: catálogo `[]`, template `{% if plan_change_catalog %}` nunca renderiza o botão.
- `calculate_plan_change`, `create_plan_change_order`, `apply_plan_change`, `get_last_paid_order_for_plan`, `refund_plan_change_leftover`, `serialize_plan_with_proration` assumem `SubscriptionPlan` em todo lugar (`membership.plan`, `RegistrationOrder.plan`).
- `PlanChangeSelectView` faz `int(request.POST.get("selected_plan"))` e busca só em `SubscriptionPlan`.
- `_handle_payment_event` (`asaas_webhooks.py` e `stripe_webhooks.py`) só chama `apply_plan_change` quando `order.plan_id` existe — uma ordem de troca para um `PlanPrice` (`order.plan_price_ref`) seria silenciosamente ignorada.

## Goal
Migrar toda a cadeia de troca de plano para o catálogo dual-source (`SubscriptionPlan` legado `sp:<pk>` + `PlanPrice` novo `pp:<pk>`), replicando o padrão já usado com sucesso nas PRD-127/128/129, preservando 100% da lógica de proração/crédito/estorno já testada.

## Context Ledger
### Files read in full
- `system/services/plan_change.py` (todas as funções relevantes)
- `system/views/plan_change_views.py`
- `system/selectors/plan_eligibility.py` (`get_eligible_plans`, `_build_audience_filter`, `PlanEligibilityContext`)
- `system/services/asaas_webhooks.py` / `system/services/stripe_webhooks.py` (branch `is_plan_change`)
- `static/system/js/home/dashboard.js` (`js-plan-change-*` — já usa `FormData`/valor de string, sem `parseInt`, não precisa mudança)

### Limitations found
- Frontend (`dashboard.js`/`dashboard.html`) já é agnóstico ao formato do ID (usa `input[name="selected_plan"]:checked".value` como string) — só o backend precisa mudar.

## Required skills
`lv-task-intake`, `lv-prd`, `lv-django-delivery`, `lv-cleanup-audit`

## Understanding approved
Usuário reportou o bug diretamente e pediu correção ("corrija").

## Scope
- `system/selectors/plan_eligibility.py`: nova função `get_eligible_plan_prices(context)` (equivalente a `get_eligible_plans` para `PlanPrice`, via `tier__audience`).
- `system/services/plan_change.py`: generalizar `calculate_plan_change`, `create_plan_change_order`, `apply_plan_change`, `get_last_paid_order_for_plan`, `refund_plan_change_leftover`, `serialize_plan_with_proration`, `build_plan_catalog` para aceitar `SubscriptionPlan` OU `PlanPrice`; `apply_plan_change` passa a chamar `recompute_family_discounts_for_person` após a troca (a pessoa pode mudar de tier).
- `system/views/plan_change_views.py`: `PlanChangeSelectView` resolve `selected_plan` via `resolve_catalog_plan`.
- `system/services/asaas_webhooks.py` / `system/services/stripe_webhooks.py`: branch `is_plan_change` reconhece `order.plan_price_ref_id` além de `order.plan_id`.
- Testes: `system/tests/test_plan_change.py`/`test_plan_change_views.py` estendidos com cenários `PlanPrice` (catálogo populado, upgrade, downgrade, crédito, estorno).

## Out of scope
- Migrar o campo `is_family_plan` legado (permanece inatingível, já documentado na PRD-129).

## Rules and constraints
- Sem migration de schema.
- Sem chamada real a gateway em teste automatizado.
- Preservar toda a suíte existente sem regressão.

## Test plan
- Catálogo de troca populado para cliente com `Membership.plan_price`.
- Downgrade/upgrade entre `PlanPrice` com proração correta, crédito e cobrança adicional.
- `PlanChangeSelectView` aceita `pp:<pk>`, rejeita id inválido, rejeita "mesmo plano atual".
- Webhook (Asaas/Stripe) aplica a troca quando a ordem referencia `plan_price_ref`.
- Suíte completa sem regressão; `manage.py check`.

## Implemented
- `system/selectors/plan_eligibility.py`: nova `get_eligible_plan_prices(context)`.
- `system/services/plan_change.py`: `_catalog_id_for_plan`, `_current_plan_reference`, `_assign_membership_plan` (helpers novos); `calculate_plan_change`, `create_plan_change_order`, `apply_plan_change` (+ chamada a `recompute_family_discounts_for_person`), `get_last_paid_order_for_plan`, `refund_plan_change_leftover`, `serialize_plan_with_proration`, `build_plan_catalog` generalizados para `SubscriptionPlan` OU `PlanPrice`.
- `system/views/plan_change_views.py::PlanChangeSelectView`: resolve `selected_plan` via `resolve_catalog_plan` (removida checagem duplicada de "mesmo plano", já coberta por `calculate_plan_change`).
- `system/services/asaas_webhooks.py` / `system/services/stripe_webhooks.py`: branch `is_plan_change` reconhece `order.plan_price_ref_id` além de `order.plan_id`.
- Testes: `system/tests/test_plan_change_plan_price.py` (6 novos); `system/tests/test_plan_change_views.py` atualizado para IDs de catálogo prefixados (`sp:<pk>`).
- **Correção adicional reportada pelo usuário após a primeira validação**: ao selecionar o filtro exato do plano atual (ex. Mensal + PIX, igual ao plano vigente), o catálogo não mostrava nada — o cliente esperava ver o próprio plano marcado como "Plano atual". Corrigido: `build_plan_catalog` agora inclui o plano atual no catálogo (via `serialize_plan_with_proration(current_plan, None, is_current=True)`, com um dict de proração neutro), e `templates/home/dashboard.html` renderiza esse card com badge "Plano atual", rádio desabilitado (não pode "trocar para si mesmo") e mensagem "Você já está neste plano" em vez do texto de proração. Teste novo: `test_current_plan_card_matches_its_own_filters`.

## Evidence
- `manage.py test system.tests.test_plan_change system.tests.test_plan_change_views` → 23 testes, `OK` (não-regressão, após ajustar 3 testes para o formato de id prefixado).
- `manage.py test system.tests.test_plan_change_plan_price` → 7 testes (6 + 1 da correção do plano atual), `OK`.
- `manage.py test` (suíte completa) → 551 testes, `OK`. `manage.py check` limpo.
- Validação visual no navegador interno: modal "Trocar plano" com filtro Mensal+PIX (igual ao plano vigente) agora mostra o card "Adulto 2x por semana — Plano atual — R$ 221,99 /mensal — Você já está neste plano" em vez de ficar vazio.
- `manage.py test` (suíte completa) → 550 testes, `OK`. `manage.py check` limpo.
- Validação visual no navegador interno com cliente real (`ana.teste.api@example.com`, `Membership.plan_price_id=1`): botão "Trocar plano" reapareceu na home; modal mostrou 15 opções reais do catálogo `PlanPrice` (antes: catálogo vazio, botão ausente); selecionar um plano mais caro criou corretamente um `RegistrationOrder` (`is_plan_change=True`, `plan_price_ref_id=5`, `plan_id=None`, total com proração correta) e retornou a URL de checkout (`/pagamentos/4/asaas-pix/`) — bloqueado apenas pela mesma limitação já conhecida do preview interno (não navega para domínio externo do Asaas), não uma regressão nova.

## Cleanup findings
Nenhum resíduo além do já documentado nas PRDs 128/129 (branch legado de `is_family_plan` permanece inatingível, fora de escopo).

## Final status
Concluída e validada — testes automatizados (550, suíte completa) + navegador interno com cliente real. O bug relatado ("Trocar plano sumiu da tela") está corrigido.
