# PRD-103: Subscription actions in the person detail

## Summary
`CancelMembershipActionView` and `ChangeMembershipPlanActionView` exist and work (through POST), but no screen has a button that triggers them — orphaned from the UI, a gap already documented in PRD-077 (Pending).

## Demand type
A UI fix (a backend action with no interface entry point).

## Current problem
- `templates/people/person_detail.html` shows the active plan (a status badge, the name, the due date) but has no cancel or change plan action.
- The manager has to use the Django Admin or a manual call for those actions.

## Goal
In the person detail's `Plano ativo` (`Active plan`) section (only for those who manage, `can_manage_people`), the manager can cancel the subscription (at the end of the period) and switch the active plan for another active plan in the catalog.

## Context Ledger
### Files read in full
- `templates/people/person_detail.html` (the `Plano ativo` — `Active plan` section)
- `system/views/billing_admin_views.py` (`CancelMembershipActionView`, `ChangeMembershipPlanActionView`)
- `system/views/person_views.py` (`PersonDetailView.get_context_data` — it already exposes `available_plans`)

### Adjacent files consulted
- `system/services/stripe_admin_actions.py`

### Limitations found
- None.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved
Authorized by the current request ("finish the whole implementation until you find no more errors"), a gap already documented in PRD-077.

## Scope
- Add the action forms (cancel, change plan) to the `Plano ativo` (`Active plan`) section of the person detail, with `next` pointing back to the page itself.

## Out of scope
- A "cancel immediately vs. at the end of the period" checkbox (it keeps the backend's `at_period_end=True` default).
- Redesigning the billing section.

## Impacted files
- `templates/people/person_detail.html`
- `system/tests/`

## Risks and edge cases
- The action must only appear when there is an `active_membership` with a cancellable status.
- Gateway errors (`StripeAdminActionError`) are already handled in the view with `messages.error` and a redirect — no change needed there.

## Rules and constraints
- It only renders for `can_manage_people`.
- CSRF on both POSTs.

## Plan
- [x] Add the two forms to the `Plano ativo` (`Active plan`) section.
- [x] A focused test.
- [x] Visual validation.

## Test plan
### Tests to author
- A person detail with an active subscription shows the buttons; with no active subscription, it does not.
- The cancel subscription POST works from the screen itself (with a redirect back).

### Execution authorization
Authorized locally.

### Execution evidence
- `system/tests/test_membership_actions_ui.py` (4 tests): the buttons appear with an active subscription; they do not appear with no active subscription; a cancel POST with no `stripe_subscription_id` cancels locally (a `canceled` status); a change plan POST with no `stripe_subscription_id` shows an error and keeps the plan.
- `.venv/Scripts/python.exe manage.py test system.tests.test_membership_actions_ui --verbosity 2` — 4 tests OK.
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 346 tests OK (the full suite).
- `.venv/Scripts/python.exe manage.py check` — 0 problems.
- Live validation in the browser (demo data created through the ORM for Aline Blanch Freiria, removed after the test): the `Mensalidade` (`Tuition`) section shows `Trocar plano` (`Change plan`) (a select with the active plans) and `Cancelar assinatura` (`Cancel subscription`); the cancellation POST changed the real status to `Cancelada` (`Cancelled`) and the section started showing `Nenhum plano ativo` (`No active plan`) with the history `CANCELADA` (`CANCELLED`); validated on mobile (375x812) and in the dark theme with no overflow.

## Visual validation
Desktop, mobile, the dark theme.

## ORM validation
`Membership.status` verified through the test.

## Quality validation
- The focused `manage.py test` and the full suite.
- `manage.py check`.

## Evidence
- `change_membership_plan` requires a `stripe_subscription_id` (old/manual subscriptions do not have one); in that case the action shows an error message and does not change the plan — correct behavior, already covered by the test.

## Implemented
- `templates/people/person_detail.html`: the `Plano ativo` (`Active plan`) section gained a change-plan form (a select with `available_plans` + a button) and a cancel-subscription form, visible only when `m.status` is `active`, `past_due`, or `exempted`; both use `next` to return to the page itself.
- `system/tests/test_membership_actions_ui.py` (new).

## Cleanup findings
- No residue; the demo data (the test membership) removed from the local database after the visual validation.

## Follow-up PRDs
- None.

## Deviations from plan
- No functional deviation.

## Pending
- None.

## Final status
Completed.
