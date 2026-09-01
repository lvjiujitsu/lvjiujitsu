# PRD-090: Registration wizard UI fixes

## Summary of the implementation

Three targeted UI fixes in the registration wizard (`register.html` + `register.js`):

1. **The Back button hidden after payment** — `showPostPaymentMode` hides `#wizard-back` with `visibility:hidden` on `step-products` and `step-review`. The button must stay visible and functional.
2. **`Resumo do cadastro` (`Registration summary`) in the wrong place** — `renderConfirmationSummary('products-confirm-area')` renders the panel on the materials screen. That panel must appear **only** on the `Confirmar cadastro` (`Confirm registration`) screen (`step-review`).
3. **Divergent materials payment buttons** — the PIX button in the materials cart has `style="background:var(--text);color:var(--panel)"` (an inline style different from the plan's checkout). Both materials payment buttons must use only `btn-checkout-pay`, with no inline override.

## Demand type

A targeted UI fix — with no backend, schema, or functional flow change.

## Current problem

| # | Where | What is wrong |
|---|---|---|
| 1 | `showPostPaymentMode()` in the JavaScript | `back.style.visibility = 'hidden'` hides the back button on `step-products` and `step-review` |
| 2 | `showPostPaymentMode()` in the JavaScript | It calls `renderConfirmationSummary('products-confirm-area')` when `stepId === 'step-products'` |
| 3 | The `register.html` template, the cart sub-view | `<button id="products-btn-pay-pix" ... style="background:var(--text);color:var(--panel)">` |

## Goal

- The Back button visible in every phase of the wizard, with contextual behavior per phase.
- `Resumo do cadastro` (`Registration summary`) exclusive to the `step-review` screen.
- Materials payment buttons visually identical to the plan's checkout.

## Context Ledger

### Files read in full
- `templates/login/register.html` — the complete template
- `static/system/js/auth/register.js` — the navigation, `showPostPaymentMode`, `renderConfirmationSummary`, `onEnterCheckout`
- `static/system/css/auth/register.css` — `btn-checkout-pay`, `btn-checkout-later`, `wizard-back`, `reg-confirm-panel`

### Adjacent files consulted
- `system/views/auth_views.py` — `PortalRegistrationView`, `MaterialsCheckoutView`, `FinalizeRegistrationView`

## Scope

### Fix 1 — The Back button after payment

**Behavior per phase:**

| Phase | The Back button's action |
|---|---|
| The wizard's steps (step-profile … step-checkout) | It stays as is: `goTo(stepIndex - 1)`; on step 0 it navigates to login |
| `step-products` | Visible; it navigates to the previous screen (`step-review` does not exist yet); the default `href` (`/login/`) is kept — the user can leave the flow |
| `step-review` | Visible; a click calls `showPostPaymentMode('step-products')` (going back to materials) |

**JavaScript changes:**
- In `showPostPaymentMode`: remove `back.style.visibility = 'hidden'`.
- Add a listener on `elWizardBack` inside `showPostPaymentMode('step-review')` to navigate to `step-products`.
- On `step-products`: the back button stays visible with the default behavior (a link to login) — with no additional JavaScript override.
- Update the `#wizard-back-label` label per phase:
  - `step-products` → `"Voltar"` (`"Back"`) (the default, navigating to login)
  - `step-review` → `"← Materiais"` (`"← Materials"`)

### Fix 2 — Remove the Registration summary from step-products

**JavaScript changes:**
- In `showPostPaymentMode`: remove the `if (stepId === 'step-products') { renderConfirmationSummary('products-confirm-area'); }` block.
- `renderConfirmationSummary` continues to be called in `renderReview()` (for `review-summary-area`).

**Template changes:**
- Remove or keep `<div id="products-confirm-area"></div>` empty (it can stay as an anchor if necessary, but nothing renders there).

### Fix 3 — Materials payment buttons identical to the plan's checkout

**Template changes** (`register.html`, the `products-subview-cart` sub-view):
- Remove `style="background:var(--text);color:var(--panel)"` from the `#products-btn-pay-pix` button.
- Both `#products-btn-pay-card` and `#products-btn-pay-pix` keep only `class="btn-checkout-pay"` — a red background, identical to the plan checkout's button.

## Out of scope

- A structural redesign of the wizard
- Backend changes
- Schema changes or migrations
- New pre-registration cancellation behavior

## Impacted files

| File | Type of change |
|---|---|
| `static/system/js/auth/register.js` | Fix 1 (remove the hiding, add the back on step-review), Fix 2 (remove renderConfirmationSummary from products) |
| `templates/login/register.html` | Fix 3 (remove the inline style from the PIX button) |
| `static/system/css/auth/register.css` | No change (the styles are already correct) |

## Acceptance criteria

- [ ] On `step-products`, the header's Back button is visible and clickable
- [ ] On `step-review`, the header's Back button is visible and leads back to `step-products`
- [ ] The `step-products` screen does not display the `Resumo do cadastro` (`Registration summary`) panel
- [ ] The `Resumo do cadastro` (`Registration summary`) panel keeps appearing normally on `step-review`
- [ ] The `Pagar com Cartão` (`Pay by card`) and `Pagar com PIX` (`Pay by PIX`) buttons in the materials cart have a red background identical to the plan checkout's payment button
- [ ] No JavaScript error in the console after the changes
- [ ] The `?v=` version of the JavaScript and the CSS updated in the templates

## Plan

- [x] 1. Full reading of the impacted files
- [x] 2. Implement Fix 1 in the JavaScript
- [x] 3. Implement Fix 2 in the JavaScript
- [x] 4. Implement Fix 3 in the template
- [x] 5. Update the `?v=` on the changed assets (JS: v15→v16)
- [x] 6. In-browser validation (the wizard flow + the post-payment state)
- [x] 7. Console inspection

## Evidence

- `manage.py check` → 0 issues
- `manage.py collectstatic --noinput` → 169 static files copied
- **step-products**: `← Voltar` (`← Back`) visible in the header; a clean catalog with no `Resumo do cadastro` (`Registration summary`) panel; the `Pagar com Cartão` (`Pay by card`) and `Pagar com PIX` (`Pay by PIX`) buttons with an identical red style (`btn-checkout-pay`); `Pular` (`Skip`) with a secondary bordered style
- **step-review**: `← Materiais` (`← Materials`) visible in the header; a click navigates back to `step-products` with the progress bar at 80%; no application JavaScript errors
- The browser console: only MCP extension errors, no application error

## Implemented

- `static/system/js/auth/register.js` (v16): `showPostPaymentMode` rewritten to keep the back button visible, contextualize the label per phase, and add a return listener on step-review; the `renderConfirmationSummary('products-confirm-area')` call removed
- `templates/login/register.html`: `style="background:var(--text);color:var(--panel)"` removed from the `#products-btn-pay-pix` button; the JavaScript version updated to `?v=16`
