# PRD-137: Recorrente Stripe ausente em ciclos longos + parcelamento Asaas quebrado no catálogo novo

## Summary
Duas falhas relacionadas à migração para o catálogo `PlanTier`/`PlanPrice` (PRD-127/128/129/130): (1) o plano recorrente Stripe nunca teve linhas de preço para semestral/anual — o arquivo de seed que as continha foi esvaziado na migração, então hoje só existe a linha mensal; (2) o cálculo de parcelamento Asaas (`asaas_checkout.py`) só lia `RegistrationOrder.plan` (catálogo legado `SubscriptionPlan`), então qualquer pedido do catálogo novo (`plan_price_ref`) caía silenciosamente para 1x, mesmo em ciclos trimestral/semestral/anual — por isso o parcelamento não aparecia nem na tela do LV nem na fatura gerada no Asaas.

## Demand type
Correção de bug (parcelamento Asaas) + lacuna de dado comercial (recorrente Stripe em ciclos longos), com documentação. Investigação solicitada após a correção de valores da PRD anterior (ajuste de preços Veterano/Individual/Kids/Juvenil).

## Current problem

### 1. Parcelamento Asaas ausente (bug de código)
- `system/services/asaas_checkout.py::_max_installments_for_order` e `get_installment_options_for_order` resolviam o ciclo de cobrança lendo exclusivamente `order.plan` (FK legada para `SubscriptionPlan`).
- Desde a PRD-129, o cadastro público cria `RegistrationOrder` com `plan_price_ref` (FK para `PlanPrice`) para Individual/Kids/Juvenil — `order.plan` fica `None` nesses pedidos.
- Com `plan is None`, o código caía em `cycle = "monthly"` → `INSTALLMENT_OPTIONS["monthly"] = [1]` → `CreateCreditCardChargeView.get()` via `len(options) <= 1` pulava direto para `_create_charge(installment_count=1)`, sem nunca renderizar a tela de escolha de parcelamento e sem nunca enviar `installmentCount` para o Asaas — por isso o parcelamento não aparecia nem no LV nem na fatura Asaas, para qualquer plano trimestral/semestral/anual pago com cartão desde a PRD-129 (Veterano, ainda em `SubscriptionPlan`, não era afetado).
- Bug reproduzido (Red) e corrigido (Green) nesta PRD — ver Evidence.

### 2. Recorrente Stripe só existe no ciclo mensal (lacuna de dado)
- O front-end (`register.js:1470-1472`) já exibe o card Stripe em qualquer aba de ciclo selecionada (mensal/trimestral/semestral/anual) quando o filtro "Cartão" está ativo — o mecanismo de exibição não está quebrado.
- O problema é que só existe UMA linha `PlanPrice` com `gateway_code="stripe_card"` por tier, sempre `billing_cycle="monthly"` (`static/initial_data/seed_system_initial_plan_prices.json`).
- Isso não é regressão desta migração: o arquivo `seed_system_initial_subscription_plans_stripe.json` (catálogo legado) também só teve linhas mensais desde a criação (commit `5acddfc`), nunca ofereceu semestral/anual.
- O commit `121eee6` ("Add plan tiers and membership pause flows") esvaziou esse arquivo (`[]`) ao migrar Individual/Kids/Juvenil para `PlanTier`/`PlanPrice` — mas a linha mensal do Stripe já tinha sido recriada no catálogo novo (`seed_system_initial_plan_prices.json`), então não há perda de funcionalidade, só a ausência histórica de semestral/anual.
- Para oferecer o recorrente como opção de fidelidade mais barata em ciclos longos (decisão de negócio do usuário), faltam `PlanPrice` novas com `gateway_code="stripe_card"` para `billing_cycle=semiannual` e `annual`, com valor comercial definido pelo usuário.

