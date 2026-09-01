# PRD-133: Payment method indicator, Stripe card change, and failed-payment history

## Summary
This is a direct complement to PRD-132 (free plan transitions and tuition pauses), requested by the user while reviewing the tuition screen. Currently, there is no indication of which **payment method** and **gateway** the client uses (PIX/Card, Asaas/Stripe), and there is no way for the client to **change the card** for a recurring Stripe subscription without changing the plan or pausing it. When a Stripe client's card is declined, the system only changes `Membership.status` to `past_due` — leaving no trace in the history and giving the client no guidance about what to do.

## Demand type
New feature and gap correction (explicitly requested by the user, with two concrete scenarios).

## Current problem
- `_build_billing_tab` (`system/services/membership.py`) does not expose the payment method or gateway — the tuition card shows only the plan name.
- There is no Stripe card-change mechanism — no view, service, or Billing Portal.
- `mark_invoice_failed` (`system/services/membership.py`) only changes `Membership.status` to `past_due`; it creates no record in `MembershipInvoice` or any other model, so the failed charge appears nowhere in the history.
- The existing "Pagar agora" ("Pay now") button appears only when there is a `tab.pending_order` (an Asaas `RegistrationOrder`). A failed recurring Stripe charge never generates that type of order, so the client had no visible action when the card failed.
- **Pre-existing bug discovered during implementation**: `_build_payment_history_items` (`system/views/home_views.py`) accessed `membership.plan.display_name` unconditionally, which caused the home page to return HTTP 500 as soon as any `MembershipInvoice` existed for a `PlanPrice`-based `Membership` (the sixth occurrence of the same bug family found in PRD-127/129/130/132).
- **Gap discovered during live validation**: the Stripe confirmation flow for the public wizard (`_handle_pre_registration_checkout_completed` in `stripe_webhooks.py` plus `finalize_pre_registration` in `pre_registration.py`) never captured or propagated `stripe_customer_id` to the `Membership`; it stored only `stripe_subscription_id`. Without `stripe_customer_id`, the new card-change feature would not work for anyone registered through the wizard.

## Goal
1. The client clearly sees their payment method and gateway (for example, "Cartão de crédito · Stripe (recorrente)" — "Credit card · Stripe (recurring)" — or "PIX · Asaas").
2. A client with a recurring Stripe subscription can change the card at any time — even while restricted by the commitment period (changing a card is never blocked; only plan changes and cancellation are) — without exposing Stripe dashboard options to cancel or change the plan.
3. When a Stripe charge fails, the client sees a clear warning plus the "Trocar cartão" ("Change card") call to action, and the invoice history records the failed attempt until it is resolved. When the same invoice is later paid, the record is updated automatically.

## Context Ledger
### Files read in full
- `system/services/membership.py` (`mark_invoice_failed`, `record_invoice_from_stripe`, `_build_billing_tab`, `activate_membership_from_paid_order`)
- `system/services/stripe_webhooks.py` (all handled event types; `_handle_pre_registration_checkout_completed`)
- `system/services/stripe_checkout.py` / `system/services/stripe_admin_actions.py` (confirmed that no Billing Portal/card-change mechanism existed)
- `templates/home/dashboard.html` (the complete `MENSALIDADE` — "TUITION" — section, including `tab.recent_invoices` and the "Histórico de pagamentos" — "Payment history" — modal)
- `system/models/plan.py` (`PlanPaymentMethod`, `gateway_code` — confirmed that the project uses only three values: `asaas_pix`, `asaas_card`, `stripe_card`)

### Internet / official documentation
- `docs.stripe.com/api/customer_portal/sessions/create` (via direct fetch): the `flow_data={"type": "payment_method_update"}` parameter sends the client directly to the card-update screen without exposing subscription cancellation or plan changes. Confirmed that the call works even without prior portal configuration in the Dashboard because it uses the automatic default configuration.

### Limitations found
- Requires the `Membership` to have `stripe_customer_id` populated — corrected in this PRD (see Goal 3 and the discovered gap).
- Complete live validation (creating a real Stripe client, simulating a failed invoice, and confirming a real Billing Portal Session) required manually adjusting the test data for "Beatriz Aluna Stripe". She had been created in an earlier session through `stripe trigger`, which generates a `checkout.session.completed` event in `payment` mode rather than `subscription` mode, so she never had real `stripe_subscription_id`/`stripe_customer_id` values. The data was restored to a clean state after validation.

