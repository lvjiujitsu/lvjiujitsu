# PRD-062: Audit of the signal → idempotent service pattern

## Summary

Audit LV's Django signal surface and the creation of derived records (backorders, payouts/`TeacherPayout`, order finances) against known failure modes — exclusive dependence on a signal, M2M/`bulk_create` timing, and a silenced exception — and codify the "idempotent service + explicit call" (belt-and-suspenders) pattern as a project rule. The initial finding is that LV **already follows** the correct pattern in its services; this PRD confirms that with evidence and hardens the single fragile point identified.

## Demand type

Preventive architectural audit + targeted hardening + rule codification. It may produce a minimal, low-risk fix in the backorders signal.

## Current problem

- In a known case, critical logic depended only on signals and failed due to M2M and `bulk_create` timing, which do not fire `post_save`. The fix was to extract an idempotent service and call it explicitly in the view.
- In LV, the preliminary audit indicates a healthy situation:
  - the repository's only `@receiver` is in `system/signals.py` (backorders) and already delegates to `system/services/product_backorders.py`;
  - the payout services (`asaas_payroll.py`) and finances (`financial_transactions.py`) create records inside `@transaction.atomic`, with no dependence on a signal.
- The fragile point identified: in `system/signals.py`, `promote_backorders_on_restock` wraps the service calls in a `try/except Exception` that only logs and moves on. A failure to promote/cancel a pre-order becomes invisible outside the log, with no reprocessing net and no equivalent explicit call in the flow that changes stock.
- There is no project rule forbidding derived logic that depends only on a signal and requiring an idempotent service + an explicit call, to prevent a future regression to the PRD-105 pattern.

## Goal

1. Map LV's entire signal surface and derived-record creation and classify each one by PRD-105 risk (timing, `bulk_create`, a silenced exception, exclusive dependence on a signal).
2. Confirm with evidence that payouts and order finances do not depend on a signal.
3. Harden the backorders signal: guarantee the service's idempotency and evaluate an explicit service call in the restock flow, keeping the signal as a secondary net.
4. Cover the promotion/cancellation of backorders with an idempotency test (calling it twice does not duplicate a `RegistrationOrder`/`ProductBackorder`).
5. Codify the "idempotent service + explicit call" rule in the `lv-cleanup-audit` skill and/or in `AGENTS.md §9`.

## Context Ledger

### Files read in full

- `system/signals.py`
- `system/apps.py`
- `system/services/product_backorders.py`
- `system/services/asaas_payroll.py`
- `system/services/financial_transactions.py`
- `system/services/payroll_rules.py`

### Adjacent files consulted

- `system/models/product.py` (ProductVariant, ProductBackorder, RegistrationOrder)
- `system/services/registration_checkout.py` (the order flow)
- the inventory of `system/services/`

### Internet / official documentation

