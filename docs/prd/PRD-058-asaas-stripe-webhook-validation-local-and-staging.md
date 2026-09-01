# PRD-058: Asaas and Stripe webhook validation — local and staging

## Summary of the implementation

A complete, verified operational guide to test every Asaas and Stripe webhook event locally, with a readiness checklist for validation through Chrome MCP in the staging environment (Supabase + Render HG). This PRD changes no code — it is an executable validation and test document.

## Demand type

Security review + external integration + functional validation

## Current problem

- The local database (SQLite) is empty: 0 RegistrationOrders, 0 PreRegistrations, 0 AsaasWebhookEvents, 0 StripeWebhookEvents.
- `SITE_BASE_URL` points at `https://lvjiujitsu-hg.onrender.com` (Render HG), not at ngrok — which makes the Asaas `successUrl` inoperative in local real-browser tests.
- The Stripe CLI is not installed locally, making it impossible to simulate Stripe webhooks with a valid signature without installing it.
- There is no consolidated script to validate both gateways in sequence, covering every event mapped in the code.

## Goal

1. Document and run the token validation (Asaas + Stripe) locally.
2. Provide the exact commands to simulate each webhook event locally through `Invoke-RestMethod`.
3. Document the script for creating test data (a PreRegistration + a RegistrationOrder) without performing a real registration.
4. Produce a readiness checklist for validation through Chrome MCP on Render HG.

---

## Context Ledger

### Files read in full

- `system/views/asaas_views.py` — `AsaasWebhookView`, auth through `asaas-access-token`
- `system/views/stripe_views.py` — `StripeWebhookView`, auth through `Stripe-Signature`
- `system/views/payment_views.py` — `PaymentSuccessView`, `_handle_pre_registration_success`
- `system/views/auth_views.py` — `PortalRegisterView`, `_create_pre_registration_plan_payment`
- `system/services/asaas_webhooks.py` — every mapped event
- `system/services/stripe_webhooks.py` — every mapped event
- `system/services/asaas_checkout.py` — `create_pix_charge_for_order`, `create_credit_card_charge_for_order`
- `system/services/asaas_client.py` — `verify_webhook_token`

### Adjacent files consulted

- `lvjiujitsu/settings.py` — `ASAAS_WEBHOOK_TOKEN`, `STRIPE_WEBHOOK_SECRET`, `SITE_BASE_URL`
- `system/urls.py` — the `/pagamentos/webhook/asaas/` and `/pagamentos/webhook/stripe/` routes
- `docs/prd/PRD-040-payment-before-person-creation-registration-flow.md` — the public wizard's contract
- `docs/prd/PRD-041-stripe-recurring-plans.md` — Recurring Stripe

### MCPs / tools verified

- Django check: **0 issues** ✓
- The `.venv` Python 3.12.10: **ok** ✓
- `manage.py check`: **passed** ✓
- Stripe CLI: **NOT installed** ⚠️ — see the Stripe section below

### Local database state (SQLite — after the 2026-06-10 validations)

| Table | Total |
|---|---|
| `RegistrationOrder` | 0 |
| `PreRegistration` | 2 (ID=1 Carlos PIX finalized; ID=2 Ana Stripe payment_confirmed) |
| `AsaasWebhookEvent` | 2 (evt_pix_test_001 PAYMENT_CONFIRMED; a second one simulated) |
| `StripeWebhookEvent` | 11+ (checkout.session.completed, charge.updated, etc.) |

### Token state (verified through the shell + decouple directly on the .env — 2026-06-10)

| Variable | Status in `.env` | Detail |
|---|---|---|
| `ASAAS_WEBHOOK_TOKEN` | ✓ **Configured** | Configured in `.env`; Asaas webhooks return HTTP 200 |
| `ASAAS_API_KEY` | ✓ **Configured** | len=166 — outbound calls to Asaas work |
| `ASAAS_API_URL` | ✓ **Configured** | `https://api-sandbox.asaas.com/v3` (sandbox) |
| `STRIPE_SECRET_KEY` | ✓ **Configured** | prefix `sk_test`, len=107 (test mode) |
| `STRIPE_WEBHOOK_SECRET` | ✓ **Configured** | The Stripe CLI's `whsec_74ab90bc...` configured; Stripe webhooks return HTTP 200 |
| `SITE_BASE_URL` | ⚠️ **Points at HG Render** | `https://lvjiujitsu-hg.onrender.com` — local browser tests require switching to ngrok |

> **Note on the earlier reading:** In the first preflight run, the `ASAAS_WEBHOOK_TOKEN` and `STRIPE_WEBHOOK_SECRET` values were read as `len: 49` and `whsec_m` respectively. That happened because they were configured as **environment variables in the PowerShell session** — `python-decouple` prioritizes environment variables over the `.env` file. Reading `.env` directly confirms the values are empty in the file. To persist them, they must be added to `.env`.

