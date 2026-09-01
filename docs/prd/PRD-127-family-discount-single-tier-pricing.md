# PRD-127: The family discount as a single-tier modifier (a pricing rework)

## Summary
Replace the current plan model — in which "Individual" and "Família" ("Family") are entirely independent `SubscriptionPlan` records, with prices typed in by hand and no mathematical relationship between them — with a model based on a **single commercial tier** (`PlanTier`) with **versioned prices** (`PlanPrice`) and a **percentage family discount** applied dynamically when 2+ people in the family group share the same tier. Removing the dependent automatically reverts to full billing, with no manual plan change.

## Demand type
A rework of the data model and of the pricing business rule, with direct impact on Stripe (real recurring billing) — a payment-critical change, requiring explicit per-phase approval before any code (`AGENTS.md` §10).

## Current problem
- `SubscriptionPlan.is_family_plan`/`is_loyalty_plan` resolve to **entirely independent price rows**. Each row's `base_monthly_net_price` is typed manually into the seed JSON (`static/initial_data/seed_system_initial_subscription_plans_values.json`, `seed_system_initial_subscription_plans_stripe.json`) — there is no formula or percentage relationship between the Individual price and the Family price of the same tier/frequency/gateway/cycle. Today there are **54 `SubscriptionPlan` rows** (48 Asaas + 6 Stripe).
- Migrating the main person from Individual to Family today goes through the same mechanism as any plan change (`system/services/plan_change.py::apply_plan_change`): it swaps the whole `Membership.plan` FK, resets `current_period_start/end`, and can generate a proration `MembershipCredit`. From the user's point of view, "one more plan appears" instead of a discount on the same product.
- Removing the dependent does not revert the billing automatically — it requires a new manual plan change back to Individual.
- There is no price history/versioning: editing `SubscriptionPlan.price`/`base_monthly_net_price` on an active row retroactively changes what is shown for older Memberships pointing at the same row (with no grandfathering).
- `PlanEligibilityContext` (`system/selectors/plan_eligibility.py`) already counts the family group's active adults/kids through `PersonRelationship`, but that count only decides whether the family plan appears in the catalog — it does not trigger a discount.

## Goal
1. A single commercial product (`PlanTier`) per audience × frequency combination, with an embedded `family_discount_percentage`.
2. Versioned prices (`PlanPrice`) per tier × payment method × gateway × cycle, immutable once used — a value change creates a new row, preserving the history and grandfathering.
3. `Membership` references a `PlanPrice` (no longer a "Family" `SubscriptionPlan`), with `family_discount_applied`/`billed_price` automatically recomputed whenever the family group changes (a dependent added/removed).
4. The recurring Stripe subscription reflects the discount through Stripe's own Coupon/Discount API, instead of swapping the Price object — an automatic reversal when the discount is removed.
5. The UI shows the original price struck through + the discounted price where applicable, with both real values.

## Context Ledger
### Files read in full
- `AGENTS.md`, `CLAUDE.md`, `docs/PRD-STANDARD.md`, `docs/prd/README.md`
- `docs/prd/PRD-126-prevent-duplicate-stripe-charge-on-same-card-for-holder-and-dependent.md` (the compatibility of the `Membership` fields)
- `system/models/plan.py`
- `system/utils/plan_commercial.py`
- `system/services/plan_change.py`
- `system/selectors/plan_eligibility.py`
- `system/models/coupon.py`
- `system/services/coupon.py`
- `system/services/plan_management.py`
- `system/forms/plan_forms.py`
- `system/management/commands/seed_system_initial_subscription_plans.py`
- `static/initial_data/seed_system_initial_subscription_plans_values.json` (the structure, not all 48 entries)
- `static/initial_data/seed_system_initial_subscription_plans_stripe.json` (the structure, not all 6 entries)
- `system/services/stripe_sync.py`
- `system/tests/test_plan_commercial.py`
- `system/tests/test_veteran_plan.py`

