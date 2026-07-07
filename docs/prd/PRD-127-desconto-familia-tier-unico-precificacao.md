# PRD-127: Desconto família como modificador de tier único (rework de precificação)

## Summary
Substituir o modelo atual de planos — em que "Individual" e "Família" são `SubscriptionPlan` totalmente independentes, com preços digitados à mão sem relação matemática entre si — por um modelo de **tier comercial único** (`PlanTier`) com **preços versionados** (`PlanPrice`) e um **desconto família percentual** aplicado dinamicamente quando 2+ pessoas do grupo familiar compartilham o mesmo tier. Remover o dependente reverte automaticamente à cobrança cheia, sem troca manual de plano.

## Demand type
Rework de modelo de dados e regra de negócio de precificação, com impacto direto em Stripe (cobrança recorrente real) — mudança de payment-critical, exige aprovação explícita por fase antes de código (`AGENTS.md` §10).

## Current problem
- `SubscriptionPlan.is_family_plan`/`is_loyalty_plan` resolvem para **linhas de preço inteiramente independentes**. O `base_monthly_net_price` de cada linha é digitado manualmente no JSON de seed (`static/initial_data/seed_system_initial_subscription_plans_values.json`, `seed_system_initial_subscription_plans_stripe.json`) — não existe fórmula ou relação percentual entre o preço Individual e o preço Família do mesmo tier/frequência/gateway/ciclo. Hoje há **54 `SubscriptionPlan` rows** (48 Asaas + 6 Stripe).
- Migrar o titular de Individual para Família hoje passa pelo mesmo mecanismo de qualquer troca de plano (`system/services/plan_change.py::apply_plan_change`): troca a FK `Membership.plan` inteira, reseta `current_period_start/end`, pode gerar `MembershipCredit` de proration. Do ponto de vista do usuário, "aparece um plano a mais" em vez de um desconto sobre o mesmo produto.
- Remover o dependente não reverte a cobrança automaticamente — exige nova troca manual de plano de volta para Individual.
- Não há histórico/versionamento de preço: editar `SubscriptionPlan.price`/`base_monthly_net_price` em uma linha ativa muda retroativamente o que é exibido para Memberships antigos que apontam para a mesma linha (sem grandfathering).
- `PlanEligibilityContext` (`system/selectors/plan_eligibility.py`) já conta adultos/kids ativos do grupo familiar via `PersonRelationship`, mas essa contagem só decide se o plano família aparece no catálogo — não aciona desconto.

## Goal
1. Um único produto comercial (`PlanTier`) por combinação audience × frequência, com um `family_discount_percentage` embutido.
2. Preços versionados (`PlanPrice`) por tier × forma de pagamento × gateway × ciclo, imutáveis uma vez usados — alteração de valor cria uma nova linha, preservando histórico e grandfathering.
3. `Membership` referencia `PlanPrice` (não mais `SubscriptionPlan` "Família"), com `family_discount_applied`/`billed_price` recomputados automaticamente sempre que o grupo familiar muda (dependente adicionado/removido).
4. Assinatura Stripe recorrente reflete o desconto via Coupon/Discount da própria Stripe API sobre a subscription, em vez de trocar o Price object — reversão automática quando o discount é removido.
5. UI mostra o preço original riscado + preço com desconto quando aplicável, com os dois valores reais.

## Context Ledger
### Files read in full
- `AGENTS.md`, `CLAUDE.md`, `docs/PRD-STANDARD.md`, `docs/prd/README.md`
- `docs/prd/PRD-126-prevenir-cobranca-duplicada-mesmo-cartao-dependente.md` (compatibilidade de campos em `Membership`)
- `system/models/plan.py`
- `system/utils/plan_commercial.py`
- `system/services/plan_change.py`
- `system/selectors/plan_eligibility.py`
- `system/models/coupon.py`
- `system/services/coupon.py`
- `system/services/plan_management.py`
- `system/forms/plan_forms.py`
- `system/management/commands/seed_system_initial_subscription_plans.py`
- `static/initial_data/seed_system_initial_subscription_plans_values.json` (estrutura, não todas as 48 entradas)
- `static/initial_data/seed_system_initial_subscription_plans_stripe.json` (estrutura, não todas as 6 entradas)
- `system/services/stripe_sync.py`
- `system/tests/test_plan_commercial.py`
- `system/tests/test_veteran_plan.py`

