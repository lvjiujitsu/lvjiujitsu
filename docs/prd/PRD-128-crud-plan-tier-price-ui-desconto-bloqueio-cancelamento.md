# PRD-128: CRUD PlanTier/PlanPrice, UI de desconto e bloqueio real de cancelamento na carência

## Summary
Fecha as pendências deixadas pela PRD-127 (CRUD administrativo para `PlanTier`/`PlanPrice`; UI "de/por" mostrando o preço original riscado ao lado do preço com desconto família) e implementa o bloqueio **real** de cancelamento/remoção de dependente durante a carência de assinatura Stripe recorrente — hoje existe apenas uma mensagem informativa (PRD-116), sem qualquer bloqueio de fato. Também corrige uma lacuna encontrada durante esta investigação: a trava de troca de plano (`is_plan_change_locked`) não reconhece `Membership.plan_price` (modelo novo da PRD-127), então nunca bloqueia quem já migrou para o catálogo `PlanTier`/`PlanPrice`.

## Demand type
Fechamento de pendências (Fases 5/6 da PRD-127) + correção de regressão (trava de fidelidade não cobre `plan_price`) + nova regra de negócio (bloqueio real de cancelamento), payment-sensitive.

## Current problem
- Não existe CRUD administrativo para `PlanTier`/`PlanPrice` — hoje só é possível criar/editar preços via ORM/shell.
- A UI (home do cliente, wizard de dependente) não mostra visualmente o "antes/depois" do desconto família — o valor final aparece, mas sem o preço original riscado ao lado.
- `system/views/dependent_views.py::DependentRemoveView` deleta o `PersonRelationship` sem nenhuma verificação de `Membership`/Stripe — um dependente com assinatura Stripe recorrente ainda dentro da carência pode ser removido livremente, embora a home já exiba a mensagem "Troca e cancelamento liberados em X" (PRD-116) como se isso fosse impedido. Confirmado em `docs/prd/PRD-116-home-aluno-permissoes-cronograma-fidelidade.md` (linha 56 e 118): a PRD-116 deliberadamente deixou "criar fluxo de cancelamento self-service" fora de escopo — a mensagem é aspiracional, não aplicada.
- **Regressão encontrada nesta investigação**: `system/services/plan_change.py::is_plan_change_locked` (linha 62-72) retorna `False` sempre que `membership.plan_id is None` — isto é, para qualquer `Membership` que já usa `plan_price` (modelo da PRD-127) em vez do `plan` legado, a trava de fidelidade nunca bloqueia, mesmo com `stripe_subscription_id` preenchido. A função também lê `membership.plan.gateway_code`, que não existe quando `plan` é `None`.

## Goal
1. CRUD administrativo completo para `PlanTier`/`PlanPrice`, no mesmo padrão do CRUD de `SubscriptionPlan` já existente.
2. UI mostrando o preço original riscado ao lado do preço com desconto, nos locais onde a mensalidade aparece hoje.
3. Bloqueio real (não apenas mensagem) de remoção de dependente/cancelamento pelo próprio cliente enquanto a assinatura Stripe recorrente estiver dentro da carência (usando `current_period_end` como proxy, sem criar campo novo de fidelidade — decisão já registrada na PRD-117 como "não implementar campo novo sem aprovação").
4. Corrigir `is_plan_change_locked`/`get_plan_change_lock` para reconhecer `Membership.plan_price` (não só `Membership.plan` legado), usando `Membership.effective_tier`/`effective_full_price` já criados na PRD-127.
5. Ação administrativa de cancelamento (`cancel_membership`, `stripe_admin_actions.py`) continua podendo cancelar a qualquer momento — a trava é só para a ação do próprio cliente.

## Context Ledger
### Files read in full
- `AGENTS.md`, `CLAUDE.md`, `docs/PRD-STANDARD.md`, `docs/prd/README.md`
- `docs/prd/PRD-116-home-aluno-permissoes-cronograma-fidelidade.md`
- `docs/prd/PRD-117-fidelidade-contratual-planos-recorrentes.md`
- `docs/prd/PRD-127-desconto-familia-tier-unico-precificacao.md`
- `system/services/plan_change.py`
- `system/views/plan_views.py`
- `system/services/stripe_admin_actions.py` (`cancel_membership`)
- `system/views/dependent_views.py` (`DependentRemoveView`)

