# PRD-137: Missing Recurring Stripe for Long Cycles and Broken Asaas Installments in the New Catalog

## Summary
Two failures related to migration to the `PlanTier`/`PlanPrice` catalog (PRD-127/128/129/130): (1) the recurring Stripe plan never had price rows for semiannual/annual cycles — the seed file containing them was emptied during migration, so only the monthly row exists today; (2) the Asaas installment calculation (`asaas_checkout.py`) read only `RegistrationOrder.plan` (the legacy `SubscriptionPlan` catalog), so any order from the new catalog (`plan_price_ref`) silently fell back to one installment, even for quarterly/semiannual/annual cycles — which is why installments appeared neither on the LV screen nor on the invoice generated in Asaas.

## Demand type
Bug fix (Asaas installments) + commercial-data gap (recurring Stripe for long cycles), with documentation. Investigation requested after the price correction in the previous PRD (Veteran/Individual/Kids/Youth price adjustment).

## Current problem

### 1. Missing Asaas installments (code bug)
- `system/services/asaas_checkout.py::_max_installments_for_order` and `get_installment_options_for_order` resolved the billing cycle exclusively from `order.plan` (legacy FK to `SubscriptionPlan`).
- Since PRD-129, public registration creates `RegistrationOrder` with `plan_price_ref` (FK to `PlanPrice`) for Individual/Kids/Youth — `order.plan` is `None` on those orders.
- With `plan is None`, the code fell through to `cycle = "monthly"` → `INSTALLMENT_OPTIONS["monthly"] = [1]` → `CreateCreditCardChargeView.get()` skipped directly to `_create_charge(installment_count=1)` through `len(options) <= 1`, never rendering the installment-choice screen and never sending `installmentCount` to Asaas — which is why installments appeared neither in LV nor on the Asaas invoice for any quarterly/semiannual/annual plan paid by card since PRD-129 (Veteran, still in `SubscriptionPlan`, was unaffected).
- Bug reproduced (Red) and corrected (Green) in this PRD — see Evidence.