### Adjacent files consulted
- `system/services/registration_checkout.py` (uso de `is_family_plan`/`plan.stripe_price_id`)
- `system/services/dependent_registration.py` (fluxo `family_upgrade`/`dependent_own`)
- `system/services/stripe_checkout.py` (merge/staggered da PRD-126 usam `plan.stripe_price_id`)
- `system/forms/dependent_forms.py`, `system/forms/registration_forms.py`
- `templates/plans/plan_detail.html`, `templates/plans/plan_list.html`
- `static/system/js/dependents/dependent_registration.js`, `static/system/js/auth/register.js`

### Internet / official documentation
- Stripe — aplicar coupon a uma subscription existente via `POST /v1/subscriptions/:id` (parâmetro `discounts`/`coupon`), atualização com proration configurável (`proration_behavior`): `https://docs.stripe.com/api/subscriptions/create`, `https://docs.stripe.com/billing/subscriptions/discounts`.
- Stripe — remover discount de uma subscription: `DELETE /v1/subscriptions/:id/discount`: `https://docs.stripe.com/api/discounts/object`, `https://docs.stripe.com/api/discounts/delete`.

### Context7 / MCPs / tools verified
- Context7 `/websites/stripe` consultado para: (1) aplicar coupon/discount a subscription existente — confirmado, suportado via update da subscription; (2) remover discount de subscription — confirmado, endpoint `DELETE /v1/subscriptions/:id/discount` dedicado. Ambos os mecanismos existem na API atual do Stripe, validando a decisão de design de usar Coupon/Discount em vez de troca de Price.

### Limitations found
- Ambiente local não tem `STRIPE_SECRET_KEY` real para os registros de teste — validação do lado Stripe será por mocks/fixtures, sem chamada real.
- Não há dado de produção a migrar neste ambiente (SQLite local, reconstruído via ciclo destrutivo) — a "migração de dados existentes" descrita no Plan é necessária apenas para HG/produção reais; localmente, os seeds são reescritos diretamente para o novo modelo.
- "Veterano" (`is_loyalty_plan`) tem elegibilidade por tempo de casa + aprovação manual administrativa (`VeteranTenureCalculationTestCase`, `VeteranManualApprovalTestCase`, `VeteranPlanDecisionView`) — estruturalmente diferente de "desconto por headcount familiar". Fica fora do escopo desta PRD; ver Follow-up.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
Usuário escolheu explicitamente "rework completo, de maneira consistente e com boas práticas para ficar bem implementado até para novos preços, valores, alteração de tabela, histórico etc." — a opção mais profunda entre as três apresentadas, com histórico/versionamento de preço.

## Execution prompt
### Persona
Agente Django sênior atuando em modelagem de domínio financeiro e integração Stripe, com atenção a migração de dado, idempotência de webhook e não regressão de fluxos de checkout/troca de plano já existentes (incluindo os recém-entregues na PRD-126).

### Action
Introduzir `PlanTier` e `PlanPrice` como novo modelo de precificação; migrar `Membership` para referenciar `PlanPrice`; implementar recomputo automático de desconto família; refletir o desconto na assinatura Stripe via Coupon/Discount; atualizar UI para exibir preço original riscado + preço com desconto.

### Context
O sistema já tem contagem de grupo familiar (`PlanEligibilityContext`) e um precedente de versionamento de preço no lado Stripe (`stripe_sync.py::_ensure_price`, arquiva preço antigo e cria novo quando não bate mais com o plano) — a fórmula de preço (`_compute_price`) e o padrão de arquivamento devem ser reaproveitados, não reinventados.

### Constraints
- Sem remover/quebrar os campos que a PRD-126 adicionou em `Membership` (`stripe_subscription_id`, `stripe_subscription_item_id`).
- Sem alterar o comportamento de "Veterano" nesta entrega.
- Sem migration incremental — alteração de schema entra na baseline única (`system/migrations/0001_initial.py`), regenerada via ciclo destrutivo local.
- Sem chamar Stripe real nesta entrega — testes usam mocks.
- Fase a fase: cada fase abaixo precisa de evidência (testes + `manage.py check`) antes de avançar para a próxima; não implementar todas as fases em uma tacada sem checkpoint.

