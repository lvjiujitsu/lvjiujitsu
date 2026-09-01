# PRD-004: Fix the materials catalog by variant

## Summary of the implementation
Fix the materials flow so it operates on real product variants, with traditional Jiu Jitsu sizes and colors in the seeds, dropdown selection during registration and in the shop, add-to-cart by variant, and consistent stock decrement when the order is marked as paid.

## Demand type
Targeted fix with a structural flow adjustment

## Current problem
The system already has `ProductVariant`, but registration and the student shop still build the cart from a bare `Product`. This prevents correct color/size selection, limits cart composition, and makes correct per-variant stock decrement impossible.

## Goal
- use real variants in the materials flow
- adjust the seeds for belts and gis with traditional sizes and colors
- allow adding distinct combinations of the same product line to the cart
- decrement stock by variant when the order is actually paid

## Context Ledger
### Files read in full
- `CLAUDE.md`
- `system/models/product.py`
- `system/models/registration_order.py`
- `system/services/registration_checkout.py`
- `system/services/seeding.py`
- `system/services/product_management.py`
- `system/services/stripe_checkout.py`
- `system/services/stripe_webhooks.py`
- `system/services/asaas_checkout.py`
- `system/services/asaas_webhooks.py`
- `system/services/membership.py`
- `system/forms/product_forms.py`
- `system/views/product_views.py`
- `system/views/billing_admin_views.py`
- `system/tests/test_product_models.py`
- `system/tests/test_product_views.py`
- `system/tests/test_services.py`
- `templates/login/register.html`
- `templates/products/product_catalog.html`
- `templates/products/product_store.html`
- `templates/products/product_detail.html`
- `static/system/js/auth/registration-wizard-clean.js`
- `static/system/css/portal/class-catalog.css`
- `static/system/css/billing/billing.css`

### Adjacent files consulted
- `system/urls.py`
- `system/tests/test_views.py`

### Internet / official documentation
- IBJJF Uniform — https://ibjjf.com/uniform
- IBJJF Graduation System — https://ibjjf.com/graduation-system
- Pretorian size guide — market convention for `A1-A4` and `M1-M3`
- Black Belt Store / Red Dragon — real-world belt offering in `A1-A4` and lines with `M1-M3`

### MCPs / tools verified
- shell / PowerShell — ok — full reading and project tests
- internet / web search — ok — lookup of size and color references
- Playwright MCP — ok — visual validation at `/register/` and `/store/`

### Limitations found
- there is no dedicated variant field in `RegistrationOrderItem`, and local policy forbids migrations without explicit authorization

## Execution prompt
### Persona
Development agent specializing in monolithic Django with a server-rendered checkout, following SDD + TDD.

### Action
Fix the materials catalog so it works by real variant across seeds, cart, order, and stock decrement.

### Context
The project already models variants in `ProductVariant`, but the purchase and enrollment flow still ignores that contract and closes items by `Product` alone.

### Constraints
- no migrations
- no brittle hardcoding
- no error masking
- mandatory full reading
- mandatory validation
- keep views thin and business rules in services

### Acceptance criteria
- [x] The seeds must reflect traditional belt and gi sizes and colors (verifiable by: test)
- [x] Registration must allow choosing a variant and adding more than one combination of the same product to the cart (verifiable by: visual validation)
- [x] The student shop must allow the same per-variant composition (verifiable by: visual validation)
- [x] Order creation must record an item snapshot with the selected variant (verifiable by: test)
- [x] Payment confirmation / manual paid must decrement stock for the correct variant exactly once (verifiable by: test)

### Expected evidence
- passing tests
- clean browser console
- terminal with no stack traces
- cart working on desktop and mobile

### Output format
Implemented code + tests + validation evidence

## Scope
- update product and variant seeds
- update the materials catalog payload
- update the cart parser/validation to work by variant
- update order creation for enrollment and the shop
- implement per-variant stock decrement on payment transitions
- update the registration and student shop UI
- cover with tests

## Out of scope
- a migration to add an explicit variant FK to the order item
- refunds with automatic stock replenishment
- a full redesign of the public materials pages