### Mandatory action before continuing the tests

```
1. ASAAS_WEBHOOK_TOKEN — obtain it from the Asaas sandbox dashboard:
   My Account → Notifications → Webhook access token
   Add it to .env: ASAAS_WEBHOOK_TOKEN=<value>

2. STRIPE_WEBHOOK_SECRET — two options:
   a) Local Stripe CLI: stripe listen → copy the displayed whsec_ → add it to .env
   b) Stripe Dashboard: Developers → Webhooks → HG endpoint → Signing secret
      (use only for tests on HG Render, not for local simulation)
```

### Limitations found

1. **`SITE_BASE_URL` points at HG Render**, not at ngrok. That affects:
   - The `successUrl` sent to Asaas when creating a charge → the browser will be redirected to HG Render after payment, not to `127.0.0.1:8000`
   - It **does not affect** the direct simulation of webhooks through `Invoke-RestMethod`

2. **The Stripe CLI is absent** locally. The static `STRIPE_WEBHOOK_SECRET` from the Stripe dashboard works with webhooks coming from Stripe's servers (e.g. HG Render), but a local simulation with `Invoke-RestMethod` and no valid HMAC signature will be rejected with HTTP 400.

3. **An empty database**: the Asaas webhooks depend on an existing `RegistrationOrder` to have any effect. A webhook processed for a non-existent order returns HTTP 200 but records nothing relevant (correct behavior — the service returns `None` for the order).

---

## Architecture of the two payment flows

### Flow A — An existing student (RegistrationOrder)

```
Logged-in student → pending order → CreatePixChargeView / CreateCreditCardChargeView
    → Asaas creates charge → returns invoice_url
    → Browser goes to Asaas → payment is made
    → Asaas sends webhook POST /pagamentos/webhook/asaas/
    → AsaasWebhookView → process_asaas_event → updates RegistrationOrder.payment_status
    → Activates the student's Membership
```

**Confirmation**: server-to-server through the Asaas webhook. `successUrl` is a convenience URL for the browser.

### Flow B — A new student (the public wizard / PreRegistration)

```
Visitor → wizard → PortalRegisterView (step-plan)
    → _create_pre_registration_plan_payment → Asaas creates a charge with successUrl
    → Browser goes to Asaas/Stripe → payment is made
    → Browser is redirected to successUrl = SITE_BASE_URL + /pagamentos/sucesso/
    → PaymentSuccessView._handle_pre_registration_success
    → PreRegistration.form_snapshot["plan_paid"] = True
    → PreRegistration.status = PAYMENT_CONFIRMED
    → Returns to the wizard (step-materials)
```

**Primary confirmation**: the browser through `successUrl`. The server-to-server Asaas webhook (for a `RegistrationOrder`) is NOT used in this flow — the confirmation is done by the `payment-success` view.

> **Critical implication**: simulating the Asaas webhook does not confirm public wizard payments. To test the wizard, `PaymentSuccessView` must be called with the correct parameters.

---

## Scope

1. Validate the tokens locally
2. Simulate every Asaas event mapped in `asaas_webhooks.py`
3. Simulate every Stripe event mapped in `stripe_webhooks.py` (through the CLI or HG)
4. Simulate the wizard's payment confirmation (flow B) through `payment-success`
5. Check the database state after each simulation
6. A readiness checklist for HG Render + Chrome MCP

## Out of scope

- Changing production code
- Creating migrations
- Testing the instructor and payout (`TRANSFER_*`) flows with real data in Asaas
- Configuring the Asaas account in the dashboard (the webhook URL must already point at ngrok or HG)

---

## Validation plan

### Step 0 — Check the active tokens

```powershell
.\.venv\Scripts\python.exe manage.py shell -c "
from django.conf import settings
print('ASAAS_WEBHOOK_TOKEN set:', bool(settings.ASAAS_WEBHOOK_TOKEN), '| len:', len(settings.ASAAS_WEBHOOK_TOKEN or ''))
print('STRIPE_SECRET_KEY prefix:', (settings.STRIPE_SECRET_KEY or '')[:7])
print('STRIPE_WEBHOOK_SECRET prefix:', (settings.STRIPE_WEBHOOK_SECRET or '')[:8])
print('SITE_BASE_URL:', settings.SITE_BASE_URL)
print('ASAAS_API_URL:', settings.ASAAS_API_URL)
print('DEBUG:', settings.DEBUG)
"
```

**Expected result:**
- `ASAAS_WEBHOOK_TOKEN set: True | len: 49` ✓
- `STRIPE_SECRET_KEY prefix: sk_test` ✓
- `STRIPE_WEBHOOK_SECRET prefix: whsec_m` ✓
- `SITE_BASE_URL:` the configured value (ngrok for local browser tests / HG for the deploy)

