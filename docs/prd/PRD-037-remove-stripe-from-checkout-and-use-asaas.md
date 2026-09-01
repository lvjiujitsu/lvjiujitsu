# PRD-037: Remove Stripe from the checkout and use Asaas

## Summary of the implementation
Remove Stripe from the operational plan and checkout flow, keeping only Asaas for PIX and credit card. The card must generate an Asaas charge and redirect the customer to the Asaas `invoiceUrl`.

## Demand type
External integration.

## Current problem
The plan catalog contains `stripe_card` rows, the frontend sends `checkout_action=stripe` for the card, and the backend tries to create a Stripe checkout. Stripe does not support the installment scheme the business needs.

## Goal
- A plan values JSON with no Stripe.
- A value seed creating only Asaas PIX and Asaas Card plans.
- A card checkout using Asaas.
- Real routes registered for the Asaas checkout.
- Tests covering the removal of Stripe from the generated plans and the Asaas card charge payload.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `system/constants.py`
- `system/forms/registration_forms.py`
- `system/views/auth_views.py`
- `system/views/payment_views.py`
- `system/views/asaas_views.py`
- `system/urls.py`
- `system/services/asaas_client.py`
- `system/services/asaas_checkout.py`
- `system/services/registration_checkout.py`
- `system/services/financial_transactions.py`
- `system/services/pricing.py`
- `system/models/plan.py`
- `system/models/registration_order.py`
- `system/management/commands/seed_system_initial_subscription_plans.py`
- `system/management/commands/seed_system_initial_subscription_plans_values.py`
- `static/initial_data/seed_system_initial_subscription_plans_values.json`
- `static/system/js/auth/register.js`
- `system/tests/test_asaas.py`
- `system/tests/test_commands.py`
- `system/tests/test_services.py`
- `system/tests/test_plan_models.py`

### Internet / official documentation
- Asaas: Credit card charges.
- Asaas: Creating an installment charge.
- Asaas: Creating an installment plan with a credit card.

### Limitations found
- Physically removing the Stripe fields and models requires a schema change. Under project policy, that stays out of this delivery.

## Acceptance criteria
- [x] The `seed_system_initial_subscription_plans_values` seed creates/updates Asaas plans only.
- [x] Existing `stripe_card` rows are deactivated by the seed.
- [x] The card plan resolves to `PaymentProvider.ASAAS`.
- [x] The registration card button sends `checkout_action=asaas_card`.
- [x] The card checkout creates an Asaas `CREDIT_CARD` charge and redirects to `invoiceUrl`.
- [x] Installment plans send `installmentCount` and `totalValue`; the 1x monthly plan sends `value`.
- [x] The Asaas checkout routes exist.
- [x] The tests and `manage.py check` pass.

## Out of scope
- Removing the Stripe fields from the models/migrations.
- Implementing transparent card data capture inside the site.
- Rewriting the entire administrative financial screen.

## Plan
- [x] 1. Context and full reading
- [x] 2. Contracts and Asaas documentation
- [x] 3. Tests
- [x] 4. Implementation
- [x] 5. Full validation
- [x] 6. Documentation update

## Evidence
- `.\.venv\Scripts\python.exe manage.py test --verbosity 2` — 163 tests, OK.
- `.\.venv\Scripts\python.exe manage.py check` — no issues.
- `.\.venv\Scripts\python.exe manage.py collectstatic --noinput` — 2 files copied, 167 unchanged.

## Implemented
- The plan values JSON reduced to Asaas PIX and Asaas Card.
- The value seed validates the supported gateways and deactivates legacy `stripe_card` plans.
- The card checkout uses Asaas `CREDIT_CARD` and redirects to `invoiceUrl`.
- The registration frontend sends `asaas_card` for the card.
- The `asaas-pix-create`, `asaas-card-create`, `payment-checkout`, and Asaas webhook routes registered.

## Pending
- Physically removing the Stripe fields/models/services requires a destructive schema cycle and was not done in this delivery.
