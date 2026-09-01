# PRD-041: Stripe — recurring plans

## Summary of the implementation

Reintroduce Stripe as a payment gateway in the registration flow, exclusively in recurring mode (Stripe Subscriptions). The student chooses a plan with `gateway_code=stripe_card`, is redirected to Stripe Checkout in `subscription` mode, Stripe handles the automatic charges on the configured cycle, and the Stripe webhooks confirm the payment and keep the subscription state in the local database.

---

## Demand type

New feature — external integration (Stripe Subscriptions)

---

## Current problem

Stripe was removed from the operational flow (PRD-037). Every recurring charge is manual through Asaas. Asaas does not manage automatic subscription renewals — each cycle requires a new charge. Stripe Subscriptions solves that natively: once the subscription is created, Stripe charges automatically every cycle, notifies through a webhook, and issues invoices.

---

## Goal

Allow the student to pay the tuition by credit card through Stripe Checkout in recurring mode. The local database reflects the subscription's real state through webhooks. The academy receives the payouts from Stripe on the configured cycle, with no manual intervention per renewal.

---

## Context Ledger

### Files read in full (mandatory before implementing)

- `system/models/plan.py` — `SubscriptionPlan`, `PlanPaymentMethod`, `STRIPE_INTERVAL_BY_CYCLE`
- `system/models/registration_order.py` — `RegistrationOrder`, `PaymentProvider`, `PaymentStatus`
- `system/models/membership.py` — `Membership` and the subscription lifecycle
- `system/models/pre_registration.py` — `PreRegistration`, `form_snapshot`
- `system/views/auth_views.py` — `PortalRegisterView.form_valid`, `_create_pre_registration_plan_payment`
- `system/views/payment_views.py` — `PaymentSuccessView`, `_handle_pre_registration_success`
- `system/views/asaas_views.py` — the existing webhook + checkout pattern
- `system/services/asaas_client.py` — the external HTTP client pattern
- `system/services/asaas_checkout.py` — the charge creation pattern
- `system/constants.py` — `CheckoutAction`
- `static/initial_data/seed_system_initial_subscription_plans_values.json` — the current plan structure
- `system/management/commands/seed_system_initial_subscription_plans_values.py` — the active seed

### Adjacent files consulted

- `lvjiujitsu/settings.py` — the `STRIPE_*` variables
- `lvjiujitsu/urls.py` — route registration
- `system/urls.py` — the existing routes
- `system/services/financial_transactions.py` — `apply_order_financials`
- `system/services/registration_checkout.py` — `gross_up_order_for_checkout`
- `static/system/js/auth/register.js` — wizard initialization and checkout
- `templates/login/register.html` — the wizard template

### Internet / official documentation

- Stripe Checkout Sessions in `subscription` mode: https://docs.stripe.com/billing/subscriptions/build-subscriptions
- Stripe Webhooks — relevant events: https://docs.stripe.com/webhooks
- Stripe Python SDK: https://github.com/stripe/stripe-python
- Required events: `checkout.session.completed`, `invoice.paid`, `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_failed`

### MCPs / tools verified

- `manage.py check` — must pass after model changes
- The destructive cycle — mandatory if any new field is added to the model

### Limitations found

- `PlanPaymentMethod` has no `STRIPE_CARD` choice — use `gateway_code="stripe_card"` as the discriminator (the field already exists)
- Stripe requires HTTPS for webhooks — in dev, use ngrok (the same pattern as Asaas)
- Stripe must not replace Asaas — the two gateways coexist; the wizard chooses based on the selected plan

---

## Execution prompt

### Persona

Development agent specializing in Django 4.x + the Stripe Python SDK, following SDD + TDD + MVT architecture with services.

### Action

Implement the complete recurring subscription flow through Stripe Checkout in the public registration wizard, including the local subscription model, checkout and webhook views, the plan seed, and the JSON adjustment.

### Context

The current registration wizard routes payments to Asaas (PIX and Card). Routing happens in `PortalRegisterView._create_pre_registration_plan_payment` based on the submitted `checkout_action`. The new `stripe_card` route must be detected there and trigger a Stripe Checkout Session in `subscription` mode.

Stripe's return to `successUrl` confirms the payment through `PaymentSuccessView`. The Stripe webhook updates the subscription state locally.

### Constraints

- no hardcoded Stripe keys — read from `.env` through `python-decouple`
- no manual migrations — the destructive cycle is run by the user
- do not change the existing Asaas flow
- the seed accepts no `--` arguments; all configuration through `.env`
- idempotent: running the seed twice does not duplicate plans

---

## Scope

### Model

| Item | Action |
|---|---|
| `SubscriptionPlan.gateway_code` | already exists — use `stripe_card` as the discriminator value |
| `Membership` or a new `StripeSubscription` | record the `stripe_subscription_id` returned by the checkout |
| `RegistrationOrder.payment_provider` | add `STRIPE = "stripe"` to the `PaymentProvider` enum |

> **Design decision**: check whether `Membership` already has a field for `stripe_subscription_id`. If not, add it. The field can be a `CharField(blank=True)` and does not break the existing logic.

