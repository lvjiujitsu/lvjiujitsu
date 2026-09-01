# PRD-119: A dependent with materials, idempotency, and a pending CPF

## Summary
Clear PRD-118's pending items in the authenticated add-a-dependent flow: include optional materials in the wizard, make the POST tolerant to a double submit/refresh, and block a CPF already used in a pending pre-registration by the same guardian.

## Demand type
A functional follow-up with impact on Django MVT, the wizard UI, the materials payment, and the pre-registration's integrity.

## Current problem
- The `/dependents/add/` wizard completes the dependent without offering optional materials, even though the public flow already has a materials catalog and payment before the completion.
- `DependentRegistrationView.post()` creates a new `PreRegistration` for every valid POST that requires payment, which can duplicate drafts/checkouts on a resubmit.
- The form only blocks a CPF existing on an active `Person`; the same guardian can create another pending pre-registration for the same CPF.
- A repeated completion after the dependent's creation today turns into an active-CPF error instead of resolving idempotently.

## Goal
The authenticated guardian/student adds a dependent with optional materials inside the same wizard, without duplicating the person, the order, or the pre-registration on a resubmit, and without being able to open two pending pre-registrations for the same CPF.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/PRD-STANDARD.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `docs/prd/README.md`
- `docs/prd/PRD-118-add-dependent-after-enrollment.md`
- `docs/prd/PRD-040-payment-before-person-creation-registration-flow.md`
- `docs/prd/PRD-009-shop-at-the-authenticated-portal-with-pre-order-arrival-queue-and-student-history.md`
- `docs/prd/PRD-106-guardian-material-purchase-for-dependent.md`
- `system/models/pre_registration.py`
- `system/models/registration_order.py`
- `system/models/product.py`
- `system/forms/dependent_forms.py`
- `system/forms/product_forms.py`
- `system/services/dependent_registration.py`
- `system/services/registration_checkout.py`
- `system/services/product_backorders.py`
- `system/services/registration.py`
- `system/services/pre_registration.py`
- `system/views/dependent_views.py`
- `system/views/product_views.py`
- `system/views/payment_views.py`
- `system/views/auth_views.py`
- `system/urls.py`
- `templates/dependents/dependent_registration.html`
- `templates/products/product_store.html`
- `static/system/css/dependents/dependent_registration.css`
- `static/system/js/products/store_cart.js`
- `system/tests/test_dependent_registration.py`
- `system/tests/test_product_store.py`

### Adjacent files consulted
- `templates/login/register.html`
- `static/system/js/auth/register.js`
- `static/system/css/auth/register.css`

### Internet / official documentation
- Django 5.2 transactions: https://docs.djangoproject.com/en/5.2/topics/db/transactions/
  - Conclusion: the final flow's multiple writes must stay inside `transaction.atomic`; database exceptions must not be masked inside the atomic block.
- Django 5.2 form validation: https://docs.djangoproject.com/en/5.2/ref/forms/validation/
  - Conclusion: the pending CPF, the selected materials, and the materials payment need to be validated server-side in `Form.clean()`.
- Django 5.2 QuerySet `select_for_update`: https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-for-update
  - Conclusion: stock consistency and pre-registration reuse depend on transactions/locks when there are concurrent writes.

### Context7 / MCPs / tools verified
- Context7 `/websites/djangoproject_en_5_2`: consulted for `transaction.atomic`, `select_for_update`, `Form.clean()`, and `FormView`/POST.
- PowerShell and `rg`: working.

### Limitations found
- The current pre-registration materials flow uses Asaas, not Stripe, in `create_pre_registration_materials_payment`.
- There will be no real external gateway in this implementation without new operational authorization; the tests use mocks/local returns.
- The PRD changes neither the schema nor `RegistrationOrderItem`; the variant is still resolved through the already-existing textual snapshot.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved
The current request enumerates exactly the three pending items recorded in PRD-118. The scope is authorized as a follow-up to the previous implementation: optional materials in the wizard, resubmit idempotency, and blocking a pending CPF.

## Execution prompt
### Persona
A senior Django/MVT agent for LV JIU JITSU, with TDD, transactional services, and visual validation in the internal browser.

### Action
Implement the follow-up to the authenticated dependent wizard, keeping the payment-before-person contract and without rewriting the public/authenticated shop.

### Context
The system already has `PreRegistration`, a plan payment by pre-registration, a materials payment by pre-registration, a product catalog by variant, and an authenticated shop. The dependent wizard must reuse those contracts in a step of its own.

### Constraints
- Do not create a `Person` before the plan/mandatory material is resolved.
- Do not duplicate a pending `PreRegistration` of the same guardian for the same CPF.
- Do not duplicate the dependent on a double POST or a refresh.
- Do not write off stock without a confirmed payment.
- Do not move a business rule into the template/JS.
- Do not edit `staticfiles/`.
- Update the `?v=` if a versioned asset changes.