### Acceptance criteria
- [ ] `PlanTier` existe com `family_discount_percentage`; `PlanPrice` existe com preço calculado pela mesma fórmula de `_compute_price()`, vinculado a um `PlanTier`.
- [ ] Alterar o preço de um tier cria uma nova `PlanPrice` (nunca edita `base_monthly_net_price` de uma linha já usada por algum `Membership`/`RegistrationOrder`); a linha antiga fica `is_active=False` com `effective_until` preenchido.
- [ ] `Membership.plan_price` substitui `Membership.plan` (`SubscriptionPlan`) sem quebrar `stripe_subscription_id`/`stripe_subscription_item_id` da PRD-126.
- [ ] Adicionar um dependente ao mesmo tier do titular aciona `family_discount_applied=True` e recomputa `billed_price` de todos os Memberships do grupo — sem troca manual de plano, sem `MembershipCredit` de proration como hoje.
- [ ] Remover o dependente reverte `family_discount_applied=False` e `billed_price` ao valor cheio automaticamente.
- [ ] Assinatura Stripe recorrente recebe/perde o desconto via Coupon/Discount da API quando o grupo familiar muda (mock em teste; sem chamada real).
- [ ] UI (wizard de dependente, tela de planos) mostra preço original riscado + preço com desconto quando `family_discount_applied=True`, com os dois valores reais.
- [ ] Seeds reescritos geram `PlanTier`+`PlanPrice` diretamente, sem duplicar linha "Família" como produto separado.
- [ ] "Veterano" continua funcionando exatamente como hoje (nenhuma regressão nos testes de `test_veteran_plan.py`).
- [ ] Testes focados por fase + suíte completa sem regressão; `manage.py check` sem issues.

### Expected evidence
- Comando e resultado real de teste (Red antes do código de produção, Green depois) por fase.
- ORM local confirmando `PlanTier`/`PlanPrice`/`Membership.plan_price`/`billed_price` recomputados corretamente ao adicionar/remover dependente.
- Mock de chamada Stripe Coupon/Discount (sem chamada real).
- Validação visual no navegador interno da exibição "de/por".

### Output format
Implementação faseada + evidências reais por fase + limitações não validadas.

## Scope
- **Fase 1 — Modelo de dados**: `PlanTier`, `PlanPrice`, migração de `Membership.plan`→`Membership.plan_price` + `family_discount_applied`/`billed_price`. Ciclo destrutivo local (schema).
- **Fase 2 — Recomputo automático**: gatilho em `PersonRelationship` (criação/remoção RESPONSIBLE_FOR) que recalcula `family_discount_applied`/`billed_price` via `PlanEligibilityContext`. Cobre PIX/Asaas Cartão (recomputo local, sem Stripe).
- **Fase 3 — Stripe Coupon/Discount**: aplicar/remover desconto na subscription Stripe quando o recomputo da Fase 2 envolve um `Membership` com `stripe_subscription_id`. Testes com mock, sem chamada real.
- **Fase 4 — Serviços/fluxos dependentes**: `plan_change.py`, `plan_management.py`, `dependent_registration.py`, `registration_checkout.py`, `stripe_checkout.py` (PRD-126) e formulários (`plan_forms.py`, `dependent_forms.py`) apontando para `PlanPrice`/`PlanTier` em vez de `SubscriptionPlan`.
- **Fase 5 — Seeds e admin**: reescrever os 3 seeds de plano para gerar `PlanTier`+`PlanPrice`; adaptar CRUD administrativo (`plan_management.py`, `templates/plans/`) para o novo modelo.
- **Fase 6 — UI "de/por"**: exibir preço original riscado + preço com desconto no wizard de dependente e na tela de planos, usando os valores reais de `PlanPrice`/`billed_price`.
- Cada fase implementa, testa e valida antes de avançar para a próxima; usuário aprova o início de cada fase.

## Out of scope
- "Veterano" (`is_loyalty_plan`) — mantém o modelo atual de linha separada nesta entrega; candidato a rework simétrico futuro (ver Follow-up).
- Migração de dado real em HG/produção — esta PRD cobre o rework local; migração de Membership reais em ambiente remoto exige PRD e autorização de ambiente separadas.
- Novos valores comerciais/preços (a PRD não define quanto deve custar cada tier — só a mecânica de como o desconto é calculado e versionado).
- Alterar o fluxo Asaas de geração de cobrança além do necessário para ler `PlanPrice` em vez de `SubscriptionPlan`.

## Impacted files
`system/models/plan.py`, `system/models/membership.py`, `system/migrations/0001_initial.py`, `system/selectors/plan_eligibility.py`, `system/services/plan_change.py`, `system/services/plan_management.py`, `system/services/registration_checkout.py`, `system/services/dependent_registration.py`, `system/services/stripe_sync.py`, `system/services/stripe_checkout.py`, `system/services/membership.py`, `system/forms/plan_forms.py`, `system/forms/dependent_forms.py`, `system/forms/registration_forms.py`, `system/admin.py`, `system/management/commands/seed_system_initial_subscription_plans*.py`, `static/initial_data/seed_system_initial_subscription_plans*.json`, `templates/plans/plan_detail.html`, `templates/plans/plan_list.html`, `templates/dependents/dependent_registration.html`, `static/system/js/dependents/dependent_registration.js`, `static/system/js/auth/register.js`, testes correspondentes.

