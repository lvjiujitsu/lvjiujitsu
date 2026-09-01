# PRD-088: Full registration flow review — pre-registration, sequential payment, and explicit finalization

> **SUPERSEDED BY PRD-040 ON 2026-05-21.**
> This PRD recorded an intermediate solution with `Person(is_active=False)` before the finalization.
> That approach is no longer accepted.
> The current source of truth is `docs/prd/PRD-040-payment-before-person-creation-registration-flow.md`: the tuition and the materials must be paid before any creation of a `Person`, `PortalAccount`, relationships, classes, or access.

## Summary of the implementation

A complete restructuring of the public registration flow so that:

1. The person's registration (Person, PortalAccount, ClassEnrollment) **is not activated** before the user clicks "Finish registration"
2. The **plan** payment happens first (Stripe or PIX), separate from the **materials** payment
3. The **materials** payment follows the same pattern as the plan (a dedicated checkout), not bundled
4. A **summary screen** shows everything that was paid before the finalization
5. "Finish registration" is the only point that activates the complete record in the system

---

## Demand type

An architectural fix + a new feature (the sequential payment flow)

---

## Current problem

### 1. The record created before the payment

In `PortalRegisterView.form_valid()`, the `create_portal_registration()` call happens immediately:

```python
# system/services/registration.py — create_portal_registration()
# Person + PortalAccount + ClassEnrollment are created HERE
result = _create_holder_registration(cleaned_data, person_types)
# AFTER that, the order is created
result["order"] = create_registration_order(result["holder"], cleaned_data)
```

The consequence: if the payment fails or the user abandons the flow, the person stays persisted in the database with the CPF "taken". On the next attempt, the form returns "CPF já cadastrado no sistema." ("CPF already registered in the system.") and the registration breaks completely.

### 2. Materials paid together with the plan (with no flow of their own)

`create_registration_order()` includes the plan + the products in a single `RegistrationOrder`. There is no checkout screen for materials — everything is summed and paid at once. The user does not see an explicit materials flow with a separate confirmation.

### 3. Incorrect redirects to login

After `PaymentSuccessView`, the flow redirects back to `/register/` with a session flag (`post_payment_complete`). That is fragile and causes:
- the wizard to reload from scratch with no user data
- `DeferPaymentView` to redirect to `system:login` even when it should go to the dashboard
- `PaymentCancelView` to redirect to login inappropriately

### 4. An inconsistent post-payment state

After the Stripe payment, `PaymentSuccessView` performs an auto-login and redirects to `/register/`. The wizard loads in "post-payment mode" but with none of the data the user filled in, because:
- the form was submitted and the Django session did not preserve the data
- `localStorage` still has the draft, but the page reloads from scratch with no wizard state

---

## Goal

Ensure that:
- **Before the finalization**: only the financial record (RegistrationOrder) exists — the person is in the `is_active=False` state
- **Plan and materials**: each has its own checkout (Stripe/PIX), sequentially
- **Finish registration**: the only point that sets `Person.is_active=True` and grants portal access

---

## Context Ledger

### Files read in full

- `system/forms/registration_forms.py` — 740 lines, the complete form with its validations
- `system/services/registration.py` — 403 lines, `create_portal_registration()` and its sub-functions
- `system/services/registration_checkout.py` — 462 lines, `create_registration_order()`, `create_product_only_order()`
- `system/views/auth_views.py` — 250 lines, `PortalRegisterView.form_valid()`
- `system/views/payment_views.py` — 263 lines, `PaymentSuccessView`, `DeferPaymentView`
- `system/views/asaas_views.py` — 278 lines, `CreatePixChargeView`
- `system/models/registration_order.py` — 276 lines, `RegistrationOrder.person` (a NOT NULL FK)
- `system/models/person.py` — Person with `is_active = models.BooleanField(default=True)` (line 128)
- `system/services/portal_auth.py` — 80 lines, `resolve_portal_account_from_session` filters by `person__is_active=True`

### The critical architectural fact

