# PRD-126: Preventing a duplicate Stripe charge on the same card between the main person and the dependent

## Summary
When a dependent contracts their own monthly fee (`DependentFinancialMode.DEPENDENT_OWN`) paying with the main person's same credit card, the two recurring Stripe subscriptions tend to charge on the same day/time, risking a refusal by the card network for duplicate operations on the same card. This PRD defines how the guardian chooses, at the moment of the dependent's registration, between merging the charge into a single Stripe subscription or keeping two subscriptions with a staggered billing time.

## Demand type
Payment risk prevention (a preventive architectural fix, with no incident recorded in production yet).

## Current problem
- `system/services/dependent_registration.py` creates the dependent's **own** `RegistrationOrder` and `Membership` when `financial_mode = DEPENDENT_OWN`.
- `system/services/stripe_checkout.py::create_subscription_session_for_pre_registration` always creates a **new Stripe Checkout Session** with `mode=subscription` for whoever is paying, without parameterizing `billing_cycle_anchor`.
- `system/services/stripe_sync.py::ensure_stripe_customer` creates a **new Stripe Customer per `Person`**, even when the main person and the dependent enter the same physical card at checkout.
- No model (`Membership`, `MembershipInvoice`, `Person`) stores a card identifier/fingerprint, nor is there any "same card" check between people.
- The main person and the dependent are usually registered in the same session, so the two Stripe subscriptions' `billing_cycle_anchor` values end up almost identical. In the following cycles the two charges fall on the same day/time; if they use the same real card, the network may refuse one of the two because they look like duplicate authorizations.
- The real state verified in the local database: Bruno (pk=8) has an active `Membership` (a family plan); Lucas (pk=9, the dependent) has no `Membership` of his own today — there is no collision in the current test data because the scenario is `family`, not `DEPENDENT_OWN`. The risk is real in the `DEPENDENT_OWN` code path, not in the current data.

## Goal
In the dependent's registration, when `financial_mode = DEPENDENT_OWN` and the payment method is a card, the guardian chooses between three card strategies:
1. **A new card** (the current default, with no behavior change).
2. **The same card — merge into 1 subscription**: the dependent's plan amount is added as an extra item on the main person's already-existing Stripe subscription (`POST /v1/subscription_items`). One invoice per cycle, the main person's same `billing_cycle_anchor`, with no new Checkout Session.
3. **The same card — keep separate, stagger the time**: the two Stripe subscriptions keep existing, but the dependent's Checkout Session receives a `subscription_data.billing_cycle_anchor` shifted a few hours from the main person's cycle, avoiding the exact time coincidence.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/PRD-STANDARD.md`
- `docs/prd/README.md`
- `docs/prd/PRD-124-dependent-family-plan-upgrade.md`
- `docs/prd/PRD-125-remote-synchronization-of-the-stripe-family-upgrade.md`
- `system/models/membership.py`
- `system/services/stripe_sync.py`
- `system/services/stripe_checkout.py`
- `system/services/stripe_webhooks.py`

### Adjacent files consulted
- `system/services/dependent_registration.py` (the `DEPENDENT_OWN` flow, the creation of the dependent's own `RegistrationOrder`/`Membership`)
- `system/services/registration_checkout.py`
- `system/services/membership.py` (`activate_membership_from_session`, `activate_membership_from_paid_order`, `record_invoice_from_stripe`, `upsert_membership_from_stripe_subscription`, `mark_membership_canceled`)
- `system/constants.py` (`DependentFinancialMode`)
- `system/views/home_views.py` (`_build_payment_history_items`, `_build_billing_context` — the consumers of `MembershipInvoice`)

### Internet / official documentation
- Stripe: `subscription_data.billing_cycle_anchor` in a Checkout Session with `mode=subscription` — `https://docs.stripe.com/get-started/use-cases/saas-subscriptions` and `https://docs.stripe.com/billing/quickstart`. It confirms that the first full cycle's date can be fixed when creating the Checkout Session.
- Stripe: `POST /v1/subscription_items` — `https://docs.stripe.com/api/subscription_items/create` and `https://docs.stripe.com/billing/subscriptions/quantities`. It confirms that an item/price can be added to an already-existing subscription, generating a single invoice per cycle with multiple items.