## Goal
1. Corrigir o cálculo de parcelamento Asaas para funcionar com pedidos de qualquer catálogo (`plan` legado ou `plan_price_ref` novo).
2. Documentar a causa raiz do recorrente Stripe ausente em ciclos longos e propor valores comerciais coerentes com o desconto já aplicado aos ciclos Asaas, para aprovação explícita antes de gravar no catálogo.

## Context Ledger
### Files read in full
- `system/services/asaas_checkout.py`
- `system/views/asaas_views.py`
- `system/models/registration_order.py`
- `templates/login/installment_select.html`
- `system/tests/test_asaas.py`
- `system/models/plan.py`
- `system/selectors/plan_eligibility.py`
- `system/services/registration_checkout.py`
- `static/initial_data/seed_system_initial_plan_prices.json`
- `static/initial_data/seed_system_initial_subscription_plans_stripe.json`
- `docs/prd/PRD-127-desconto-familia-tier-unico-precificacao.md`
- `docs/prd/PRD-117-fidelidade-contratual-planos-recorrentes.md`

### Adjacent files consulted
- `static/system/js/auth/register.js` (trecho `getFilteredPlans`/`planCycles`, linhas ~1449-1483)
- `docs/prd/PRD-129-migrar-cadastro-publico-catalogo-plantier-planprice.md` (índice)
- `system/urls.py` (rota `asaas-card-create`)
- Histórico git: `git log --oneline -- static/initial_data/seed_system_initial_subscription_plans_stripe.json` (commits `5acddfc`, `121eee6`)

### Internet / official documentation
- Não aplicável — bug de lógica interna do projeto, sem dependência de API/SDK externo nesta correção. O cálculo de parcelas usa o próprio `asaas_client.create_credit_card_payment` (`installmentCount`/`totalValue`), já implementado e testado em PRDs anteriores (referência: `docs/GUIA-PREENCHIMENTO-TESTE-CLIENTE.md`, PRD-058).

### Context7 / MCPs / tools verified
- Não aplicável nesta PRD — sem biblioteca/SDK novo envolvido.

### Limitations found
- Não há teste automatizado prévio cobrindo `_max_installments_for_order`/`get_installment_options_for_order`/`CreateCreditCardChargeView` com pedidos do catálogo novo — por isso o bug passou despercebido desde a PRD-129. Cobertura adicionada nesta PRD.
- Não há valor comercial definido pelo usuário para o recorrente Stripe em semestral/anual — proposta calculada nesta PRD, pendente de aprovação explícita (ver "Pending").
- Ambiente local sem `STRIPE_SECRET_KEY`/gateway Asaas sandbox real conectado nesta sessão — validação do parcelamento foi feita simulando a view (`RequestFactory`) e mockando `asaas_client`, sem chamada real ao Asaas.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
Usuário escolheu, entre as opções apresentadas: implementar o bug de parcelamento (ponto 3) diretamente, e para o recorrente Stripe (ponto 2) — "proponho valores e você aprova": calcular valores de semestral/anual coerentes com o padrão de desconto já usado, documentar a proposta nesta PRD, e só gravar no catálogo após aprovação explícita dos números.

## Execution prompt
### Persona
Agente Django sênior atuando em correção de bug de checkout financeiro (Asaas) e modelagem de precificação, com atenção a não regressão dos fluxos de cadastro público e troca de plano já entregues nas PRDs 126-135.

### Action
Corrigir `asaas_checkout.py` para resolver o ciclo de cobrança via `plan` OU `plan_price_ref`; corrigir bug correlato no template de parcelamento (`order.plan.name` inexistente); documentar e propor valores para o recorrente Stripe em semestral/anual.

### Context
`RegistrationOrder` já tem os dois FKs (`plan` legado, `plan_price_ref` novo) desde a PRD-127 Fase 4 — o padrão de resolver "legado OU novo" já existe em outros pontos do código (`Membership.effective_tier`, `resolve_catalog_plan`) e foi reaproveitado aqui via `_billing_cycle_for_order`.