---

### Step 1 — Create test data for the Asaas webhook (a RegistrationOrder)

The database is empty. To test the Flow A webhooks, at least one `RegistrationOrder` with `asaas_payment_id` filled in is required.

**Option 1a — create it through the shell (the fastest for webhooks):**

**Note (2026-07-15, PRD-151 fix):** the canonical catalog of the public
flows since PRD-127/129/130 is `PlanTier`/`PlanPrice`, no longer
`SubscriptionPlan`. `RegistrationOrder.plan_price_ref` (an FK to `PlanPrice`)
is the field the real flow uses — `plan` (`SubscriptionPlan`) is legacy and only
exists for old orders. Use the snippet below:

```powershell
.\.venv\Scripts\python.exe manage.py shell -c "
from system.models.registration_order import RegistrationOrder, PaymentStatus, PaymentProvider
from system.models import Person
from system.models.plan import PlanPrice

# Requires at least one Person and PlanPrice in the database
# If the database is empty, run these first:
# .\.venv\Scripts\python.exe manage.py seed_system_initial_person_type
# .\.venv\Scripts\python.exe manage.py seed_system_initial_plan_tiers
# .\.venv\Scripts\python.exe manage.py seed_system_initial_plan_prices

person = Person.objects.filter(is_active=True).first()
plan_price = PlanPrice.objects.filter(is_active=True).first()

if person and plan_price:
    order = RegistrationOrder.objects.create(
        person=person,
        plan_price_ref=plan_price,
        plan_price=plan_price.price,
        total=plan_price.price,
        payment_status=PaymentStatus.PENDING,
        provider=PaymentProvider.ASAAS,
        asaas_payment_id='pay_test_webhook_001',
    )
    print(f'RegistrationOrder created: pk={order.pk} asaas_id={order.asaas_payment_id}')
else:
    print('ERROR: Person or PlanPrice not found — run seeds first')
"
```

**Option 1b — through the wizard + real Asaas (with ngrok active):**

Run the public wizard up to step-plan, choose a plan, and pay in the Asaas sandbox. Asaas returns and creates the `asaas_payment_id` automatically through `create_pix_charge_for_order`.

---

### Step 2 — Get the Asaas token for the headers

```powershell
# Assign the token to a PowerShell variable (without revealing it in the log)
$AsaasToken = .\.venv\Scripts\python.exe manage.py shell -c "from django.conf import settings; print(settings.ASAAS_WEBHOOK_TOKEN)"
$AsaasToken = $AsaasToken.Trim()
```

---

### Step 3 — Simulate the Asaas webhooks

Replace `ORDER_PK` with the real pk of the `RegistrationOrder` obtained in Step 1.
Each call must return **HTTP 200**.

#### 3.1 PAYMENT_CONFIRMED — payment confirmed (activates the membership)

```powershell
Invoke-RestMethod -Method POST `
  -Uri "http://127.0.0.1:8000/pagamentos/webhook/asaas/" `
  -Headers @{"asaas-access-token"=$AsaasToken} `
  -ContentType "application/json" `
  -Body '{"id":"evt_local_confirmed_001","event":"PAYMENT_CONFIRMED","payment":{"id":"pay_test_webhook_001","status":"CONFIRMED","externalReference":"ORDER_PK"}}'
```

**Expected state afterwards:** `RegistrationOrder.payment_status = PAID`, an `AsaasWebhookEvent` created.

```powershell
.\.venv\Scripts\python.exe manage.py shell -c "
from system.models.registration_order import RegistrationOrder
from system.models.asaas import AsaasWebhookEvent
o = RegistrationOrder.objects.get(pk=ORDER_PK)
print('Order status:', o.payment_status, '| paid_at:', o.paid_at)
print('Webhook events:', AsaasWebhookEvent.objects.filter(order=o).count())
"
```

#### 3.2 PAYMENT_RECEIVED — equivalent to CONFIRMED (idempotent on the second send)

```powershell
Invoke-RestMethod -Method POST `
  -Uri "http://127.0.0.1:8000/pagamentos/webhook/asaas/" `
  -Headers @{"asaas-access-token"=$AsaasToken} `
  -ContentType "application/json" `
  -Body '{"id":"evt_local_received_001","event":"PAYMENT_RECEIVED","payment":{"id":"pay_test_webhook_001","status":"RECEIVED","externalReference":"ORDER_PK"}}'
```

**Expected state:** HTTP 200, `duplicate=False` when the event_id differs, and the order stays PAID.

#### 3.3 PAYMENT_OVERDUE — payment overdue (marks it FAILED)

> Create a new `RegistrationOrder` with a PENDING status before testing this event.