- [Django 5.2 — signals](https://docs.djangoproject.com/en/5.2/topics/signals/)
- [Django 5.2 — m2m_changed](https://docs.djangoproject.com/en/5.2/ref/signals/#m2m-changed)
- [Django 5.2 — bulk_create caveats](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#bulk-create)
- [Django 5.2 — database transactions](https://docs.djangoproject.com/en/5.2/topics/db/transactions/)

### Context7 / MCPs / tools verified

- Context7 to be consulted for Django signals/transactions during execution.
- PowerShell, Git, and `rg` available.
- The internal browser available for visual evidence of the backorders flow, should the fix touch the UI.

### Limitations found

- The creation of a `TeacherPayout` happens in a scheduled command/service; validating it requires authorization to run a command.
- Legacy backorder data, if any exists, requires a read-only ORM inspection before any mutation.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved

- Summary presented: audit LV's signals/services against the PRD-105 lesson and harden the single fragile point, without inventing a non-existent bug.
- User approval: an explicit request for complete PRDs for sequential implementation.
- Date: 2026-06-28.

## Execution prompt

### Persona

Django engineer responsible for signals, transactional services, and the integrity of derived records.

### Action

Audit the signal/service surface, write an idempotency test for the backorders flow, harden the signal, and codify the project rule.

### Context

LV is a Django 5.2 monolith with its domain in `system/`. The only `@receiver` is in `system/signals.py`. Payouts and finances are already in transactional services.

### Constraints

- Do not create migrations.
- Do not run tests without authorization.
- Do not mutate production/HG data.
- Every derived write must remain idempotent.
- Keep the signal as a secondary net; never remove a protection without replacing it.

### Acceptance criteria

- [ ] There is a map classifying every signal and every derived-record creation by PRD-105 risk.
- [ ] There is evidence that `TeacherPayout` and order finances do not depend on a signal.
- [ ] `restock_variant`/`cancel_all_active_for_variant` are demonstrably idempotent through a test.
- [ ] Calling the backorder promotion service twice does not duplicate a `RegistrationOrder` or reactivate cancelled pre-orders.
- [ ] The signal's silent `except Exception` is reassessed: it either gains a reprocessing/visibility net, or it is replaced by an explicit call in the stock flow with the signal as a fallback.
- [ ] The "idempotent service + explicit call" rule recorded in `lv-cleanup-audit` and/or `AGENTS.md §9`.

### Expected evidence

- The signal/service map with a risk classification.
- The output of the idempotency test (after authorization).
- The diff of the signal hardening and the codified rule.

### Output format

A short summary, a risk map, evidence, limitations, and status.

## Scope

- `system/signals.py`
- `system/services/product_backorders.py`
- `system/tests/` (a new backorders idempotency test)
- `system/views/` or the service that triggers a restock (an explicit call, when applicable)
- `AGENTS.md` (§9) and/or the `lv-cleanup-audit` skill
- this PRD.

## Out of scope

- Redesigning the financial or payout module.
- Changing models or migrations.
- The external Asaas/Stripe payment flow.
- Fixing legacy data without separate authorization.

## Impacted files

- `system/signals.py`
- `system/services/product_backorders.py`
- `system/tests/test_product_backorders_signal.py` (new)
- the governance rule in `AGENTS.md` and/or `lv-cleanup-audit`
- this PRD.

## Risks and edge cases

- `ProductVariant.save()` does not involve M2M; the PRD-105 timing risk does not apply directly, but it must be confirmed and documented, not presumed.
- Adding an explicit call may duplicate a promotion if the service is not idempotent — which is why the idempotency test is a prerequisite for the explicit call.
- Scheduled payouts may create a `TeacherPayout` in a concurrent window; confirm the use of `unique`/`get_or_create` as a net.
- Silencing an exception masks a failure (the project's clean code rule): the reassessment must not introduce an `except: pass`.

## Rules and constraints

- The smallest correct change and the root cause.
- The service is the source of truth; the signal is a secondary net.
- No masked exception.
- `transaction.atomic` for multiple writes.

## Plan

- [ ] Context and research (the signal/service map)
- [ ] Write the idempotency test (test-first)
- [ ] Confirm the independence from signals in payouts/finances
- [ ] Harden the backorders signal / the explicit call
- [ ] Codify the project rule
- [ ] Request authorization and run the tests
- [ ] Cleanup audit
- [ ] Documentation

## Test plan

### Tests to author

- `test_product_backorders_signal.py`: the idempotency of `restock_variant` and `cancel_all_active_for_variant`; no duplication of a `RegistrationOrder`; no reactivation of a cancelled pre-order.

### Execution authorization

- Status: not requested. The tests are written before the code and run only after authorization.

### Execution evidence

To be collected after authorization. Do not declare Red/Green without an execution.

## Visual validation

To be determined: if the explicit call touches the stock/shop screen, validate it in the internal browser (desktop/mobile, the console, a screenshot). Otherwise, not applicable.

## ORM validation

- A read-only inspection of the backorders and payouts before any mutation.
- Mutating legacy data requires separate authorization.

## Quality validation

- `manage.py check` (after authorization).
- The risk map reviewed.
- `git diff --check`.

## Evidence

Planned — not executed. To be collected during the implementation.

## Implemented

Pending.

## Cleanup findings

Pending.

## Follow-up PRDs

- A possible PRD to fix legacy backorder/payout data, should the ORM inspection reveal an inconsistency.

## Deviations from plan

None so far.

## Pending

- Authorization to run the tests and the payout commands.

## Final status

**Not completed** — the PRD is specified; the implementation is pending sequential execution.
