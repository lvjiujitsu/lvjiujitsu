# PRD-009: Shop in the authenticated portal with pre-orders, arrival queue, and student history

## Summary of the implementation

Bring the authenticated shop (`/store/`) to an accessible place in the portal for any authenticated profile (student/instructor/admin) through a discreet link in the side menu, and add three new capabilities:

1. **Pre-order** when the student clicks a variant that is out of stock — records interest with no immediate charge.
2. **First-come, first-served queue** when the product is restocked — the system automatically allocates the reservations.
3. **Badge notification in the portal** when a product is available for confirmation, and a student screen to **confirm** (generating an order + a one-off PIX/Card checkout) or **give up**.
4. The student's own **history**.
5. An **administrative screen** to manage the queue by variant and mark restocks.

One-off payment follows the same principle as the tuition: one-off PIX through Asaas, one-off Card (1x) through Stripe.

## Demand type

New feature with a new schema, business logic (queue allocation, expiration), new UI (3 screens + badge + 1 button in the shop), and integration with the existing checkout.

## Current problem

1. A student opens `/store/`, finds a gi sold out in their size, and has no path forward — they can only try to reach out over WhatsApp.
2. There is no trail of what the student bought (`RegistrationOrder` exists, but the student has no read screen of their own).
3. Admins have no visibility into unmet demand (how many students want which product/variant).
4. The `/store/` shop is reachable, but ordinary students do not even have the link in the menu.

## Goal

- The shop reachable from the menu for any authenticated profile.
- Cover the "product out of stock" case with a transparent waiting list.
- Give the student autonomy to confirm/cancel and follow their history.
- Give the admin an actionable queue (who is waiting for what, and for how long).

## Context Ledger

### Files read in full

- [system/models/product.py](system/models/product.py) — `Product`, `ProductVariant`, `ProductCategory`
- [system/models/registration_order.py](system/models/registration_order.py) — the `RegistrationOrder`/`RegistrationOrderItem` flow
- [system/views/product_views.py](system/views/product_views.py) — `ProductStoreView`, `CreateProductOrderView`
- [system/services/registration_checkout.py](system/services/registration_checkout.py) — `create_product_only_order`, `apply_order_variant_stock`
- [templates/products/product_store.html](templates/products/product_store.html)
- [templates/base.html](templates/base.html) — drawer/side menu
- [system/views/payment_views.py](system/views/payment_views.py) — `PaymentMethodChoiceView`, `CreateCheckoutSessionView`, `CreatePixChargeView`
- [system/services/financial_transactions.py](system/services/financial_transactions.py) — `apply_order_financials`, `resolve_payment_provider_for_plan`

### Adjacent files consulted

- [system/admin.py](system/admin.py) — current Product/ProductVariant admin
- [system/services/membership.py](system/services/membership.py) — subscription flow reference (proration)
- [system/forms/product_forms.py](system/forms/product_forms.py)

### Internet / official documentation

- N/A for this delivery (no new libraries).

### MCPs / tools verified

- `Glob`, `Read`, `Grep`, `Edit`, `Write`, `Bash` — working.

### Limitations found

- Installment card charges (Stripe) would require an account with a custom contract to offer installments at a different X%. For that reason this delivery treats one-off card payments as **1x, paid in full** — aligned with the standard public fee (3.99% + R$ 0.39).
- Email notification is **out of scope** (decision item 4 of the review). Only a badge in the portal.
- Decision item 6 still requires user confirmation about card installments (proposed default: 1x).

## Execution prompt

### Persona

Senior Django agent in control-first mode with SDD + TDD.

### Action

Create the pre-order domain (`ProductBackorder`), update the existing shop (`/store/`) with an `Avise-me quando chegar` (`Notify me when it arrives`) button for sold-out variants, create the management screens (student and admin), a notification badge in the menu, the student history, and a management command to expire reservations.

### Context

The shop already exists at `/store/` (`ProductStoreView`) and generates a `RegistrationOrder` through `create_product_only_order`. The checkout (PIX/Card) is already in place. What is missing is the pre-order + queue + screens building block.

### Constraints

