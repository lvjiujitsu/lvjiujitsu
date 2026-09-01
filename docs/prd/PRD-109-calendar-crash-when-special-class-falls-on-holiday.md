# PRD-109: The administrative calendar crashes when an open class falls on a holiday

## Summary
`get_calendar_month_data()` builds the `holidays` dictionary as `{date: holiday_name (a string)}`, but when assembling the day's open class data (line 1365) it calls `_special_cancel_state(sc, holiday_name)` passing that string — while the function expects an object with a `.name` attribute (that is how the function's other 4 call sites use it, passing the `Holiday` object). When an open class falls on a day with a registered active holiday, the page crashes with `AttributeError: 'str' object has no attribute 'name'`.

## Demand type
A bug fix (a runtime crash).

## Current problem
- `system/services/class_calendar.py:139-146` (`_special_cancel_state`): `if holiday: cancellation_reason = holiday.name` — it expects a `Holiday` object.
- `system/services/class_calendar.py:1299-1300`: `holidays = {h.date: h.name for h in Holiday.objects.filter(...)}` — the dictionary holds strings, not objects.
- `system/services/class_calendar.py:1338`: `holiday_name = holidays.get(current_date, "")` — a string.
- `system/services/class_calendar.py:1365`: `_special_cancel_state(sc, holiday_name)` — it passes the string into the parameter that expects the object, unlike the function's other 4 uses (lines 182, 270, 689, 773), which pass the `Holiday` object correctly.
- The effect: `CalendarView` (`system/views/calendar_views.py:66`, `context["calendar"] = get_calendar_month_data(...)`) fails with a 500 whenever there is a `SpecialClass` (an open class) on a date with a registered `Holiday.is_active=True`.

## Goal
The administrative calendar renders normally even with an open class scheduled on a holiday, showing the holiday as the cancellation reason.

## Context Ledger
### Files read in full
- `system/services/class_calendar.py` (`_special_cancel_state` and its 5 call sites; the complete `get_calendar_month_data`)
- `system/views/calendar_views.py` (`CalendarView.get_context_data`, confirming it is the only path that uses `get_calendar_month_data`)

### Adjacent files consulted
- `system/tests/test_calendar.py` (`test_calendar_month_data_includes_specials`): it was confirmed that it does not cover the open class + holiday on the same day case — which is why the bug was not caught earlier.

### Limitations found
- None.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
Authorized by the current request ("finish the whole implementation until you find no more errors"). The only real finding of a re-audit of the Schedule module (the other aspects investigated — the holiday CRUD, orphaned routes — showed no problem).

## Scope
- Fix the call on line 1365 to pass the `Holiday` object (not the string), replicating the pattern of the other 4 call sites — this requires either the `holidays` dictionary to hold the object rather than just the name, or the object to be resolved separately.

## Out of scope
- A holidays CRUD (there is no dedicated screen today; there is no evidence it is a real gap — holidays are a low-frequency operation, handled today through the Django Admin, and it was neither requested nor identified as a breakage).

## Impacted files
- `system/services/class_calendar.py`
- `system/tests/test_calendar.py`

## Risks and edge cases
- Preserve the `is_holiday`/`holiday_name` (string) behavior already used in the day's context (lines 1385-1386), which other parts of the template consume — the fix must resolve the `Holiday` object only to pass it into the function, without breaking the string's other uses.

## Rules and constraints
- No migration necessary (a pure logic change in Python).

## Plan
- [x] Fix the argument passing.
- [x] A focused test covering an open class + a holiday on the same day.
- [x] The full suite.

## Test plan
### Tests to author
- `get_calendar_month_data` does not raise an exception and returns the correct `cancellation_reason` when there is an open class on a day with an active holiday.

### Execution authorization
Authorized locally.

### Execution evidence
- `system/tests/test_calendar.py::SpecialClassServiceTestCase::test_calendar_month_data_does_not_crash_when_special_falls_on_holiday` (new): before the fix, this test reproduced the `AttributeError: 'str' object has no attribute 'name'`; after the fix, `get_calendar_month_data` returns normally with `is_cancelled=True` and `cancellation_reason="Feriado Aulão Fundacao"`.
- `.venv/Scripts/python.exe manage.py test system.tests.test_calendar --verbosity 2` — 92 tests OK.
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 355 tests OK (the full suite).
- `.venv/Scripts/python.exe manage.py check` — 0 problems.

## Visual validation
Not applicable to this targeted fix (the automated test coverage is enough to prove the crash no longer happens); the calendar as a whole was already validated visually in earlier PRDs.

## ORM validation
`Holiday`/`SpecialClass` used in the focused test.

## Quality validation
- `manage.py test system.tests.test_calendar` and the full suite.
- `manage.py check`.

## Evidence
- A real bug confirmed by direct reproduction: the new test failed with an `AttributeError` before the fix, proving the exploration agent's diagnosis (one of the few in this session that was not a false positive).

## Implemented
- `system/services/class_calendar.py`: `get_calendar_month_data` now stores the `Holiday` object in the `holidays` dictionary (not the string), derives `holiday_name` from it, and passes the object (not the string) into `_special_cancel_state`, just like the function's other 4 call sites.
- `system/tests/test_calendar.py`: 1 new test covering an open class + a holiday on the same day.

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