## Risks and edge cases
- **Proration na transição**: hoje trocar pra família gera `MembershipCredit`; no novo modelo, a mudança de `billed_price` no meio do ciclo precisa de uma regra explícita (cobrar diferença pro-rata na próxima fatura vs. aplicar só no próximo ciclo) — decisão de negócio a confirmar antes da Fase 2.
- **Stripe Coupon por percentual dinâmico**: se `family_discount_percentage` variar por tier, cada tier precisa de seu próprio Coupon Stripe (ou um Coupon único reaproveitado quando o percentual coincidir) — evitar duplicar Coupons desnecessariamente no Stripe.
- **Concorrência**: duas pessoas do mesmo grupo familiar podendo ter Memberships em tiers diferentes (ex. um adulto 2x, outro 5x) — `family_discount_percentage` vive no tier, então o desconto só se aplica dentro do mesmo tier; confirmar se a regra de negócio realmente é "por tier" ou "por grupo familiar independente do tier" (ambiguidade a esclarecer na Fase 1).
- **Dado histórico de `MembershipInvoice`**: faturas já emitidas referenciam `Membership`, não `PlanPrice` diretamente — confirmar que o histórico financeiro não muda retroativamente ao trocar `plan_price` de uma Membership existente.
- **Webhooks da PRD-126** (fatura multi-linha, subscription compartilhada) precisam continuar funcionando com `Membership.plan_price` no lugar de `Membership.plan` — qualquer leitura de `membership.plan.stripe_price_id` no código atual precisa apontar para `membership.plan_price.stripe_price_id`.

## Rules and constraints
- `PlanPrice` nunca é editado in-place uma vez referenciado por `Membership`/`RegistrationOrder` — alteração de valor sempre cria nova linha.
- `family_discount_percentage` é decisão de tier, não de Membership individual.
- Desconto Stripe é sempre refletido via Coupon/Discount da subscription, nunca por troca de Price.
- Nenhuma migration incremental.

## Plan
Ver "Scope" (Fases 1 a 6). Cada fase: escrever teste (Red) → implementar mínimo → `manage.py check` → suíte focada → suíte completa → validação visual quando aplicável → checkpoint de aprovação antes da próxima fase.

## Test plan
### Tests to author
- Fase 1: criação de `PlanTier`/`PlanPrice`; imutabilidade (nova linha ao "alterar" preço já usado); `Membership.plan_price` substitui `plan` sem quebrar campos da PRD-126.
- Fase 2: adicionar dependente no mesmo tier aciona `family_discount_applied`/`billed_price` corretos; remover dependente reverte; grupo com 1 pessoa não aplica desconto.
- Fase 3: mock de aplicação/remoção de Coupon/Discount na subscription Stripe ao recomputar.
- Fase 4: `plan_change.py`/`dependent_registration.py`/`registration_checkout.py`/`stripe_checkout.py` funcionando com `PlanPrice`.
- Fase 5: seeds geram `PlanTier`+`PlanPrice` sem duplicar linha família; admin CRUD funcional.
- Fase 6: template renderiza preço riscado + preço com desconto corretamente.
- Regressão: `test_veteran_plan.py` sem alteração de resultado.

### Execution authorization
Fase 1 aprovada e executada em 2026-07-06 ("implemente"). Fases 2 a 6 seguem pendentes de novo checkpoint.

### Execution evidence (Fase 1)
- `system/tests/test_plan_tier_pricing.py` (novo, 11 testes): criação de `PlanTier` com `family_discount_percentage`; `_compute_price`/`compute_gross_price` calcula `price` corretamente com taxa fixa e percentual do gateway; `monthly_reference_price` preenchido para ciclos multi-mês; `family_price()` aplica o desconto do tier; imutabilidade — editar campos de preço de uma `PlanPrice` NÃO referenciada é permitido, editar uma REFERENCIADA por `Membership` levanta `ValueError`, arquivar (`is_active`/`effective_until`) uma referenciada continua permitido; `Membership.plan` aceita `null` e pode referenciar só `plan_price`; `Membership.recompute_billed_price()` calcula `billed_price` com e sem desconto família.
- Comando: `.\.venv\Scripts\python.exe manage.py test system.tests.test_plan_tier_pricing --verbosity 2` → 11 testes, OK.
- Regressão: `.\.venv\Scripts\python.exe manage.py test --verbosity 1` → 500 testes (489 pré-existentes + 11 novos), OK.
- `.\.venv\Scripts\python.exe manage.py check` → sem issues.
- Ciclo destrutivo executado (`clear_migrations.py` + `makemigrations`) para incluir `PlanTier`/`PlanPrice` e os novos campos de `Membership` na baseline única.