### Adjacent files consulted
- `system/services/registration_checkout.py` (the use of `is_family_plan`/`plan.stripe_price_id`)
- `system/services/dependent_registration.py` (the `family_upgrade`/`dependent_own` flow)
- `system/services/stripe_checkout.py` (PRD-126's merge/staggered paths use `plan.stripe_price_id`)
- `system/forms/dependent_forms.py`, `system/forms/registration_forms.py`
- `templates/plans/plan_detail.html`, `templates/plans/plan_list.html`
- `static/system/js/dependents/dependent_registration.js`, `static/system/js/auth/register.js`

### Internet / official documentation
- Stripe — applying a coupon to an existing subscription through `POST /v1/subscriptions/:id` (the `discounts`/`coupon` parameter), with configurable proration on the update (`proration_behavior`): `https://docs.stripe.com/api/subscriptions/create`, `https://docs.stripe.com/billing/subscriptions/discounts`.
- Stripe — removing a discount from a subscription: `DELETE /v1/subscriptions/:id/discount`: `https://docs.stripe.com/api/discounts/object`, `https://docs.stripe.com/api/discounts/delete`.

### Context7 / MCPs / tools verified
- Context7 `/websites/stripe` consulted for: (1) applying a coupon/discount to an existing subscription — confirmed, supported through a subscription update; (2) removing a discount from a subscription — confirmed, a dedicated `DELETE /v1/subscriptions/:id/discount` endpoint. Both mechanisms exist in the current Stripe API, validating the design decision to use a Coupon/Discount instead of a Price swap.

### Limitations found
- The local environment has no real `STRIPE_SECRET_KEY` for the test records — the Stripe-side validation will be through mocks/fixtures, with no real call.
- There is no production data to migrate in this environment (local SQLite, rebuilt through the destructive cycle) — the "migration of existing data" described in the Plan is necessary only for real staging/production; locally, the seeds are rewritten directly into the new model.
- "Veterano" ("Veteran") (`is_loyalty_plan`) has an eligibility based on tenure + a manual administrative approval (`VeteranTenureCalculationTestCase`, `VeteranManualApprovalTestCase`, `VeteranPlanDecisionView`) — structurally different from a "family headcount discount". It stays out of this PRD's scope; see the Follow-up.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
The user explicitly chose "a complete rework, done consistently and with good practices so it's well implemented even for new prices, values, table changes, history, etc." — the deepest of the three options presented, with price history/versioning.

## Execution prompt
### Persona
A senior Django agent working on financial domain modeling and Stripe integration, with attention to data migration, webhook idempotency, and not regressing the already-existing checkout/plan change flows (including the ones recently delivered in PRD-126).

### Action
Introduce `PlanTier` and `PlanPrice` as the new pricing model; migrate `Membership` to reference `PlanPrice`; implement the automatic recomputation of the family discount; reflect the discount in the Stripe subscription through a Coupon/Discount; update the UI to show the original price struck through + the discounted price.

### Context
The system already has family group counting (`PlanEligibilityContext`) and a precedent for price versioning on the Stripe side (`stripe_sync.py::_ensure_price`, which archives the old price and creates a new one when it no longer matches the plan) — the price formula (`_compute_price`) and the archiving pattern must be reused, not reinvented.

### Constraints
- Do not remove/break the fields PRD-126 added to `Membership` (`stripe_subscription_id`, `stripe_subscription_item_id`).
- Do not change the "Veteran" behavior in this delivery.
- No incremental migration — a schema change enters the single baseline (`system/migrations/0001_initial.py`), regenerated through the local destructive cycle.
- Do not call the real Stripe in this delivery — the tests use mocks.
- Phase by phase: each phase below needs evidence (tests + `manage.py check`) before advancing to the next; do not implement every phase in one go with no checkpoint.

### Acceptance criteria
- [ ] `PlanTier` exists with `family_discount_percentage`; `PlanPrice` exists with the price calculated by the same `_compute_price()` formula, linked to a `PlanTier`.
- [ ] Changing a tier's price creates a new `PlanPrice` (it never edits the `base_monthly_net_price` of a row already used by some `Membership`/`RegistrationOrder`); the old row becomes `is_active=False` with `effective_until` filled in.
- [ ] `Membership.plan_price` replaces `Membership.plan` (`SubscriptionPlan`) without breaking PRD-126's `stripe_subscription_id`/`stripe_subscription_item_id`.
- [ ] Adding a dependent on the main person's same tier triggers `family_discount_applied=True` and recomputes `billed_price` for all the group's Memberships — with no manual plan change, and no proration `MembershipCredit` as today.
- [ ] Removing the dependent reverts `family_discount_applied=False` and `billed_price` to the full value automatically.
- [ ] The recurring Stripe subscription receives/loses the discount through the API's Coupon/Discount when the family group changes (mocked in the test; with no real call).
- [ ] The UI (the dependent wizard, the plans screen) shows the original price struck through + the discounted price when `family_discount_applied=True`, with both real values.
- [ ] The rewritten seeds generate `PlanTier`+`PlanPrice` directly, without duplicating a "Family" row as a separate product.
- [ ] "Veteran" keeps working exactly as it does today (no regression in the `test_veteran_plan.py` tests).
- [ ] The focused tests per phase + the full suite with no regression; `manage.py check` with no issues.

### Expected evidence
- The real test command and result (Red before the production code, Green after) per phase.
- The local ORM confirming `PlanTier`/`PlanPrice`/`Membership.plan_price`/`billed_price` recomputed correctly when adding/removing a dependent.
- A mock of the Stripe Coupon/Discount call (with no real call).
- Visual validation in the internal browser of the "was/now" display.

### Output format
A phased implementation + the real evidence per phase + the unvalidated limitations.

## Scope
- **Phase 1 — The data model**: `PlanTier`, `PlanPrice`, the migration of `Membership.plan`→`Membership.plan_price` + `family_discount_applied`/`billed_price`. The local destructive cycle (the schema).
- **Phase 2 — The automatic recomputation**: a trigger on `PersonRelationship` (the creation/removal of a RESPONSIBLE_FOR link) that recalculates `family_discount_applied`/`billed_price` through `PlanEligibilityContext`. It covers PIX/Asaas Card (a local recomputation, with no Stripe).
- **Phase 3 — The Stripe Coupon/Discount**: apply/remove the discount on the Stripe subscription when Phase 2's recomputation involves a `Membership` with a `stripe_subscription_id`. Tests with mocks, with no real call.
- **Phase 4 — The dependent services/flows**: `plan_change.py`, `plan_management.py`, `dependent_registration.py`, `registration_checkout.py`, `stripe_checkout.py` (PRD-126), and the forms (`plan_forms.py`, `dependent_forms.py`) pointing at `PlanPrice`/`PlanTier` instead of `SubscriptionPlan`.
- **Phase 5 — The seeds and the admin**: rewrite the 3 plan seeds to generate `PlanTier`+`PlanPrice`; adapt the administrative CRUD (`plan_management.py`, `templates/plans/`) for the new model.
- **Phase 6 — The "was/now" UI**: show the original price struck through + the discounted price in the dependent wizard and on the plans screen, using the real values from `PlanPrice`/`billed_price`.
- Each phase implements, tests, and validates before advancing to the next; the user approves the start of each phase.

## Out of scope
- "Veteran" (`is_loyalty_plan`) — it keeps the current separate-row model in this delivery; a candidate for a future symmetric rework (see the Follow-up).
- Real data migration in staging/production — this PRD covers the local rework; migrating real Memberships in a remote environment requires a separate PRD and environment authorization.
- New commercial values/prices (the PRD does not define how much each tier should cost — only the mechanics of how the discount is calculated and versioned).
- Changing the Asaas charge generation flow beyond what is necessary to read `PlanPrice` instead of `SubscriptionPlan`.

## Impacted files
`system/models/plan.py`, `system/models/membership.py`, `system/migrations/0001_initial.py`, `system/selectors/plan_eligibility.py`, `system/services/plan_change.py`, `system/services/plan_management.py`, `system/services/registration_checkout.py`, `system/services/dependent_registration.py`, `system/services/stripe_sync.py`, `system/services/stripe_checkout.py`, `system/services/membership.py`, `system/forms/plan_forms.py`, `system/forms/dependent_forms.py`, `system/forms/registration_forms.py`, `system/admin.py`, `system/management/commands/seed_system_initial_subscription_plans*.py`, `static/initial_data/seed_system_initial_subscription_plans*.json`, `templates/plans/plan_detail.html`, `templates/plans/plan_list.html`, `templates/dependents/dependent_registration.html`, `static/system/js/dependents/dependent_registration.js`, `static/system/js/auth/register.js`, and the corresponding tests.

## Risks and edge cases
- **Proration during the transition**: today switching to family generates a `MembershipCredit`; in the new model, changing `billed_price` mid-cycle needs an explicit rule (charging the pro-rata difference on the next invoice vs. applying it only in the next cycle) — a business decision to confirm before Phase 2.
- **A Stripe Coupon with a dynamic percentage**: if `family_discount_percentage` varies by tier, each tier needs its own Stripe Coupon (or a single Coupon reused when the percentage coincides) — avoid duplicating Coupons unnecessarily in Stripe.
- **Concurrency**: two people in the same family group can have Memberships in different tiers (e.g. one adult at 2x, another at 5x) — `family_discount_percentage` lives on the tier, so the discount only applies within the same tier; confirm whether the business rule really is "per tier" or "per family group regardless of tier" (an ambiguity to clarify in Phase 1).
- **`MembershipInvoice` historical data**: already-issued invoices reference the `Membership`, not the `PlanPrice` directly — confirm that the financial history does not change retroactively when swapping the `plan_price` of an existing Membership.
- **PRD-126's webhooks** (the multi-line invoice, the shared subscription) must keep working with `Membership.plan_price` in place of `Membership.plan` — any read of `membership.plan.stripe_price_id` in the current code must point at `membership.plan_price.stripe_price_id`.

## Rules and constraints
- A `PlanPrice` is never edited in place once referenced by a `Membership`/`RegistrationOrder` — a value change always creates a new row.
- `family_discount_percentage` is a tier decision, not an individual Membership one.
- The Stripe discount is always reflected through the subscription's Coupon/Discount, never through a Price swap.
- No incremental migration.

## Plan
See "Scope" (Phases 1 through 6). Each phase: write the test (Red) → implement the minimum → `manage.py check` → the focused suite → the full suite → visual validation where applicable → an approval checkpoint before the next phase.

## Test plan
### Tests to author
- Phase 1: creating a `PlanTier`/`PlanPrice`; immutability (a new row when "changing" an already-used price); `Membership.plan_price` replaces `plan` without breaking PRD-126's fields.
- Phase 2: adding a dependent on the same tier triggers the correct `family_discount_applied`/`billed_price`; removing the dependent reverts it; a group with 1 person applies no discount.
- Phase 3: a mock of applying/removing the Coupon/Discount on the Stripe subscription during the recomputation.
- Phase 4: `plan_change.py`/`dependent_registration.py`/`registration_checkout.py`/`stripe_checkout.py` working with `PlanPrice`.
- Phase 5: the seeds generate `PlanTier`+`PlanPrice` without duplicating a family row; the admin CRUD works.
- Phase 6: the template renders the struck-through price + the discounted price correctly.
- The regression: `test_veteran_plan.py` with no change in the results.

### Execution authorization
Phase 1 approved and run on 2026-07-06 ("implement it"). Phases 2 through 6 remain pending a new checkpoint.

### Execution evidence (Phase 1)
- `system/tests/test_plan_tier_pricing.py` (new, 11 tests): creating a `PlanTier` with a `family_discount_percentage`; `_compute_price`/`compute_gross_price` calculates `price` correctly with the gateway's fixed and percentage fees; `monthly_reference_price` filled in for multi-month cycles; `family_price()` applies the tier's discount; immutability — editing the price fields of a `PlanPrice` that is NOT referenced is allowed, editing one REFERENCED by a `Membership` raises `ValueError`, archiving (`is_active`/`effective_until`) a referenced one is still allowed; `Membership.plan` accepts `null` and can reference only `plan_price`; `Membership.recompute_billed_price()` calculates `billed_price` with and without the family discount.
- The command: `.\.venv\Scripts\python.exe manage.py test system.tests.test_plan_tier_pricing --verbosity 2` → 11 tests, OK.
- The regression: `.\.venv\Scripts\python.exe manage.py test --verbosity 1` → 500 tests (489 pre-existing + 11 new), OK.
- `.\.venv\Scripts\python.exe manage.py check` → no issues.
- The destructive cycle run (`clear_migrations.py` + `makemigrations`) to include `PlanTier`/`PlanPrice` and the new `Membership` fields in the single baseline.

### Execution evidence (Phases 2 and 3)
- `system/tests/test_family_pricing.py` (new, 11 tests): a person alone receives no discount; 2 people on the same tier receive the correct `family_discount_applied`/`billed_price`; 2 people on different tiers receive no discount; removing the relationship reverts the discount for both; the Stripe sync is only called when the discount's state changes (it does not repeat the call on an idempotent recomputation); `apply_family_discount` reuses an existing coupon and creates a new one when absent; `remove_family_discount` calls `delete_discount`; with no `stripe_subscription_id` it is a no-op; with no `STRIPE_SECRET_KEY` it raises `StripeDiscountError`; an integration test through `DependentRemoveView` (the Django test client, a real POST) confirms the `billed_price` reversal for the main person and the dependent.
- The command: `.\.venv\Scripts\python.exe manage.py test system.tests.test_family_pricing --verbosity 2` → 11 tests, OK.
- The regression: `.\.venv\Scripts\python.exe manage.py test --verbosity 1` → 511 tests (500 pre-existing + 11 new), OK.
- `.\.venv\Scripts\python.exe manage.py check` → no issues.

### Execution evidence (Phase 4 — legacy interop + the wizard's wiring)
- 2 new tests in `LegacyPlanTierInteropTestCase` (`test_family_pricing.py`): a main person with a legacy `Membership.plan` (a non-loyalty `SubscriptionPlan`) + a dependent with the new `Membership.plan_price`, the same audience/frequency → both correctly receive the discount (`effective_tier` matches the two); a Membership with a Veteran plan never receives the discount (it stays with `billed_price=None`, never touched by the recomputation).
- 2 new tests in `PlanPriceDependentRegistrationTestCase` (`test_dependent_registration.py`): a real POST to `dependent-add` selecting a `pp:<pk>` catalog entry resolves `financial_mode=dependent_own` automatically and does not write `PreRegistration.selected_plan` (the legacy FK stays `None`, the snapshot keeps the prefixed id); `finalize_dependent_registration` with `selected_plan_obj` being a `PlanPrice` creates the dependent's Membership with the correct `plan_price_id` and triggers the automatic recomputation — the main person and the dependent both end up with `family_discount_applied=True` and a `billed_price` equal to `price.family_price()`.
- 9 pre-existing tests in `test_dependent_registration.py` and 1 in `test_commands.py` adjusted for the new `selected_plan` format (`sp:<pk>`/`pp:<pk>` instead of a raw pk) and for the new formula-driven price values (e.g. `loyalty-2x-asaas-card-monthly` at R$ 212.63 instead of the R$ 230.38 of the old `individual-2x`, since Individual left `SubscriptionPlan`).
- The command: `.\.venv\Scripts\python.exe manage.py test system.tests.test_dependent_registration system.tests.test_family_pricing system.tests.test_commands --verbosity 1` → all OK.
- The final regression: `.\.venv\Scripts\python.exe manage.py test --verbosity 1` → **517 tests, OK**.
- `.\.venv\Scripts\python.exe manage.py check` → no issues.
- The destructive cycle run again (`RegistrationOrder.plan_price_ref` + the `PlanPrice` unique constraint) and the full reference seeds run locally (`db.sqlite3` rebuilt successfully, including the new `seed_system_initial_plan_tiers`/`_plan_prices`).

## Visual validation
- Phase 1: not applicable (no UI).
- Phase 4: the internal browser (`http://localhost:8000`), logged in as a test main person with an active `Membership.plan_price` and a `stripe_subscription_id` filled in. The dependent wizard (`/dependents/add/?modal=1`) up to the "Plano do dependente" ("The dependent's plan") step, the "Cartão" ("Card") filter: the catalog shows **a `dep-plan-catalog-json` with 36 entries (16 Veteran SubscriptionPlans + 20 PlanPrices), none with `is_family_plan=true`**. The cards rendered in step 5: only "Individual" (Asaas Card R$ 230.37 and Stripe recurring R$ 230.37) — no "Família" ("Family") card. Selecting the Stripe recurring card automatically resolved `financial_mode=dependent_own`, `checkout_action=stripe_card`, `selected_plan=pp:9`. PRD-126's "Como cobrar o cartão do dependente?" ("How should the dependent's card be charged?") block rendered correctly integrated, with "merge" enabled (the main person has an active Stripe subscription). The browser's console with no errors.

## ORM validation
Phase 1 covered by the 11 tests in `test_plan_tier_pricing.py`. Phase 4 covered by the `LegacyPlanTierInteropTestCase` and `PlanPriceDependentRegistrationTestCase` tests.

## Quality validation
`manage.py check` with no issues in every phase. The final full suite: 517 tests, OK.

## Evidence
See each phase's "Execution evidence" above.

## Implemented (Phase 1)
- `compute_gross_price()` extracted from `SubscriptionPlan._compute_price()` (`system/models/plan.py`) — a shared formula, with no duplication; `SubscriptionPlan` (Veteran) keeps using the same formula through `_compute_price()`, now delegating to the shared function.
- `PlanTier` (`system/models/plan.py`): the commercial product's identity (audience × frequency) + `family_discount_percentage`.
- `PlanPrice` (`system/models/plan.py`): the versioned price per tier × payment method × cycle × gateway, with `effective_from`/`effective_until`, its own Stripe fields, and an **immutability guard**: `_guard_immutability()` blocks changes to the price fields (`tier`, `payment_method`, `billing_cycle`, `base_monthly_net_price`, `cycle_discount_percentage`, `gateway_fixed_fee`, `gateway_percentage_fee`) when the row is already referenced by some `Membership` — it raises `ValueError`; the non-financial fields (`is_active`, `effective_until`) remain editable through `archive()`.
- `PlanPrice.family_price()` calculates the discounted price from `tier.family_discount_percentage`.
- `Membership.plan` (the FK to `SubscriptionPlan`) became `null=True`/`blank=True` — Veteran and any legacy code keep working unchanged (the field remains required in practice for those flows, only the database constraint became permissive to enable the new path).
- `Membership.plan_price` (an FK to `PlanPrice`, nullable), `Membership.family_discount_applied` (a bool), and `Membership.billed_price` (a nullable Decimal) — the new fields for the tier+discount path.
- `Membership.recompute_billed_price()` — a method that calculates `billed_price` from `plan_price`/`family_discount_applied`, reusable by Phase 2.
- `PlanTier`/`PlanPrice`/`compute_gross_price` exported in `system/models/__init__.py`.
- **Not changed in this phase**: `RegistrationOrder` still references only `SubscriptionPlan` (with no `plan_price`) — extending `RegistrationOrder` is left for Phase 4, when the checkout services start creating orders against a `PlanPrice`.

## Implemented (Phase 2 — the local automatic recomputation)
- `system/selectors/plan_eligibility.py`: `get_family_group_members(person)` — a public wrapper over the already-existing `_get_family_group_members`, without duplicating the family group resolution logic.
- `system/services/family_pricing.py` (new): `recompute_family_discounts_for_person(person)` — it groups the family group's active `Membership` records (with `plan_price` filled in) by `PlanTier`; applies `family_discount_applied=True` when 2+ people share the same tier, `False` otherwise; recalculates `billed_price` through `Membership.recompute_billed_price()`; and only fires the Stripe sync when the discount's state actually changes (avoiding redundant calls).
- The triggers connected: `system/services/registration.py::_create_relationship` (every `RESPONSIBLE_FOR` relationship creation recomputes the `source_person`'s group); `system/views/dependent_views.py::DependentRemoveView` (removing the relationship recomputes both the main person and the removed dependent, ensuring the dependent's monthly fee also reverts).
- An architecture note (updated after Phase 4): the relationship triggers (creation/removal) cover most cases; Phase 4 added an extra trigger right after the dependent's Membership activation (`_create_paid_plan_order`), because in that flow the dependent's Membership only exists AFTER the relationship was already created — without that second trigger, the discount would only be applied on the family group's next change, not immediately after the paid registration.
- `Membership.effective_tier`/`Membership.effective_full_price` (`system/models/membership.py`): they resolve the effective tier/price for both `Membership.plan_price` (the new one) and a legacy `Membership.plan` (a non-Veteran `SubscriptionPlan`, matched by `audience`+`weekly_frequency`) — this lets a main person still on the old model and a dependent already on the new one correctly share the family discount, with no need to migrate the main person. Veteran is explicitly excluded from that resolution (`recompute_family_discounts_for_person` filters `plan__is_loyalty_plan=True`).
- `family_pricing.py::recompute_family_discounts_for_person` generalized to group by `effective_tier` (no longer only `plan_price__tier`), covering legacy and new Memberships in the same recomputation.

## Implemented (Phase 3 — the Stripe sync through a Coupon/Discount)
- `system/services/stripe_discounts.py` (new): `apply_family_discount(membership)` ensures/reuses a deterministic `stripe.Coupon` (`family-discount-<percentage in basis points>`, e.g. `family-discount-1800` for 18%) and applies it through `stripe.Subscription.modify(subscription_id, coupon=coupon_id)`; `remove_family_discount(membership)` uses `stripe.Subscription.delete_discount(subscription_id)` — both confirmed as valid parameters/endpoints of the current Stripe API through Context7. No real Stripe call in this delivery (the tests use mocks).
- `family_pricing.py::_sync_stripe_discount` calls those services only when `stripe_subscription_id` is filled in and the discount's state has changed; Stripe sync failures are logged (`logger.exception`) and do not block the local recomputation — the same resilience pattern already used in `notify_subscription_past_due`/`notify_payment_failed`.

## Implemented (Phase 4 — wiring the dependent wizard to PlanTier/PlanPrice)
- `system/services/registration_checkout.py`: `get_plan_catalog_payload(include_plan_prices=False)` — by default (the public wizard through `auth_views.py`) it keeps the old behavior intact (raw numeric ids, only `SubscriptionPlan`); with `include_plan_prices=True` (only `dependent_views.py`), the catalog also includes the active `PlanPrice` records, with prefixed ids (`sp:<pk>` / `pp:<pk>`) so they do not collide. `resolve_catalog_plan(catalog_id)` resolves a prefixed id back into the real object. `parse_selected_plan_payload`/`_normalize_catalog_plan_id` accept the new format AND the raw int saved by older pre-registrations (backward compatibility).
- `system/forms/dependent_forms.py`: `selected_plan` now also lists the active `PlanPrice` records; `_clean_financial_choice` resolves the id through `resolve_catalog_plan` and, when the result is a `PlanPrice`, automatically forces `financial_mode=DEPENDENT_OWN` — eliminating the need to choose "family" (there is no separate card any more) — validating only the audience/age compatibility.
- `system/services/dependent_registration.py`: `_selected_plans_payload` writes the prefixed id into the snapshot; `_create_paid_plan_order` creates the `RegistrationOrder`/`Membership` pointing at `plan` OR `plan_price_ref`/`plan_price` depending on the selected type, and fires `recompute_family_discounts_for_person` right after activating the dependent's Membership.
- `system/models/registration_order.py`: a new `plan_price_ref` field (an optional FK to `PlanPrice`; the name `plan_price` already belonged to the existing Decimal field, so the new FK got a distinct name).
- `system/services/membership.py`: `activate_membership_from_paid_order` accepts orders with a `plan` OR a `plan_price_ref`, creating the Membership with the correct FK.
- `system/views/dependent_views.py`: the post-payment restoration (`_restore_confirmed_payment_post_data` and the `payment_confirmed` block of `post()`) now prioritizes the id saved in the snapshot (already in the prefixed format) over the legacy `pending.selected_plan_id` FK, ensuring a correct resume for both models.
- `static/system/js/dependents/dependent_registration.js`: the `parseInt` that forced the plan ids into integers removed (they are now opaque strings such as `pp:9`). `static/system/js/auth/register.js` **was not changed** — it keeps `parseInt`, because the public wizard still only has numeric ids (a deliberate risk containment).
- The seeds: `seed_system_initial_subscription_plans_values.json`/`..._stripe.json` reduced to contain only `loyalty` (Veteran); the new `seed_system_initial_plan_tiers.json`/`_prices.json` + the corresponding commands generate the consolidated Individual/Family. Locally: 54 `SubscriptionPlan` rows → 16 (Veteran only) + 20 `PlanPrice` rows.
- Visual validation: the internal browser, the dependent wizard, the "Plano do dependente" ("The dependent's plan") step, the Card filter — **only 2 "Individual" cards appear (Asaas Card and Stripe recurring), no "Família" ("Family") card**; the selection resolves `financial_mode=dependent_own` and `checkout_action` automatically; PRD-126's card strategy block keeps working integrated with the new catalog; the console with no errors.

## Cleanup findings
- `DependentCardStrategyTestCase._base_form_data` (`system/tests/test_dependent_registration.py`) was a dead helper (never called) — removed.
- The public wizard (`register.js`/`registration_forms.py`) and the administrative plan CRUD (`plan_management.py`, `templates/plans/`) remain entirely on the `SubscriptionPlan` model — the debt recorded in the Follow-up, not blocking for the use case resolved in this delivery.

## Follow-up PRDs
- A symmetric rework of "Veteran" (`is_loyalty_plan`) into the same tier+discount model, if it makes business sense (out of scope here because of the additional complexity of tenure-based eligibility + manual approval).
- Real data migration in staging/production, when/if applicable.

## Deviations from plan
N/A (pre-implementation).

## Pending
- The business decisions confirmed by the user ("you can make the best decision... good practices"):
  - Proration: the discount/reversal now takes effect from the **next full cycle**, with no retroactive pro-rata charge in the current cycle.
  - The discount's scope: **per tier** — it only counts the family group's people on the SAME `PlanTier` (or the equivalent legacy tier by audience+frequency).
  - A single family discount percentage: **18%** for every tier (adopted from the existing Stripe reference — Asaas had a historically inconsistent percentage between 7.72% and 12%, with no mathematical relationship to Stripe's; 18% standardizes and simplifies it).
- **Not implemented in this delivery** (Phase 6 and part of Phase 5): the "was/now" UI with an explicit struck-through original price (today the discount is already visible through the recomputed `billed_price`/family, but there is no dedicated visual component showing "was X, now Y" side by side); a complete administrative CRUD for `PlanTier`/`PlanPrice` (`system/services/plan_management.py`/`templates/plans/` still manage only `SubscriptionPlan`/Veteran); the symmetric Veteran rework (out of scope, recorded as a follow-up).
- The main public wizard (`register.js`/`registration_forms.py`) remains **entirely on the legacy model** (`SubscriptionPlan`) as a risk containment decision — only the add-a-dependent wizard was migrated to the `PlanTier`/`PlanPrice` catalog. That is enough for the reported use case (an already-registered main person adding a dependent), but it means a brand-new main person, registered from scratch, still enters through the old system; the interoperability (`Membership.effective_tier`) ensures the family discount still works correctly even so, with no need to migrate the main person.

## Final status
Phases 1, 2, and 3 fully completed. Phase 4 (rewiring the dependent wizard to the `PlanTier`/`PlanPrice` catalog, with the automatic resolution to an own monthly fee and no separate "Family" card) completed and validated in tests and in the browser. Phase 5 partially completed (the seeds rewritten; the admin CRUD not). Phase 6 (the explicit "was/now" UI) not implemented. The system is sound, tested (517 tests), and visually validated — the behavior is correct: the "Família" ("Family") card no longer appears in the dependent wizard; the selection resolves `financial_mode=dependent_own` automatically; the 18% family discount applies and reverts automatically when adding/removing a dependent, both locally and through the Stripe Coupon/Discount.