### CheckoutAction

Add `STRIPE_CARD = "stripe_card"` in `system/constants.py`.

### Routing in the wizard

In `PortalRegisterView._create_pre_registration_plan_payment`:
```python
if checkout_action == CheckoutAction.STRIPE_CARD:
    return _create_stripe_checkout_session(pre_registration, plans_by_id, selected_plans)
```

### New view: `CreateStripeCheckoutSessionView`

```
POST /pagamentos/<pre_registration_id>/stripe-checkout/
```

Or integrate it directly into `_create_pre_registration_plan_payment`, returning the `session.url`.

Checkout Session parameters:
- `mode = "subscription"`
- `line_items`: one entry per selected plan, using `stripe_price_id`
- `success_url = SITE_BASE_URL + /pagamentos/sucesso/?pre_registration_id=X&stage=plan&session_id={CHECKOUT_SESSION_ID}`
- `cancel_url = SITE_BASE_URL + /pagamentos/cancelado/`
- `client_reference_id = f"pre-registration:{pre_registration.pk}:plan"`
- `customer_email` from the snapshot

### Stripe webhook

```
POST /pagamentos/webhook/stripe/
```

Handled events:

| Event | Action |
|---|---|
| `checkout.session.completed` | confirm the pre-registration payment; record `stripe_subscription_id` |
| `invoice.paid` | renewal confirmed — update the local subscription status |
| `invoice.payment_failed` | mark the subscription as delinquent |
| `customer.subscription.updated` | synchronize the status and cycle |
| `customer.subscription.deleted` | cancel the local subscription |

### PaymentSuccessView

Add a fallback by `session_id` (Stripe) in addition to `id` (Asaas):
```python
stripe_session_id = request.GET.get("session_id")
if stripe_session_id:
    # look up the pre-registration by the session_id recorded in the session's metadata
```

### Seed

**Command:** `seed_system_initial_subscription_plans_stripe`

- Reads `static/initial_data/seed_system_initial_subscription_plans_stripe.json`
- Depends on: nothing (the Stripe plans are independent of the Asaas plans)
- Creates Stripe plans with `gateway_code="stripe_card"`, `is_active=True`
- For each plan, synchronizes with the Stripe API: creates the `Product` if it does not exist, creates a recurring `Price`
- Stores `stripe_product_id` and `stripe_price_id` on the model

### The seed's data JSON

**File:** `static/initial_data/seed_system_initial_subscription_plans_stripe.json`

Structure per item:
```json
{
  "code": "individual_2x_stripe_monthly",
  "display_name": "Individual 2x por semana - Stripe Cartão - Mensal",
  "audience": "adult",
  "weekly_frequency": 2,
  "billing_cycle": "monthly",
  "payment_method": "credit_card",
  "gateway_code": "stripe_card",
  "is_family_plan": false,
  "is_loyalty_plan": false,
  "base_monthly_net_price": "200.00",
  "gateway_fixed_fee": "0.00",
  "gateway_percentage_fee": "0.0399",
  "cycle_discount_percentage": "0.00",
  "display_order": 50
}
```

The retained `display_name` literal means "Individual twice per week—Stripe Card—Monthly."

Plans to create (the same logic as the existing Asaas plans):
- Individual 2x / 5x × Monthly / Quarterly / Biannual / Annual
- Kids/Juvenile 2x / 5x × the same cycles
- Family 2x / 5x × the same cycles
- Total: the same number as the Asaas plans, but with `gateway_code=stripe_card`

### Required environment variables

```env
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### Update in the wizard (register.js)

In `elStepPlanNext.addEventListener`:
```javascript
var action = (firstPlan && firstPlan.payment_method === 'pix') ? 'pix'
           : (firstPlan && firstPlan.gateway_code === 'stripe_card') ? 'stripe_card'
           : 'asaas_card';
