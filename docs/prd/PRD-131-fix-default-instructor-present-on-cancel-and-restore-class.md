# PRD-131: Fixing the instructor's default presence when cancelling/restoring a class

## Summary
This fixes a latent regression in the student check-in gating (PRD-094): cancelling and then restoring a class of the day — without the instructor ever having declared themselves absent — leaves the session stuck at "instructor not confirmed" (`instructor_present=False`) forever, blocking the check-in of **every** student enrolled in that class, even though the main instructor will teach the class normally. The business rule the user expects: every class is active/with the instructor present by default every day; it only becomes pending confirmation when the instructor **explicitly** cancels their own presence or names a substitute.

## Demand type
A business rule regression fix (reported by the user through a screenshot: two newly registered students, enrolled in the same class/schedule, saw different check-in states at different moments — an investigation paired with the user identified the root cause).

## Current problem
- `system/services/class_calendar.py::toggle_session_cancel` (used both by `InstructorToggleSessionView`, the calendar page's toggle, and by `cancel_class_without_instructor`, the dashboard's `Cancelar aula` — "Cancel class" — button) creates the day's `ClassSession` through `ClassSession.objects.get_or_create(schedule=.., date=.., defaults={"status": SessionStatus.SCHEDULED})` — **without** `instructor_present=True` in the defaults.
- That differs from the pattern already used in `register_instructor_self_checkin` (`_session_creation_defaults()`, which includes `instructor_present=True`).
- The result: if the **first** action touching the day's session is a cancellation (the calendar or "Cancelar aula"), without the instructor having declared themselves absent beforehand (`cancel_instructor_self_checkin`) or named a substitute (`assign_session_substitute`), the session is born with `instructor_present=False` (the model field's default). Cancelling does not expose the problem (a cancelled class does not show the check-in gate), but **restoring** it (`toggle_session_cancel` again, returning `status=SCHEDULED`) does not reset `instructor_present` — the class comes back showing as normal, but with the instructor marked "not confirmed", blocking every student's check-in until someone confirms the presence manually.
- Reproduced in this session: two new students (Beatriz and Carlos), enrolled in the same two classes of the day, saw different check-in states at different moments — not because of a difference between them, but because, between one screenshot and the next, the day's two `ClassSession` records were created (probably through a cancel/restore in the calendar) with `instructor_present=False`, retroactively freezing the check-in for both.
- Validated live: logging in as Beatriz, in the current state, shows the same block as Carlos — confirming it is not a registration/enrollment bug, it is `toggle_session_cancel`.

## Goal
Every class is born with the main instructor assumed present by default, every day — requiring no prior action. The student's check-in must only be blocked (the message "Solicite ao professor..." — "Ask the instructor...") when the instructor **explicitly** declares an absence (`cancel_instructor_self_checkin`) or when a substitute is named and has not yet confirmed (`assign_session_substitute`). Cancelling and restoring a class, on its own, must never freeze the students' check-in.

