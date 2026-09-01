# PRD-106: The guardian cannot buy/see materials on a dependent's behalf

## Summary
PRD-101 explicitly documented it ("a guardian buying for a dependent needs the person selector") and the validation evidence cited the `Comprar para` (`Buy for`) selector with 7 people — but that test was done as a technical admin. For an ordinary guardian (not staff), `get_material_request_recipient_queryset()` returns only their own person, never the dependents. On top of that, even if the guardian could buy on the dependent's behalf, the pre-order and the purchase history become invisible to them afterwards, because the lists filter strictly by `request.portal_person`.

## Demand type
A functional bug fix (a partially implemented feature that contradicts the scope already documented in PRD-101).

## Current problem
- `system/selectors/person_selectors.py:96-112` (`get_material_request_recipient_queryset`): it only widens the recipient list for `CLASS_STAFF_PERSON_TYPE_CODES` (instructor/back office); for any other actor (including a guardian with dependents) it returns `queryset.filter(pk=actor.pk)` — only themselves.
- `system/views/product_views.py:264-265` (`StudentBackorderListView.get_queryset`) and `system/views/product_views.py:309-322` (`StudentOrderHistoryView.get_queryset`): both filter only by the logged-in person (or their billing owner, which does not help in the guardian→dependent direction), so even if a pre-order/order is created with `person=dependent`, the guardian never sees it on their own screens.
- The result: a guardian cannot buy a gi/belt for their dependent child through the shop, and even with a manual adjustment (e.g. through the admin) the order would not appear in the guardian's history.

## Goal
A guardian with dependents can select each dependent in `Comprar para` (`Buy for`) in the shop, create orders/pre-orders for them, and see those orders/pre-orders on their own history and pre-order screens.

## Context Ledger
### Files read in full
- `system/selectors/person_selectors.py` (`get_material_request_recipient_queryset`, `resolve_material_request_recipient`)
- `system/views/product_views.py` (`ProductStoreView._build_purchase_person_choices`, `CreateProductOrderView`, `ProductBackorderCreateView`, `StudentBackorderListView`, `StudentOrderHistoryView`)
- `system/selectors/product_backorders.py` (`get_backorders_for_person`)
- `templates/products/product_store.html` (the `Comprar para` — `Buy for` selector inside the cart's own `<form>` — it was confirmed that `purchase_person_id` is sent correctly along with any of the form's buttons, including the pre-order one; there is no CSRF/missing-field bug here)
- `docs/prd/PRD-101-public-store-pre-orders-and-student-history.md` (line 70: the original scope already foresaw this case)
- `system/services/membership.py` (`get_membership_owner`, `has_dependents`)

### Adjacent files consulted
- `system/constants.py` (`CLASS_STAFF_PERSON_TYPE_CODES`, `MATERIAL_REQUEST_PERSON_TYPE_CODES`)
- `system/tests/test_product_store.py` (the existing coverage: no test covers a guardian with a dependent)

### Limitations found
- None. Two of the exploration agent's hypotheses (a CSRF issue on the pre-order button and a missing `purchase_person_id`) were discarded after reading: the pre-order button is inside the cart's own `<form>`, so the CSRF token and the selector's `purchase_person_id` field are sent normally with any submit of that form.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved
Authorized by the current request ("finish the whole implementation until you find no more errors"). The finding was confirmed by reading the code directly and comparing it with the scope already recorded in PRD-101.

## Scope
- `get_material_request_recipient_queryset()`: include the dependents (through a `RESPONSIBLE_FOR` `PersonRelationship`) in the recipient list when the actor is a guardian, not only when they are staff.
- `StudentBackorderListView`/`StudentOrderHistoryView`: widen the filter to include every person the actor can buy on behalf of (themselves + their dependents), not just the logged-in person.

## Out of scope
- Changing the billing owner logic (`get_membership_owner`) used in finance.
- Any change to the staff (instructor/back office) flow, which already works.

## Impacted files
- `system/selectors/person_selectors.py`
- `system/views/product_views.py`
- `system/tests/test_product_store.py`

## Risks and edge cases
- A guardian with no dependents: unchanged behavior (only themselves).
- A dependent who is also the guardian of another dependent (a chain): out of scope, handling only one level as the rest of the system already does (`has_dependents`/`_build_dependents` also look at only one level).

## Rules and constraints
- Reuse `has_dependents`/`PersonRelationship` already used in PRD-105, without duplicating logic.

## Plan
- [x] Adjust `get_material_request_recipient_queryset`.
- [x] Adjust `StudentBackorderListView`/`StudentOrderHistoryView`.
- [x] Focused tests.
- [x] Visual validation.

## Test plan
### Tests to author
- A guardian with a dependent sees the dependent in the `Comprar para` (`Buy for`) selector.
- A pre-order created for the dependent appears in the guardian's pre-order list.
- A paid order created for the dependent appears in the guardian's history.

### Execution authorization
Authorized locally.

### Execution evidence
- `system/tests/test_product_store.py` (`GuardianBuysForDependentTestCase`, 3 new tests): the guardian sees the dependent in the `Comprar para` (`Buy for`) selector; a pre-order created for the dependent appears in the guardian's pre-order list; the dependent's paid order appears in the guardian's history.
- `.venv/Scripts/python.exe manage.py test system.tests.test_product_store --verbosity 2` — 8 tests OK (5 existing + 3 new).
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 351 tests OK (the full suite).
- `.venv/Scripts/python.exe manage.py check` — 0 problems.
- Live validation in the browser (a demo guardian + Aline as the dependent, created through the ORM and removed after the test; the server restarted because it runs with `--noreload`): the `Comprar para` (`Buy for`) selector at `/store/` shows `Responsavel Demo PRD106` and `Aline Blanch Freiria` correctly.

## Visual validation
The shop and the pre-order/history screens with a guardian logged in and a real dependent.

## ORM validation
A `ProductBackorder`/`RegistrationOrder` with `person` = the dependent.

## Quality validation
- `manage.py test system.tests.test_product_store` and the full suite.
- `manage.py check`.

## Evidence
- `StudentOrderHistoryView` used `get_membership_owner()` (the concept of the tuition's financial owner) to decide whose orders to show — an improper use of that helper, since `RegistrationOrder.person` is always the order's real person (`create_product_only_order`), not the tuition payer. Replaced with `person__in=recipients`, consistent with the pre-order.
- Two of the exploration agent's hypotheses (a CSRF bug and a missing `purchase_person_id` on the pre-order button) were discarded: both false, since the button is inside the cart's own `<form>` and sends every field normally.

## Implemented
- `system/selectors/person_selectors.py`: `get_material_request_recipient_queryset()` now includes the dependents (through a `RESPONSIBLE_FOR` `PersonRelationship`) for any guardian, not only for staff.
- `system/selectors/product_backorders.py`: `get_backorders_for_person()` now accepts a set of people (`person__in`) instead of a single person.
- `system/views/product_views.py`: `StudentBackorderListView` and `StudentOrderHistoryView` now filter by every person the actor can buy on behalf of (through `get_material_request_recipient_queryset`); the orphaned `get_membership_owner` import removed.
- `system/tests/test_product_store.py`: a new `GuardianBuysForDependentTestCase` class (3 tests).

## Cleanup findings
- No residue; the demo data (the guardian + the relationship) removed from the local database after the visual validation.

## Follow-up PRDs
- None.

## Deviations from plan
_None so far._

## Pending
_None so far._

## Final status
Completed.