```powershell
Invoke-RestMethod -Method POST `
  -Uri "http://127.0.0.1:8000/pagamentos/webhook/asaas/" `
  -Headers @{"asaas-access-token"=$AsaasToken} `
  -ContentType "application/json" `
  -Body '{"id":"evt_local_overdue_001","event":"PAYMENT_OVERDUE","payment":{"id":"pay_test_webhook_002","externalReference":"ORDER_PK_2"}}'
```

#### 3.4 PAYMENT_REFUNDED — a full refund

```powershell
Invoke-RestMethod -Method POST `
  -Uri "http://127.0.0.1:8000/pagamentos/webhook/asaas/" `
  -Headers @{"asaas-access-token"=$AsaasToken} `
  -ContentType "application/json" `
  -Body '{"id":"evt_local_refunded_001","event":"PAYMENT_REFUNDED","payment":{"id":"pay_test_webhook_001","refundedValue":"150.00","externalReference":"ORDER_PK"}}'
```

#### 3.5 PAYMENT_PARTIALLY_REFUNDED — a partial refund

```powershell
Invoke-RestMethod -Method POST `
  -Uri "http://127.0.0.1:8000/pagamentos/webhook/asaas/" `
  -Headers @{"asaas-access-token"=$AsaasToken} `
  -ContentType "application/json" `
  -Body '{"id":"evt_local_partial_001","event":"PAYMENT_PARTIALLY_REFUNDED","payment":{"id":"pay_test_webhook_001","refundedValue":"50.00","externalReference":"ORDER_PK"}}'
```

#### 3.6 An invalid token — must return HTTP 401

```powershell
Invoke-WebRequest -Method POST `
  -Uri "http://127.0.0.1:8000/pagamentos/webhook/asaas/" `
  -Headers @{"asaas-access-token"="token_invalido_qualquer"} `
  -ContentType "application/json" `
  -Body '{"id":"evt_auth_test","event":"PAYMENT_CONFIRMED","payment":{"id":"x"}}' `
  | Select-Object StatusCode
# Expected: 401
```

#### 3.7 A duplicate event — must return HTTP 200 with duplicate=True

Resend exactly the same body as event 3.1 (the same `id`). The service must return `duplicate=True` and not reprocess it.

```powershell
Invoke-RestMethod -Method POST `
  -Uri "http://127.0.0.1:8000/pagamentos/webhook/asaas/" `
  -Headers @{"asaas-access-token"=$AsaasToken} `
  -ContentType "application/json" `
  -Body '{"id":"evt_local_confirmed_001","event":"PAYMENT_CONFIRMED","payment":{"id":"pay_test_webhook_001","status":"CONFIRMED","externalReference":"ORDER_PK"}}'
# Expected: HTTP 200; AsaasWebhookEvent.count() does not increase
```

---

### Step 4 — Simulate the public wizard's confirmation (Flow B — PreRegistration)

The wizard does not use a server-to-server webhook to confirm — it uses the browser redirect to `/pagamentos/sucesso/`. The simulation is done by calling the view directly.

#### 4.1 Create a test PreRegistration through the shell

```powershell
.\.venv\Scripts\python.exe manage.py shell -c "
from system.models import PreRegistration, PreRegistrationStatus
from system.constants import CheckoutAction

pr = PreRegistration.objects.create(
    session_key='test-session-key-001',
    registration_profile='student',
    holder_cpf='00000000000',
    holder_email='teste@lvjiujitsu.com.br',
    status=PreRegistrationStatus.AWAITING_PAYMENT,
    checkout_action=CheckoutAction.ASAAS_PIX,
    form_snapshot={
        'plan_payment': {
            'asaas_payment_id': 'pay_pr_test_001',
        },
        'plan_paid': False,
    },
)
print(f'PreRegistration pk={pr.pk} status={pr.status}')
"
```

#### 4.2 Simulate the Asaas redirect to payment-success (stage=plan)

> This call simulates what happens when the user's browser is redirected back by Asaas.
> It requires Django running at 127.0.0.1:8000.

```powershell
# Through the browser: open http://127.0.0.1:8000/pagamentos/sucesso/?pre_registration_id=PR_PK&stage=plan
# Django processes it and marks plan_paid=True in the snapshot