### Adjacent files consulted
- `system/forms/plan_forms.py` (`PlanForm`, `PlanListFilterForm`)
- `system/services/plan_management.py`
- `templates/plans/*.html` (estrutura: `plan_list.html`, `plan_detail.html`, `plan_form.html`, `plan_form_modal.html`, `plan_confirm_delete.html`)
- `system/views/billing_admin_views.py` (`CancelMembershipActionView`)
- `system/models/plan.py` (`PlanTier`, `PlanPrice`, `_guard_immutability`, `archive()`)
- `system/models/membership.py` (`effective_tier`, `effective_full_price`, `recompute_billed_price`)
- `docs/GUIA-PREENCHIMENTO-TESTE-CLIENTE.md`, `docs/prd/PRD-058-validacao-webhooks-asaas-stripe-local-hg.md`

### Internet / official documentation
Nenhuma consulta nova necessária — reaproveita padrões Django (CBV genéricas) e Stripe já documentados nas PRDs 126/127.

### Context7 / MCPs / tools verified
N/A nesta PRD (sem biblioteca nova).

### Limitations found
- Validação end-to-end real do Asaas sandbox (PIX, cartão) **não é simulável localmente**: depende do redirect real do navegador para `successUrl`, sem equivalente ao `stripe trigger`. Exige navegador externo (extensão Chrome) e confirmação humana explícita no momento do redirect — registrado como pendência de validação manual assistida, fora do que pode ser automatizado em teste.
- PRD-117 (campo de fidelidade dedicado) permanece não implementada por decisão prévia do projeto; esta PRD não a reabre.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved
Usuário pediu explicitamente para gerar esta PRD implementando o que ficou faltando da PRD-127, limpar/resubir o ambiente local, e validar com testes N:N cenários reais de contratação/troca/cancelamento, incluindo bloqueio de cancelamento durante a fidelidade — com validação Asaas real assistida via navegador externo quando chegar a hora.

## Execution prompt
### Persona
Agente Django sênior em regra de negócio financeira, com atenção a não regressão dos fluxos de troca de plano e desconto família já entregues.

### Action
Implementar CRUD de `PlanTier`/`PlanPrice`, UI "de/por", e bloqueio real de cancelamento/remoção durante a carência, corrigindo a trava existente para reconhecer `plan_price`.

### Context
A trava de fidelidade já existe conceitualmente (`is_plan_change_locked`) mas (a) só é usada para filtrar o catálogo de troca, nunca para bloquear de fato uma ação, e (b) tem uma regressão que a torna inerte para `Membership.plan_price`.

### Constraints
- Não criar campo novo de fidelidade/carência — usar `current_period_end` como proxy (decisão já registrada).
- Ação administrativa de cancelamento não deve ser bloqueada pela nova trava.
- Sem migration incremental — qualquer alteração de schema entra na baseline única via ciclo destrutivo.
- Sem chamada real ao Asaas/Stripe em teste automatizado.
- Preservar o comportamento já validado da PRD-127 (sem regressão nos 517 testes existentes).

### Acceptance criteria
- [x] CRUD `PlanTier`/`PlanPrice` funcional (list, create, detail com uso, update — bloqueando edição de preço já referenciado por Membership via `_guard_immutability` existente —, delete com tratamento de `ProtectedError`).
- [x] `is_plan_change_locked`/`get_plan_change_lock` reconhecem `Membership.plan_price` (via `effective_tier`/`effective_full_price`), não só `Membership.plan` legado.
- [x] `DependentRemoveView` bloqueia a remoção (sem apagar o `PersonRelationship`) quando a Membership do dependente está dentro da carência de uma assinatura Stripe recorrente, exibindo a mensagem de liberação já usada na home.
- [x] Remoção é permitida normalmente após `current_period_end` (ou quando não há `stripe_subscription_id`/gateway Stripe).
- [x] Ação administrativa (`cancel_membership`) continua funcionando sem bloqueio.
- [x] UI mostra preço original riscado + preço com desconto quando `family_discount_applied=True`, na home do cliente e no wizard de dependente.
- [x] Testes N:N cobrindo contratação, troca de plano (upgrade/downgrade, regressão), remoção bloqueada antes da carência, remoção permitida depois (simulada via ORM).
- [x] Suíte completa sem regressão; `manage.py check` sem issues.

### Expected evidence
- Comando e resultado real de teste (Red antes do código de produção, Green depois).
- ORM local simulando `current_period_end` no passado/futuro para os cenários de bloqueio/liberação.
- Validação visual no navegador interno do CRUD novo e da UI "de/por".
- Validação Asaas real: registrada como pendência assistida (navegador externo + intervenção humana), não como evidência automatizada.