### Execution evidence (Fases 2 e 3)
- `system/tests/test_family_pricing.py` (novo, 11 testes): pessoa sozinha não recebe desconto; 2 pessoas no mesmo tier recebem `family_discount_applied`/`billed_price` corretos; 2 pessoas em tiers diferentes não recebem desconto; remover o vínculo reverte o desconto para ambos; sincronização Stripe só é chamada quando o estado do desconto muda (não repete chamada em recomputo idempotente); `apply_family_discount` reaproveita coupon existente e cria um novo quando ausente; `remove_family_discount` chama `delete_discount`; sem `stripe_subscription_id` é no-op; sem `STRIPE_SECRET_KEY` levanta `StripeDiscountError`; teste de integração via `DependentRemoveView` (cliente de teste Django, POST real) confirma reversão de `billed_price` para titular e dependente.
- Comando: `.\.venv\Scripts\python.exe manage.py test system.tests.test_family_pricing --verbosity 2` → 11 testes, OK.
- Regressão: `.\.venv\Scripts\python.exe manage.py test --verbosity 1` → 511 testes (500 pré-existentes + 11 novos), OK.
- `.\.venv\Scripts\python.exe manage.py check` → sem issues.

### Execution evidence (Fase 4 — interop legado + wiring do wizard)
- 2 novos testes em `LegacyPlanTierInteropTestCase` (`test_family_pricing.py`): titular com `Membership.plan` legado (`SubscriptionPlan` não-loyalty) + dependente com `Membership.plan_price` novo, mesmo audience/frequência → ambos recebem o desconto corretamente (`effective_tier` casa os dois); Membership com plano Veterano nunca recebe desconto (fica com `billed_price=None`, nunca tocado pelo recomputo).
- 2 novos testes em `PlanPriceDependentRegistrationTestCase` (`test_dependent_registration.py`): POST real ao `dependent-add` selecionando um catálogo `pp:<pk>` resolve `financial_mode=dependent_own` automaticamente e não grava `PreRegistration.selected_plan` (FK legada fica `None`, snapshot guarda o id prefixado); `finalize_dependent_registration` com `selected_plan_obj` sendo um `PlanPrice` cria a Membership do dependente com `plan_price_id` correto e aciona o recomputo automático — titular e dependente terminam com `family_discount_applied=True` e `billed_price` igual a `price.family_price()`.
- 9 testes pré-existentes em `test_dependent_registration.py` e 1 em `test_commands.py` ajustados para o novo formato de `selected_plan` (`sp:<pk>`/`pp:<pk>` em vez de pk cru) e para os novos valores de preço formula-driven (ex. `loyalty-2x-asaas-card-monthly` R$ 212,63 em vez do R$ 230,38 do antigo `individual-2x`, já que Individual saiu do `SubscriptionPlan`).
- Comando: `.\.venv\Scripts\python.exe manage.py test system.tests.test_dependent_registration system.tests.test_family_pricing system.tests.test_commands --verbosity 1` → todos OK.
- Regressão final: `.\.venv\Scripts\python.exe manage.py test --verbosity 1` → **517 testes, OK**.
- `.\.venv\Scripts\python.exe manage.py check` → sem issues.
- Ciclo destrutivo executado novamente (`RegistrationOrder.plan_price_ref` + `PlanPrice` unique constraint) e seeds de referência completos rodados localmente (`db.sqlite3` reconstruído com sucesso, incluindo os novos `seed_system_initial_plan_tiers`/`_plan_prices`).