# Through the shell (a direct equivalent with no browser):
.\.venv\Scripts\python.exe manage.py shell -c "
from system.models import PreRegistration, PreRegistrationStatus
pr = PreRegistration.objects.get(pk=PR_PK)
snap = pr.form_snapshot or {}
snap['plan_paid'] = True
pr.form_snapshot = snap
pr.status = PreRegistrationStatus.PAYMENT_CONFIRMED
pr.save(update_fields=['form_snapshot', 'status', 'updated_at'])
print('PreRegistration updated:', pr.pk, pr.status, 'plan_paid:', snap.get('plan_paid'))
"
```

#### 4.3 Check the wizard's state after the confirmation

```powershell
.\.venv\Scripts\python.exe manage.py shell -c "
from system.models import PreRegistration
pr = PreRegistration.objects.get(pk=PR_PK)
snap = pr.form_snapshot or {}
print('status:', pr.status)
print('plan_paid:', snap.get('plan_paid'))
print('materials_paid:', snap.get('materials_paid'))
"
```

---

### Step 5 — Simulate the Stripe webhooks

#### 5.1 Checking the secret's status

The configured `STRIPE_WEBHOOK_SECRET` (`whsec_m*`) is the static secret generated by the Stripe dashboard for the endpoint registered in HG Render. **That secret cannot be used to sign a payload manually** — Stripe's validation uses HMAC-SHA256 with a timestamp.

**For a local simulation, install the Stripe CLI:**

```powershell
# Windows — through Scoop (recommended)
scoop bucket add stripe https://github.com/stripe/scoop-stripe-cli.git
scoop install stripe

# Or download directly: https://github.com/stripe/stripe-cli/releases
# Extract stripe.exe and add it to PATH
```

**Check the installation:**

```powershell
stripe --version
stripe login
```

#### 5.2 Start the local listener (Stripe CLI)

```powershell
# Terminal 1 — listener (generates a temporary whsec_ for the session)
stripe listen --forward-to http://127.0.0.1:8000/pagamentos/webhook/stripe/

# Copy the displayed "webhook signing secret" (whsec_xxx)
# Temporarily update .env: STRIPE_WEBHOOK_SECRET=whsec_xxx (the CLI value)
# Restart Django to load the new value
```

#### 5.3 Trigger the events (Terminal 2, with the listener active)

```powershell
# checkout.session.completed — session payment confirmed
stripe trigger checkout.session.completed

# checkout.session.expired — session expired (marks the order CANCELED)
stripe trigger checkout.session.expired

# payment_intent.payment_failed — payment failed
stripe trigger payment_intent.payment_failed

# invoice.paid — recurring invoice paid (Stripe Subscription)
stripe trigger invoice.paid

# invoice.payment_failed — recurring invoice payment failed
stripe trigger invoice.payment_failed

# customer.subscription.updated — plan updated
stripe trigger customer.subscription.updated

# customer.subscription.deleted — plan cancelled
stripe trigger customer.subscription.deleted

# charge.refunded — refund
stripe trigger charge.refunded
```

**Expected state after each event:** HTTP 200 in the listener's terminal, a `StripeWebhookEvent` created in the database.

```powershell
.\.venv\Scripts\python.exe manage.py shell -c "
from system.models.registration_order import StripeWebhookEvent
for e in StripeWebhookEvent.objects.order_by('-created_at')[:10]:
    print(e.created_at.strftime('%H:%M:%S'), e.event_type, 'order:', e.order_id, 'membership:', e.membership_id)
"
```

#### 5.4 Without the Stripe CLI — an alternative for HG (with no local simulation)

If the Stripe CLI is not installed, the Stripe events must be tested directly in HG Render:

1. Open the [Stripe Dashboard](https://dashboard.stripe.com/test/webhooks)
2. Select the `https://lvjiujitsu-hg.onrender.com/pagamentos/webhook/stripe/` endpoint
3. Click "Send test webhook" for each event in the list above
4. Check the status in the Stripe dashboard and in the HG database through `manage.py shell` with `.env.hg`

---

### Step 6 — Consolidated database check after the tests

```powershell
.\.venv\Scripts\python.exe manage.py shell -c "
from system.models.registration_order import RegistrationOrder, StripeWebhookEvent
from system.models.asaas import AsaasWebhookEvent
from system.models import PreRegistration

print('=== FINAL DATABASE STATE ===')
print()
print('RegistrationOrders:')
for o in RegistrationOrder.objects.all():
    print(f'  pk={o.pk} status={o.payment_status} asaas_id={o.asaas_payment_id}')

print()
print('PreRegistrations:')
for pr in PreRegistration.objects.all():
    snap = pr.form_snapshot or {}
    print(f'  pk={pr.pk} status={pr.status} plan_paid={snap.get(\"plan_paid\")} materials_paid={snap.get(\"materials_paid\")}')

print()
print('AsaasWebhookEvents:')
for e in AsaasWebhookEvent.objects.order_by('created_at'):
    print(f'  {e.event_type} order={e.order_id} duplicate_check: id={e.event_id[:20]}...')

print()
print('StripeWebhookEvents:')
for e in StripeWebhookEvent.objects.order_by('created_at'):
    print(f'  {e.event_type} order={e.order_id} membership={e.membership_id}')
"
```

---

## Readiness checklist for HG Render + Chrome MCP

### HG environment configuration