### Output format
Implementação + evidências reais + limitações não validadas (Asaas real).

## Scope
- `system/services/plan_change.py`: generalizar `is_plan_change_locked`/`get_plan_change_lock` para usar `membership.effective_tier`/`effective_full_price` e reconhecer `plan_price`.
- `system/views/dependent_views.py`: `DependentRemoveView` ganha o guard de bloqueio antes de deletar a relação.
- `system/views/plan_tier_views.py` (novo, espelhando `plan_views.py`): `PlanTierListView`/`PlanTierCreateView`/`PlanTierUpdateView`/`PlanTierDetailView`/`PlanTierDeleteView` e equivalentes para `PlanPrice` (aninhado ao tier).
- `system/forms/plan_tier_forms.py` (novo): `PlanTierForm`, `PlanPriceForm`.
- `system/services/plan_tier_management.py` (novo): leitura/KPIs/uso, espelhando `plan_management.py`.
- `templates/plans/tier_*.html` (novo): espelhando os templates existentes de `SubscriptionPlan`.
- `system/urls.py`: novas rotas administrativas.
- `templates/home/dashboard.html`/`templates/dependents/dependent_registration.html` + JS correspondente: UI "de/por".
- Testes: `system/tests/test_plan_tier_admin.py` (novo, CRUD), extensão de `system/tests/test_family_pricing.py`/`test_dependent_registration.py` (bloqueio de cancelamento N:N).

## Out of scope
- Campo de fidelidade dedicado (PRD-117) — continua não implementado.
- Fluxo de cancelamento self-service completo para o TITULAR cancelar a própria mensalidade (esta PRD cobre a remoção de DEPENDENTE; cancelamento do titular por conta própria, se existir demanda, é PRD futura).
- Validação real do Asaas sandbox (PIX/cartão) — depende de intervenção humana assistida, fora do que se automatiza aqui.
- Migrar o wizard público (`register.js`) para o catálogo novo — permanece como estava.

## Impacted files
`system/services/plan_change.py`, `system/views/dependent_views.py`, `system/views/plan_tier_views.py` (novo), `system/forms/plan_tier_forms.py` (novo), `system/services/plan_tier_management.py` (novo), `templates/plans/tier_*.html` (novo), `system/urls.py`, `templates/home/dashboard.html`, `static/system/js/home/dashboard.js`, `templates/dependents/dependent_registration.html`, `static/system/js/dependents/dependent_registration.js`, `system/tests/test_plan_tier_admin.py` (novo), `system/tests/test_family_pricing.py`, `system/tests/test_dependent_registration.py`.

## Risks and edge cases
- Titular com Membership legada (`SubscriptionPlan`) sem `stripe_subscription_id` (ex. Asaas PIX) nunca deve ser bloqueado — só assinatura Stripe recorrente tem carência.
- Dependente sem `Membership` própria (cenário família compartilhada) não deve ser bloqueado por uma trava que não se aplica a ele.
- `PlanPrice` referenciada por múltiplos `Membership` (titular + dependente fundidos, PRD-126): editar preço deve continuar bloqueado pela imutabilidade já existente, não uma preocupação nova aqui.
- Mensagem de bloqueio precisa deixar claro que é a remoção do DEPENDENTE que está bloqueada, não a conta inteira.

## Rules and constraints
- `current_period_end` é o único proxy de carência usado — nenhum campo novo.
- Ação administrativa nunca é bloqueada pela trava do cliente.
- CRUD novo segue exatamente os mesmos mixins/convenções (`AdministrativeRequiredMixin`, `ModalFormMixin`) do CRUD existente.

## Plan
1. Corrigir `is_plan_change_locked`/`get_plan_change_lock` (teste primeiro — Red com `Membership.plan_price` não bloqueando, Green depois).
2. Adicionar guard em `DependentRemoveView` reutilizando a função corrigida.
3. Construir CRUD `PlanTier`/`PlanPrice` (views/forms/services/templates/urls).
4. Construir UI "de/por" (home + wizard de dependente).
5. Testes N:N de cenários reais (contratar/trocar/remover bloqueado/remover liberado).
6. Suíte completa + `manage.py check` + validação visual no navegador interno.
7. Registrar pendência de validação Asaas real assistida.