## Context Ledger
### Files read in full
- `system/services/class_calendar.py` (all the presence/session functions: `_student_instructor_present`, `_instructor_presence_state`, `_session_creation_defaults`, `register_instructor_self_checkin`, `cancel_instructor_self_checkin`, `assign_session_substitute`, `toggle_session_cancel`, `cancel_class_without_instructor`, `perform_checkin`)
- `system/models/calendar.py` (`ClassSession`, `SpecialClass` — `instructor_present` defaults to `False` on the model)
- `system/views/calendar_views.py` (`InstructorToggleSessionView`, `InstructorCancelClassTodayView`)
- `templates/home/partials/today_classes_list.html` (the `{% elif not item.instructor_present %}` gate → the "Solicite ao professor..." message)
- `docs/prd/PRD-094-student-checkin-dual-role-instructor-precondition.md` (the gate's origin, confirming the "no session = present by default" behavior)
- `system/tests/test_calendar.py` (the existing toggle/cancellation/substitute tests — none pins the value of `instructor_present` after a cancel+restore done **without** a prior absence declaration, confirming that the gap had no coverage)

### Adjacent files consulted
- `system/services/class_calendar.py::create_special_class` (an open class is always born with `instructor_present=True` — it does not have the same problem, confirming that the correct pattern is already used elsewhere in the same file)

### Limitations found
- N/A — the root cause investigation was completed through the live ORM/shell, with no need for external documentation (it is an internal business rule, not a third-party integration).

## Required skills
`lv-task-intake`, `lv-prd`, `lv-django-delivery`, `lv-cleanup-audit`

## Understanding approved
The user confirmed the business rule directly: "the classes are expected to be active every day; only if the instructor is not going to teach does he cancel his presence... it is pre-understood that he will teach, so he doesn't have to check in every day. Only if he isn't going does he cancel the class or name another instructor." And they explicitly asked: "re-evaluate the complete flow and the tests in a new PRD."

## Scope
- `system/services/class_calendar.py::toggle_session_cancel`: swap `defaults={"status": SessionStatus.SCHEDULED}` for `defaults=_session_creation_defaults()` in the `get_or_create`, aligning it with the same pattern already used in `register_instructor_self_checkin`.
- New tests covering exactly the reported scenario: cancel a class that never had an instructor absence declaration, restore it, and confirm that `instructor_present` stays/returns to `True` (the check-in released) — both through `toggle_session_cancel`/`cancel_class_without_instructor` directly and through `get_today_classes_for_person` (the student's view).
- Confirm (a non-regression test) that the path where the instructor **explicitly** declares themselves absent before cancelling (`cancel_instructor_self_checkin` → `cancel_class_without_instructor` → restore) still requires a manual confirmation after restoring (the correct behavior, already covered by `test_today_classes_exposes_can_uncancel_class_after_instructor_cancel`).

## Out of scope
- Any change to `assign_session_substitute`/`cancel_instructor_self_checkin` (already correct — they create the session with `instructor_present=False` deliberately, reflecting an explicit declaration).
- Any change to `SpecialClass`/the open class (it is already born with `instructor_present=True` through `create_special_class`).
- Creating a routine/cron to pre-generate the `ClassSession` records every day — the "lazy" model (a session only exists when something touches it) stays; only the default value at creation changes.

## Rules and constraints
- No schema migration (the `instructor_present` field already exists, only the default value used at creation through this specific flow changes).
- Preserve 100% of `test_calendar.py`'s existing tests with no regression.
- TDD: a Red test before the fix.

## Test plan
### Tests to author
- `test_cancel_class_without_instructor_declaration_keeps_instructor_present_after_restore`: with no prior absence declaration, cancel and restore a class — `instructor_present` must be `True` after restoring.
- `test_toggle_session_cancel_creates_session_with_instructor_present_true_by_default`: `toggle_session_cancel` called directly on a class with no prior session — the created session is born with `instructor_present=True` (even though it is cancelled at that moment).
- `test_student_checkin_available_after_cancel_restore_without_absence_declaration`: the student's view (`get_today_classes_for_person`) shows `instructor_present=True` (the Check-in button) after that cancel/restore cycle with no prior declaration.
- Non-regression: `test_today_classes_exposes_can_uncancel_class_after_instructor_cancel` (already existing) stays OK unchanged — confirming that an explicit absence declaration still requires a re-confirmation after restoring.

### Execution authorization
Local.

## Plan
1. [x] Write the 3 new tests (Red).
2. [x] Adjust `toggle_session_cancel` to use `_session_creation_defaults()`.
3. [x] Run the new tests (Green) and `test_calendar.py`'s full suite (the non-regression).
4. [x] `manage.py check`.
5. [x] Validate live in the internal browser logging in as Beatriz (a real account already created), checking that the check-in comes back.

## Implemented
- `system/services/class_calendar.py::toggle_session_cancel`: the `get_or_create` now uses `defaults=_session_creation_defaults()` (`instructor_present=True`, `instructor_checked_in_at=now()`) instead of `defaults={"status": SessionStatus.SCHEDULED}` — aligned with the same pattern already used in `register_instructor_self_checkin`.
- `system/services/class_calendar.py::cancel_class_without_instructor`: the two guards (`instructor_present` and `substitute_teacher_id`) now also consider `not session.is_cancelled` — this avoids blocking the **restoration** of a cancelled class (the guard existed to prevent cancelling a class with the instructor already confirmed/a substitute named, not to prevent restoring one). Without that fix, the previous item's fix made the restoration fail with "Cancele a confirmação antes de cancelar a aula." ("Cancel the confirmation before cancelling the class.") even with no pending confirmation.
- `system/tests/test_calendar.py` (`InstructorSelfCheckinServiceTestCase`): 3 new tests — `test_toggle_session_cancel_creates_session_with_instructor_present_true_by_default`, `test_cancel_class_without_instructor_declaration_keeps_instructor_present_after_restore`, `test_student_checkin_available_after_cancel_restore_without_absence_declaration`.
- The real data fixed through the ORM: today's two `ClassSession` records (schedules 2 and 10, created before the fix with `instructor_present=False`) had the value corrected to `True` — reflecting what the creation would already have done with the fix applied, requiring no manual action from the instructor.

## Evidence
- The Red test confirmed before the fix: the 3 new tests failed (`AssertionError: False is not true`), reproducing exactly the reported bug.
- After the fix: `manage.py test system.tests.test_calendar --verbosity 2` → **103 tests, OK** (100 pre-existing + 3 new, no regression).
- `manage.py check` → clean.
- Live validation in the internal browser: logged in as Beatriz Aluna Stripe (CPF `529.982.247-25`) — before the fix it showed "Solicite ao professor..." ("Ask the instructor...") in both of the day's classes; after fixing the existing data (reflecting the new default) and restarting the preview server to load the new code, the same account shows the "Check-in" button normally again in both classes.
- `manage.py test` (the full suite) → **554 tests, OK**. `manage.py check` → clean. No regression in any other area of the system.

## Cleanup findings
No residue. The fix was surgical (2 lines of behavior in `toggle_session_cancel`/`cancel_class_without_instructor`), with no new field, migration, or configuration introduced.

## Final status
Completed and validated — the automated tests (103, the calendar suite + the full suite) and a live visual validation.