### Acceptance criteria
- [x] The `/dependents/add/` wizard shows a `Materiais opcionais` ("Optional materials") step with a catalog of in-stock variants.
- [x] If no material is selected, the flow moves on to the completion with no material charge.
- [x] If a material is selected, the wizard requires Asaas PIX/card for the materials and only completes after `materials_paid`.
- [x] A dependent's material payment writes `materials_payment` into `PreRegistration.form_snapshot`.
- [x] A `payment-success?stage=materials` return from the dependent flow goes back to `/dependents/add/` and marks `materials_paid`.
- [x] An active CPF already linked to the same guardian makes the POST idempotent and redirects to the home, with no error and no duplication.
- [x] An active CPF with no link to the guardian stays blocked.
- [x] A CPF in the same guardian's pending pre-registration blocks a new POST when it is not the session's own draft.
- [x] A POST resubmit with a pending plan payment reuses the session's/guardian's existing `PreRegistration`.
- [x] Focused tests cover the selected materials, the skipped materials, the material return, the pending CPF, and the idempotent completion.
- [ ] The internal browser validates desktop/mobile, the light/dark theme, and a console with no critical error.

### Expected evidence
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_dependent_registration system.tests.test_product_store`
- `.\.venv\Scripts\python.exe manage.py check`
- The local ORM for `PreRegistration.form_snapshot["materials_paid"]`, the person created once, and the absence of duplication.
- The internal browser at `/dependents/add/` and `/home/`.

### Output format
The PRD updated, the real tests and checks, the visual validation, an implementation summary, the pending items, and the status.

## Scope
- Extend `DependentRegistrationForm` with an optional per-variant material selection.
- Reuse the already-existing product catalog.
- Extend the dependent service to find/reuse a pending pre-registration and apply completion idempotency.
- Extend `PaymentSuccessView` for the dependent flow's `materials` stage.
- Adjust the dependent wizard's template/CSS.
- Update the focused tests.

## Out of scope
- A broad redesign of the `/store/` shop.
- The purchase and monthly fee history beyond what already exists.
- A backorder inside the dependent wizard.
- A real external payment in Asaas/Stripe.
- A new migration/schema.

## Impacted files
| File | Expected change |
|---|---|
| `system/forms/dependent_forms.py` | The pending CPF and materials validation |
| `system/services/dependent_registration.py` | Pre-registration reuse, the materials snapshot, and idempotency |
| `system/views/dependent_views.py` | The plan/material/completion orchestration |
| `system/views/payment_views.py` | The dependent flow's materials return |
| `templates/dependents/dependent_registration.html` | The optional materials step |
| `static/system/css/dependents/dependent_registration.css` | The materials layout in the wizard |
| `system/tests/test_dependent_registration.py` | The contract tests |
| `docs/prd/README.md` | The PRD's index entry |

## Risks and edge cases
- A simultaneous double click can arrive before the session is saved; the additional mitigation searches for a pending draft of the same owner/CPF.
- A product can go out of stock between the rendering and the POST; mitigated through server-side validation in `resolve_selected_product_items`.
- The materials payment can be confirmed before the visual return; `PaymentSuccessView` must accept snapshot idempotency.
- An active CPF of a person linked to the same guardian must be treated as an idempotent success, not as an error.

## Rules and constraints
- `transaction.atomic` on the completion and on the pre-registration creation/reuse.
- Server-side validation rules; the UI only collects.
- Messages in pt-BR.
- No new `innerHTML`.
- No hardcoded product/plan/CPF.

## Plan
- [x] 1. Create PRD-119.
- [x] 2. Add the Red tests.
- [x] 3. Implement the form/service/view.
- [x] 4. Update the template/CSS.
- [x] 5. Run the tests and `check`.
- [ ] 6. Validate in the internal browser.
- [x] 7. Audit the diff and update the PRD.

## Test plan
### Tests to author
- `test_materials_selected_after_plan_payment_redirects_to_materials_payment`
- `test_materials_success_returns_to_dependent_flow`
- `test_paid_resume_with_materials_paid_finalizes_once`
- `test_same_owner_pending_pre_registration_blocks_duplicate_cpf`
- `test_existing_owned_dependent_submission_is_idempotent`
- `test_product_catalog_renders_in_dependent_wizard`

### Execution authorization
Authorized locally. A real external payment is out of scope.

### Execution evidence
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_dependent_registration --verbosity 2`
  - The initial Red: the expected failures for the missing materials catalog, the `stage=materials` return, the pending CPF, and the idempotency.
  - Green after the implementation: 11 tests OK.
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_dependent_registration system.tests.test_product_store --verbosity 2`
  - 19 tests OK.
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_dependent_registration system.tests.test_product_store system.tests.test_pre_registration_service system.tests.test_registration_flow system.tests.test_stripe_webhook_view --verbosity 1`
  - 28 tests OK.
- `.\.venv\Scripts\python.exe manage.py test --verbosity 1`
  - 446 tests OK in 95.739s.
- `.\.venv\Scripts\python.exe manage.py check`
  - `System check identified no issues (0 silenced).`