- [ ] `SITE_BASE_URL` on Render HG points at `https://lvjiujitsu-hg.onrender.com` ✓ (already configured locally)
- [ ] `ASAAS_API_URL` points at `https://api-sandbox.asaas.com/v3` (sandbox) ✓
- [ ] `ASAAS_WEBHOOK_TOKEN` configured in the Render HG Dashboard (the same value as in `.env.hg`)
- [ ] `STRIPE_SECRET_KEY` configured in the Render HG Dashboard (sk_test)
- [ ] The `STRIPE_WEBHOOK_SECRET` from the Stripe dashboard configured for the HG endpoint

### Webhook URL validation in the Asaas dashboard

- [ ] Asaas sandbox dashboard → My Account → Notifications → URL = `https://lvjiujitsu-hg.onrender.com/pagamentos/webhook/asaas/`
- [ ] The token configured in the Asaas dashboard = the same value as `ASAAS_WEBHOOK_TOKEN`

### Webhook URL validation in the Stripe dashboard

- [ ] Stripe Dashboard → Webhooks → endpoint = `https://lvjiujitsu-hg.onrender.com/pagamentos/webhook/stripe/`
- [ ] Enabled events: `checkout.session.completed`, `checkout.session.expired`, `payment_intent.payment_failed`, `invoice.paid`, `invoice.payment_failed`, `customer.subscription.updated`, `customer.subscription.deleted`, `charge.refunded`, `charge.refund.updated`

### Test script through Chrome MCP on HG Render

#### Flow A — An existing student (a RegistrationOrder + a real webhook)

1. Log in to HG Render as a student with a pending order
2. Navigate to the checkout `/pagamentos/<order_id>/asaas-pix/`
3. Complete the PIX payment in the Asaas sandbox
4. Wait for the webhook to arrive (1–5 seconds)
5. Check through the HG shell that `RegistrationOrder.payment_status = PAID`

```powershell
$env:DJANGO_ENV_FILE=".env.hg"
.\.venv\Scripts\python.exe manage.py shell -c "
from system.models.registration_order import RegistrationOrder, PaymentStatus
from system.models.asaas import AsaasWebhookEvent
print('Latest orders:', list(RegistrationOrder.objects.filter(payment_status=PaymentStatus.PAID).values('pk', 'paid_at').order_by('-paid_at')[:5]))
print('Latest events:', list(AsaasWebhookEvent.objects.order_by('-created_at').values('event_type', 'created_at')[:5]))
"
```

#### Flow B — The public wizard (a PreRegistration through Chrome MCP)

1. Chrome MCP navigates to `https://lvjiujitsu-hg.onrender.com/cadastro/`
2. Fill in the data → choose a plan
3. Click to pay → go to the Asaas sandbox
4. In the Asaas sandbox: use the test card `4111 1111 1111 1111` or a fictional PIX
5. Wait for the redirect back to `/pagamentos/sucesso/?pre_registration_id=X&stage=plan`
6. Check that the wizard advances to step-materials
7. Complete materials and the summary
8. Finish → check that a `Person` was created in the HG database

```powershell
$env:DJANGO_ENV_FILE=".env.hg"
.\.venv\Scripts\python.exe manage.py shell -c "
from system.models import PreRegistration, Person
from system.models import PreRegistrationStatus
finalized = PreRegistration.objects.filter(status=PreRegistrationStatus.FINALIZED).order_by('-updated_at')[:3]
for pr in finalized:
    print(f'PR pk={pr.pk} email={pr.holder_email}')
new_persons = Person.objects.order_by('-created_at')[:3]
for p in new_persons:
    print(f'Person pk={p.pk} name={p.full_name} active={p.is_active}')
"
```

---

## Acceptance criteria

- [ ] `manage.py check` passes with 0 issues (verifiable: the command)
- [ ] An Asaas webhook with the correct token returns HTTP 200 (verifiable: Invoke-RestMethod)
- [ ] An Asaas webhook with an invalid token returns HTTP 401 (verifiable: Invoke-WebRequest + StatusCode)
- [ ] A duplicate event returns HTTP 200 without duplicating the `AsaasWebhookEvent` (verifiable: a shell count)
- [ ] PAYMENT_CONFIRMED updates `RegistrationOrder.payment_status = PAID` (verifiable: the shell)
- [ ] PAYMENT_OVERDUE updates it to `FAILED` (verifiable: the shell)
- [ ] PAYMENT_REFUNDED updates it to `REFUNDED` and records `refunded_at` (verifiable: the shell)
- [ ] Confirming a PreRegistration through `payment-success` marks `plan_paid=True` and `status=PAYMENT_CONFIRMED` (verifiable: the shell)
- [ ] A Stripe webhook returns HTTP 200 for valid events (verifiable: the Stripe CLI or the dashboard)
- [ ] A Stripe webhook returns HTTP 400 for a payload with no signature (verifiable: curl/Invoke-WebRequest)
- [ ] A `StripeWebhookEvent` created for each Stripe event processed (verifiable: the shell)
- [ ] On HG Render: `SITE_BASE_URL` configured correctly → a valid successUrl for Asaas

