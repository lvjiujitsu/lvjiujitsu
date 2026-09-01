# PRD-107: The instructor can approve a check-in for an already-cancelled regular class

## Summary
`approve_special_checkin` (an open class) validates `if checkin.special_class.is_cancelled: raise ValueError(...)` before approving attendance, but the equivalent function for a regular class, `approve_class_checkin`, does not have that same validation — allowing attendance to be approved for a class that has already been marked as cancelled.

## Demand type
A bug fix (a validation asymmetry between two analogous paths).

## Current problem
- `system/services/class_calendar.py:1250-1269` (`approve_class_checkin`): it validates the permission (`instructor_group_ids`/the substitute) and `checkin.is_approved`, but it does not validate `checkin.session.is_cancelled` — it silently approves attendance for a cancelled class.
- `system/services/class_calendar.py:1272-1289` (`approve_special_checkin`): it validates the same things and, additionally, `if checkin.special_class.is_cancelled: raise ValueError("Este aulão foi cancelado.")` ("This open class was cancelled.").
- `system/views/calendar_views.py:511-516` (`InstructorApproveCheckinView.post`) and `:547-552` (`InstructorApproveSpecialCheckinView.post`): neither view catches a `ValueError` coming from the service — only `ClassCheckin.DoesNotExist`/`SpecialClassCheckin.DoesNotExist` and `PermissionError`. That means that, even with `approve_special_checkin`'s existing validation, today it produces an **unhandled 500 error** instead of a clean error message, because the `ValueError` propagates uncaught.
- `ClassSession` and `SpecialClass` (`system/models/calendar.py`) both expose the `is_cancelled` property.

## Goal
`approve_class_checkin` refuses to approve attendance for an already-cancelled class session, with the same message/pattern as the open class path; and both views return a clean JSON error (400) instead of a 500 when the class/open class is cancelled.

## Context Ledger
### Files read in full
- `system/services/class_calendar.py` (`approve_class_checkin`, `approve_special_checkin`, and the class/open class cancellation and instructor self check-in functions)
- `system/models/calendar.py` (`ClassSession.is_cancelled`, `SpecialClass.is_cancelled`)

### Adjacent files consulted
- `system/views/calendar_views.py` (`InstructorApproveCheckinView`, `InstructorApproveSpecialCheckinView`)

### Limitations found
- None.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
Authorized by the current request ("finish the whole implementation until you find no more errors"). The finding was confirmed by directly comparing the code of the two analogous paths (a regular class vs. an open class); the other hypotheses from the same re-audit (that cancelling a class/open class or the instructor's self check-in do not validate already-approved check-ins) were left out because they are debatable product decisions, not a proven code asymmetry like this one.

## Scope
- Add the same `is_cancelled` validation to `approve_class_checkin`, mirroring `approve_special_checkin`.
- Add an `except ValueError` to `InstructorApproveCheckinView.post` and `InstructorApproveSpecialCheckinView.post`, returning `JsonResponse({"error": str(e)}, status=400)`.

## Out of scope
- Validating pending check-ins in `cancel_class_without_instructor`/`cancel_special_without_instructor`/the instructor's self check-in (the current behavior may be intentional; there is no evidence of a regression, only a risk hypothesis — do not open a change without confirming it is genuinely unwanted).

## Impacted files
- `system/services/class_calendar.py`
- `system/tests/`

## Risks and edge cases
- None: the change only blocks a path that should already have been blocked, replicating an already validated pattern.

## Rules and constraints
- The error message in Brazilian Portuguese, in the same pattern as the open class ("Esta aula foi cancelada." — "This class was cancelled.").

## Plan
- [x] Add the validation.
- [x] A focused test.
- [x] The full suite.

## Test plan
### Tests to author
- Approving a check-in for a cancelled session raises a `ValueError` and does not change the check-in's status.

### Execution authorization
Authorized locally.

### Execution evidence
- `system/tests/test_calendar.py::CheckinApprovalServiceTestCase::test_approve_class_checkin_blocks_cancelled_session` (new): approving a check-in for a cancelled session raises a `ValueError` and keeps the `PENDING` status.
- `system/tests/test_calendar.py::InstructorApproveCheckinViewTestCase::test_approve_checkin_of_cancelled_session_returns_clean_400` (new): the view returns a 400 with a clean JSON message instead of a 500.
- `.venv/Scripts/python.exe manage.py test system.tests.test_calendar --verbosity 2` — 91 tests OK.
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 353 tests OK (the full suite).
- `.venv/Scripts/python.exe manage.py check` — 0 problems.

## Visual validation
Not applicable (a business rule change in a service, with no new UI; the view already handles validation exceptions of the same pattern).

## ORM validation
`ClassCheckin`/`ClassSession` used in the focused test.

## Quality validation
- `manage.py test system.tests.test_lv_foundation_calendar` (or the new test) and the full suite.
- `manage.py check`.

## Evidence
- A relevant collateral finding: `approve_special_checkin` already validated `is_cancelled` before this PRD, but the `ValueError` it raised was never caught by `InstructorApproveSpecialCheckinView` — that is, the open class path already had that protection "active" in the code but it produced a 500 error for the user. Fixing the view benefits both paths.

## Implemented
- `system/services/class_calendar.py`: `approve_class_checkin` now validates `checkin.session.is_cancelled` before approving, mirroring `approve_special_checkin`.
- `system/views/calendar_views.py`: `InstructorApproveCheckinView.post` and `InstructorApproveSpecialCheckinView.post` now catch `ValueError` and return `JsonResponse({"error": ...}, status=400)` instead of letting the exception propagate as a 500.
- `system/tests/test_calendar.py`: 2 new tests (the service + the view).

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