`RegistrationOrder.person` is a **NOT NULL** FK. It is impossible to create an order without having a Person first. The solution with no new migration is: **create the Person with `is_active=False`** — the field already exists and is already checked in `resolve_portal_account_from_session`.

### No new migration

`Person.is_active` already exists. No schema change is necessary to implement this PRD.

---

## The complete desired flow

```
[Wizard steps 1–5]
Type → Personal data → Jiu Jitsu → Medical record → Classes
         (client-side, localStorage draft)
                ↓
[Step 6: Plan]
Select plan → choose payment method
"Pay for plan" → POST form → create Person(is_active=False) + RegistrationOrder(plan)
                               store person_id in session
                ↓
[Plan checkout]
Stripe (card) or PIX → payment confirmed
                ↓
[PaymentSuccessView—plan paid]
automatic login → session: plan_paid=True, plan_order_id=X, reg_person_id=Y
→ redirect → /register/ (wizard step: materials)
                ↓
[Step 7: Materials] ← NEW STEP AFTER PLAN PAYMENT
Display "✓ Plan paid" badge
Product catalog with selection (Color select + Size select + qty)
[Pay for materials] or [Finish without materials]
                ↓ (if materials selected)
POST → MaterialsCheckoutView → create RegistrationOrder(products, person=session person)
→ Stripe or PIX → payment confirmed
→ PaymentSuccessView (materials) → session: materials_paid=True, materials_order_id=Z
→ redirect → /register/ (wizard step: summary/finalize)
                ↓
[Step 8: Summary and finalization] ← NEW STEP
Show: paid plan (name, amount) + paid materials (items, total)
Button: "Finalize registration"
                ↓
POST → FinalizeRegistrationView
→ person.is_active = True
→ clear pre-registration session
→ redirect → dashboard
```

---

## Scope

### Backend

1. **`create_portal_registration()`** (`system/services/registration.py`)
   - Create the Person with `is_active=False`
   - Create the PortalAccount (necessary for the post-payment login)
   - Create the ClassEnrollments normally (an inactive person does not appear in queries with no explicit filter)
   - Create only the plan's RegistrationOrder (with no products in the first order)

2. **`PortalRegisterView.form_valid()`** (`system/views/auth_views.py`)
   - Remove the products from the initial order (the plan only)
   - Store `person.pk` in the session as `pending_registration_person_id`
   - Keep the redirect to Stripe/PIX/deferred according to `checkout_action`

3. **`_validate_single_cpf()`** (`system/forms/registration_forms.py`)
   - If a Person with that CPF exists and `is_active=False`: allow the replacement (overwriting the inactive record)
   - If a Person with that CPF exists and `is_active=True`: block with "CPF já cadastrado" ("CPF already registered")

4. **`PaymentSuccessView`** (`system/views/payment_views.py`)
   - Detect whether it is a plan or a materials payment through the RegistrationOrder's type
   - The plan paid: set the session `post_plan_payment_complete=True`, `plan_order_id`, and redirect → `/register/` (the materials step)
   - The materials paid: set the session `post_materials_payment_complete=True`, and redirect → `/register/` (the summary step)

5. **`MaterialsCheckoutView`** — A NEW VIEW (`system/views/auth_views.py` or a new file)
   - A POST with the materials cart (a JSON payload)
   - Recovers the Person through `pending_registration_person_id` in the session
   - Creates a `RegistrationOrder` (kind=ONE_TIME) with the products
   - Redirects to Stripe or PIX

6. **`FinalizeRegistrationView`** — A NEW VIEW
   - A POST (with CSRF)
   - Recovers the Person through `pending_registration_person_id` in the session
   - Validates that the plan was paid (`plan_order_id` with `payment_status=PAID` or `EXEMPTED`)
   - `person.is_active = True` + `person.save()`
   - Clears the pre-registration keys from the session
   - Auto-login (already logged in through `PaymentSuccessView`)
   - Redirect → the dashboard