## Required skills
`lv-task-intake`, `lv-prd`, `lv-django-delivery`, `lv-cleanup-audit`

## Understanding approved
The user requested this directly, with two explicit acceptance scenarios: (1) a recurring Stripe client cannot cancel or pause except with a medical certificate, but if the card fails, the system must instruct them to change it and keep the outstanding charge in the history until it is resolved; (2) an Asaas card client wants to use a different card the following month without pausing the service.

## Scope
- `system/models/membership.py::Membership`: new properties `effective_payment_method`, `effective_gateway_code`, `effective_payment_summary_label`, and `is_stripe_recurring`.
- `system/services/stripe_checkout.py::create_billing_portal_session(membership, request)`: creates a Billing Portal Session with `flow_data={"type": "payment_method_update"}`.
- `system/views/plan_change_views.py::MembershipUpdateCardView`: client view (GET) that redirects to the real Billing Portal and blocks the action when there is no Stripe subscription.
- `system/services/membership.py::mark_invoice_failed`: now records `MembershipInvoice(status="failed", amount_paid=0, paid_at=None)` through `update_or_create` keyed by `stripe_invoice_id`. If the same invoice is paid later, `record_invoice_from_stripe` automatically updates that record to `paid`.
- `system/services/membership.py::activate_membership_from_paid_order` / `system/services/stripe_webhooks.py::_handle_pre_registration_checkout_completed` / `system/services/pre_registration.py::finalize_pre_registration`: capture and propagate `stripe_customer_id` (correcting a pre-existing gap).
- `system/views/home_views.py::_build_payment_history_items`: corrects the pre-existing bug (`membership.plan.display_name` → `membership.effective_display_name`).
- `templates/home/dashboard.html`: payment-method badge; "Pagamento pendente" ("Payment pending") warning plus "Trocar cartão" ("Change card") button, always visible for a non-cancelled Stripe subscription regardless of lock/pause; invoice list and "Histórico de pagamentos" ("Payment history") modal distinguish `Pago` ("Paid"), `Falhou` ("Failed"), and `Estornado` ("Refunded").
- `static/system/css/home/dashboard.css`: `.billing-lock-notice--danger`, `.billing-compact-info__method`.

## Out of scope
- Custom Stripe Customer Portal configuration (logo, text, and features beyond the default) — handled in the Stripe Dashboard and outside the codebase.
- Automatic retry of failed charges (Stripe already provides Smart Retries, configurable in the Dashboard; this is not project code).
- "Card change" for Asaas clients — this project does not store cards in Asaas; each charge uses a new checkout, so the client naturally uses a different card when entering the details for the next charge.

## Rules and constraints
- Never use the generic Stripe portal without `flow_data=payment_method_update`; doing so could expose self-service cancellation or plan changes through Stripe and break the entire commitment-period restriction from PRD-132.
- No real gateway calls in automated tests — mock `stripe.billing_portal.Session.create`.
- Preserve the existing suite without regressions.

## Test plan
- Label/gateway properties for the three existing gateways.
- `create_billing_portal_session`: error without `stripe_customer_id`; session created with the correct `flow_data` when mocked.
- `MembershipUpdateCardView`: redirects to the portal for Stripe; redirects to the home page with an error for non-Stripe memberships.
- `mark_invoice_failed`: creates `MembershipInvoice(status=failed)`; paying the same invoice later updates the same record instead of duplicating it.
- Regression: the home page renders (200, without a 500 error) with a `MembershipInvoice` for a `PlanPrice`-based `Membership`.
- Capture and propagation of `stripe_customer_id` in the wizard confirmation flow.

### Execution authorization
Local — Stripe mocked in automated tests; live validation against the real Stripe test-mode API.

## Implemented
See Scope — all items were implemented in this session.