## Visual validation
- Fase 1: não aplicável (sem UI).
- Fase 4: navegador interno (`http://localhost:8000`), login como titular de teste com `Membership.plan_price` ativo e `stripe_subscription_id` preenchido. Wizard de dependente (`/dependents/add/?modal=1`) até a etapa "Plano do dependente", filtro "Cartão": catálogo mostra **`dep-plan-catalog-json` com 36 entradas (16 SubscriptionPlan Veterano + 20 PlanPrice), zero com `is_family_plan=true`**. Cards renderizados na etapa 5: apenas "Individual" (Asaas Cartão R$ 230,37 e Stripe recorrente R$ 230,37) — nenhum card "Família". Selecionar o card Stripe recorrente resolveu automaticamente `financial_mode=dependent_own`, `checkout_action=stripe_card`, `selected_plan=pp:9`. Bloco "Como cobrar o cartão do dependente?" (PRD-126) renderizou corretamente integrado, com "fundir" habilitado (titular tem assinatura Stripe ativa). Console do navegador sem erros.

## ORM validation
Fase 1 coberta pelos 11 testes de `test_plan_tier_pricing.py`. Fase 4 coberta pelos testes de `LegacyPlanTierInteropTestCase` e `PlanPriceDependentRegistrationTestCase`.

## Quality validation
`manage.py check` sem issues em todas as fases. Suíte completa final: 517 testes, OK.

## Evidence
Ver "Execution evidence" de cada fase acima.

## Implemented (Fase 1)
- `compute_gross_price()` extraído de `SubscriptionPlan._compute_price()` (`system/models/plan.py`) — fórmula compartilhada, sem duplicação; `SubscriptionPlan` (Veterano) continua usando a mesma fórmula via `_compute_price()`, agora delegando para a função compartilhada.
- `PlanTier` (`system/models/plan.py`): identidade do produto comercial (audience × frequência) + `family_discount_percentage`.
- `PlanPrice` (`system/models/plan.py`): preço versionado por tier × forma de pagamento × ciclo × gateway, com `effective_from`/`effective_until`, campos Stripe próprios, e **guarda de imutabilidade**: `_guard_immutability()` bloqueia alteração de campos de preço (`tier`, `payment_method`, `billing_cycle`, `base_monthly_net_price`, `cycle_discount_percentage`, `gateway_fixed_fee`, `gateway_percentage_fee`) quando a linha já está referenciada por algum `Membership` — levanta `ValueError`; campos não-financeiros (`is_active`, `effective_until`) continuam editáveis via `archive()`.
- `PlanPrice.family_price()` calcula o preço com desconto a partir de `tier.family_discount_percentage`.
- `Membership.plan` (FK para `SubscriptionPlan`) passou a ser `null=True`/`blank=True` — Veterano e qualquer código legado continuam funcionando sem alteração (campo continua obrigatório na prática para esses fluxos, só a constraint de banco ficou permissiva para viabilizar o novo caminho).
- `Membership.plan_price` (FK para `PlanPrice`, nullable), `Membership.family_discount_applied` (bool) e `Membership.billed_price` (Decimal, nullable) — novos campos para o caminho tier+desconto.
- `Membership.recompute_billed_price()` — método que calcula `billed_price` a partir de `plan_price`/`family_discount_applied`, reutilizável pela Fase 2.
- `PlanTier`/`PlanPrice`/`compute_gross_price` exportados em `system/models/__init__.py`.
- **Não alterado nesta fase**: `RegistrationOrder` continua referenciando só `SubscriptionPlan` (sem `plan_price`) — a extensão de `RegistrationOrder` fica para a Fase 4, quando os serviços de checkout passarem a criar pedidos contra `PlanPrice`.