---

## Risks and edge cases

| Risk | Impact | Mitigation |
|---|---|---|
| `SITE_BASE_URL` pointing at HG locally | The Asaas successUrl redirects the browser to HG, not to 127.0.0.1 | For local browser tests, temporarily switch it to ngrok |
| The Stripe CLI is absent | Simulating signed Stripe webhooks locally is impossible | Install it through Scoop or use the Stripe dashboard to test directly on HG |
| An empty database with no seeds | The webhooks process with no effect (the order is not found) | Run the minimal seeds or create data through the shell before the tests |
| A unique `AsaasWebhookEvent.event_id` | A second send of the same `id` returns `duplicate=True` | Use a different `id` in each test or verify the behavior is intentional |
| An Asaas sandbox vs production token | A webhook with a prod token does not work locally/in hg | Check that `ASAAS_WEBHOOK_TOKEN` matches the correct Asaas dashboard environment |

---

## Rules and constraints

- SDD before code — this PRD is a validation document, with no code changes
- No hardcoding — no token revealed in a log or in the document
- No migrations — this PRD does not change the schema
- Mandatory full reading — every file in the flow was read before this PRD

---

## Minimum technical validation

```powershell
# 1. Check Django
.\.venv\Scripts\python.exe manage.py check

# 2. Check tokens
.\.venv\Scripts\python.exe manage.py shell -c "
from django.conf import settings
assert settings.ASAAS_WEBHOOK_TOKEN, 'ASAAS_WEBHOOK_TOKEN is empty'
assert settings.STRIPE_SECRET_KEY, 'STRIPE_SECRET_KEY is empty'
assert settings.STRIPE_WEBHOOK_SECRET, 'STRIPE_WEBHOOK_SECRET is empty'
print('All tokens configured.')
"

# 3. Check that the routes respond (expect 405 for GET, not 404)
Invoke-WebRequest -Method GET -Uri "http://127.0.0.1:8000/pagamentos/webhook/asaas/" | Select StatusCode
# Expected: 405 (Method Not Allowed) — the route exists but accepts only POST
```

---

## Execution plan

- [x] 1. Run Step 0 — check the tokens
- [x] 2. Run the minimal seeds (the destructive cycle + 19 seeds, 220 tests)
- [ ] 3. Create a test RegistrationOrder (Step 1) — not executed (Flow A with no existing student)
- [x] 4. Simulate the Asaas PAYMENT_CONFIRMED webhook for a PreRegistration
- [x] 5. Check the database after each event
- [x] 6. Create a test PreRegistration and simulate the complete wizard (Flow B PIX + Stripe)
- [x] 7. Install the Stripe CLI and test the webhooks locally (v1.42.10)
- [ ] 8. Check the Asaas HG and Stripe HG dashboards for the correct URLs
- [ ] 9. Test the complete flow through Chrome MCP on HG Render
- [ ] 10. Check the HG database after the end-to-end test

---

## Evidence

### Local tokens (verified directly in the .env — 2026-06-10)

```
ASAAS_WEBHOOK_TOKEN:   configured     ✓   (whsec_5Wws... — Asaas webhooks HTTP 200)
ASAAS_API_KEY:         configured     ✓   (len=166, outbound calls work)
ASAAS_API_URL:         configured     ✓   (sandbox api-sandbox.asaas.com/v3)
STRIPE_SECRET_KEY:     configured     ✓   (sk_test, len=107)
STRIPE_WEBHOOK_SECRET: configured     ✓   (whsec_74ab90bc... — active Stripe CLI session)
SITE_BASE_URL:         configured     ✓   (https://lvjiujitsu-hg.onrender.com)
manage.py check:       0 issues       ✓
Stripe CLI:            installed      ✓   (v1.42.10, lvjiujitsu account acct_1TLsxdItFp0xr82s)
```

### The destructive cycle and the seeds

```
clear_migrations.py → makemigrations → test (220 passed) → migrate  ✓
19 seeds executed in sequence                                          ✓
Clean database ready for testing                                       ✓
```

### Flow 1 — Asaas PIX wizard (2026-06-10)