- no hardcoding
- no error masking
- hand-writing a migration file is forbidden (it goes through the destructive cycle `clear_migrations.py` → `makemigrations`)
- mandatory full reading (completed above)
- mandatory tests (model, service, view, command)
- stock consumed only at payment time, **not** at pre-order creation
- reservations expire **7 days** after notification, releasing stock to the next in the queue
- a student may have only 1 active backorder per (`person`, `variant`)
- one-off payment: PIX in full, Card **1x in full** (default — to confirm with the user)
- notification through the badge only (no email)

### Acceptance criteria

- [ ] The `ProductBackorder` model created with the status choices `PENDING`, `READY`, `CONFIRMED`, `CANCELED`, `EXPIRED` (verifiable: reading the model + test)
- [ ] The `/store/` screen shows an `Avise-me quando chegar` (`Notify me when it arrives`) button for variants with `stock_quantity == 0` and `is_active=True` (verifiable: view test + visual)
- [ ] A POST to `/store/backorders/create/` creates a backorder with status `PENDING` (verifiable: test)
- [ ] Creating a duplicate backorder for the same (person, variant) with an active status is not allowed (verifiable: test)
- [ ] When `restock_variant(variant, quantity)` is called, it marks `quantity` PENDING backorders as READY in chronological order (verifiable: test)
- [ ] A READY reservation has `expires_at = notified_at + 7 days` (verifiable: test)
- [ ] An authenticated student sees a badge in the drawer with the count of READY pre-orders (verifiable: template test)
- [ ] The `/store/pedidos/` screen lists the student's pre-orders with Confirm/Cancel buttons on the READY ones (verifiable: view test)
- [ ] Confirming a READY pre-order generates a `RegistrationOrder` + redirects to `payment-checkout` (verifiable: test)
- [ ] A confirmed payment marks the backorder as `CONFIRMED` and decrements `stock_quantity` (through `apply_order_variant_stock`) (verifiable: integration test)
- [ ] Cancelling a READY pre-order releases stock and tries to promote the next in the queue (verifiable: test)
- [ ] The `/store/historico/` screen lists all of the student's paid `RegistrationOrder` records (verifiable: test)
- [ ] The `/billing/backorders/` screen (admin/instructor) lists the queue by variant with age (verifiable: test)
- [ ] The `manage.py expire_backorders` command marks READY records with `expires_at < now` as EXPIRED, promoting the queue (verifiable: command test)
- [ ] The drawer shows a `Loja` (`Shop`) link for any authenticated profile (verifiable: template test)
- [ ] The drawer shows a `Meus pedidos` (`My orders`) link for students (verifiable: template test)
- [ ] The drawer shows a `Pré-pedidos` (`Pre-orders`) link for back-office/admin (verifiable: template test)
- [ ] `manage.py test --verbosity 2` passes with 0 failures
- [ ] `manage.py check` passes with no new warnings

### Expected evidence

- passing tests
- a manual browser sequence: create a pre-order as student A; the admin restocks; student A sees the badge; student A confirms; the checkout opens; the payment is simulated; the order appears in the history.
- shell check: `ProductBackorder.objects.filter(status="ready", expires_at__lt=now())` must be empty after `expire_backorders`.

### Output format

Code + tests + report.

## Scope

### Models
1. `ProductBackorderStatus` (TextChoices): `PENDING`, `READY`, `CONFIRMED`, `CANCELED`, `EXPIRED`.
2. `ProductBackorder(TimeStampedModel)`:
   - `person` (FK Person, `related_name="product_backorders"`)
   - `variant` (FK ProductVariant, `related_name="backorders"`)
   - `status` (default PENDING)
   - `notified_at` (null)
   - `confirmed_at` (null)
   - `canceled_at` (null)
   - `expires_at` (null)
   - `confirmed_order` (FK RegistrationOrder, null, on_delete=SET_NULL)
   - `notes` (TextField blank)
   - **constraint**: `UniqueConstraint(person, variant)` filtered on active statuses (PENDING or READY) — implemented through `condition=Q(status__in=...)`.
   - **ordering**: `("created_at",)`

### Selectors / Services
3. `system/selectors/product_backorders.py`:
   - `get_active_backorder(person, variant)`
   - `get_ready_backorders_for_person(person)`
   - `get_backorder_queue_for_variant(variant)` (PENDING + READY ordered by created_at)
   - `count_ready_for_person(person)` — for the badge
