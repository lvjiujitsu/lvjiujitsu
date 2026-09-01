# PRD-020: Plan change with balance→time, future credit, and automatic refund

## Summary of the implementation
Rewrite the plan change engine (`system/services/plan_change.py`) and the plan change UI toward a model where **the money already paid is preserved as much as possible** inside the subscription:

- The system computes the **financial balance** (amount paid − consumption proportional to the days used).
- If the balance covers one or more full cycles of the new plan, the new plan's term is extended with no new charge; any leftover (not enough to close a full cycle) becomes a `MembershipCredit` applied as a discount on the next renewal.
- If the balance does not cover the new plan (an upgrade), it charges the difference (`new_plan.price − available_credit`) and grants a full term.
- When there is a leftover, the customer may choose to **get the leftover back** automatically (a refund triggered directly in Stripe or Asaas, with no administrative approval).

The plan change UI now shows: the current plan, the amount paid, days used/remaining, the available balance, the new term (a computed date), the additional amount (for an upgrade), and — where applicable — the leftover with a `manter como crédito` (`keep as credit`) / `receber de volta` (`get it back`) toggle.

## Demand type
Architectural refactoring + external integration (Stripe Refund API + Asaas Refund API).

## Current problem
The current change engine (`calculate_plan_change`) computes day-by-day proration for the **same remaining period** of the current plan's cycle and charges when there is a difference to pay; when there is not, it returns "Free". That does not preserve the money already paid. Problematic scenarios:

- A customer on the annual plan (R$ 3,204) with 4 months used (R$ 1,068 consumed, R$ 2,136 of balance). When switching to the R$ 267 monthly plan, the current system shows "Free" for the 8 remaining months, but does not give the customer the right to keep using that balance if the annual plan is cancelled.
- The customer lost the "implicit value" of what they paid, contradicting the expectation that the money debited is respected.