### Constraints
- Sem inventar valor comercial para o recorrente Stripe sem aprovação explícita do usuário — só propor.
- Sem alterar o mecanismo de exibição do card Stripe no front-end (já funciona corretamente).
- Sem migration incremental — nenhuma mudança de schema nesta PRD.
- Teste antes do código: reproduzir o bug (Red) antes de corrigir (Green).

### Acceptance criteria
- [x] `_max_installments_for_order`/`get_installment_options_for_order` retornam o parcelamento correto para pedidos com `plan_price_ref` preenchido (catálogo novo).
- [x] `CreateCreditCardChargeView` renderiza a tela de escolha de parcelamento (`installment_select.html`) para esses pedidos, em vez de pular direto para 1x.
- [x] `create_credit_card_charge_for_order` envia o `installmentCount` correto ao Asaas para pedidos do catálogo novo.
- [x] Nome do plano exibido corretamente na tela de parcelamento para ambos os catálogos (bug correlato encontrado e corrigido).
- [x] Valores comerciais do recorrente Stripe para semestral/anual gravados no catálogo — aprovado pelo usuário ("implemente") e gravado.
- [x] `sync_plan_to_stripe` funciona com `PlanPrice` além de `SubscriptionPlan` — descoberto que não funcionava (bug adicional), corrigido e testado (sem chamada real ao Stripe).

### Expected evidence
- Teste Red (bug reproduzido revertendo a correção via `git stash`) e Green (suíte após correção) com comando e saída reais.
- Simulação da view real (`RequestFactory`) confirmando renderização da tela de parcelamento com opções corretas.
- Suíte completa sem regressão.

### Output format
Correção implementada e testada (parcelamento) + proposta documentada aguardando aprovação (recorrente Stripe) + limitações registradas.

## Scope
- Corrigir `system/services/asaas_checkout.py` (`_billing_cycle_for_order`, `_max_installments_for_order`, `get_installment_options_for_order`).
- Corrigir `system/views/asaas_views.py` (`select_related` incluindo `plan_price_ref`).
- Corrigir `templates/login/installment_select.html` (nome do plano ausente para catálogo novo, e campo inexistente `plan.name` para o legado).
- Adicionar testes de regressão (`system/tests/test_asaas.py`).
- Documentar e propor valores do recorrente Stripe semestral/anual (implementação da gravação fica para depois da aprovação).

## Out of scope
- Fidelidade contratual/carência do recorrente Stripe (`PRD-117`, já registrada como pendente separada).
- Qualquer mudança de preço nos ciclos Asaas (PIX/Cartão) — já corrigidos na entrega anterior.
- Sincronização real com o Stripe (criação de Product/Price) — só ocorre quando `STRIPE_PLAN_SYNC_ENABLED=True`, fora do escopo local desta correção.

## Impacted files
`system/services/asaas_checkout.py`, `system/views/asaas_views.py`, `templates/login/installment_select.html`, `system/tests/test_asaas.py`, `system/tests/test_commands.py`, `static/initial_data/seed_system_initial_plan_prices.json`, `system/services/stripe_sync.py`, `system/management/commands/seed_system_initial_plan_prices.py`, `system/tests/test_stripe_sync.py`.

## Risks and edge cases
- Pedidos antigos (pré-PRD-129) com `plan` preenchido continuam resolvendo pelo caminho legado — `_billing_cycle_for_order` prioriza `order.plan_id` antes de `plan_price_ref_id`, preservando o comportamento anterior.
- Pedidos sem nenhum dos dois FKs (caso não deveria existir, mas o modelo permite `null=True` em ambos) caem em `"monthly"` (1x) — comportamento seguro por padrão, igual ao anterior.
- Se o usuário aprovar os valores propostos do recorrente Stripe, será necessário decidir se o gateway Stripe real (`STRIPE_PLAN_SYNC_ENABLED`) deve sincronizar Product/Price novos — fora do escopo local, mas a marcar como follow-up quando aplicável.