- `git diff --check -- docs/prd/PRD-119-dependent-material-idempotency-and-cpf.md docs/prd/README.md system/forms/dependent_forms.py system/services/dependent_registration.py system/views/dependent_views.py system/views/payment_views.py templates/dependents/dependent_registration.html static/system/css/dependents/dependent_registration.css system/tests/test_dependent_registration.py`
  - No whitespace error; only CRLF warnings in already-touched files.

## Visual hierarchy
- The wizard keeps the current top, the numbered steps, and the final CTA.
- The materials appear after the financial condition, as step 5.
- Each product sits in a simple block: the name, the price, the variants/stock, and the quantity.
- The materials payment choice sits near the catalog.

## Wireframe
### Region: Step 5 — Optional materials
- Title: `Materiais opcionais`
- Subtitle: `Selecione materiais para o dependente ou deixe tudo zerado para comprar depois.`
- The list:
  - The product
  - The price
  - The variant/size/color
  - A quantity field capped at the stock
- Payment:
  - `Comprar depois` ("Buy later")
  - `PIX`
  - `Cartão` ("Card")
- A per-field/per-list error when the stock is invalid.

### Region: Actions
- Cancel
- `Finalizar dependente` ("Complete dependent"), `Pagar materiais` ("Pay for materials"), or `Ir para pagamento` ("Go to payment"), depending on the state.

## State machine
### The dependent
- `draft` -> `plan_payment_pending`
- `plan_payment_pending` -> `plan_paid`
- `plan_paid` -> `materials_pending`
- `materials_pending` -> `materials_paid`
- `plan_paid` -> `materials_skipped`
- `materials_paid|materials_skipped|family_plan` -> `finalized`
- `finalized` + a new POST -> `already_finalized`

## Visual validation
- [x] The authenticated rendering through the Django Client at `/dependents/add/`.
- [x] The HTML contains the `Materiais opcionais` ("Optional materials") step.
- [x] The HTML contains the dynamic `material_variant_<id>` field for an active in-stock variant.
- [x] The HTML contains the `Comprar depois` ("Buy later"), `PIX`, and `Cartão` ("Card") options.
- [x] An authenticated POST with a material selected and `Comprar depois` ("Buy later") returns the correct server-side error.
- [ ] Desktop `/dependents/add/` in the internal browser.
- [ ] Mobile `/dependents/add/` in the internal browser.
- [ ] The light theme in the internal browser.
- [ ] The dark theme in the internal browser.
- [ ] A console with no critical error in the internal browser.

Limitation: the internal browser's plugin was connected and the documentation was read, but the `browser.tabs.list()` and `browser.tabs.selected()` calls hung until timeout even after reconnecting and reading `browser-troubleshooting`. No external browser was used.

## ORM validation
- [x] The same owner/CPF does not create two active `PreRegistration` records.
- [x] `materials_payment` and `materials_paid` stay in the snapshot.
- [x] The dependent's `Person` is created once.

## Quality validation
- [x] The focused tests.
- [x] `manage.py check`.
- [x] The diff reviewed.

## Evidence
- The focused tests and the full suite run locally with success.
- The authenticated rendering through the Django Client returned:
  - `get_status: 200`
  - `has_materials_step: True`
  - `has_variant_field: True`
  - `has_materials_checkout_options: True`
  - `post_status: 200`
  - `has_material_payment_error: True`
  - `default_cta_requires_payment: True`
  - `pending_count_for_validation_cpf: 0`
- The internal browser was not visually validated because of a failure in the control plugin.

## Implemented
- `DependentRegistrationForm` now builds dynamic fields for active in-stock variants, validates the quantities, requires PIX/card when a material is selected, and blocks a CPF in the same guardian's pending pre-registration.
- The same active CPF already linked to the guardian is treated as an idempotent success.
- `dependent_registration` reuses the same owner/CPF's pending `PreRegistration`, persists the materials selection into the snapshot, preserves the payment states, and completes with `select_for_update`.
- The `stage=materials` payment return for the dependent flow marks `materials_paid` and goes back to `/dependents/add/`.
- On completing a dependent with paid materials, the system creates the paid product order exactly once, applies the financials, and writes off the stock.
- The template/CSS add the `Materiais opcionais` ("Optional materials") step to the wizard and adjust the CTA to depend on the real choice of a family plan or a confirmed payment.

## Cleanup findings
- No dead code or temporary file introduced in the scope.
- `staticfiles/` was not changed.
- `git diff --check` with no whitespace error in the follow-up's files.

## Follow-up PRDs
- No new functional follow-up opened by this PRD.

## Deviations from plan
- The visual validation in the internal browser could not be run because the plugin hung while listing/selecting tabs. The substitute validation was done through an authenticated Django Client, the focused tests, and the full suite.

## Pending
- Visually validate desktop/mobile/theme/console in the internal browser when the plugin responds again.

## Final status
Completed, with the internal browser's visual validation as a limitation.