setHidden('id_checkout_action', action);
document.getElementById('wizard-form').submit();
```

The plan catalog JSON needs to include `gateway_code` so the JavaScript can tell them apart.

---

## Out of scope

- A subscription self-management portal (cancel, change plan through the Stripe Portal)
- Installments through Stripe (only monthly/cyclic recurring charges)
- Migrating existing Asaas subscribers to Stripe
- Stripe revenue reports in the admin panel

---

## Impacted files

| File | Type of change |
|---|---|
| `system/constants.py` | add `STRIPE_CARD` to `CheckoutAction` |
| `system/models/plan.py` | no schema change (gateway_code already exists) |
| `system/models/registration_order.py` | add `STRIPE` to `PaymentProvider` |
| `system/models/membership.py` | add `stripe_subscription_id` (if it does not exist) |
| `system/services/stripe_client.py` | **new** — the Stripe HTTP client |
| `system/services/stripe_checkout.py` | **new** — create the Checkout Session, handle the webhook |
| `system/views/stripe_views.py` | **new** — `CreateStripeCheckoutView`, `StripeWebhookView` |
| `system/views/auth_views.py` | `STRIPE_CARD` routing in `_create_pre_registration_plan_payment` |
| `system/views/payment_views.py` | fallback by `session_id` in `PaymentSuccessView` |
| `system/urls.py` | register the Stripe routes |
| `system/management/commands/seed_system_initial_subscription_plans_stripe.py` | **new** |
| `static/initial_data/seed_system_initial_subscription_plans_stripe.json` | **new** |
| `static/system/js/auth/register.js` | detect `gateway_code=stripe_card` for `checkout_action` |
| `system/services/registration_checkout.py` | include `gateway_code` in the plan catalog payload |
| `lvjiujitsu/settings.py` | read `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET` |
| `.env` | add the Stripe variables |
| `system/tests/test_stripe_checkout.py` | **new** |
| `system/tests/test_stripe_webhook.py` | **new** |

---

## Risks and edge cases

| Risk | Mitigation |
|---|---|
| `stripe_price_id` does not exist in Stripe (sandbox vs prod) | the seed synchronizes and persists the ID; check before creating the Checkout Session |
| The webhook arrives before the `successUrl` redirect | `checkout.session.completed` is the canonical event; `successUrl` is UI — the two are handled independently |
| A Stripe plan is selected but has no `stripe_price_id` | validate in the service; an explicit error before creating the session |
| Asaas and Stripe coexisting in the wizard | the plan catalog filters by gateway correctly; the JavaScript detects it through `gateway_code` |
| A subscription cancelled in Stripe with no local action | the `subscription.deleted` webhook deactivates the local subscription |

---

## Rules and constraints

- SDD before code
- TDD for the implementation
- no hardcoding
- no error masking
- no migrations (project policy) — if `stripe_subscription_id` is a new field, instruct the destructive cycle
- mandatory full reading before touching any file
- mandatory validation of the complete flow (wizard → Stripe Checkout → webhook → wizard)

---

## Plan

- [ ] 1. Read in full every file listed in the Context Ledger
- [ ] 2. Check whether `Membership` already has `stripe_subscription_id`; if not, add it and request the destructive cycle
- [ ] 3. Add `STRIPE_CARD` to `CheckoutAction` and `STRIPE` to `PaymentProvider`
- [ ] 4. Create `stripe_client.py` with `create_checkout_session`, `retrieve_session`, `construct_webhook_event`
- [ ] 5. Create `stripe_checkout.py` with the session creation service and webhook event handling
- [ ] 6. Create `stripe_views.py` with `CreateStripeCheckoutView` and `StripeWebhookView`
- [ ] 7. Register the Stripe routes in `system/urls.py`
- [ ] 8. Update `PortalRegisterView._create_pre_registration_plan_payment` for the Stripe route
- [ ] 9. Update `PaymentSuccessView` with the `session_id` fallback
- [ ] 10. Include `gateway_code` in the plan catalog payload (services)
- [ ] 11. Update `register.js` to detect `gateway_code=stripe_card`
- [ ] 12. Create the `seed_system_initial_subscription_plans_stripe.json` data file
- [ ] 13. Create the `seed_system_initial_subscription_plans_stripe` command
- [ ] 14. Write tests (Red → Green → Refactor)
- [ ] 15. Validate the complete flow with an active ngrok (Stripe also needs a public webhook in dev)
- [ ] 16. Final cleanup
- [ ] 17. Update CLAUDE.md (the new seed, the new environment variables)

---

## Visual validation

### Desktop
- The wizard's step-plan shows the Stripe plans as an option (filtered by method)
- Clicking `Pagar mensalidade` (`Pay tuition`) with a Stripe plan redirects to Stripe Checkout
- After payment, the wizard shows the confirmed state and allows advancing to materials

### Mobile
- The same navigation as desktop; Stripe Checkout is responsive

### Browser console
- No JavaScript errors related to selecting a Stripe plan

### Terminal
- No stack trace when creating the Checkout Session
- The webhook processed with no error

---

## ORM validation

```python
from system.models import SubscriptionPlan
SubscriptionPlan.objects.filter(gateway_code='stripe_card', is_active=True).count()
# must return the correct number of plans

from system.models import PreRegistration
pr = PreRegistration.objects.latest('created_at')
pr.form_snapshot.get('plan_payment', {})
# must contain the asaas or stripe payment id depending on the gateway
```

---

## Quality validation

- No hardcoded `STRIPE_SECRET_KEY`
- The webhook validates `Stripe-Signature` before processing
- `except: pass` forbidden — Stripe errors raise an explicit exception
- No `stripe_price_id` → an error before redirecting

---

## Evidence (fill in after implementation)

- [ ] `manage.py check` — 0 issues
- [ ] `manage.py test --verbosity 2` — 0 failures
- [ ] The Stripe plan displayed in the wizard
- [ ] The redirect to Stripe Checkout confirmed
- [ ] The `checkout.session.completed` webhook processed
- [ ] `pre_registration.status == PAYMENT_CONFIRMED` after the webhook
- [ ] The wizard shows the "paid" state when returning from Stripe

## Implemented

_(fill in after completion)_

## Deviations from plan

_(fill in after completion)_

## Pending

_(fill in after completion)_