## Rules and constraints
- Toda resolução de catálogo legado vs. novo deve seguir o padrão já estabelecido (`plan` tem prioridade quando preenchido; senão `plan_price_ref`) — não duplicar lógica de resolução em múltiplos lugares sem necessidade.
- Nenhum valor comercial é gravado sem aprovação explícita do usuário (obtida via `AskUserQuestion` — "Proponho valores e você aprova" — e confirmada com "implemente").

## Plan
1. Reproduzir o bug do parcelamento com teste (Red) usando um pedido `plan_price_ref`-based.
2. Corrigir `_billing_cycle_for_order`/`_max_installments_for_order`/`get_installment_options_for_order`.
3. Corrigir `select_related` na view e o nome do plano no template.
4. Confirmar Green com suíte focada + suíte completa.
5. Validar a view real via simulação (`RequestFactory`) sem chamada Asaas real.
6. Documentar e propor valores do recorrente Stripe; aguardar aprovação para gravar.
7. Aprovação recebida ("implemente") — calcular `base_monthly_net_price`/`cycle_discount_percentage` exatos por engenharia reversa da fórmula (mesmo método da correção de preços anterior), gravar no seed e no banco local, validar no catálogo servido pelo wizard.

## Test plan
### Tests to author
- `AsaasCheckoutPlanPriceCatalogTests` (`system/tests/test_asaas.py`): `_max_installments_for_order` resolve 6x para `plan_price_ref` semestral; `get_installment_options_for_order` retorna `[1, 2, 3, 6]`; `create_credit_card_charge_for_order` envia `installment_count=6` ao Asaas (mock).
- `PlanTierPriceSeedCommandTestCase.test_seed_creates_tiers_and_prices_idempotently` (`system/tests/test_commands.py`) estendido: contagem total de `PlanPrice` (36→44) e preço exato das 4 novas linhas Stripe semestral/anual (`adult-2x`, `kids-5x`).

### Execution authorization
Aprovado ("investigue e implemente") para o bug de parcelamento; recorrente Stripe aprovado em duas etapas — primeiro "propor valores e você aprova", depois "implemente" (confirmação explícita dos números da tabela em "Pending").

### Execution evidence
- Red: `git stash` do arquivo corrigido + `.\.venv\Scripts\python.exe manage.py test system.tests.test_asaas.AsaasCheckoutPlanPriceCatalogTests --verbosity 2` → **3 falhas** (`1 != 6`, `[1] != [1, 2, 3, 6]`, `1 != 6`), confirmando o bug real antes da correção.
- Green: `git stash pop` (restaura a correção) + mesmo comando → **3 testes, OK**.
- Regressão focada: `.\.venv\Scripts\python.exe manage.py test system.tests.test_asaas --verbosity 2` → **28 testes, OK**.
- Simulação real da view (`RequestFactory` + `SessionStore` com `pending_checkout_order_id`, sem mock de `asaas_client` pois `.get()` não chama o gateway): pedido `PlanPrice` semestral (`adult-2x`, Asaas Cartão) → `CreateCreditCardChargeView.get()` retorna `status_code=200` renderizando `installment_select.html` com opções `1x`, `2x`, `3x`, `6x` presentes no HTML — antes da correção, esse mesmo pedido pulava direto para `_create_charge(installment_count=1)` sem nunca renderizar a tela.
- Mesmo teste confirmou `order-summary__plan` exibindo `"Adulto 2x por semana"` corretamente após a correção do template (antes: campo `plan.name` inexistente, sempre vazio).
- Após aprovação dos valores do recorrente Stripe: `.\.venv\Scripts\python.exe manage.py seed_system_initial_plan_prices` → 4 linhas `criado` (semestral/anual × adult-2x/adult-5x/kids-2x/kids-5x) com preço exato (`1195.00`, `2265.00`, `1250.00`, `2390.00`) — conferido centavo a centavo via `compute_gross_price`.
- Catálogo servido pelo wizard (`GET /register/`, `#reg-plan-catalog-json`) confirmado com as 12 linhas `stripe_card` (4 tiers × 3 ciclos: mensal/semestral/anual) e os valores exatos.
- Regressão completa (após ajustar contagem em `test_commands.py`): `.\.venv\Scripts\python.exe manage.py test --verbosity 1` → **644 testes, OK**.
- `.\.venv\Scripts\python.exe manage.py check` → sem issues.