### Context7 / MCPs / tools verified
- Context7 `/websites/stripe` consulted for `billing_cycle_anchor` in a Checkout Session subscription mode and for `subscription_items` (creation and the single-invoice-with-multiple-items behavior). Both mechanisms exist and are supported by the current Stripe API.

### Limitations found
- The local environment has no active `STRIPE_SECRET_KEY` for the test records (Bruno/Lucas), so it is not possible to validate against the real Stripe in this PRD; the planned validation is through mocks/fixtures and the local ORM.
- The current flow uses exclusively the Stripe Checkout Session (hosted) to create subscriptions; it never calls `Subscription`/`SubscriptionItem` directly. The "merge" strategy introduces the first billing path **without an external redirect** (a server-to-server call), which changes the payment confirmation experience for that specific case (no Stripe Checkout success screen).
- `MembershipInvoice` is today 1-to-1 with `Membership`. A merged Stripe invoice has multiple `lines`, one per item/price — the adopted solution (see Plan) splits the invoice per line instead of changing the `MembershipInvoice` schema.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
The user identified the risk, asked for a simulation to avoid the problem, and explicitly confirmed that **both "same card" strategies must be available simultaneously**, with the guardian choosing which to use at the moment of the dependent's registration.

## Execution prompt
### Persona
A senior Django agent working on Stripe payment integration, with attention to webhook idempotency and to not regressing the existing checkout flow.

### Action
Implement the card strategy choice in the registration of a dependent with their own plan, and the three corresponding billing paths (new card / merge / stagger).

### Context
A dependent with `financial_mode = DEPENDENT_OWN` today always generates a new, independent Stripe Checkout Session. The main person must have an active recurring Stripe subscription (`stripe_subscription_id` filled in) for the "merge" option to be offered; without that, only "new card" and "stagger" make sense (the merge option requires an existing subscription to receive the extra item).

### Constraints
- Do not change the "new card" path's behavior (zero regression).
- Do not invent a new commercial price.
- The business rule in the backend; the form/JS only collects the choice and displays the state.
- `system/migrations/0001_initial.py` is the project's single baseline — any new field on `Membership` is added there and regenerated locally through the destructive cycle (`clear_migrations` + `makemigrations`), never as an incremental migration (see `[[feedback_migrations_policy]]`).
- The webhooks must stay idempotent (`StripeWebhookEvent` already guarantees that by `event_id`); the change to "multiple Memberships per `stripe_subscription_id`" must not break that guarantee.
- Do not touch a real payment, the Stripe dashboard, or the staging/production environment without separate explicit authorization.

### Acceptance criteria
- [ ] The dependent wizard (`financial_mode = DEPENDENT_OWN`, card payment method) shows the choice "Novo cartão" ("New card") / "Mesmo cartão — fundir" ("Same card — merge") / "Mesmo cartão — escalonar horário" ("Same card — stagger the time").
- [ ] "Merge" is offered only when the main person has an active `Membership` with `stripe_subscription_id` filled in.
- [ ] "Merge": a call to `POST /v1/subscription_items` on the main person's subscription; no new Stripe Checkout Session is created for the dependent; the dependent gets an active local `Membership` referencing the main person's `stripe_subscription_id` and their own `stripe_subscription_item_id`.
- [ ] "Stagger": the dependent's Checkout Session receives a `subscription_data.billing_cycle_anchor` shifted (parameterizable, e.g. +4h) from the main person's cycle; two distinct Stripe subscriptions keep existing.
- [ ] The `invoice.paid` webhook knows how to split a Stripe invoice with multiple `lines` into one `MembershipInvoice` per `Membership` (through `stripe_subscription_item_id`), without breaking the existing single-item invoice path.
- [ ] The `customer.subscription.updated`/`customer.subscription.deleted` webhook updates **all** the `Membership` records linked to the same `stripe_subscription_id`, not just one.
- [ ] A tampered POST trying to force "merge" when the main person has no active Stripe subscription is rejected in the backend.
- [ ] The new and existing focused tests (`test_dependent_registration`, `test_home_dependents_section`) pass.
- [ ] `manage.py check` passes.
- [ ] The full suite with no regression.

### Expected evidence
- The real test commands and results (Red before the production code, Green after).
- The local ORM confirming the correctly split `Membership`/`MembershipInvoice` for the "merge" case.
- A mock/fixture of the Stripe webhook payload (a multi-line `invoice.paid`, `customer.subscription.updated`) exercising the new split.
- No real call to Stripe (the local environment has no active key for these records) — validation through mocks.