```
User: Carlos Teste PIX
CPF: 529.982.247-25
Profile: Student (holder)
Plan: Individual twice a week - Asaas PIX - Monthly (R$ 221.99)
Class: Adult Jiu Jitsu

Completed steps:
  Step 1 (profile)      ✓  profile-card-holder selected
  Step 2 (data)         ✓  every field filled in; sex set through nativeSetter
  Step 3 (health)       ✓  O+ blood type, emergency contact configured
  Step 4 (martial art)  ✓  "I do not practice martial arts"
  Step 5 (classes)      ✓  Adult · Jiu Jitsu selected
  Step 6 (plan)         ✓  Asaas PIX selected; checkout_action=pix

POST /register/ → 302  (PreRegistration created)
  PreRegistration ID=1  status=awaiting_payment
  asaas_customer: cus_000008140775  (customer created in the Asaas sandbox)
  asaas_payment_id: pay_jabllbvma5u4izrz  (PIX charge created)

PAYMENT_CONFIRMED webhook simulated through curl:
  POST /pagamentos/webhook/asaas/ → 200  ✓
  AsaasWebhookEvent created: id=1 type=PAYMENT_CONFIRMED

Simulated redirect: GET /pagamentos/sucesso/?id=pay_jabllbvma5u4izrz → 302
  PreRegistration ID=1: status=payment_confirmed, plan_paid=True  ✓

Materials: skipped
Summary: Ana Teste Stripe / correct plan displayed  ✓

POST /register/finalizar/ → 302
  Person created: Carlos Teste PIX  is_active=True  ✓
  Membership: active  Individual twice a week - Asaas PIX - Monthly  ✓
  Dashboard loaded: "Registration completed successfully!"  ✓
  PreRegistration ID=1: status=finalized  ✓
```

### Flow 2 — Recurring Stripe card wizard (2026-06-10)

```
User: Ana Teste Stripe
CPF: 871.443.267-69
Profile: Student (holder)
Plan: Individual twice a week - Stripe Card - Monthly Recurring Subscription (R$ 228.80)
Class: Adult Jiu Jitsu

POST /register/ → 302  (PreRegistration created)
  PreRegistration ID=2  status=awaiting_payment
  checkout_action=stripe_card
  stripe_session_id: cs_test_a14oHBE7tIKAXetl7JwkSpjUV6BuTCeTIjKkOf1FxSDNFe6DRjq3ic5Gk6

checkout.session.completed webhook through the Stripe CLI:
  stripe trigger checkout.session.completed
    --override checkout_session:client_reference_id="pre-registration:2"
  POST /pagamentos/webhook/stripe/ → 200  ✓  (11+ events processed)
  PreRegistration ID=2: status=payment_confirmed, plan_paid=True  ✓
  Note: stripe trigger uses a fictitious session ID — it replaces stripe_session_id in the snapshot

Redirect simulated with the fixture ID:
  GET /pagamentos/sucesso/?session_id=cs_test_a17z3OHVA... → 302
  Wizard: step-plan in "Payment confirmed" mode ✓

Materials: skipped
Summary: Ana Teste Stripe / Recurring Stripe / R$ 228.80  ✓

POST /register/finalizar/ → 302
  Person created: Ana Teste Stripe  is_active=True  ✓
  Membership: active  Individual twice a week - Stripe Card - Monthly Recurring Subscription  ✓
  Dashboard: "Registration completed successfully! Welcome."  ✓
```

### Webhook simulations executed

| Event | HTTP | Result |
|---|---|---|
| Asaas PAYMENT_CONFIRMED (`pay_jabllbvma5u4izrz`) | 200 ✓ | An AsaasWebhookEvent created (a PreRegistration — order_id=None as expected) |
| Stripe `checkout.session.completed` (`pre-registration:2`) | 200 ✓ | A StripeWebhookEvent created; the PreRegistration confirmed |
| Stripe `charge.updated`, `payment_intent.created`, etc. | 200 ✓ | Events recorded with no effect (the order does not exist — correct) |

### The browser console (the preview browser)

No critical JavaScript error during the entire flow of both registrations.

### HG Render

- [ ] The Asaas webhook URL configured in the dashboard
- [ ] The Stripe webhook URL configured in the dashboard
- [ ] The complete wizard flow through Chrome MCP on HG
- [ ] A Person created in the HG database after finalization

## Implemented

An operational validation document — no code changed.  
The Stripe CLI installed (v1.42.10) and `STRIPE_WEBHOOK_SECRET` configured in the `.env`.

## Deviations from plan

- `stripe trigger` with `--override checkout_session:id` is not supported — the fixture uses a session ID different from the real one. Consequence: the `stripe_session_id` in the snapshot gets overwritten by the fixture's ID after the webhook. The redirect back must use the fixture's ID, not the original one. In production/HG this problem does not occur (the session ID is always consistent).
- `SITE_BASE_URL` points at HG Render: the Asaas `successUrl` points at HG, not at localhost. In local tests the redirect is simulated manually through the browser.

## Pending

- [ ] Confirm the webhook URLs in the Asaas sandbox and Stripe test dashboards for the HG environment
- [ ] Run the test script through Chrome MCP on HG after the next deploy