## Visual validation
Parcelamento: não aplicável via clique real no navegador nesta sessão (fluxo depende de sessão de checkout autenticada com `pending_checkout_order_id`), exercitado via simulação de view/`RequestFactory`. Recorrente Stripe: confirmado via `fetch('/register/')` no navegador interno (servidor `preview_start`), extraindo `#reg-plan-catalog-json` e conferindo as 12 linhas `stripe_card` com os preços exatos aprovados.

## ORM validation
Pedido de teste criado/consultado/removido via ORM local (`PlanPrice`, `PlanTier`, `RegistrationOrder`, `Person`) para a simulação da view de parcelamento — sem resíduo deixado no banco local. Seed do recorrente Stripe reaplicado localmente (`seed_system_initial_plan_prices`), confirmando as 4 novas linhas com preço exato.

## Quality validation
`manage.py check`: sem issues. Suíte completa: 644 testes, OK.

## Evidence
Ver "Execution evidence" acima.

## Implemented
- `system/services/asaas_checkout.py`: nova função `_billing_cycle_for_order(order)` — resolve `order.plan.billing_cycle` (legado) ou `order.plan_price_ref.billing_cycle` (novo), com fallback `"monthly"`. `_max_installments_for_order` e `get_installment_options_for_order` passaram a usá-la em vez de ler `order.plan` diretamente.
- `system/views/asaas_views.py`: `select_related("plan", "plan_price_ref", "person")` nas 3 consultas de `RegistrationOrder` em `CreateCreditCardChargeView`/`AsaasPixQrCodeView` (evita N+1 ao resolver o tier no template).
- `templates/login/installment_select.html`: `{{ order.plan.name }}` (campo inexistente, sempre vazio) → `{{ order.plan.display_name|default:order.plan_price_ref.tier.display_name }}` — funciona para os dois catálogos.
- `system/tests/test_asaas.py`: nova classe `AsaasCheckoutPlanPriceCatalogTests` com 3 testes cobrindo o cenário do catálogo novo.
- `static/initial_data/seed_system_initial_plan_prices.json`: 8 novas linhas `gateway_code=stripe_card` (semestral + anual × `adult-2x`/`adult-5x`/`kids-2x`/`kids-5x`), com `base_monthly_net_price`/`cycle_discount_percentage` calculados por engenharia reversa de `compute_gross_price` para reproduzir exatamente os valores aprovados (R$ 1.195,00/2.265,00 para 2x; R$ 1.250,00/2.390,00 para 5x/Kids/Juvenil).
- `system/tests/test_commands.py`: `test_seed_creates_tiers_and_prices_idempotently` estendido com a nova contagem (44) e asserções de preço exato para as 4 linhas Stripe novas.
- `system/services/stripe_sync.py`: `sync_plan_to_stripe` generalizado para funcionar com `SubscriptionPlan` (legado) OU `PlanPrice` (novo) — antes só funcionava com `SubscriptionPlan` hardcoded (`SubscriptionPlan.objects.filter(pk=plan.pk).update(...)`), quebrando com `AttributeError` para `PlanPrice` (sem campos `code`/`description`). Novas funções `_plan_code(plan)` (deriva `tier.code-gateway_code-billing_cycle` quando não há `code` próprio) e `_plan_description(plan)` (retorna `None` quando o modelo não tem o campo). A persistência do resultado usa `type(plan).objects.filter(...)` em vez do modelo fixo.
- `system/management/commands/seed_system_initial_plan_prices.py`: passou a sincronizar com o Stripe real quando `STRIPE_PLAN_SYNC_ENABLED=True` (mesmo padrão já usado em `seed_system_initial_subscription_plans_stripe.py`), só para linhas `gateway_code="stripe_card"`.
- `system/tests/test_stripe_sync.py` (novo): 5 testes — regressão de `SubscriptionPlan` (criação de Product/Price, preço zero pulado, erro sem `STRIPE_SECRET_KEY`) + 2 testes novos de `PlanPrice` (criação de Product/Price com `plan_code` derivado do tier, e substituição/arquivamento de Price quando o valor muda). Bug reproduzido em Red (`AttributeError: 'PlanPrice' object has no attribute 'description'`) antes da correção.
- `system/tests/test_commands.py`: 2 novos testes no seed de preços — erro sem `STRIPE_SECRET_KEY` quando `STRIPE_PLAN_SYNC_ENABLED=True`; sincronização chamada só para linhas `stripe_card` (mock de `sync_plan_to_stripe`, sem chamada real).