## Evidence
- `manage.py test system.tests.test_membership_card_update` → **12 tests, OK**.
- `manage.py test` (complete suite) → **597 tests, OK** (585 from PRD-132 plus 12 new tests), with no regressions.
- `manage.py check` → clean.
- **Live validation against the real Stripe test-mode API**:
  - Created a real `stripe.Customer.create` (`cus_UqGp3TeMKgVw04`) and linked it to Beatriz's Membership.
  - `stripe.billing_portal.Session.create(..., flow_data={"type": "payment_method_update"})` returned a real, valid URL (`billing.stripe.com/p/session/...`).
  - The real view (`GET /minha-mensalidade/trocar-cartao/`) was confirmed to return 302 (a real redirect to the Billing Portal).
  - Simulated `mark_invoice_failed` with a real invoice (`amount_due=22914`): `Membership.status` became `past_due`; the `CARTÃO DE CRÉDITO · STRIPE (RECORRENTE)` ("CREDIT CARD · STRIPE (RECURRING)") badge and the warning `Pagamento pendente — a cobrança automática não foi concluída. Atualize seu cartão para regularizar.` ("Payment pending — the automatic charge could not be completed. Update your card to resolve it.") appeared correctly, with the "Trocar cartão" ("Change card") button highlighted (`btn--primary`).
  - The invoice list and "Histórico de pagamentos" ("Payment history") modal correctly showed `Falhou` ("Failed"): `billing-invoice-list` → `"07/07/2026\nR$ 0,00\nFalhou"` ("07/07/2026\nR$ 0.00\nFailed"); modal → `"Adulto 2x por semana\nR$ 0,00\nFalhou"` ("Adult twice a week\nR$ 0.00\nFailed").
  - Validation data was restored to a clean state (Beatriz's Membership returned to `active`, and the failed test invoice was removed; `stripe_customer_id` was retained because it correctly represents a real Stripe subscription).

## Evidence — round 2 (complete end-to-end validation following `docs.stripe.com/testing#cards`)
The user requested changing a card according to Stripe's official testing documentation, pausing tuition and checking the validity period, adding three dependents (one for each gateway), pausing all three, changing the card for two, changing one payment method from PIX to credit, and changing one billing cycle to semiannual — all against the real APIs (Asaas sandbox and Stripe test mode) to simulate end-to-end system integrity.

- **Three real dependents created** under the account holder Diana (Asaas PIX), each with a different gateway: Eduarda (Asaas PIX), Fabio (recurring Stripe — a REAL checkout completed in the external browser with test card `4242 4242 4242 4242`, expiration `12/34`, and CVC `123`, exactly as documented in `docs.stripe.com/testing#cards`), and Gustavo (Asaas card). Belt ranks were varied (white/blue/brown).
- **Pause approved for all three dependents**: Eduarda and Gustavo through self-service suspension (allowed because they were outside the commitment period); Fabio through a medical certificate (required because his recurring Stripe membership was within the commitment period, confirmed by the real `ValidationError` when self-service was attempted before changing the request to `medical`). `current_period_end` was postponed by 10 days for all three; `fidelity_extension_days` increased only for Fabio (`medical`), confirming the exact business rule requested by the user.
- **Real card change against the Stripe test-mode API, using the official test card**: the Billing Portal was opened in the external browser and filled with `4242 4242 4242 4242` / `12/34` / `123`. Stripe created a new `PaymentMethod` (`pm_1TqbQPItFp0xr82skkS4VH6I`) and set it as the real customer's `invoice_settings.default_payment_method`, confirmed through a direct `stripe.Customer.retrieve` API call rather than only through the UI.
- **Asaas card change**: confirmed that no equivalent button exists or should exist. This project does not store cards in Asaas; each charge uses a new checkout, so the "change" happens naturally when the client enters a different card for the next charge.
- **Payment-method change** (Eduarda, PIX → Credit, same tier/cycle) and **billing-cycle change** (Gustavo, monthly → semiannual): both used a real `POST /minha-mensalidade/trocar-plano/`, generated an upgrade `RegistrationOrder`, had a real Asaas payment confirmed through `/sandbox/payment/{id}/confirm`, and applied the change by processing the `PAYMENT_CONFIRMED` event (`process_asaas_event`). Database confirmation showed Eduarda with `plan_price.gateway_code=asaas_card`, and Gustavo with `billing_cycle=semiannual` and a validity period approximately six months ahead.

### Critical bug found and corrected during validation
A real card change for Fabio (Stripe) triggered a real `customer.subscription.updated` event, captured by the local `stripe listen`, that **cleared `Membership.current_period_start`/`current_period_end`**. This was discovered while inspecting the final summary. Root cause: in recent Stripe API versions, `current_period_start`/`current_period_end` **moved from the `Subscription` object to the `SubscriptionItem`**. This was confirmed by inspecting the real payload through `stripe.Subscription.retrieve`: the fields no longer exist at the top level. `upsert_membership_from_stripe_subscription`, `activate_membership_from_session`, and `_apply_stripe_plan_change_migration` (the latter added in this session under PRD-132) read only the old top-level fields, so they now always received `None`. The first function **unconditionally overwrote** the Membership validity dates with `None` on every real synchronization event. Any action can trigger this, including changing a card or acting in the Stripe Dashboard, silently corrupting the validity period of any recurring Stripe student. No test or earlier validation caught it because this was the first time the complete real cycle (real checkout → real synchronization event → second real synchronization event) was exercised end to end.

**Corrected**: a new `extract_stripe_subscription_period` helper (`system/services/membership.py`) first checks the top level and falls back to `items.data[0]` when the values are absent; it is used at all three read points. `upsert_membership_from_stripe_subscription` also no longer overwrites a valid date with `None`; it updates the value only when extraction returns one. Four new regression tests cover this, including the exact bug scenario: an event with no period at either level must not erase the existing validity period. Fabio's data was corrected manually after the fix.

- `manage.py test system.tests.test_membership_card_update system.tests.test_membership_shared_subscription` → **24 tests, OK**.
- `manage.py test` (complete suite) → **603 tests, OK**, with no regressions.
- `manage.py check` → clean.
- Final live visual validation (Fabio): the `CARTÃO DE CRÉDITO · STRIPE (RECORRENTE)` ("CREDIT CARD · STRIPE (RECURRING)") badge; the correctly applied family discount (R$ 229.14 → R$ 187.89, because he is Diana's dependent); `Vigência 07/07/2026 → 17/08/2026` ("Validity 07/07/2026 → 17/08/2026"), reflecting the 10-day medical pause; the commitment-period notice `liberados em 17/08/2026` ("available on 17/08/2026"), using the same date and correct extension; and the "Pausar mensalidade" ("Pause tuition") and "Trocar cartão" ("Change card") buttons, without "Trocar plano" ("Change plan"), correctly blocked by the commitment period.

### Another gap corrected along the way
`_create_paid_plan_order` (`system/services/dependent_registration.py`) had the same gap already corrected in round 1 for the account-holder flow: it never propagated `stripe_customer_id` to the dependent's `Membership`. This was corrected at both points (the function signature and the call in `finalize_dependent_registration`), with a regression test.

## Cleanup findings
- This was the sixth occurrence in the session of the bug family in which code reads only `SubscriptionPlan`/`membership.plan`: `_build_payment_history_items`. Corrected.
- The gap where `stripe_customer_id` was never captured in either the public wizard flow **or** the dependent flow was corrected in both places, with regression tests.
- Critical data-integrity bug: `current_period_start/end` were being cleared by any real `customer.subscription.updated` event because of the Stripe API field migration from Subscription to SubscriptionItem. Corrected with a fallback and protection against overwriting values with `None`.
- Test data (Fabio's Membership) was corrected manually after the fix to reflect the value that the corrected system would already have calculated.

## Final status
Completed and validated in two rounds — automated tests (12 plus 12 new tests, for 24 tests specific to this PRD; final complete suite: **603 tests, OK**) and complete live validation against real APIs (Stripe test mode: customer, real Billing Portal Session using the official `4242 4242 4242 4242` test card, real subscription checkout, and real synchronization event; Asaas sandbox: three real payments plus payment-method and billing-cycle changes). A critical validity-period integrity bug caused by a Stripe API field migration and a gap in capturing `stripe_customer_id` in the dependent flow were discovered and corrected during the second round; they appeared only when the complete real cycle was exercised, not in any earlier test.