### 2. Recurring Stripe exists only for the monthly cycle (data gap)
- The frontend (`register.js:1470-1472`) already displays the Stripe card in any selected cycle tab (monthly/quarterly/semiannual/annual) when the "Card" filter is active — the display mechanism is not broken.
- The problem is that only ONE `PlanPrice` row with `gateway_code="stripe_card"` exists per tier, always with `billing_cycle="monthly"` (`static/initial_data/seed_system_initial_plan_prices.json`).
- This is not a regression from this migration: `seed_system_initial_subscription_plans_stripe.json` (legacy catalog) also had only monthly rows since its creation (commit `5acddfc`) and never offered semiannual/annual cycles.
- Commit `121eee6` ("Add plan tiers and membership pause flows") emptied that file (`[]`) when migrating Individual/Kids/Youth to `PlanTier`/`PlanPrice` — but Stripe's monthly row had already been recreated in the new catalog (`seed_system_initial_plan_prices.json`), so there was no functionality loss, only the historical absence of semiannual/annual cycles.
- Offering recurring billing as a cheaper loyalty option for long cycles (the user's business decision) requires new `PlanPrice` rows with `gateway_code="stripe_card"` for `billing_cycle=semiannual` and `annual`, using a commercial value defined by the user.

## Goal
1. Correct the Asaas installment calculation for orders from either catalog (legacy `plan` or new `plan_price_ref`).
2. Document the root cause of missing recurring Stripe options for long cycles and propose commercial values consistent with the discount already applied to Asaas cycles, for explicit approval before writing them to the catalog.

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
- `docs/prd/PRD-127-family-discount-single-tier-pricing.md`
- `docs/prd/PRD-117-contractual-fidelity-to-recurring-plans.md`

### Adjacent files consulted
- `static/system/js/auth/register.js` (`getFilteredPlans`/`planCycles` excerpt, lines ~1449-1483)
- `docs/prd/PRD-129-migrate-public-registration-to-plantier-planprice-catalog.md` (index)
- `system/urls.py` (`asaas-card-create` route)
- Git history: `git log --oneline -- static/initial_data/seed_system_initial_subscription_plans_stripe.json` (commits `5acddfc`, `121eee6`)

### Internet / official documentation
- Not applicable — an internal project logic bug without an external API/SDK dependency in this correction. The installment calculation uses the existing `asaas_client.create_credit_card_payment` (`installmentCount`/`totalValue`), already implemented and tested in previous PRDs (reference: `docs/GUIA-PREENCHIMENTO-TESTE-CLIENTE.md`, PRD-058).

### Context7 / MCPs / tools verified
- Not applicable in this PRD — no new library/SDK involved.

### Limitations found
- There was no previous automated test covering `_max_installments_for_order`/`get_installment_options_for_order`/`CreateCreditCardChargeView` with orders from the new catalog — which is why the bug went unnoticed since PRD-129. Coverage was added in this PRD.
- The user had not defined a commercial value for recurring Stripe on semiannual/annual cycles — this PRD calculated a proposal pending explicit approval (see `Pending`).
- The local environment had no `STRIPE_SECRET_KEY` or real Asaas sandbox gateway connected in this session — installment validation simulated the view (`RequestFactory`) and mocked `asaas_client`, without a real Asaas call.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
The user selected, from the presented options: implement the installment bug (item 3) directly; and for recurring Stripe (item 2), "I propose values and you approve": calculate semiannual/annual values consistent with the existing discount pattern, document the proposal in this PRD, and write them to the catalog only after explicit approval of the figures.

## Execution prompt
### Persona
Senior Django agent correcting a financial checkout bug (Asaas) and modelling pricing, with attention to avoiding regressions in public registration and plan-switching flows already delivered in PRDs 126-135.

### Action
Correct `asaas_checkout.py` so it resolves the billing cycle through `plan` OR `plan_price_ref`; correct the related installment-template bug (nonexistent `order.plan.name`); document and propose values for recurring Stripe on semiannual/annual cycles.

### Context
`RegistrationOrder` has had both FKs (legacy `plan`, new `plan_price_ref`) since PRD-127 Phase 4 — the pattern for resolving "legacy OR new" already exists elsewhere in the code (`Membership.effective_tier`, `resolve_catalog_plan`) and was reused here through `_billing_cycle_for_order`.

### Constraints
- Do not invent a commercial value for recurring Stripe without explicit user approval — propose only.
- Do not alter the Stripe card display mechanism on the frontend (it already works correctly).
- No incremental migration — no schema change in this PRD.
- Test before code: reproduce the bug (Red) before correcting it (Green).

### Acceptance criteria
- [x] `_max_installments_for_order`/`get_installment_options_for_order` return the correct installments for orders populated with `plan_price_ref` (new catalog).
- [x] `CreateCreditCardChargeView` renders the installment-choice screen (`installment_select.html`) for these orders instead of skipping directly to one installment.
- [x] `create_credit_card_charge_for_order` sends the correct `installmentCount` to Asaas for new-catalog orders.
- [x] Plan name displayed correctly on the installment screen for both catalogs (related bug found and corrected).
- [x] Commercial values for recurring Stripe on semiannual/annual cycles written to the catalog — approved by the user ("implement") and recorded.
- [x] `sync_plan_to_stripe` works with `PlanPrice` as well as `SubscriptionPlan` — discovered not to work (additional bug), corrected and tested (without a real Stripe call).

### Expected evidence
- Red test (bug reproduced by reverting the correction through `git stash`) and Green test (suite after correction), with actual command and output.
- Simulation of the actual view (`RequestFactory`) confirming the installment screen renders with the correct options.
- Full suite without regressions.

### Output format
Implemented and tested correction (installments) + documented proposal awaiting approval (recurring Stripe) + recorded limitations.

## Scope
- Correct `system/services/asaas_checkout.py` (`_billing_cycle_for_order`, `_max_installments_for_order`, `get_installment_options_for_order`).
- Correct `system/views/asaas_views.py` (`select_related` including `plan_price_ref`).
- Correct `templates/login/installment_select.html` (missing plan name for the new catalog and nonexistent legacy `plan.name` field).
- Add regression tests (`system/tests/test_asaas.py`).
- Document and propose semiannual/annual recurring Stripe values (writing them remains pending until approval).

## Out of scope
- Contractual loyalty/waiting period for recurring Stripe (`PRD-117`, already recorded as separately pending).
- Any price change in Asaas cycles (PIX/Card) — already corrected in the previous delivery.
- Real Stripe synchronisation (Product/Price creation) — occurs only when `STRIPE_PLAN_SYNC_ENABLED=True`, outside the local scope of this correction.

## Impacted files
`system/services/asaas_checkout.py`, `system/views/asaas_views.py`, `templates/login/installment_select.html`, `system/tests/test_asaas.py`, `system/tests/test_commands.py`, `static/initial_data/seed_system_initial_plan_prices.json`, `system/services/stripe_sync.py`, `system/management/commands/seed_system_initial_plan_prices.py`, `system/tests/test_stripe_sync.py`.

## Risks and edge cases
- Old orders (pre-PRD-129) with `plan` populated continue resolving through the legacy path — `_billing_cycle_for_order` prioritises `order.plan_id` before `plan_price_ref_id`, preserving previous behaviour.
- Orders with neither FK (a case that should not exist, although the model allows `null=True` on both) fall back to `"monthly"` (one installment) — a safe default identical to previous behaviour.
- If the user approves the proposed recurring Stripe values, it will be necessary to decide whether the real Stripe gateway (`STRIPE_PLAN_SYNC_ENABLED`) should synchronise new Products/Prices — outside local scope, but to be marked as a follow-up when applicable.

## Rules and constraints
- Every legacy-versus-new catalog resolution must follow the established pattern (`plan` takes priority when populated; otherwise `plan_price_ref`) — do not duplicate resolution logic unnecessarily across multiple places.
- No commercial value is written without explicit user approval (obtained through `AskUserQuestion` — "I propose values and you approve" — and confirmed with "implement").

## Plan
1. Reproduce the installment bug with a test (Red) using a `plan_price_ref`-based order.
2. Correct `_billing_cycle_for_order`/`_max_installments_for_order`/`get_installment_options_for_order`.
3. Correct `select_related` in the view and the plan name in the template.
4. Confirm Green with the focused suite and full suite.
5. Validate the actual view through simulation (`RequestFactory`) without a real Asaas call.
6. Document and propose recurring Stripe values; await approval before writing them.
7. Approval received ("implement") — calculate exact `base_monthly_net_price`/`cycle_discount_percentage` values by reverse-engineering the formula (the same method used for the previous price correction), write them to the seed and local database, and validate the catalog served by the wizard.

## Test plan
### Tests to author
- `AsaasCheckoutPlanPriceCatalogTests` (`system/tests/test_asaas.py`): `_max_installments_for_order` resolves six installments for a semiannual `plan_price_ref`; `get_installment_options_for_order` returns `[1, 2, 3, 6]`; `create_credit_card_charge_for_order` sends `installment_count=6` to Asaas (mock).
- Extended `PlanTierPriceSeedCommandTestCase.test_seed_creates_tiers_and_prices_idempotently` (`system/tests/test_commands.py`): total `PlanPrice` count (36→44) and exact price of the 4 new semiannual/annual Stripe rows (`adult-2x`, `kids-5x`).

### Execution authorization
Approved ("investigate and implement") for the installment bug; recurring Stripe approved in two stages — first "propose values and you approve", then "implement" (explicit confirmation of the figures in the `Pending` table).

### Execution evidence
- Red: `git stash` of the corrected file + `.\.venv\Scripts\python.exe manage.py test system.tests.test_asaas.AsaasCheckoutPlanPriceCatalogTests --verbosity 2` → **3 failures** (`1 != 6`, `[1] != [1, 2, 3, 6]`, `1 != 6`), confirming the actual bug before the correction.
- Green: `git stash pop` (restores the correction) + the same command → **3 tests, OK**.
- Focused regression: `.\.venv\Scripts\python.exe manage.py test system.tests.test_asaas --verbosity 2` → **28 tests, OK**.
- Actual view simulation (`RequestFactory` + `SessionStore` with `pending_checkout_order_id`, with no `asaas_client` mock because `.get()` does not call the gateway): semiannual `PlanPrice` order (`adult-2x`, Asaas Card) → `CreateCreditCardChargeView.get()` returns `status_code=200`, rendering `installment_select.html` with `1x`, `2x`, `3x`, and `6x` options present in the HTML — before the correction, the same order skipped directly to `_create_charge(installment_count=1)` without ever rendering the screen.
- The same test confirmed `order-summary__plan` displaying `"Adulto 2x por semana"` correctly after the template correction (previously: nonexistent `plan.name`, always empty).
- After approval of recurring Stripe values: `.\.venv\Scripts\python.exe manage.py seed_system_initial_plan_prices` → 4 `criado` rows (semiannual/annual × adult-2x/adult-5x/kids-2x/kids-5x) with exact prices (`1195.00`, `2265.00`, `1250.00`, `2390.00`) — verified to the cent through `compute_gross_price`.
- Catalog served by the wizard (`GET /register/`, `#reg-plan-catalog-json`) confirmed with all 12 `stripe_card` rows (4 tiers × 3 cycles: monthly/semiannual/annual) and the exact values.
- Full regression (after adjusting the count in `test_commands.py`): `.\.venv\Scripts\python.exe manage.py test --verbosity 1` → **644 tests, OK**.
- `.\.venv\Scripts\python.exe manage.py check` → no issues.

## Visual validation
Installments: real browser clicks were not applicable in this session (the flow depends on an authenticated checkout session with `pending_checkout_order_id`); exercised through view/`RequestFactory` simulation. Recurring Stripe: confirmed through `fetch('/register/')` in the internal browser (`preview_start` server), extracting `#reg-plan-catalog-json` and checking all 12 `stripe_card` rows with the exact approved prices.

## ORM validation
A test order was created/queried/removed through the local ORM (`PlanPrice`, `PlanTier`, `RegistrationOrder`, `Person`) for the installment-view simulation — no residue left in the local database. The recurring Stripe seed was reapplied locally (`seed_system_initial_plan_prices`), confirming the 4 new rows with exact prices.

## Quality validation
`manage.py check`: no issues. Full suite: 644 tests, OK.

## Evidence
See `Execution evidence` above.

## Implemented
- `system/services/asaas_checkout.py`: new `_billing_cycle_for_order(order)` function — resolves `order.plan.billing_cycle` (legacy) or `order.plan_price_ref.billing_cycle` (new), with a `"monthly"` fallback. `_max_installments_for_order` and `get_installment_options_for_order` now use it instead of reading `order.plan` directly.
- `system/views/asaas_views.py`: `select_related("plan", "plan_price_ref", "person")` in all 3 `RegistrationOrder` queries in `CreateCreditCardChargeView`/`AsaasPixQrCodeView` (avoids N+1 when resolving the tier in the template).
- `templates/login/installment_select.html`: `{{ order.plan.name }}` (nonexistent field, always empty) → `{{ order.plan.display_name|default:order.plan_price_ref.tier.display_name }}` — works for both catalogs.
- `system/tests/test_asaas.py`: new `AsaasCheckoutPlanPriceCatalogTests` class with 3 tests covering the new-catalog scenario.
- `static/initial_data/seed_system_initial_plan_prices.json`: 8 new `gateway_code=stripe_card` rows (semiannual + annual × `adult-2x`/`adult-5x`/`kids-2x`/`kids-5x`), with `base_monthly_net_price`/`cycle_discount_percentage` reverse-engineered from `compute_gross_price` to reproduce the exact approved amounts (R$ 1,195.00/2,265.00 for 2x; R$ 1,250.00/2,390.00 for 5x/Kids/Youth).
- `system/tests/test_commands.py`: extended `test_seed_creates_tiers_and_prices_idempotently` with the new count (44) and exact-price assertions for the 4 new Stripe rows.
- `system/services/stripe_sync.py`: generalised `sync_plan_to_stripe` to work with either `SubscriptionPlan` (legacy) OR `PlanPrice` (new) — previously it worked only with a hardcoded `SubscriptionPlan` (`SubscriptionPlan.objects.filter(pk=plan.pk).update(...)`), failing with `AttributeError` for `PlanPrice` (no `code`/`description` fields). New `_plan_code(plan)` (derives `tier.code-gateway_code-billing_cycle` when there is no dedicated `code`) and `_plan_description(plan)` (returns `None` when the model lacks the field) functions. Result persistence uses `type(plan).objects.filter(...)` instead of the fixed model.
- `system/management/commands/seed_system_initial_plan_prices.py`: now synchronises with real Stripe when `STRIPE_PLAN_SYNC_ENABLED=True` (the same pattern already used in `seed_system_initial_subscription_plans_stripe.py`), only for `gateway_code="stripe_card"` rows.
- `system/tests/test_stripe_sync.py` (new): 5 tests — `SubscriptionPlan` regression (Product/Price creation, zero price skipped, error without `STRIPE_SECRET_KEY`) + 2 new `PlanPrice` tests (Product/Price creation with a plan code derived from the tier, and Price replacement/archival when the amount changes). Bug reproduced in Red (`AttributeError: 'PlanPrice' object has no attribute 'description'`) before the correction.
- `system/tests/test_commands.py`: 2 new price-seed tests — error without `STRIPE_SECRET_KEY` when `STRIPE_PLAN_SYNC_ENABLED=True`; synchronisation called only for `stripe_card` rows (`sync_plan_to_stripe` mock, without a real call).

## Cleanup findings
- No residue introduced. The nonexistent `plan.name` bug in the template was pre-existing (also affecting legacy orders) and was corrected as part of the same touched flow — this does not expand scope; it is the same template/line as the main correction.

## Follow-up PRDs
- `PRD-117` (contractual loyalty/waiting period for recurring Stripe) remains pending, unrelated to this correction.
- Running `seed_system_initial_plan_prices` with `STRIPE_PLAN_SYNC_ENABLED=True` in staging/production (actual Stripe Product/Price creation) requires environment authorisation and real credentials — not run in this local session (no staging/production `STRIPE_SECRET_KEY` available here).

## Deviations from plan
No deviation from the original scope — Stripe synchronisation for `PlanPrice` was added as an extension explicitly authorised by the user ("implement synchronisation now, locally, tested, without a real call") after discovering that the mechanism did not exist for the new model.

## Pending
No pending local implementation. Real Stripe synchronisation (Product/Price in staging/production, `STRIPE_PLAN_SYNC_ENABLED=True`) requires environment authorisation and separate execution — no real Stripe call was made in this PRD. `PRD-117` (contractual loyalty/waiting period) remains separately pending and does not block this delivery.

**Approved and recorded values** (reference — see `Implemented`):

| Tier | Cycle | Asaas Card (reference) | Recurring Stripe (approved) | Discount vs. Asaas Card |
|---|---|---|---|---|
| Individual Adult 2x | Semiannual | R$ 1,260.00 | R$ 1,195.00 | ~5.2% |
| Individual Adult 2x | Annual | R$ 2,388.00 | R$ 2,265.00 | ~5.1% |
| Individual Adult 5x / Kids / Youth | Semiannual | R$ 1,320.00 | R$ 1,250.00 | ~5.3% |
| Individual Adult 5x / Kids / Youth | Annual | R$ 2,520.00 | R$ 2,390.00 | ~5.2% |

## Final status
**Completed.** Asaas installment bug corrected, tested (Red→Green), and validated through an actual view simulation. Recurring Stripe for long cycles: values approved by the user and written to the catalog. Additional discovery during closeout: `sync_plan_to_stripe` did not support `PlanPrice` (only legacy `SubscriptionPlan`) — corrected, tested (Red→Green), and without a real Stripe call (mocked in every test; actual staging/production execution remains for when environment authorisation and credentials are available). Full suite: 651 tests, OK. `manage.py check`: no issues.