## Cleanup findings
- Nenhum resíduo introduzido. O bug do `plan.name` inexistente no template era pré-existente (afetava também pedidos legados) e foi corrigido como parte do mesmo fluxo tocado — não expande o escopo, é o mesmo template/linha da correção principal.

## Follow-up PRDs
- `PRD-117` (fidelidade contratual/carência do recorrente Stripe) continua pendente, sem relação direta com esta correção.
- Rodar `seed_system_initial_plan_prices` com `STRIPE_PLAN_SYNC_ENABLED=True` em HG/produção (criação real de Product/Price no Stripe) exige autorização de ambiente e credenciais reais — não executado nesta sessão local (sem `STRIPE_SECRET_KEY` de HG/produção disponível aqui).

## Deviations from plan
Nenhum desvio no escopo original — a sincronização Stripe para `PlanPrice` foi adicionada como extensão explicitamente autorizada pelo usuário ("implementar a sincronização agora, local, testada, sem chamada real") após a descoberta de que o mecanismo não existia para o modelo novo.

## Pending
Nenhuma pendência de implementação local. Sincronização real com o Stripe (Product/Price em HG/produção, `STRIPE_PLAN_SYNC_ENABLED=True`) exige autorização de ambiente e execução separada — nenhuma chamada real ao Stripe foi feita nesta PRD. `PRD-117` (fidelidade contratual/carência) segue como pendente separada e não bloqueia esta entrega.

**Valores aprovados e gravados** (referência — ver "Implemented"):

| Tier | Ciclo | Asaas Cartão (referência) | Recorrente Stripe (aprovado) | Desconto vs. Asaas Cartão |
|---|---|---|---|---|
| Individual Adulto 2x | Semestral | R$ 1.260,00 | R$ 1.195,00 | ~5,2% |
| Individual Adulto 2x | Anual | R$ 2.388,00 | R$ 2.265,00 | ~5,1% |
| Individual Adulto 5x / Kids / Juvenil | Semestral | R$ 1.320,00 | R$ 1.250,00 | ~5,3% |
| Individual Adulto 5x / Kids / Juvenil | Anual | R$ 2.520,00 | R$ 2.390,00 | ~5,2% |

## Final status
**Concluída.** Bug de parcelamento Asaas corrigido, testado (Red→Green) e validado via simulação real da view. Recorrente Stripe em ciclos longos: valores aprovados pelo usuário e gravados no catálogo. Descoberta adicional durante o fechamento: `sync_plan_to_stripe` não suportava `PlanPrice` (só `SubscriptionPlan` legado) — corrigido, testado (Red→Green) e sem chamada real ao Stripe (mock em todos os testes; execução real em HG/produção fica para quando houver autorização de ambiente e credenciais). Suíte completa: 651 testes, OK. `manage.py check`: sem issues.
