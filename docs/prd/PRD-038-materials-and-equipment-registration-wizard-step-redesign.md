# PRD-038: Redesign of the `Materiais e equipamentos` (`Materials and equipment`) step in the registration wizard

## Summary of the implementation

Completely rewrite the `step-products` step of the registration wizard to follow the same visual and interaction pattern as the plan and class steps: clickable cards with an internal transition (product → variant → cart), light/dark theme, and working payment buttons.

## Demand type

Screen redesign with behavior bug fixes

## Current problem

1. **A layout incompatible with the design system** — `step-products` uses a flat list with selects and steppers that do not follow the wizard's visual tokens (`plan-card`, `plan-filter-pill`, `wizard-step__actions`, etc.)
2. **`Pagar com Cartão` (`Pay by card`) does not work** — `setPayloads()` is called as a `submit` listener, but the hidden input payload is not updated before the submit fires; the form sends `[]`
3. **`Pular` (`Skip`) does not work** — `products-skip-form` submits the form correctly, but the button renders inside the footer with no guarantee that the CSRF token is in the form; investigate whether there is a nested `<form>` conflict
4. **No consistent theme** — elements such as `.product-item`, `.qty-stepper`, and `.product-variant-select` do not use the design system's CSS variables (`--panel`, `--border`, `--accent`, `--text`, `--muted`, `--radius-card`)
5. **Non-modular UX** — it shows every product at once in a vertical list, with no guided step-by-step flow

## Goal

Replace the current implementation with:

- **Sub-step 1 — Catalog**: a grid of product cards (1 card per product), similar to `plan-cards`, with an `Adicionar` (`Add`) button per card
- **Sub-step 2 — Configure item**: when `Adicionar` (`Add`) is clicked on a product with variants, transition to a variant (size/color) and quantity selection screen within the same `section`, with no separate modal
- **Sub-step 3 — Cart**: a list of the selected items with the total, payment buttons (Card / PIX), and a `Pular` (`Skip`) link
- Fix the payment forms' payload so it is set before the submit
- Ensure `Pular` (`Skip`) works
- Keep the light and dark themes with no elements using hardcoded colors

---

## Context Ledger

### Files read in full

- `templates/login/register.html` (the `step-products` section, lines 649–691)
- `static/system/js/auth/register.js` (the `renderProductGrid`, `bindProductForms`, `buildProductsPayload` functions, lines 1772–1872)
- `static/system/css/auth/register.css` (the existing product classes)

### Adjacent files consulted

- `system/views/auth_views.py` — `MaterialsCheckoutView` and `RegisterMaterialsCheckoutView`
- `system/services/registration.py` — `create_product_only_order`
- `templates/login/register.html` (the `step-plan` and `step-checkout` sections as a visual pattern reference)

### Internet / official documentation

- Not needed — a purely frontend implementation (HTML/CSS/JS) with a pattern already defined in the project

### MCPs / tools verified

- Playwright MCP — mandatory visual validation at the end

### Limitations found

- None

---

## Execution prompt

### Persona

Django + vanilla JavaScript development agent following SDD + the visual pattern already established in the LV Jiu-Jitsu registration wizard.

### Action

Reimplement the `step-products` step, replacing the flat list with a sub-step flow in 3 phases: a card catalog → configure the variant/quantity → a cart with payment.

### Context

The registration wizard (`templates/login/register.html` + `static/system/js/auth/register.js` + `static/system/css/auth/register.css`) already has a complete design system with CSS tokens, clickable plan cards (`plan-card`, `plan-card--selected`), pill filters (`plan-filter-pill`), and actions in `wizard-step__actions`. The materials step must follow that same system.

The backend (`RegisterMaterialsCheckoutView`) already accepts `selected_products_payload` as JSON with `[{"variant_id": N, "quantity": N}, ...]` and `checkout_action` as `asaas_card`, `pix`, or `pay_later`. No backend change is required.

### Constraints

- no hardcoded colors — use the design system's CSS variables
- no business logic in the frontend
- no migrations
- do not create new folders — only edit the existing files in `static/system/css/auth/`, `static/system/js/auth/`, and `templates/login/`
- the payment forms' payload must be serialized _before_ the submit
- mandatory full reading of the impacted files before editing
- when changing CSS or JS versioned by `?v=`, update the number in the template

---

## Scope

### Sub-step 1: Card catalog

- Replace `<div id="products-grid">` with a grid of cards with the same look as `plan-card`
- Each card shows: the product name, category, price range (`a partir de R$ X,XX` — `from R$ X.XX` when there are variants with different prices, or the single price), and a `Sem estoque` (`Out of stock`) badge when `total_stock === 0`
- A card with zero stock is disabled (no hover, default cursor, reduced opacity) — matching the unavailable class pattern
- The `Adicionar` (`Add`) button inside the card activates sub-step 2 for that product
- An item counter for the cart shown in the section heading when `cart.length > 0`: `X item(ns) no carrinho` (`X item(s) in the cart`)

### Sub-step 2: Configure item