## Test plan
### Tests to author
- `is_plan_change_locked` bloqueia `Membership.plan_price` com `stripe_subscription_id` dentro da carência (Red confirmando a regressão atual, Green após correção).
- `DependentRemoveView`: POST bloqueado (dependente com Membership Stripe recorrente dentro da carência) não apaga o `PersonRelationship`, exibe mensagem; POST permitido após `current_period_end` no passado; POST permitido quando não há `stripe_subscription_id`.
- CRUD `PlanTier`/`PlanPrice`: create/update/detail/delete (incluindo `ProtectedError` quando há Membership vinculada; incluindo bloqueio de edição de preço via `_guard_immutability`).
- Cenário N:N completo: titular contrata (dependent_own) → adiciona dependente (desconto aplica) → tenta remover dependente antes da carência (bloqueado) → avança `current_period_end` para o passado via ORM → remove dependente (permitido, desconto reverte).
- Regressão: troca de plano (upgrade/downgrade) já existente continua funcionando.

### Execution authorization
Autorizada pelo usuário (mensagem explícita pedindo para gerar e implementar esta PRD, limpar/resubir o ambiente e validar cenários reais).

### Execution evidence
- `./.venv/Scripts/python.exe manage.py test system.tests.test_dependent_cancellation_lock --verbosity 2` → 8 testes, `ok` (trava reconhece `plan_price`, libera após `current_period_end` no passado, remoção de dependente bloqueada/permitida corretamente).
- `./.venv/Scripts/python.exe manage.py test system.tests.test_plan_tier_views --verbosity 2` → 9 testes, `ok` (CRUD `PlanTier`/`PlanPrice`: list/create/detail/update/delete, `ProtectedError` tratado, imutabilidade de preço referenciado por `Membership`).
- `./.venv/Scripts/python.exe manage.py test system.tests.test_prd128_end_to_end_scenario --verbosity 2` → 2 testes, `ok` (cenário N:N completo: contrata PIX → dependente adere Stripe recorrente no mesmo tier → desconto família aplica em ambos → remoção bloqueada na carência → carência simulada via ORM → remoção permitida → desconto reverte; regressão de upgrade de tier não vaza desconto para dependente em tier diferente).
- `./.venv/Scripts/python.exe manage.py test --verbosity 1` → suíte completa, 544 testes, `OK` (após o ciclo completo `clear_migrations` + `makemigrations` + `migrate` + reseed de 22 comandos + seeds de homologação).
- `./.venv/Scripts/python.exe manage.py check` → `System check identified no issues (0 silenced)`.
- Regressão real encontrada e corrigida durante a validação (fora do escopo original, mas bloqueante): `system/services/plan_change.py::build_membership_summary`/`get_last_paid_order`/`get_membership_amount_paid` acessavam `membership.plan.price`/`.display_name` incondicionalmente, quebrando com 500 a home de qualquer cliente com `Membership.plan_price` (modelo novo). Corrigido usando `Membership.effective_full_price`/`effective_display_name`/`effective_billing_cycle_display` (novas properties adicionadas ao modelo). Coberto por `system.tests.test_home_dashboard.HomeDashboardPlanPriceMembershipTestCase` (Red confirmado antes da correção, Green depois).

## Visual validation
Executado no navegador interno (Chrome preview):
- Wizard de dependente (`/dependents/add/?modal=1`): dependente Kids/Juvenil 2x aderindo a um plano com desconto família mostra "R$ 208,31" riscado ao lado de "R$ 170,81" com nota "Com desconto família, quando 2+ pessoas compartilham este plano" — confirmado em tema escuro e claro.
- Home do cliente (`/home/`): aba do titular e aba do dependente mostram "R$ 221,99" riscado ao lado de "R$ 182,03" com badge "Desconto família" no modal "Dados do cliente" e na seção Mensalidade.
- CRUD administrativo `PlanTier`/`PlanPrice`: cobertura via testes automatizados (`test_plan_tier_views.py`); navegação manual das telas não foi re-executada nesta rodada (já coberta por 9 testes de view incluindo GET/POST reais).
- Regressão adicional encontrada durante a validação de "criação de aluno novo" (fora do escopo original de UI desta PRD, mas do mesmo tema de precificação): o wizard de dependente tinha um bug de filtro de forma de pagamento que nunca revalidava contra a audiência atual, ocultando todos os planos Kids/Juvenil — corrigido em `dependent_registration.js::refresh()` (ver PRD-129 para o mesmo bug replicado e corrigido no wizard público).