7. **`DeferPaymentView`** (`system/views/payment_views.py`)
   - After deferring: do NOT redirect to login
   - Set `post_plan_payment_complete=True` (the plan "paid" through a trial/deferral)
   - Redirect → `/register/` (the materials step) or straight to the finalization

8. **`PaymentCancelView`** (`system/views/payment_views.py`)
   - Redirect to `/register/` (re-showing the plan payment step), NOT to login

### New URLs

```python
# system/urls.py
path("register/materials-checkout/", MaterialsCheckoutView.as_view(), name="materials-checkout"),
path("register/finalize/", FinalizeRegistrationView.as_view(), name="finalize-registration"),
```

### Frontend — the wizard JavaScript (`static/system/js/auth/registration-wizard-clean.js`)

1. **Step 6 (Plan)**: the action button changes to `Pagar plano` (`Pay for the plan`) (no longer `Avançar` — `Next`) — it triggers the complete form's submit

2. **Step 7 (Materials) — NEW after the payment**:
   - The badge `✓ Plano pago` (`✓ Plan paid`) (the green badge is already implemented)
   - The product catalog with a select-based UI (already implemented)
   - The `Pagar materiais` (`Pay for materials`) button → a POST to `/register/materials-checkout/` (a form with its `action` pointing at the new URL)
   - The `Continuar sem materiais` (`Continue without materials`) button → goes straight to the summary step

3. **Step 8 (Summary/Finish) — NEW**:
   - It reads `plan_order_data` and `materials_order_data` from the session (injected as JSON in the template)
   - It shows: the selected plan + the amount; the material items + the total
   - The `Finalizar cadastro` (`Finish registration`) button → a POST to `/register/finalize/`

### CSS (`static/system/css/auth/login.css`)

- Styles for the summary step (the visual pattern already exists)
- The materials step already has styles (catalog-product-*)

### The template (`templates/login/register.html`)

- Inject the post-payment context JSON: `plan_order_json` and `materials_order_json`
- Inject the new views' URLs as JSON data (do not hardcode them in the JavaScript)

---

## Out of scope

- Changing the Membership / Stripe subscription model
- Changing the administrative orders panel
- Financial reports
- Resending the welcome email (it can be added later)
- Cancelling / refunding materials (the post-purchase flow)

---

## Impacted files

| File | Type of change |
|---|---|
| `system/services/registration.py` | Create the Person with is_active=False |
| `system/forms/registration_forms.py` | Allow overwriting an inactive Person in the CPF check |
| `system/views/auth_views.py` | A revised form_valid + the new views (Materials, Finalize) |
| `system/views/payment_views.py` | PaymentSuccessView, DeferPaymentView, PaymentCancelView |
| `system/urls.py` | New routes |
| `system/services/registration_checkout.py` | create_registration_order → the plan only; create_product_only_order already exists |
| `templates/login/register.html` | New JSON contexts, the asset version updated |
| `static/system/js/auth/registration-wizard-clean.js` | Steps 7 and 8, the revised post-payment logic |
| `static/system/css/auth/login.css` | Styles for the summary step |

---

## Risks and edge cases

| Risk | Mitigation |
|---|---|
| An inactive person with the CPF "taken" if the user abandons | _validate_single_cpf allows overwriting a Person with is_active=False |
| The user pays for the plan but closes the browser before the materials | The session persists; on returning to /register/, the wizard resumes at the correct step through the session flags |
| Materials with insufficient stock between the selection and the payment | apply_order_variant_stock (already existing) applies an atomic deduction in the success webhook |
| The payment webhook arrives before the redirect | The order already exists with payment_status=PENDING; the webhook updates it to PAID; the redirect only sets the session flag |
| An authenticated user reaching /register/ with no pre-registration session | If person.is_active=True and the session has no pending_registration: redirect to the dashboard |
| A double submit of the finalization | FinalizeRegistrationView is idempotent: if person.is_active is already True, it just redirects to the dashboard |
| A plan paid through "pay later" (a trial) | DeferPaymentView sets plan_paid=True in the session, allowing the flow to advance to the materials |

---

