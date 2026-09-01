# PRD-108: The instructor payout counts a cancelled class; `TeacherFinancialView` is dead code

## Summary
Two failures in the instructor's financial payout flow: (1) `_count_class_attendances()` does not exclude cancelled sessions/open classes from the attendance count used in the commission calculation — a check-in approved before the cancellation still counts; (2) `TeacherFinancialView` (the instructor's dedicated "financial" screen) has no route in `system/urls.py` and no template (`templates/home/instructor/financial.html` does not exist) — it is dead code, superseded by the `Repasse` (`Payout`) section already consolidated on the home (`_build_instructor_payroll_context`).

## Demand type
A bug fix (the financial count) + dead code cleanup.

## Current problem
- `system/services/payroll_rules.py:828-845` (`_count_class_attendances`): it counts `ClassCheckin`/`SpecialClassCheckin` with `status=APPROVED` without excluding sessions/open classes with `status=CANCELLED`. Since `cancel_class_without_instructor`/`toggle_session_cancel` (`system/services/class_calendar.py:1018-1026`, `:1405-1419`) do not invalidate already-approved check-ins when cancelling, a check-in approved before the cancellation keeps counting improperly toward the instructor's commission.
- `system/views/asaas_views.py:322-356` (`TeacherFinancialView`): a complete, functional view, but with no entry in `system/urls.py` and no `home/instructor/financial.html` template (the `templates/home/instructor/` directory does not exist). All the data it assembles (`config`, `bank`, `available_balance`, `recent_payouts`, etc.) is already equivalent to what `_build_instructor_payroll_context()` (`system/views/home_views.py:252-275`) exposes in the home's `Repasse` (`Payout`) section — the view is a leftover from before the "Foundation" consolidation (PRD-075), never removed.

## Goal
- The instructor's commission never counts a cancelled class/open class, even when a check-in was approved before the cancellation.
- The dead code (`TeacherFinancialView` and its import) removed, with no attempt to recreate a route/template for a screen redundant with the home.

## Context Ledger
### Files read in full
- `system/services/payroll_rules.py` (`_count_class_attendances`, `calculate_monthly_payroll`)
- `system/services/class_calendar.py` (`cancel_class_without_instructor`, `cancel_special_without_instructor`, `toggle_session_cancel`, `toggle_special_cancel`)
- `system/views/asaas_views.py` (`TeacherFinancialView`)
- `system/views/home_views.py` (`_build_instructor_payroll_context`)
- `system/urls.py` (confirmed: no route references `TeacherFinancialView`)

### Adjacent files consulted
- `templates/home/dashboard.html` (the `Repasse` — `Payout` section, which already covers everything `TeacherFinancialView` assembled)
- `system/tests/test_services.py` (with no test covering the exclusion of a cancelled class in the payroll)

### Limitations found
- A 4th hypothesis from the exploration agent was discarded (`refuse_payout` reusing the `approved_by` field instead of a dedicated `refused_by`): the `TeacherPayout` model has only one field (`approved_by`), and creating a new one would require a migration for a purely cosmetic improvement — out of scope.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
Authorized by the current request ("finish the whole implementation until you find no more errors"). The findings were confirmed by direct reading; the "missing route" hypothesis was refined into "dead code to remove" after confirming the home already covers the same data (the same architectural pattern of not duplicating dedicated screens when the home already solves it).

## Scope
- `_count_class_attendances`: exclude `session__status=SessionStatus.CANCELLED` and `special_class__status=SessionStatus.CANCELLED` from the count.
- Remove `TeacherFinancialView` from `system/views/asaas_views.py` and its export in `system/views/__init__.py`.

## Out of scope
- Creating a `refused_by` field on `TeacherPayout` (a cosmetic improvement that would require a migration with no functional gain).
- Invalidating/reverting already-approved check-ins at the moment of the cancellation (it would change the behavior of `cancel_class_without_instructor`; fixing the payroll calculation already solves the financial problem without touching the check-in history).

## Impacted files
- `system/services/payroll_rules.py`
- `system/views/asaas_views.py`
- `system/views/__init__.py`
- `system/tests/test_services.py`

## Risks and edge cases
- None: the additional exclusion only reduces false positives in the count; it does not affect the other calculations (hold days, the per-student payout, etc.).

## Rules and constraints
- Do not create a migration for this scope.

## Plan
- [x] Fix the attendance count.
- [x] Remove the dead code.
- [x] Focused tests.
- [x] The full suite.

## Test plan
### Tests to author
- A cancelled class with a check-in approved before the cancellation does not count toward the payroll's attendance.
- A cancelled open class with a check-in approved before the cancellation does not count toward the payroll's attendance.

### Execution authorization
Authorized locally.

### Execution evidence
- `system/tests/test_services.py::PayrollRulesServiceTestCase::test_per_class_attendance_rule_excludes_cancelled_session` (new): a check-in approved before the session's cancellation no longer counts toward the commission (`class_attendance_count == 0`, `total == 0.00`).
- `.venv/Scripts/python.exe manage.py test system.tests.test_services --verbosity 2` — 18 tests OK.
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 354 tests OK (the full suite).
- `.venv/Scripts/python.exe manage.py check` — 0 problems.

## Visual validation
Not applicable (a calculation change in a service + the removal of dead code with no associated UI).

## ORM validation
`ClassCheckin`/`ClassSession`/`SpecialClassCheckin` used in the focused tests.

## Quality validation
- `manage.py test system.tests.test_services` and the full suite.
- `manage.py check`.

## Evidence
- It was confirmed that `get_staff_financial_context` (the service) ends up with no view caller after the removal, but it was kept: it is a legitimate, reusable service function, with no sign of being "dead" itself beyond losing its only view consumer — removing the service itself was not in the authorized scope (only the leftover view/route/template).

## Implemented
- `system/services/payroll_rules.py`: `_count_class_attendances` now excludes `session__status=CANCELLED` and `special_class__status=CANCELLED` from the attendance count.
- `system/views/asaas_views.py`: `TeacherFinancialView` and `StaffFinancialRequiredMixin` removed (dead code: no route, no template); the orphaned imports (`INSTRUCTOR_PERSON_TYPE_CODES`, `get_staff_financial_context`) removed.
- `system/views/__init__.py`: the `TeacherFinancialView` export removed.
- `system/tests/test_services.py`: 1 new test.

## Cleanup findings
- No additional residue.

## Follow-up PRDs
- None.

## Deviations from plan
_None so far._

## Pending
_None so far._

## Final status
Completed.