4. `system/services/product_backorders.py`:
   - `create_backorder(person, variant)` — validates duplicates
   - `restock_variant(variant, quantity_added)` — promotes the queue
   - `confirm_backorder(backorder)` — generates a RegistrationOrder with 1 item, returns the order
   - `cancel_backorder(backorder)` — marks CANCELED, triggers `restock_variant(variant, 1)` if it was READY
   - `expire_pending_reservations()` — for the cron job

### Views (HTTP)
5. `ProductBackorderCreateView` — POST `/store/backorders/create/` (authenticated, student/admin/instructor profile)
6. `StudentBackorderListView` — GET `/store/pedidos/`
7. `StudentBackorderConfirmView` — POST `/store/pedidos/<int:pk>/confirmar/`
8. `StudentBackorderCancelView` — POST `/store/pedidos/<int:pk>/cancelar/`
9. `StudentOrderHistoryView` — GET `/store/historico/`
10. `AdminBackorderQueueView` — GET `/billing/backorders/` (back-office + admin)

### Templates
11. `templates/products/product_store.html` — an inline `Avise-me quando chegar` (`Notify me when it arrives`) button on the sold-out variant.
12. `templates/products/student_backorder_list.html` — the student's list with READY at the top.
13. `templates/products/student_order_history.html` — the student's history.
14. `templates/billing/admin_backorder_queue.html` — the administrative queue.
15. `templates/base.html` — add the `Loja` (`Shop`), `Meus pedidos` (`My orders`), and `Pré-pedidos` (`Pre-orders`) links to the drawer + the badge.

### Context processor
16. `system/context_processors.py` (new) or middleware: expose `pending_backorder_count` to the template from `request.portal_person`. Register it in `settings.TEMPLATES`.

### Management command
17. `system/management/commands/expire_backorders.py` — calls `expire_pending_reservations()`.

### Signals / hook
18. In `system/signals.py` (or a new module): a `post_save` on `ProductVariant` that detects an increase in `stock_quantity` and calls `restock_variant`. Atomic implementation using `pre_save` + `post_save` to detect the delta. Avoid a loop with a flag on `_meta`.

### Tests
19. `system/tests/test_product_backorders.py` (new): model, services, command.
20. `system/tests/test_product_views.py` (update): the new views (create, list, confirm, cancel, history, admin queue).
21. `system/tests/test_signals.py` (update or create): the restock signal.

### Cache-busting + styling
22. Bump `?v=` on `product-store.js` (because the new button + the UX on sold-out cards may require extra JavaScript).
23. Add CSS for the drawer badge (`.drawer-badge`), the `Avise-me` (`Notify me`) button, and the pre-order cards.

## Out of scope

- Email notification.
- A limit on how many backorders a student may hold at once (no limit — only the rule against duplicating the same variant).
- Refunds after confirmation (it becomes a regular RegistrationOrder).
- Unmet-demand statistics (an admin report).
- Card installments > 1x — pending a final decision.

## Impacted files

- `system/models/product.py` (change) or a new `system/models/product_backorder.py`
- `system/models/__init__.py`
- `system/migrations/0001_initial.py` (regenerated through the destructive cycle)
- `system/admin.py` (register `ProductBackorder`)
- `system/selectors/__init__.py`
- `system/selectors/product_backorders.py` (new)
- `system/services/product_backorders.py` (new)
- `system/views/product_views.py`
- `system/views/billing_admin_views.py`
- `system/views/__init__.py`
- `system/urls.py`
- `system/signals.py`
- `system/context_processors.py` (new)
- `lvjiujitsu/settings.py` (register the context processor)
- `system/management/commands/expire_backorders.py` (new)
- Templates: `product_store.html`, `student_backorder_list.html` (new), `student_order_history.html` (new), `admin_backorder_queue.html` (new), `base.html`
- CSS: `static/system/css/portal/portal.css` (badge), and/or a new `static/system/css/portal/store.css`
- JS: `static/system/js/products/product-store.js` (update)
- Tests: `test_product_backorders.py` (new), `test_product_views.py`, `test_signals.py` or similar

## Risks and edge cases