## Implemented (Fase 2 — recomputo automático local)
- `system/selectors/plan_eligibility.py`: `get_family_group_members(person)` — wrapper público sobre `_get_family_group_members` já existente, sem duplicar lógica de resolução de grupo familiar.
- `system/services/family_pricing.py` (novo): `recompute_family_discounts_for_person(person)` — agrupa os `Membership` ativos (com `plan_price` preenchido) do grupo familiar por `PlanTier`; aplica `family_discount_applied=True` quando 2+ pessoas compartilham o mesmo tier, `False` caso contrário; recalcula `billed_price` via `Membership.recompute_billed_price()`; só dispara sincronização Stripe quando o estado do desconto realmente muda (evita chamadas redundantes).
- Gatilhos conectados: `system/services/registration.py::_create_relationship` (toda criação de vínculo `RESPONSIBLE_FOR` recomputa o grupo do `source_person`); `system/views/dependent_views.py::DependentRemoveView` (remoção do vínculo recomputa tanto o titular quanto o dependente removido, garantindo que a mensalidade do dependente também reverta).
- Nota de arquitetura (atualizada após a Fase 4): os gatilhos de relacionamento (criação/remoção) cobrem a maior parte dos casos; a Fase 4 acrescentou um gatilho adicional logo após a ativação da Membership do dependente (`_create_paid_plan_order`), porque nesse fluxo a Membership do dependente só existe DEPOIS que a relação já foi criada — sem esse segundo gatilho, o desconto só seria aplicado na próxima alteração do grupo familiar, não imediatamente após o cadastro pago.
- `Membership.effective_tier`/`Membership.effective_full_price` (`system/models/membership.py`): resolvem o tier/preço efetivos tanto para `Membership.plan_price` (novo) quanto para `Membership.plan` legado (`SubscriptionPlan` não-Veterano, casado por `audience`+`weekly_frequency`) — permite que um titular ainda no modelo antigo e um dependente já no novo modelo compartilhem corretamente o desconto família, sem exigir migração do titular. Veterano é explicitamente excluído dessa resolução (`recompute_family_discounts_for_person` filtra `plan__is_loyalty_plan=True`).
- `family_pricing.py::recompute_family_discounts_for_person` generalizado para agrupar por `effective_tier` (não mais só `plan_price__tier`), cobrindo Memberships legadas e novas no mesmo recomputo.

## Implemented (Fase 3 — sincronização Stripe via Coupon/Discount)
- `system/services/stripe_discounts.py` (novo): `apply_family_discount(membership)` garante/reaproveita um `stripe.Coupon` determinístico (`family-discount-<percentual em pontos base>`, ex. `family-discount-1800` para 18%) e aplica via `stripe.Subscription.modify(subscription_id, coupon=coupon_id)`; `remove_family_discount(membership)` usa `stripe.Subscription.delete_discount(subscription_id)` — ambos confirmados como parâmetros/endpoints válidos da API Stripe atual via Context7. Nenhuma chamada real ao Stripe nesta entrega (testes com mock).
- `family_pricing.py::_sync_stripe_discount` chama esses serviços apenas quando `stripe_subscription_id` está preenchido e o estado do desconto mudou; falhas de sincronização Stripe são logadas (`logger.exception`) e não bloqueiam o recomputo local — mesmo padrão de resiliência já usado em `notify_subscription_past_due`/`notify_payment_failed`.

## Implemented (Fase 4 — wiring do wizard de dependente para PlanTier/PlanPrice)
- `system/services/registration_checkout.py`: `get_plan_catalog_payload(include_plan_prices=False)` — por padrão (wizard público via `auth_views.py`) mantém o comportamento antigo intacto (ids numéricos crus, só `SubscriptionPlan`); com `include_plan_prices=True` (só `dependent_views.py`), o catálogo passa a incluir também `PlanPrice` ativas, com ids prefixados (`sp:<pk>` / `pp:<pk>`) para não colidir. `resolve_catalog_plan(catalog_id)` resolve um id prefixado de volta ao objeto real. `parse_selected_plan_payload`/`_normalize_catalog_plan_id` aceitam o novo formato E o int cru salvo por pré-cadastros antigos (retrocompatibilidade).
- `system/forms/dependent_forms.py`: `selected_plan` passa a listar também os `PlanPrice` ativos; `_clean_financial_choice` resolve o id via `resolve_catalog_plan` e, quando o resultado é um `PlanPrice`, força `financial_mode=DEPENDENT_OWN` automaticamente — elimina a necessidade de escolher "família" (não existe mais card separado) — validando só compatibilidade de audience/idade.
- `system/services/dependent_registration.py`: `_selected_plans_payload` grava o id prefixado no snapshot; `_create_paid_plan_order` cria `RegistrationOrder`/`Membership` apontando para `plan` OU `plan_price_ref`/`plan_price` conforme o tipo selecionado, e dispara `recompute_family_discounts_for_person` logo após ativar a Membership do dependente.
- `system/models/registration_order.py`: novo campo `plan_price_ref` (FK opcional para `PlanPrice`; o nome `plan_price` já pertencia ao campo Decimal existente, por isso o FK novo recebeu nome distinto).
- `system/services/membership.py`: `activate_membership_from_paid_order` aceita pedidos com `plan` OU `plan_price_ref`, criando a Membership com o FK correto.
- `system/views/dependent_views.py`: a restauração pós-pagamento (`_restore_confirmed_payment_post_data` e o bloco `payment_confirmed` do `post()`) passa a priorizar o id salvo no snapshot (já no formato prefixado) sobre a FK legada `pending.selected_plan_id`, garantindo retomada correta para ambos os modelos.
- `static/system/js/dependents/dependent_registration.js`: removido o `parseInt` que forçava os ids de plano a inteiro (agora são strings opacas como `pp:9`). `static/system/js/auth/register.js` **não foi alterado** — mantém `parseInt`, pois o wizard público continua só com ids numéricos (contenção de risco deliberada).
- Seeds: `seed_system_initial_subscription_plans_values.json`/`..._stripe.json` reduzidos para conter só `loyalty` (Veterano); novos `seed_system_initial_plan_tiers.json`/`_prices.json` + comandos correspondentes geram Individual/Família consolidados. Local: 54 `SubscriptionPlan` rows → 16 (só Veterano) + 20 `PlanPrice` rows.
- Validação visual: navegador interno, wizard de dependente, etapa "Plano do dependente", filtro Cartão — **apenas 2 cards "Individual" aparecem (Asaas Cartão e Stripe recorrente), nenhum card "Família"**; seleção resolve `financial_mode=dependent_own` e `checkout_action` automaticamente; bloco de estratégia de cartão da PRD-126 continua funcionando integrado ao novo catálogo; console sem erros.