## Rules and constraints

- SDD before code
- TDD for the implementation
- No hardcoding
- No error masking
- **No new migrations** — Person.is_active already exists and is enough
- Mandatory full reading before any edit
- Mandatory in-browser validation

---

## Plan

- [ ] 1. Context and full reading (completed)
- [ ] 2. Red tests: create tests for the new flow in `system/tests/test_views.py` and `test_services.py`
- [ ] 3. `_validate_single_cpf`: allow overwriting an inactive Person
- [ ] 4. `create_portal_registration()`: the Person with is_active=False
- [ ] 5. `create_registration_order()`: separate the products (the materials order becomes exclusive to create_product_only_order)
- [ ] 6. `PortalRegisterView.form_valid()`: store person_id in the session; the correct redirect
- [ ] 7. `PaymentSuccessView`: differentiate plan vs. materials; set the correct session
- [ ] 8. `DeferPaymentView` + `PaymentCancelView`: fix the redirects
- [ ] 9. `MaterialsCheckoutView`: the new view
- [ ] 10. `FinalizeRegistrationView`: the new view
- [ ] 11. The new URLs
- [ ] 12. The wizard JavaScript: steps 7 and 8, the post-payment logic
- [ ] 13. The template: the new JSON contexts + the asset version
- [ ] 14. CSS: styles for the summary step
- [ ] 15. Green tests: everything passing
- [ ] 16. Validation with `manage.py test --verbosity 2`
- [ ] 17. In-browser visual validation
- [ ] 18. Cleanup of the temporary artifacts (`_patch_buildProductCard.py`)
- [ ] 19. Documentation update

---

## Acceptance criteria

- [ ] On submitting the wizard up to the plan, the Person is created with is_active=False — verifiable through the shell: `Person.objects.filter(cpf=X).first().is_active == False`
- [ ] The CPF of an inactive Person can be reused in the wizard with no "CPF já cadastrado" ("CPF already registered") error — verifiable through a test
- [ ] After the plan is paid (Stripe/PIX), the redirect goes to the wizard at the materials step, NOT to login
- [ ] `Pagar materiais` (`Pay for materials`) creates a new RegistrationOrder separate from the plan's order — verifiable through the ORM
- [ ] `Finalizar cadastro` (`Finish registration`) sets person.is_active=True — verifiable through the shell
- [ ] After the finalization, the redirect goes to the dashboard (never to login)
- [ ] "Pay later" (a trial) follows the same flow: it goes to the materials, not to login
- [ ] Cancelling the payment returns to the plan step in the wizard, not to login
- [ ] The browser console with no critical JavaScript errors
- [ ] The terminal with no stack trace

---

## Expected evidence

- `manage.py test --verbosity 2` — 0 failures, 0 errors
- `manage.py check` — no issues
- A screenshot: the wizard's plan step → submit → the inactive Person created
- A screenshot: the wizard's materials step → pay → the materials order created
- A screenshot: the summary step → finish → the active Person + the dashboard

---

## Fix 2026-05-11 — The plan payment confused with materials

**Cause:** `create_checkout_session_for_order` persisted `order.kind = OrderKind.ONE_TIME` for every Stripe checkout. `PaymentSuccessView` treated `ONE_TIME` as a materials-only order, setting `post_materials_payment_complete` and skipping the materials step in the wizard.

**Fix:** In `PaymentSuccessView`, classify through `order.plan_id is None` (a products-only order) vs. the presence of a plan in the order, instead of relying on `order.kind` alone.

**UX:** The post-plan wizard now includes an explicit **Summary** step between the materials and finishing (`registration-wizard-clean.js` + `register.html`).

**UX (pre-payment indicators):** For flows with a plan step, the progress bar now lists **Materials**, **Summary**, and **Finish** from the start, in a locked state (`phaseLocked`) until the plan is paid, aligning the user's expectation with the complete path.

---

## Implemented

_To be filled in after implementation_

## Deviations from plan

_To be filled in if necessary_

## Pending

_To be filled in after validation_