- **Race condition on allocation**: two admins restocking at the same time. Mitigation: `select_for_update` in `restock_variant` wrapped in `transaction.atomic`.
- **The student confirms and the payment fails**: the `RegistrationOrder` stays pending; the backorder stays READY until payment or expiration. After expiration, the queue is released. No stock was touched.
- **The student cancels a READY reservation**: it must revert to the next in the queue → `restock_variant(variant, 1)`.
- **A deactivated variant**: pending/ready backorders for that variant must be marked CANCELED automatically. Implement in the `pre_save` signal when `is_active` changes to False.
- **An inactive person**: the backorder becomes orphaned. Acceptable (the admin can clean it up).
- **The student history respects the financial owner**: use `get_membership_owner` for the guardian-student case.
- **The drawer `Loja` (`Shop`) link**: must also appear for back-office/admin (they can buy too) — treat it as an ordinary link, not conditioned on type.

## Rules and constraints

- SDD before code (this PRD)
- TDD for the implementation
- no hardcoding
- no error masking
- hand-writing a migration file is forbidden (destructive cycle)
- mandatory full reading (completed)
- mandatory validation

## Plan

- [x] 1. Context and full reading
- [ ] 2. Confirm with the user: card installments (1x proposed as the default)
- [ ] 3. The `ProductBackorder` model + statuses + constraints + export
- [ ] 4. The `product_backorders` selector
- [ ] 5. The `product_backorders` service (create, restock, confirm, cancel, expire)
- [ ] 6. Signal: `post_save` on `ProductVariant` detecting a stock increase
- [ ] 7. Signal: deactivating a variant cancels active backorders
- [ ] 8. The `pending_backorder_count` context processor
- [ ] 9. Views (Create, List, Confirm, Cancel, History, Admin Queue)
- [ ] 10. New URLs
- [ ] 11. New templates + drawer + the `Avise-me` (`Notify me`) button in product_store
- [ ] 12. CSS for the badge + button
- [ ] 13. The `expire_backorders` management command
- [ ] 14. Tests (model + service + view + command + signal)
- [ ] 15. Update `test_product_views.py`
- [ ] 16. Bump the CSS/JS cache
- [ ] 17. Request authorization and run the destructive cycle (`clear_migrations.py` → `makemigrations` → `test` → `migrate` → seeds)
- [ ] 18. Final `manage.py check` + `collectstatic`
- [ ] 19. In-browser visual validation
- [ ] 20. Final cleanup
- [ ] 21. Documentation update

## Visual validation

### Desktop
- The drawer with the new links (`Loja` — `Shop`, `Meus pedidos` — `My orders` for the student; `Pré-pedidos` — `Pre-orders` for the admin)
- The `/store/` shop with an `Avise-me quando chegar` (`Notify me when it arrives`) button on sold-out variants
- `/store/pedidos/` with READY at the top + Confirm/Cancel buttons
- `/store/historico/` listing paid RegistrationOrders
- `/billing/backorders/` for the admin with the queue by variant
- The drawer badge with a visible count

### Mobile
- A responsive drawer, with the badge visible at ≤480px

### Console
- No asset 404s (cache-busting bumped)
- No JavaScript errors

## ORM validation

### Database
- The `system_productbackorder` table created after `migrate`.
- `system_productvariant.stock_quantity` unchanged.

### Shell checks
```python
from system.models import ProductBackorder, ProductBackorderStatus
ProductBackorder.objects.filter(status=ProductBackorderStatus.PENDING).count()
ProductBackorder.objects.filter(status=ProductBackorderStatus.READY, expires_at__lt=timezone.now()).count()  # 0 after expire_backorders
```

### Flow integrity
- 1 backorder per (person, variant) with an active status.
- READY always has `expires_at` filled in.
- CONFIRMED always has `confirmed_order` filled in.

## Quality validation

### No hardcoding
- `BACKORDER_RESERVATION_DAYS = 7` in `settings.py` (not in the code).

### No brittle conditional structures
- The service uses guard clauses + `transaction.atomic`.

### No `except: pass`
- Nothing introduced.

### No error masking
- Nothing.

### No unnecessary comments or docstrings
- Nothing.

## Evidence

(to be filled in after implementation)

## Implemented

(to be filled in after implementation)

## Deviations from plan

(to be filled in after implementation)

## Pending

- Confirmation of card installments for one-off purchases (default 1x).
- Future PRD: email notification and an unmet-demand report.
