# PRD-110: Graduation eligibility counts a cancelled class/open class

## Summary
The same bug pattern fixed in PRD-108 (the instructor's payout), now in the graduation eligibility calculation: `count_approved_classes_in_window()` counts `ClassCheckin`/`SpecialClassCheckin` with `status=APPROVED` without excluding sessions/open classes with `status=CANCELLED`. A check-in approved before the class was cancelled still counts toward the window of classes required to graduate.

## Demand type
A bug fix (an incorrect count), the same root cause as PRD-108.

## Current problem
- `system/services/graduation.py:21-40` (`count_approved_classes_in_window`): it excludes neither `session__status=CANCELLED` nor `special_class__status=CANCELLED` from the counts.
- The same root cause documented in PRD-108: `cancel_class_without_instructor`/`toggle_session_cancel` do not invalidate already-approved check-ins when cancelling the session.

## Goal
The class count for graduation eligibility never includes a cancelled class/open class.

## Context Ledger
### Files read in full
- `system/services/graduation.py` (`count_approved_classes_in_window`, `compute_graduation_progress`, `get_graduation_history`, `get_current_graduation`)
- `system/services/payroll_rules.py` (`_count_class_attendances`, already fixed in PRD-108 — used as the reference for the fix pattern)

### Adjacent files consulted
- `system/tests/test_graduation.py` (confirmed: no test covers a cancelled session in the counting window)

### Limitations found
- None.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
Authorized by the current request ("finish the whole implementation until you find no more errors"). The finding was confirmed by direct reading and by comparison with the fix already applied in PRD-108 for the same bug pattern.

## Scope
- Add `.exclude(session__status=SessionStatus.CANCELLED)` and `.exclude(special_class__status=SessionStatus.CANCELLED)` to `count_approved_classes_in_window`.

## Out of scope
- Any other change in the graduation module (the views, templates, and belt rules were already confirmed correct by the re-audit).

## Impacted files
- `system/services/graduation.py`
- `system/tests/test_graduation.py`

## Risks and edge cases
- None: the additional exclusion only reduces false positives in the count.

## Rules and constraints
- No migration.

## Plan
- [x] Fix the count.
- [x] A focused test.
- [x] The full suite.

## Test plan
### Tests to author
- A cancelled class with a check-in approved before the cancellation does not count toward the graduation eligibility window.

### Execution authorization
Authorized locally.

### Execution evidence
- `system/tests/test_graduation.py::GraduationServiceTestCase::test_count_approved_classes_excludes_cancelled_session` (new): a check-in approved before the session's cancellation no longer counts toward the window (`0` instead of `1`).
- `.venv/Scripts/python.exe manage.py test system.tests.test_graduation --verbosity 2` — 17 tests OK.
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 356 tests OK (the full suite).
- `.venv/Scripts/python.exe manage.py check` — 0 problems.

## Visual validation
Not applicable (a calculation change in a service, with no new UI).

## ORM validation
`ClassCheckin`/`ClassSession` used in the focused test.

## Quality validation
- `manage.py test system.tests.test_graduation` and the full suite.
- `manage.py check`.

## Evidence
- The same bug pattern and the same fix as PRD-108 (the payout), now applied in `count_approved_classes_in_window`.

## Implemented
- `system/services/graduation.py`: the `SessionStatus` import; `count_approved_classes_in_window` now excludes `session__status=CANCELLED` and `special_class__status=CANCELLED`.
- `system/tests/test_graduation.py`: 1 new test.

## Cleanup findings
- No residue.

## Follow-up PRDs
- None.

## Deviations from plan
_None so far._

## Pending
_None so far._

## Final status
Completed.
