# PRD-104: Removing dead code from the registration wizard (onEnterCheckout)

## Summary
`static/system/js/auth/register.js` registers `onEnterCheckout()` to fire when `stepId === 'step-checkout'`, but that step never exists in the wizard's real sequence (`TRAILING_STEPS = ['step-plan', 'step-products', 'step-review']`). The entire function (81 lines) and its only helper consumer (`getSelectedPlan()`) are unreachable.

## Demand type
Dead code cleanup (a finding from the public wizard re-audit, a PRD-081 follow-up).

## Current problem
- `register.js:396` registers the call `if (stepId === 'step-checkout') onEnterCheckout();`, but no element with `id="step-checkout"` exists in the template or in the step sequence.
- `onEnterCheckout()` (lines 1605-1685) and `getSelectedPlan()` (lines 1600-1603) never run.
- The real checkout summary/payment logic was already migrated into `onEnterPlan()` and into the post-payment flow — the old function was left orphaned.

## Goal
Remove the dead code without changing any observable behavior of the wizard.

## Context Ledger
### Files read in full
- `static/system/js/auth/register.js` (the section of lines 1480-1690 and the `TRAILING_STEPS`/step dispatcher declaration)

### Adjacent files consulted
- `templates/login/register.html` (confirmed: there is no `id="step-checkout"`)
- `system/tests/test_register_wizard_contract.py` (confirmed: it references neither `step-checkout` nor `onEnterCheckout`)

### Limitations found
- None.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved
Authorized by the current request ("finish the whole implementation until you find no more errors"); a wizard re-audit finding confirmed manually before opening this PRD (7 of the exploration agent's 8 findings were discarded as false positives or as already-correct behavior).

## Scope
- Remove `onEnterCheckout()`, `getSelectedPlan()`, and the dispatcher line that invokes them in `register.js`.

## Out of scope
- Any other change to the wizard (the other 7 re-audit findings were discarded as not being real bugs).

## Impacted files
- `static/system/js/auth/register.js`
- `templates/login/register.html` (an asset `?v=` bump, per the project's convention)

## Risks and edge cases
- None: the code is demonstrably unreachable (no `step-checkout` element exists to trigger the dispatcher).

## Rules and constraints
- Update the script's `?v=` per the convention (`CLAUDE.md` section 2).

## Plan
- [x] Remove the dead code.
- [x] Bump the asset's version.
- [x] The complete test suite.
- [x] Visual validation of the wizard (a non-regressive happy path).

## Test plan
### Tests to author
- No new test (removing unreachable code does not change testable behavior). The existing suite (`test_register_wizard_contract.py` and related) serves as the regression check.

### Execution authorization
Authorized locally.

### Execution evidence
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 346 tests OK (the full suite, including `test_register_wizard_contract.py` updated to `?v=38`).
- Live validation in the browser: `/register/` loads normally, with no console errors; step 1 (profile selection) responds to a click with no undefined reference exception (confirming that removing `getSelectedPlan`/`onEnterCheckout`/`selectedPlanId` did not break `selectPlan`/`onEnterPlan`/`resolvePlanCheckoutAction`, which stay intact and are the only real paths the wizard uses).

## Visual validation
The public wizard walked through in the internal browser up to the plan/payment step.

## ORM validation
Not applicable (a client-side change).

## Quality validation
- `manage.py test system` — the full suite.

## Evidence
- Besides `onEnterCheckout()`/`getSelectedPlan()`, the `selectedPlanId` variable became write-only (with no reader) after the removal — removed in the same cleanup since it shares the same root cause (its only consumer was the dead function).

## Implemented
- `static/system/js/auth/register.js`: `onEnterCheckout()`, `getSelectedPlan()`, the `selectedPlanId` variable (and its 2 assignments), and the `if (stepId === 'step-checkout') onEnterCheckout();` dispatcher line removed.
- `templates/login/register.html`: bumped `register.js?v=37` → `?v=38`.
- `system/tests/test_register_wizard_contract.py`: the assert updated to `?v=38`.

## Cleanup findings
- A complete re-audit of the wizard (`system/views/auth_views.py`, `register.js`, `templates/login/register.html`, and the pre-registration/checkout/validation services) through an exploration agent; of the 8 findings reported, only this one (the dead code) was confirmed as a real bug after a line-by-line manual check. The other 7 were discarded:
  - CPF validation: the normalization is deterministic (`ensure_formatted_cpf`), with no real divergence.
  - The materials snapshot on a payment failure: it preserves the user's state correctly (the correct behavior, not a bug).
  - Multi-plan in the checkout: `validatePlan()` already blocks mixed payment methods before proceeding — there is no bug.
  - `selected_plans_payload` outside the form: it is a valid architectural decision (a raw POST snapshot for dynamic list data, consumed by `registration_checkout.py`), not a broken inconsistency.
  - The ambiguous class message, `person_type_code` vs. `registration_profile`, and the hardcoded coupon URL: low-impact nitpicks with no evidence of a concrete bug; they do not justify their own PRD now.

## Follow-up PRDs
- None.

## Deviations from plan
_None so far._

## Pending
_None so far._

## Final status
Completed.