## Cleanup findings
- `DependentCardStrategyTestCase._base_form_data` (`system/tests/test_dependent_registration.py`) era um helper morto (nunca chamado) — removido.
- Wizard público (`register.js`/`registration_forms.py`) e o CRUD administrativo de planos (`plan_management.py`, `templates/plans/`) permanecem inteiramente no modelo `SubscriptionPlan` — dívida registrada no Follow-up, não bloqueante para o caso de uso resolvido nesta entrega.

## Follow-up PRDs
- Rework simétrico de "Veterano" (`is_loyalty_plan`) para o mesmo modelo de tier+desconto, se fizer sentido de negócio (fora de escopo aqui pela complexidade adicional de elegibilidade por tempo de casa + aprovação manual).
- Migração de dado real em HG/produção, quando/se aplicável.

## Deviations from plan
N/A (pré-implementação).

## Pending
- Decisões de negócio confirmadas pelo usuário ("pode tomar a melhor decisão... boas práticas"):
  - Proration: desconto/reversão passam a valer a partir do **próximo ciclo completo**, sem cobrança pro-rata retroativa no ciclo corrente.
  - Escopo do desconto: **por tier** — só conta pessoas do grupo familiar no MESMO `PlanTier` (ou tier legado equivalente por audience+frequência).
  - Percentual único de desconto família: **18%** para todos os tiers (adotado a partir da referência Stripe existente — Asaas tinha um percentual histórico inconsistente entre 7,72% e 12%, sem relação matemática com o Stripe; 18% uniformiza e simplifica).
- **Não implementado nesta entrega** (Fase 6 e parte da Fase 5): UI "de/por" com preço original riscado explícito (hoje o desconto já é visível via `billed_price`/família recomputada, mas não há um componente visual dedicado mostrando "de X por Y" lado a lado); CRUD administrativo completo para `PlanTier`/`PlanPrice` (`system/services/plan_management.py`/`templates/plans/` continuam gerenciando só `SubscriptionPlan`/Veterano); rework simétrico de Veterano (fora de escopo, registrado como follow-up).
- Wizard público principal (`register.js`/`registration_forms.py`) permanece **inteiramente no modelo legado** (`SubscriptionPlan`) por decisão de contenção de risco — só o wizard de adicionar dependente foi migrado para o catálogo `PlanTier`/`PlanPrice`. Isso é suficiente para o caso de uso relatado (titular já cadastrado adicionando dependente), mas significa que um titular novo, cadastrado do zero, ainda entra no sistema antigo; a interoperabilidade (`Membership.effective_tier`) garante que o desconto família funciona corretamente mesmo assim, sem exigir migração do titular.

## Final status
Fases 1, 2, 3 concluídas integralmente. Fase 4 (rewiring do wizard de dependente para o catálogo `PlanTier`/`PlanPrice`, com resolução automática para mensalidade própria e sem card "Família" separado) concluída e validada em teste e navegador. Fase 5 concluída parcialmente (seeds reescritos; admin CRUD não). Fase 6 (UI "de/por" explícita) não implementada. Sistema íntegro, testado (517 testes) e validado visualmente — comportamento correto: card "Família" não aparece mais no wizard de dependente; seleção resolve `financial_mode=dependent_own` automaticamente; desconto família de 18% aplica-se e reverte-se automaticamente ao adicionar/remover dependente, local e via Stripe Coupon/Discount.
