# PRD-130: Migrating the plan change (upgrade/downgrade) to the PlanTier/PlanPrice catalog

## Summary
This fixes one more regression from the same family as PRDs 128/129: the `Trocar plano` ("Change plan") button disappeared from the client's home because `build_plan_catalog`/`get_eligible_plans` (`system/services/plan_change.py`/`system/selectors/plan_eligibility.py`) only read from `SubscriptionPlan`, and that model's non-Veteran rows were deactivated by PRD-127. Any client with a `Membership.plan_price` (the new model) or even a legacy non-Veteran `Membership.plan` sees an empty change catalog.

## Demand type
A regression fix (reported by the user: "the plan change isn't accessible, it disappeared from the client's screen").

## Current problem
- `get_eligible_plans` (`plan_eligibility.py`) queries only `SubscriptionPlan.objects.filter(is_active=True)`; after PRD-127, that returns only the Veteran variants.
- `build_plan_catalog` excludes `gateway_code="stripe_card"` and the current plan, but starts from an already-empty catalog for non-Veterans — the result: a `[]` catalog, and the `{% if plan_change_catalog %}` template never renders the button.
- `calculate_plan_change`, `create_plan_change_order`, `apply_plan_change`, `get_last_paid_order_for_plan`, `refund_plan_change_leftover`, and `serialize_plan_with_proration` assume `SubscriptionPlan` everywhere (`membership.plan`, `RegistrationOrder.plan`).
- `PlanChangeSelectView` does `int(request.POST.get("selected_plan"))` and looks only in `SubscriptionPlan`.
- `_handle_payment_event` (`asaas_webhooks.py` and `stripe_webhooks.py`) only calls `apply_plan_change` when `order.plan_id` exists — a change order for a `PlanPrice` (`order.plan_price_ref`) would be silently ignored.

## Goal
Migrate the whole plan change chain to the dual-source catalog (the legacy `SubscriptionPlan` `sp:<pk>` + the new `PlanPrice` `pp:<pk>`), replicating the pattern already used successfully in PRDs 127/128/129, preserving 100% of the already-tested proration/credit/refund logic.

## Context Ledger
### Files read in full
- `system/services/plan_change.py` (all the relevant functions)
- `system/views/plan_change_views.py`
- `system/selectors/plan_eligibility.py` (`get_eligible_plans`, `_build_audience_filter`, `PlanEligibilityContext`)
- `system/services/asaas_webhooks.py` / `system/services/stripe_webhooks.py` (the `is_plan_change` branch)
- `static/system/js/home/dashboard.js` (`js-plan-change-*` — it already uses `FormData`/a string value, with no `parseInt`, so it needs no change)

### Limitations found
- The frontend (`dashboard.js`/`dashboard.html`) is already agnostic to the ID's format (it uses `input[name="selected_plan"]:checked".value` as a string) — only the backend needs to change.

## Required skills
`lv-task-intake`, `lv-prd`, `lv-django-delivery`, `lv-cleanup-audit`

## Understanding approved
The user reported the bug directly and asked for a fix ("fix it").

## Scope
- `system/selectors/plan_eligibility.py`: a new `get_eligible_plan_prices(context)` function (the `PlanPrice` equivalent of `get_eligible_plans`, through `tier__audience`).
- `system/services/plan_change.py`: generalize `calculate_plan_change`, `create_plan_change_order`, `apply_plan_change`, `get_last_paid_order_for_plan`, `refund_plan_change_leftover`, `serialize_plan_with_proration`, and `build_plan_catalog` to accept a `SubscriptionPlan` OR a `PlanPrice`; `apply_plan_change` now calls `recompute_family_discounts_for_person` after the change (the person can change tier).
- `system/views/plan_change_views.py`: `PlanChangeSelectView` resolves `selected_plan` through `resolve_catalog_plan`.
- `system/services/asaas_webhooks.py` / `system/services/stripe_webhooks.py`: the `is_plan_change` branch recognizes `order.plan_price_ref_id` in addition to `order.plan_id`.
- The tests: `system/tests/test_plan_change.py`/`test_plan_change_views.py` extended with `PlanPrice` scenarios (a populated catalog, an upgrade, a downgrade, a credit, a refund).

## Out of scope
- Migrating the legacy `is_family_plan` field (it stays unreachable, already documented in PRD-129).

