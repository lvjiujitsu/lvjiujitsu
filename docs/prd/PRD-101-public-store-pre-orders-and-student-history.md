# PRD-101: Public shop, pre-orders, and the student's history

## Summary
Implement the 3 student/guardian screens that still have no template, confirmed by the programmatic inventory of active routes (PRD-078): `product-store` (the shop), `student-backorders` (the pre-orders), and `student-order-history` (the order history). The views, forms, and services already exist; only the UI is missing.

## Demand type
A new UI feature (the missing screens documented since PRD-077/078).

## Current problem
- `ProductStoreView`, `StudentBackorderListView`, and `StudentOrderHistoryView` are routed at `/store/`, `/my-materials/backorders/`, and `/my-materials/orders/`, but they raise `TemplateDoesNotExist` when accessed (confirmed through the `get_resolver()` + `get_template()` inventory).
- The student/guardian has no way to buy materials, view a pre-order, or see their purchase history in the UI.

## Goal
An active student/guardian:
- sees the catalog of active materials grouped by category, with the real stock per variant;
- buys in-stock variants (a simple cart, with no price calculation in the frontend);
- requests a pre-order for a sold-out variant;
- sees and cancels/confirms their own pre-orders;
- sees the history of paid/waived orders.

## Context Ledger
### Files read in full
- `system/views/product_views.py` (`ProductStoreView`, `CreateProductOrderView`, `ProductBackorderCreateView`, `StudentBackorderListView`, `StudentBackorderConfirmView`, `StudentBackorderCancelView`, `StudentOrderHistoryView`)
- `system/forms/product_forms.py` (`ProductCartForm`)
- `system/services/registration_checkout.py` (`parse_selected_products`, `resolve_selected_product_items`, `get_product_catalog_payload`)
- `system/services/product_management.py` (`get_public_product_cards`)
- `system/models/product_backorder.py`
- `system/models/registration_order.py`

### Adjacent files consulted
- `templates/products/product_list.html` and `product_form.html` (the visual pattern already established in PRDs 077/078)
- `static/system/css/lv/base.css`, `static/system/css/people/people.css`, `static/system/css/classes/classes.css`

### Internet / official documentation
- Django 5.2 templates: https://docs.djangoproject.com/en/5.2/topics/templates/

### Context7 / MCPs / tools verified
- Not applicable (it reuses the foundation already validated through Context7 in the earlier PRDs).

### Limitations found
- No price/total calculation in the frontend in this round (the backend computes the order); keeping the scope simple is a conscious decision, not a gap.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved
Authorized by the user's current request ("finish the whole implementation until you find no more errors"), which had already identified this pending item in PRDs 077/078.

## Scope
- `templates/products/product_store.html`, `student_backorder_list.html`, `student_order_history.html`.
- Minimal JavaScript (with no business rules) to assemble the `cart_payload` JSON from the quantity inputs.
- Rendering and flow tests (buy, pre-order, cancel, confirm).

## Out of scope
- A real payment gateway (the checkout flow already exists and is not changed).
- A broad visual redesign of the catalog (it reuses the already validated list pattern).

## Impacted files
- `templates/products/product_store.html` (new)
- `templates/products/student_backorder_list.html` (new)
- `templates/products/student_order_history.html` (new)
- `system/tests/`

## Risks and edge cases
- A variant with no stock cannot be bought, only requested as a pre-order.
- A guardian buying for a dependent needs the person selector.
- An invalid quantity (0, negative, non-numeric) must be ignored in the cart, not block the POST.

## Rules and constraints
- The UI in Brazilian Portuguese, with no `innerHTML` carrying user data and no business rules in JavaScript.
- Reuse the existing tokens/CSS (`lv/base.css`, `people.css`, `classes.css`).

## Plan
- [x] Read the views/forms/services involved.
- [x] Create the 3 templates.
- [x] Rendering and buy/pre-order/history flow tests.
- [x] Validate in the internal browser.