- Shown inside `section#step-products`, hiding the catalog (`products-subview--catalog`) and showing `products-subview--configure`
- Heading: the product's name
- If the product has only 1 variant in stock: skip the variant selection and show the quantity stepper directly
- If there are multiple variants: render clickable pills per variant (`variant-pill`, `variant-pill--selected`) instead of a select — the same pattern as `plan-filter-pill`; a variant with no stock: a disabled pill
- Quantity stepper: min 1, max = the selected variant's `stock_quantity`
- An `Adicionar ao carrinho` (`Add to cart`) button — adds the item to the JavaScript `cart[]` state and returns to sub-step 1
- A `Cancelar` (`Cancel`) button — returns to the catalog without adding

### Sub-step 3: Cart

- `products-subview--cart` appears when `cart.length > 0`, through the `Ver carrinho (X)` (`View cart (X)`) button in the catalog's footer
- A list of items with name, variant, quantity, and subtotal; an `×` button to remove an item
- The grand total
- Two payment buttons: `Pagar com Cartão` (`Pay by card`) and `Pagar com PIX` (`Pay by PIX`) — each submits a POST form with the cart's serialized JSON payload
- A `Pular — adicionar materiais depois` (`Skip — add materials later`) link that submits the form with `checkout_action=pay_later` and the payload `[]`
- A `Continuar comprando` (`Keep shopping`) button to return to the catalog

### Critical payload fix

The payload must be serialized on the button's `click` (or on `mousedown`/`pointerdown`), not on `submit`, to guarantee the hidden input is filled in before the POST.

A safer alternative: use a single form with `action` and `checkout_action` set dynamically, and serialize on the click of the relevant submit button.

---

## Out of scope

- Changes to the backend / views / forms / models
- Changes to other wizard steps
- Creating new routes
- Implementing a floating modal (the transition happens inside the section, not in an overlay)

---

## Impacted files

| File | Type of change |
|---|---|
| `templates/login/register.html` | Replace the `step-products` HTML; update the CSS and JS `?v=` |
| `static/system/js/auth/register.js` | Replace `renderProductGrid`, `bindProductForms`; add `renderProductsCatalog`, `renderProductsConfigure`, `renderProductsCart`, `bindProductsSection` |
| `static/system/css/auth/register.css` | Add product classes that follow the design system; remove the old orphaned product classes |

---

## Risks and edge cases

- A product with only 1 variant in stock → skip the variant selection screen
- A product with no variant in stock → a disabled card, with no `Adicionar` (`Add`) button
- A variant sold out while the user is configuring → stepper max = 0; block `Adicionar ao carrinho` (`Add to cart`)
- The user returns to the catalog and tries to add a product already in the cart → increment the quantity or replace it (behavior: replace, for simplicity)
- An empty `productCatalog` (no product on record) → show an empty catalog message + a `Pular` (`Skip`) button
- An invalid JSON payload in the POST → the backend already handles `IntegrityError` and validation errors; the frontend must guarantee valid JSON

---

## Rules and constraints

- SDD before code
- TDD for the payload serialization logic
- no hardcoding
- no error masking
- no migrations
- mandatory full reading
- mandatory visual validation on desktop and mobile

---

## Plan

- [ ] 1. Full reading of the impacted files
- [ ] 2. Write tests for `buildProductsPayload` (correct cart serialization)
- [ ] 3. Update the `step-products` HTML with the new sub-view structure
- [ ] 4. Implement the CSS for the new design system classes
- [ ] 5. Implement the JavaScript: cart state, render functions, payload fix
- [ ] 6. Update the `?v=` versions in register.html
- [ ] 7. Visual validation: desktop and mobile, light and dark themes
- [ ] 8. Functional validation: Card, PIX, Skip — check the payload in the POST
- [ ] 9. Clean up orphaned CSS classes
- [ ] 10. Documentation update

---

## Visual validation

### Desktop

- Sub-step 1: an aligned grid of product cards, with no horizontal overflow
- Sub-step 2: aligned variant pills, a readable stepper, buttons with correct spacing
- Sub-step 3: a cart list with items, the total, and the payment buttons

### Mobile

- Cards stacked in a single column below 480px
- Variant pills wrapping appropriately
- A footer with buttons stacked in a column

### Browser console

- No JavaScript errors while navigating between sub-steps
- No form warnings

### Terminal

- No stack trace on the POST to `register-materials-checkout`

---

## ORM validation

### Database

- A `RegistrationOrder` created with the correct `selected_products_payload` after the card or PIX POST
- A `RegistrationOrder` created with the payload `[]` after `Pular` (`Skip`)

### Shell checks

```python
from system.models import RegistrationOrder
order = RegistrationOrder.objects.order_by('-created_at').first()
print(order.selected_products_payload)
```

### Flow integrity

- After a card payment: redirects to Asaas, then returns to `/register/` at the review step
- After PIX: shows the QR code or redirects
- After Skip: advances to `step-review`

---

## Expected evidence

- Screenshots of sub-steps 1, 2, and 3 on desktop and mobile
- A clean browser console
- A terminal with no stack traces
- A shell check confirming the correct payload in the `RegistrationOrder`

---

## Implemented

_Pending_

## Deviations from plan

_None_

## Pending

_None_