## Rules and constraints
- No schema migration.
- No real gateway call in an automated test.
- Preserve the whole existing suite with no regression.

## Test plan
- The change catalog populated for a client with a `Membership.plan_price`.
- A downgrade/upgrade between `PlanPrice` records with correct proration, a credit, and an additional charge.
- `PlanChangeSelectView` accepts `pp:<pk>`, rejects an invalid id, and rejects "the same current plan".
- The webhook (Asaas/Stripe) applies the change when the order references a `plan_price_ref`.
- The full suite with no regression; `manage.py check`.

## Implemented
- `system/selectors/plan_eligibility.py`: the new `get_eligible_plan_prices(context)`.
- `system/services/plan_change.py`: `_catalog_id_for_plan`, `_current_plan_reference`, `_assign_membership_plan` (new helpers); `calculate_plan_change`, `create_plan_change_order`, `apply_plan_change` (+ the call to `recompute_family_discounts_for_person`), `get_last_paid_order_for_plan`, `refund_plan_change_leftover`, `serialize_plan_with_proration`, and `build_plan_catalog` generalized for a `SubscriptionPlan` OR a `PlanPrice`.
- `system/views/plan_change_views.py::PlanChangeSelectView`: it resolves `selected_plan` through `resolve_catalog_plan` (the duplicated "same plan" check removed, already covered by `calculate_plan_change`).
- `system/services/asaas_webhooks.py` / `system/services/stripe_webhooks.py`: the `is_plan_change` branch recognizes `order.plan_price_ref_id` in addition to `order.plan_id`.
- The tests: `system/tests/test_plan_change_plan_price.py` (6 new); `system/tests/test_plan_change_views.py` updated for the prefixed catalog IDs (`sp:<pk>`).
- **An additional fix reported by the user after the first validation**: when selecting the exact filter of the current plan (e.g. Monthly + PIX, the same as the plan in force), the catalog showed nothing — the client expected to see their own plan marked as `Plano atual` ("Current plan"). Fixed: `build_plan_catalog` now includes the current plan in the catalog (through `serialize_plan_with_proration(current_plan, None, is_current=True)`, with a neutral proration dict), and `templates/home/dashboard.html` renders that card with a `Plano atual` ("Current plan") badge, a disabled radio (you cannot "change to yourself"), and the message "Você já está neste plano" ("You are already on this plan") instead of the proration text. A new test: `test_current_plan_card_matches_its_own_filters`.

## Evidence
- `manage.py test system.tests.test_plan_change system.tests.test_plan_change_views` → 23 tests, `OK` (the non-regression, after adjusting 3 tests for the prefixed id format).
- `manage.py test system.tests.test_plan_change_plan_price` → 7 tests (6 + 1 from the current-plan fix), `OK`.
- `manage.py test` (the full suite) → 551 tests, `OK`. `manage.py check` clean.
- Visual validation in the internal browser: the `Trocar plano` ("Change plan") modal with the Monthly+PIX filter (the same as the plan in force) now shows the card "Adulto 2x por semana — Plano atual — R$ 221,99 /mensal — Você já está neste plano" ("Adult 2x per week — Current plan — R$ 221.99 /monthly — You are already on this plan") instead of staying empty.
- `manage.py test` (the full suite) → 550 tests, `OK`. `manage.py check` clean.
- Visual validation in the internal browser with a real client (`ana.teste.api@example.com`, `Membership.plan_price_id=1`): the `Trocar plano` ("Change plan") button reappeared on the home; the modal showed 15 real options from the `PlanPrice` catalog (before: an empty catalog, the button absent); selecting a more expensive plan correctly created a `RegistrationOrder` (`is_plan_change=True`, `plan_price_ref_id=5`, `plan_id=None`, with the correct prorated total) and returned the checkout URL (`/pagamentos/4/asaas-pix/`) — blocked only by the same known limitation of the internal preview (it does not navigate to Asaas's external domain), not a new regression.

## Cleanup findings
No residue beyond what is already documented in PRDs 128/129 (the legacy `is_family_plan` branch remains unreachable, out of scope).

## Final status
Completed and validated — the automated tests (550, the full suite) + the internal browser with a real client. The reported bug ("Change plan disappeared from the screen") is fixed.