## Test plan
### Tests to author
- A GET of the 3 routes renders 200 for an authorized profile.
- A purchase POST with an in-stock variant creates the order and redirects to the checkout.
- A pre-order POST for a sold-out variant creates a `ProductBackorder`.
- Cancelling a pre-order removes the record.

### Execution authorization
Authorized locally per `AGENTS.md`.

### Execution evidence
- `system/tests/test_product_store.py` (5 tests): the shop renders with real data; buying an in-stock variant creates a `RegistrationOrder` and redirects to `/pagamentos/...`; requesting a pre-order for a sold-out variant creates a `ProductBackorder` and redirects to the pre-orders list; the pre-orders list renders and cancelling updates the status to `canceled` (it does not delete the record — the real behavior of the `cancel_backorder` service, corrected in the test after I had wrongly assumed it would be a delete); the history renders the empty state.
- Two tests failed on the first attempt due to my own wrong assumptions about the real behavior (the redirect target, and delete vs. a status change) — corrected after reading the `cancel_backorder` service and the `ProductBackorderCreateView` view.
- `.venv/Scripts/python.exe manage.py test system.tests.test_product_store --verbosity 2` — 5 tests OK.
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 338 tests OK (the full suite).
- The final programmatic inventory (`get_resolver()` + `get_template()` over every registered view): **0 missing templates** (it was 36 at the start of the session).
- End-to-end validation in the internal browser, logged in as an admin: the shop renders with `Faixa LV` (35 real variants) and the other products, each in-stock variant with a quantity input; buying 1 unit created a real `RegistrationOrder` (R$ 69.90, Aline, pending status) and redirected to `/pagamentos/1/asaas-pix/`; the pre-orders list renders the empty state correctly. Mobile (375×812) with no horizontal overflow in the shop or the pre-orders.

## Visual validation
Run in the internal browser: desktop (the shop with real data, the `Comprar para` (`Buy for`) selector with the 7 seeded people), mobile (the shop and the pre-orders with no overflow), the dark theme, and the empty state (the pre-orders and the history).

## ORM validation
`RegistrationOrder` and `ProductBackorder` verified through the focused test and through the local shell during the visual validation.

## Quality validation
- `manage.py test system.tests.test_product_store` — 5 tests OK.
- `manage.py test system` — 338 tests OK.
- `manage.py check` — 0 problems.

## Evidence
- `ProductBackorderCreateView` redirects to `student-backorders` (not to `product-store`, as I initially assumed while writing the PRD) — the correct behavior; I only adjusted the test's expectation.
- `cancel_backorder` is a state transition (`status="canceled"`), not a deletion — consistent with the "append-only with a trail" pattern already used in the rest of the system (e.g. `MembershipInvoice`, `Graduation`).

## Implemented
- `templates/products/product_store.html`: a catalog grouped by category, a quantity per in-stock variant, an `Esgotado` (`Sold out`) notice with a pre-order button, and a person selector for a guardian/admin buying on someone else's behalf.
- `templates/products/student_backorder_list.html`: a list of pre-orders with confirm (when `ready`) and cancel (when `pending`/`ready`) actions.
- `templates/products/student_order_history.html`: a history of paid orders with the items and the amount.
- `static/system/js/products/store_cart.js`: a minimal script that only reads the quantity inputs and assembles the cart's JSON on submit — with no business rule or price calculation in the frontend.
- `system/tests/test_product_store.py`: 5 tests covering the 4 flows (the shop, a purchase, a pre-order, a cancellation, and the history).

## Cleanup findings
- No code residue. The demonstration order (`RegistrationOrder` #1, Aline, R$ 69.90) created during the visual validation was removed from the development database at the end.

## Follow-up PRDs
- None new identified in this PRD.

## Deviations from plan
- No functional deviation; the two test adjustments (the redirect and status vs. delete) were corrections of my own initial assumption, not of the code.

## Pending
- None.

## Final status
Completed — the 3 screens render, the purchase flow creates a real order and redirects to the existing checkout, and the pre-order/cancellation work, tested (5 new tests + the full suite of 338) and validated live in the browser (desktop, mobile, real data). The inventory of missing templates reaches zero.