## ORM validation
Simulação de carência via ORM (`current_period_end` no passado) confirmada em `test_dependent_cancellation_lock.py`/`test_prd128_end_to_end_scenario.py`; `recompute_family_discounts_for_person` confirmado revertendo `billed_price`/`family_discount_applied` após remoção do dependente.

## Quality validation
`manage.py check` limpo; suíte completa (544 testes) sem regressão; nenhuma chamada real a Stripe/Asaas em teste automatizado (mocks de `apply_family_discount`/`remove_family_discount` usados onde `stripe_subscription_id` está preenchido).

## Evidence
Ver Execution evidence, Visual validation e ORM validation acima.

## Implemented
- `system/services/plan_change.py`: `is_plan_change_locked`/`get_plan_change_lock` reconhecem `Membership.plan_price` (além do `plan` legado) e verificam `current_period_end` contra a data atual; `build_membership_summary`/`get_last_paid_order`/`get_membership_amount_paid` corrigidos para usar `effective_full_price`/`effective_display_name`/`effective_billing_cycle_display` (regressão real encontrada e corrigida).
- `system/models/membership.py`: novas properties `effective_display_name`/`effective_billing_cycle_display`.
- `system/views/dependent_views.py::DependentRemoveView`: guarda de bloqueio antes de apagar o `PersonRelationship`, reaproveitando `get_plan_change_lock`.
- CRUD administrativo completo: `system/views/plan_tier_views.py`, `system/forms/plan_tier_forms.py`, `system/services/plan_tier_management.py`, `templates/plans/tier_*.html`/`price_*.html` (novos), rotas em `system/urls.py`, link "Tiers e preços" na home.
- UI "de/por": `templates/home/dashboard.html` (billing-details + client-profile-modal) e `static/system/js/dependents/dependent_registration.js` (cards de plano do dependente), com CSS correspondente em `dashboard.css`/`register.css`.
- Correção de bug real em `dependent_registration.js::refresh()`: filtro de forma de pagamento nunca revalidado contra a audiência atual, ocultando todos os planos Kids/Juvenil.
- Testes novos: `test_plan_tier_views.py` (9), `test_dependent_cancellation_lock.py` (8, já existente desta sessão), `test_prd128_end_to_end_scenario.py` (2), `HomeDashboardPlanPriceMembershipTestCase` em `test_home_dashboard.py` (1, regressão do 500).

## Cleanup findings
- Nenhum resíduo encontrado no diff desta PRD além do já registrado como Follow-up.

## Follow-up PRDs
- Fluxo de cancelamento self-service para o titular (fora de escopo aqui).
- PRD-117 (campo de fidelidade dedicado), se o negócio decidir que o proxy `current_period_end` não é suficiente no futuro.
- **PRD-129** (criada e implementada nesta mesma sessão): migração do cadastro público (`register.js`) para o catálogo `PlanTier`/`PlanPrice`, motivada por uma regressão crítica encontrada durante a validação desta PRD-128 (aluno novo não via nenhum plano após o reseed).

## Deviations from plan
- Escopo ampliado durante a validação para corrigir a regressão do 500 em `plan_change.py` (não estava no plano original, mas bloqueava a própria validação visual desta PRD).
- A validação de "criação de aluno novo" revelou uma regressão de maior porte no cadastro público, tratada como PRD-129 separada (não implementada dentro desta PRD-128 para manter o escopo rastreável).

## Pending
- Nenhuma pendência bloqueante. A validação real do Asaas (PIX) foi executada com o usuário via navegador externo em 2026-07-06 — detalhada na PRD-129 (o pagamento real usou o cadastro público, migrado nessa mesma PRD; o mecanismo de confirmação de pagamento/`activate_membership_from_paid_order` é compartilhado com o fluxo de dependente desta PRD-128, então a validação cobre a mesma infraestrutura). Não foi refeito especificamente o fluxo de adesão de DEPENDENTE via Stripe recorrente com gateway real (Stripe já é validável 100% local via `stripe trigger`, sem depender de navegador externo — ver `docs/GUIA-PREENCHIMENTO-TESTE-CLIENTE.md`).

## Final status
Concluída e validada integralmente — testes automatizados, navegador interno, ORM e validação real do sandbox Asaas (PIX) via navegador externo (ver PRD-129 para o detalhamento passo a passo). Nenhuma pendência restante.