## Goal
1. Compute the current plan's balance (`amount_paid − amount_consumed`) and convert it into term time on the new plan (whole cycles).
2. The leftover (the balance remaining after rounding the number of cycles down) → a `MembershipCredit` consumable on the next renewal.
3. An upgrade (balance < the new plan's full price) → charge the difference, full term.
4. An optional button: `Receber sobra de volta` (`Get the leftover back`) → triggers an automatic refund in the correct provider (Stripe or Asaas), with no administrative approval.
5. The UI shows the complete calculation in the summary.

## Context Ledger
### Files read in full
- `AGENTS.md`, `CLAUDE.md`
- `system/models/membership.py` — `Membership`, `MembershipInvoice`, `MembershipStatus`
- `system/models/registration_order.py` — `RegistrationOrder`, `PaymentStatus`, `PaymentProvider`, `OrderKind`
- `system/services/membership.py` — `add_billing_cycle`, `get_billing_cycle_day_count`, `record_refund_from_charge`, `_ensure_active_membership_for_person`
- `system/services/plan_change.py` (to be rewritten)
- `system/services/stripe_admin_actions.py` — the reusable `refund_order`
- `system/services/asaas_client.py` — missing the `refund_payment` endpoint (to be added)
- `system/services/asaas_webhooks.py` — the `apply_plan_change` flow in PIX
- `system/services/stripe_webhooks.py` (lines 162-173) — the `apply_plan_change` flow in Stripe
- `system/views/plan_change_views.py` (refactored in PRD-019)
- `templates/billing/plan_change_select.html`, `static/system/js/billing/plan-change-selector.js`, `static/system/css/shared/plan-selector.css`

### Adjacent files consulted
- `system/services/financial_transactions.py` (resolve_payment_provider_for_plan)
- `system/services/payroll_rules.py` (`append_order_refund_record`)
- `system/tests/test_views.py` (PlanChangeSelectViewTest)
- `docs/prd/PRD-019-plan-change-plan-selector-standard.md`

### Internet / official documentation
- Stripe Refund API: `stripe.Refund.create(payment_intent=..., amount=...)` — already used in `stripe_admin_actions`.
- Asaas Refund API: `POST /payments/{id}/refund` (body `{value}`); the webhook sends `PAYMENT_REFUNDED`/`PAYMENT_PARTIALLY_REFUNDED` (already handled in `asaas_webhooks`).

### MCPs / tools verified
- PowerShell shell — ok
- Preview MCP — ok (used in PRD-019)
- Destructive reset authorized by the user (clear_migrations.py + makemigrations + migrate)

### Limitations found
- The Stripe `charge.refunded` webhook is already handled and updates `Order.payment_status=REFUNDED` + `MembershipInvoice.amount_refunded`. A refund we trigger must be **idempotent with the webhook**: save it immediately in `Order.notes` through `append_order_refund_record(cumulative=False)` and let the webhook eventually reinforce it.
- An Asaas refund can be partial; is it safe to call it multiple times? Yes, but we will keep a `MembershipMovement`-like log in `notes` through the same `append_order_refund_record` helper.

## Execution prompt
### Persona
Django + Stripe/Asaas integrations development agent following SDD + TDD.

### Action
Rewrite `system/services/plan_change.py` with the new engine (balance→time, leftover→credit, upgrade→charge), implement `request_plan_change_refund` triggering the providers, and update the UI and tests.

### Context
See above. The user explicitly authorized a destructive reset + automatic creation of a consolidated migration (`0001_initial`).

### Constraints
- No hardcoded rules (every monetary value comes from the plan and the paid `RegistrationOrder`).
- No `except: pass` or error masking.
- Keep the `apply_plan_change(order, membership, new_plan)` signature used in the webhooks compatible.
- Idempotency: a refund we trigger plus a subsequent webhook must not credit twice.
- No duplicate `MembershipCredit` for the same change.

### Acceptance criteria
- [ ] A customer on the annual plan with 4 months used, switching to monthly: the term extends by N full cycles (`floor(balance / monthly_price)`), the leftover becomes a `MembershipCredit`, with no charge.
- [ ] A customer on monthly switching to annual: charges `annual.price − balance`, full term (1 year).
- [ ] When there is a leftover, the UI shows the leftover amount + a `receber esse valor de volta` (`get this amount back`) button; on click, the refund is triggered **automatically** in the provider of the last paid order (Stripe or Asaas) and the order's history is updated.
- [ ] If the last order was `MANUAL`, "get it back" records the pending item (fallback) and shows a warning.
- [ ] No new endpoint requires administrative approval.
- [ ] `manage.py test --verbosity 2` passes with no failures (full suite).
- [ ] The destructive reset ran with no error; migrations consolidated into `0001_initial`.
- [ ] Visual validation on desktop and mobile with a clean console.

### Expected evidence
- Test output
- Output of `clear_migrations.py`, `makemigrations`, `migrate`
- Desktop + mobile screenshots
- A clean browser console

### Output format
Model + service + integration + view + template + JS + tests + destructive reset.

## Scope
- `system/models/membership.py`: a new `MembershipCredit`.
- `system/services/plan_change.py`: rewritten.
- `system/services/asaas_client.py`: a new `refund_payment(payment_id, value=None)`.
- `system/services/asaas_refunds.py` **(new)** or inline in `plan_change.py`: orchestration of the Asaas refund (idempotent, recorded in `Order.notes`).
- `system/views/plan_change_views.py`: GET with the new payload (new fields), POST with `action`/`leftover_action` (`keep_credit` default | `refund`).
- `templates/billing/plan_change_select.html`: a new "your current plan" panel + summary adjustments.
- `static/system/js/billing/plan-change-selector.js`: renders the new fields + the refund button + the leftover toggle.
- `static/system/css/shared/plan-selector.css` or `billing.css`: styles for the new blocks.
- `system/tests/test_services.py` or `test_plan_change.py` (a new file): engine tests (calculation, cycles, leftover, upgrade, mocked refund).
- `system/tests/test_views.py`: cover POST with the new modes.

## Out of scope
- Full cancellation with the 7-day statutory cooling-off window → a separate PRD-021.
- Email/SMS notifications to the customer after a change/refund.
- An administrative screen to view/force refunds (the current admin keeps using `stripe_admin_actions`).
- Partial refunds in situations other than a plan change.

## Impacted files
| File | Type |
|---|---|
| `system/models/membership.py` | + `MembershipCredit` |
| `system/services/plan_change.py` | full rewrite |
| `system/services/asaas_client.py` | + the `refund_payment` function |
| `system/views/plan_change_views.py` | new GET/POST fields |
| `templates/billing/plan_change_select.html` | panel + toggle |
| `static/system/js/billing/plan-change-selector.js` | new rendering |
| `static/system/css/shared/plan-selector.css` | new classes |
| `system/tests/test_services.py` | new engine tests |
| `system/tests/test_views.py` | new view tests |
| `system/migrations/0001_initial.py` | regenerated through the destructive reset |
| `system/views/__init__.py` | (probably unchanged) |

## Risks and edge cases
- **No linkable paid order**: an exempted customer or a seed with no `RegistrationOrder`. Fallback: use `membership.plan.price` as `amount_paid`.
- **Multiple paid orders** for the same plan (renewals): take the most recent paid, non-refunded one.
- **A balance equal to exactly N cycles** (no leftover): `leftover_credit = 0`, no refund button.
- **A Stripe refund fails** (a charge too old, etc.): show the error and keep the leftover as a `MembershipCredit` automatically.
- **An Asaas refund fails**: likewise.
- **The customer clicks refund during an upgrade** (there is no leftover): the UI must not offer the button.
- **Destructive reset**: with the disposable local SQLite database (`db.sqlite3`), apply it as defined in `CLAUDE.md`.

## Rules and constraints
- SDD + TDD
- Destructive reset authorized
- No hardcoded monetary values
- Idempotency in external integrations

## Plan
- [ ] 1. The `MembershipCredit` model
- [ ] 2. Add `refund_payment` to `asaas_client.py`
- [ ] 3. Rewrite `plan_change.py` (engine + apply + refund)
- [ ] 4. Update the view (GET/POST with `leftover_action`)
- [ ] 5. Update the template + JS + CSS
- [ ] 6. Tests (engine + view + mocked refund)
- [ ] 7. Destructive reset + migrate
- [ ] 8. Desktop + mobile visual validation
- [ ] 9. Documentation update

## Visual validation
### Desktop
- A "your current plan" panel with the amount paid, days used/remaining, and balance
- A summary of the target plan with the new term, the leftover (when there is one), and the refund button
- The `Confirmar troca` (`Confirm change`) / `Confirmar e pagar` (`Confirm and pay`) button depends on the scenario

### Mobile
- An adapted layout that stays readable

### Console
- Clean on both screens

### Terminal
- No stack traces

## ORM validation
### Database
- `MembershipCredit` created, migration 0001_initial regenerated

### Shell checks
- `MembershipCredit.objects.filter(applied_at__isnull=True).count()` in change scenarios with a leftover
- `RegistrationOrder.objects.filter(refunded_at__isnull=False)` after the refund is triggered

### Flow integrity
- A subsequent webhook does not duplicate credits or refunds

## Quality validation
- No hardcoding
- No `except: pass`
- Small functions, comments only where necessary
- Idempotency protected

## Evidence
*(to be filled in after execution)*

## Implemented
*(to be filled in after execution)*

## Deviations from plan
*(to be filled in after execution)*

## Pending
*(to be filled in after execution)*