## Impacted files
- `docs/prd/PRD-004-correction-of-catalogue-of-materials-by-variant.md`
- `system/services/seeding.py`
- `system/services/registration_checkout.py`
- `system/forms/product_forms.py`
- `system/forms/registration_forms.py`
- `system/services/membership.py`
- `system/services/stripe_webhooks.py`
- `system/services/asaas_webhooks.py`
- `system/views/product_views.py`
- `templates/login/register.html`
- `templates/products/product_store.html`
- `static/system/js/auth/registration-wizard-clean.js`
- `static/system/js/products/product-store.js`
- `static/system/css/portal/class-catalog.css`
- `static/system/css/billing/billing.css`
- `system/tests/test_product_models.py`
- `system/tests/test_product_views.py`
- `system/tests/test_services.py`

## Risks and edge cases
- an old registration draft with a legacy product payload
- an order paid twice through a webhook retry or a repeated manual action
- the lack of a dedicated variant schema on the order item
- residual concurrency risk if stock changes between order creation and payment confirmation

## Rules and constraints
- SDD before code
- TDD for the implementation
- no migrations
- no hardcoding
- no error masking
- mandatory full reading
- mandatory validation

## Plan
- [x] 1. Context and modeling of the per-variant flow
- [x] 2. Tests for seeds, order, and stock decrement
- [x] 3. Backend implementation
- [x] 4. Registration and shop UI implementation
- [x] 5. Full technical validation
- [x] 6. Desktop and mobile visual validation
- [x] 7. Final cleanup
- [x] 8. Documentation update

## Visual validation
### Desktop
- `/register/` materials step with per-variant selection and cart
- student shop with per-variant selection and cart

### Mobile
- the same flows in a mobile viewport

### Browser console
- no critical JavaScript errors

### Terminal
- no stack traces

## ORM validation
### Database
- no migration

### Shell checks
- not required if the tests cover the order and the stock decrement

### Flow integrity
- order items must carry a readable snapshot of the variant

## Quality validation
### No hardcoding
- size and color lists concentrated in the seeds

### No brittle conditional structures
- payload and variant resolution centralized in a service

### No `except: pass`
- do not introduce any

### No error masking
- an invalid cart must fail explicitly

### No unnecessary comments or docstrings
- do not introduce any

## Evidence
- `.\.venv\Scripts\python.exe manage.py test --verbosity 2` → 195 tests OK
- `.\.venv\Scripts\python.exe manage.py check` → no errors
- `.\.venv\Scripts\python.exe manage.py check --deploy` → only the expected local-environment warnings (`DEBUG`, cookies/SSL/HSTS)
- `.\.venv\Scripts\python.exe manage.py collectstatic --noinput` → OK
- `.\.venv\Scripts\python.exe manage.py showmigrations` → no new migrations
- Playwright mobile at `/register/` → categories `Faixas` (`Belts`), `Kimonos` (`Gis`), `Rash Guard`, `Patches`; payload `variant_id`; cart rendered
- Playwright desktop and mobile at `/store/` → dropdown by category, variant selection, quantity 2 of the same variant + an item of another variant in the same cart
- Browser console → 0 errors / 0 warnings
- Server terminal (`runserver-8000.out.log` / `runserver-8000.err.log`) → no stack traces

## Implemented
- Product seeds remodeled into traditional variants:
  - belts in graduation colors and sizes `A1-A4` / `M1-M3`
  - LV adult and kids gis in the colors `Branco` (`White`), `Azul` (`Blue`), `Preto` (`Black`)
  - 2 units per seeded variant
- The materials catalog for registration and the shop now operates on real variants, with a payload containing `variant_id`, `color`, `size`, `label`, and `snapshot_name`
- The registration and shop cart allows:
  - adding 2 units of the same color/size
  - combining different colors and sizes in the same order
  - keeping a readable snapshot of the selected item
- Order creation and payment confirmation decrement stock for the correct variant with idempotent protection

## Deviations from plan
- Since a migration was not authorized, the variant link on the order item remained a textual snapshot in `RegistrationOrderItem.product_name`, with variant resolution in the stock-decrement service

## Pending
- None within the defined scope