### Output format
The implementation + the real evidence + the unvalidated limitations.

## Scope
- A new field on `Membership`: `stripe_subscription_item_id` (to locate the specific line inside a potentially shared subscription).
- A new `DependentCardStrategy` enum (`new_card`, `same_card_merged`, `same_card_staggered`) in `system/constants.py`.
- `system/services/dependent_registration.py`: accept and validate the card strategy when `financial_mode = DEPENDENT_OWN` + a card payment.
- `system/services/stripe_checkout.py`: the new "merge" path (a direct call to `SubscriptionItem.create`, with no Checkout Session) and the `billing_cycle_anchor` parameterization on the "stagger" path.
- `system/services/stripe_webhooks.py` + `system/services/membership.py`: split a multi-line invoice per `Membership`; update all the `Membership` records of a shared `stripe_subscription_id`.
- The dependent's form/wizard (`templates/dependents/dependent_registration.html`, `static/system/js/dependents/dependent_registration.js`): a new card strategy step/selection.
- Focused tests covering the three paths and the rejection of tampering.

## Out of scope
- Automatic "same card" detection through the Stripe fingerprint (the choice is always the guardian's explicit one, never inferred).
- Retroactively synchronizing already-existing subscriptions that already collide (this PRD prevents new registrations; migrating historical data is a separate follow-up, if necessary).
- Changing the Asaas flow (this is exclusive to recurring Stripe cards).
- Implementing without explicit approval of this plan.

## Impacted files
- `system/constants.py`
- `system/models/membership.py`
- `system/migrations/0001_initial.py`
- `system/services/dependent_registration.py`
- `system/services/stripe_checkout.py`
- `system/services/stripe_webhooks.py`
- `system/services/membership.py`
- `system/forms/dependent_forms.py`
- `templates/dependents/dependent_registration.html`
- `static/system/js/dependents/dependent_registration.js`
- `system/tests/test_dependent_registration.py`
- `system/tests/test_commands.py` (if it affects the seeds/migrations)

## Risks and edge cases
- A main person with no `stripe_subscription_id` (they paid through Asaas, or have no active plan, or have a pending payment) trying to "merge" — it must be blocked in the backend, not just hidden in the UI.
- Cancelling the dependent when "merged": remove only the dependent's `subscription_item`, without cancelling the main person's whole subscription.
- Cancelling/expiring the main person's subscription when there is a merged dependent: the dependent loses their active billing along with it — it needs an explicit warning/handling (record it as a pending item if not covered in this delivery).
- A partial refund (`amount_refunded`) on a multi-line invoice: the split must reflect the refund on the correct line, not across the whole invoice.
- A failure to create the `subscription_item` (e.g. the network, Stripe down) must not leave the dependent in a locally "paid" state with no corresponding remote charge.

## Rules and constraints
- The card strategy only exists for `financial_mode = DEPENDENT_OWN` + a card payment; `family_existing`/`family_upgrade` do not use this contract (they already share the same `Membership`, with no duplication).
- `DependentCardStrategy` is validated in the backend; the JS only reflects the choice.
- No incremental migration — a schema change enters the single baseline per `CLAUDE.md` section 6.

## Plan
1. Add `DependentCardStrategy` to `system/constants.py` and `stripe_subscription_item_id` to `Membership` (regenerate the local baseline).
2. Extend `system/forms/dependent_forms.py` and `dependent_registration.py` to accept/validate the strategy, conditioned on the `financial_mode`/payment method/the existence of the main person's Stripe subscription.
3. Implement in `stripe_checkout.py`:
   - `merge_dependent_into_existing_subscription(owner_membership, dependent_plan, dependent_person)` → `SubscriptionItem.create`, with no Checkout Session.
   - An optional `billing_cycle_anchor` parameter in `create_subscription_session_for_pre_registration` for the "stagger" path.
4. Update `system/services/membership.py`/`stripe_webhooks.py`:
   - `record_invoice_from_stripe` now iterates `invoice["lines"]["data"]`, resolving the `Membership` through `stripe_subscription_item_id` when there is more than one line.
   - `upsert_membership_from_stripe_subscription`/`mark_membership_canceled` operate on `Membership.objects.filter(stripe_subscription_id=...)` (all the lines), not `.get()`.
5. Adjust the wizard (`dependent_registration.html`/`.js`) to show the choice where applicable.
6. Write the tests (Red) before each production snippet; implement the minimum; run the focused and the full suite (Green).
7. Validate the wizard's new step in the internal browser (the default state, "merge" enabled/disabled per eligibility, "stagger").

## Test plan
### Tests to author
- The wizard blocks "merge" when the main person has no `stripe_subscription_id`.
- A tampered POST forcing `same_card_merged` with no active Stripe subscription on the main person is rejected.
- A mock of `SubscriptionItem.create` called correctly for "merge"; no Checkout Session created on that path.
- A mock of the Checkout Session receiving the correct `billing_cycle_anchor` for "stagger".
- The `invoice.paid` webhook with a 2-line invoice creates 2 `MembershipInvoice` records, one per `Membership`, with the correct amounts.
- The `customer.subscription.updated`/`deleted` webhook updates both `Membership` records of a shared `stripe_subscription_id`.
- The "new card" path stays with no regression (the existing `DEPENDENT_OWN` tests).

### Execution authorization
Explicitly approved by the user on 2026-07-06 ("I approve the payment rule change").

### Execution evidence
- `system/tests/test_membership_shared_subscription.py` (new, 6 tests): `activate_membership_from_paid_order` writes/omits `stripe_subscription_id`/`stripe_subscription_item_id`; `record_invoice_from_stripe` splits a multi-line invoice per `Membership` through `stripe_subscription_item_id` and preserves the single-invoice behavior; `upsert_membership_from_stripe_subscription` and `mark_membership_canceled` update every `Membership` sharing a `stripe_subscription_id`.
- `system/tests/test_stripe_checkout_merge.py` (new, 3 tests): `merge_plan_into_existing_subscription` calls `stripe.SubscriptionItem.create` with the correct parameters and raises `StripeCheckoutError` with no main person's subscription or no plan `stripe_price_id`.
- `system/tests/test_dependent_registration.py` (`DependentCardStrategyTestCase`, new, 6 tests): the form validation rejects `same_card_merged` with no active Stripe subscription on the main person and accepts it with an active subscription; `card_strategy` always falls back to `new_card` outside the `dependent_own` + card flow; `create_pre_registration_plan_payment` merges correctly (a mock) and writes `plan_payment` into the snapshot; `create_pre_registration_plan_payment` staggers the `billing_cycle_anchor` correctly from the main person's `current_period_end` + 4h; `finalize_dependent_registration` synchronizes the snapshot's `stripe_subscription_id`/`stripe_subscription_item_id` to the dependent's `Membership`.
- The command: `.\.venv\Scripts\python.exe manage.py test system.tests.test_membership_shared_subscription system.tests.test_stripe_checkout_merge system.tests.test_dependent_registration.DependentCardStrategyTestCase --verbosity 2` → 15 new tests, all OK.
- The regression: `.\.venv\Scripts\python.exe manage.py test --verbosity 1` → 489 tests (474 pre-existing + 15 new), OK.
- `.\.venv\Scripts\python.exe manage.py check` → no issues.
- The destructive cycle run for the new `stripe_subscription_item_id` field: `clear_migrations.py` + `makemigrations` + the reference seeds (1 through 18) recreated locally.

## Visual validation
- The internal browser: logged in as a test main person with an active `Membership` (`stripe_subscription_id` filled in), the dependent wizard up to the "Plano do dependente" ("The dependent's plan") step, the "Cartão" ("Card") filter selected, the "Individual RECORRENTE" ("Individual RECURRING") card (a Stripe plan) selected.
- The "Como cobrar o cartão do dependente?" ("How should the dependent's card be charged?") block appears with the 3 options (New card / Merge / Stagger), all enabled because the main person has an active Stripe subscription.
- Selecting "Mesmo cartão do responsável — fundir em 1 cobrança" ("The guardian's same card — merge into 1 charge") correctly updates the hidden `id_card_strategy` field to `same_card_merged`.
- The internal browser's console with no errors.
- Not validated in this cycle: a real payment submission (it requires a configured `STRIPE_SECRET_KEY` and a real Stripe environment — outside the local scope); the behavior of the disabled "merge" block when the main person does NOT have an active Stripe subscription (covered by an automated form test, not replicated manually in the browser).

## ORM validation
Covered by the automated tests cited above (the creation/update of `Membership`/`MembershipInvoice` through the local ORM, with no real Stripe call).

## Quality validation
`manage.py check` with no issues after all the model/service/form/view/template/JS changes.

## Evidence
See "Execution evidence" and "Visual validation" above.

## Implemented
- `DependentCardStrategy` (`system/constants.py`): `new_card`, `same_card_merged`, `same_card_staggered`.
- `Membership.stripe_subscription_item_id` (`system/models/membership.py`), with the baseline migration regenerated.
- `activate_membership_from_paid_order` accepts an optional `stripe_subscription_id`/`stripe_subscription_item_id`.
- **A fix for a pre-existing gap** (a scope expansion approved by the user): `finalize_pre_registration` (`system/services/pre_registration.py`) and `_create_paid_plan_order` (`system/services/dependent_registration.py`) now synchronize the `plan_payment` snapshot's `stripe_subscription_id`/`stripe_subscription_item_id` to the newly activated `Membership` — before, that field was never filled in by the pre-registration flow (only by the direct `RegistrationOrder` flow, used by the plan change).
- `merge_plan_into_existing_subscription` and an optional `billing_cycle_anchor` in `create_subscription_session_for_pre_registration` (`system/services/stripe_checkout.py`).
- `record_invoice_from_stripe` splits a multi-line invoice per `Membership`; `upsert_membership_from_stripe_subscription`, `mark_membership_canceled`, and `mark_invoice_failed` update every `Membership` sharing a `stripe_subscription_id` (`system/services/membership.py`).
- `create_pre_registration_plan_payment` (`system/services/registration_checkout.py`) gains `card_strategy`/`owner`; the "merge" branch calls the merge and returns a local success URL (with no Checkout Session); the "stagger" branch computes the `billing_cycle_anchor` through `compute_staggered_billing_cycle_anchor` (a 4h offset over the main person's next cycle).
- `DependentRegistrationForm.card_strategy` + `_clean_card_strategy` (`system/forms/dependent_forms.py`): it validates that "merge" is only accepted with an active Stripe subscription on the main person.
- `_build_owner_plan_context` (`system/views/dependent_views.py`) exposes `owner_has_stripe_subscription` to the wizard.
- The wizard (`templates/dependents/dependent_registration.html`, `static/system/js/dependents/dependent_registration.js`, `static/system/css/dependents/dependent_registration.css`): the "Como cobrar o cartão do dependente?" ("How should the dependent's card be charged?") block with the 3 options, enabled only when `financial_mode=dependent_own` + `checkout_action=stripe_card`, disabling "merge" when the main person has no active Stripe subscription.

## Cleanup findings
No functional residue introduced in the scope. The `stripe_invoice_id` of merged invoices uses the synthetic key `f"{invoice_id}::{item_id}"` (documented in the code) to preserve the field's uniqueness without requiring an additional schema change.

## Follow-up PRDs
- Migrate/fix already-existing subscriptions in production that already collide on the same card (out of scope — this delivery prevents only new registrations).
- Synchronize `Person.stripe_customer_id`/`Membership.stripe_customer_id` from the pre-registration flow (today the subscription Checkout Session does not pass an explicit `customer=`; a related gap, not blocking for this delivery).

## Deviations from plan
The scope was expanded during the implementation, with the user's explicit approval: it was necessary to fix the pre-existing gap where `Membership.stripe_subscription_id` was never synchronized from a payment confirmed through the pre-registration (`finalize_pre_registration`/`_create_paid_plan_order`) — without that fix, the "merge" option would never have a real `stripe_subscription_id` from the main person to use.

## Pending
- End-to-end validation with the real Stripe (a real checkout, a real webhook) — not runnable in this local environment without a configured test `STRIPE_SECRET_KEY`.
- A closed business definition of the 4h offset used in the "stagger" path (a pragmatic value adopted, not confirmed as the final rule).
- The synchronization of already-existing subscriptions that already collide (out of scope, see the Follow-up).

## Final status
Completed (the local implementation + the automated tests + the wizard's visual validation). The end-to-end validation with the real Stripe is pending a configured environment.
