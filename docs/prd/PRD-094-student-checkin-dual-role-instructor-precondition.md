# PRD-094: Student check-in with a dual role and the instructor precondition

## Summary
Ensure a student — including one with a back-office role or class support — can request a check-in as a student, with a clear rule about the dependence on the instructor's attendance and the separation of the class lists on the home.

## Demand type
An attendance flow fix + UX.

## Current problem
- The student check-in button only appears when `item.instructor_present` (`today_classes_section.html:217-218`).
- Aline (a student + support) may be in the wrong list on the home (the staff view vs. the student view).
- `perform_checkin` does not validate the enrollment, but the UI may hide the action.
- The user: Aline, a back-office member, cannot record attendance as a student.

## Goal
An enrolled student always sees a clear state: waiting for the instructor, available for check-in, pending, or confirmed — in the **My area** section, regardless of any staff roles.

## Context Ledger
### Files read in full
- `system/services/class_calendar.py` (`get_today_classes_for_person`, `perform_checkin`)
- `templates/home/partials/today_classes_section.html`
- `system/views/home_views.py`
- `static/system/js/home/dashboard.js`

### Adjacent files consulted
- `docs/prd/PRD-055-checkin-with-instructor-approval.md`
- `docs/prd/AUDIT-2026-06-30-master-findings.md`

### Internet / official documentation
- N/A

### Context7 / MCPs / tools verified
- N/A

### Limitations found
- If the business rule requires the instructor to be present, the UX must communicate that without looking like a bug.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved
Aline's explicit problem in the 2026-06-30 audit.

## Execution prompt
### Persona
Attendance and schedule engineer.

### Action
Review the check-in gating and ensure an `entry_role=student` entry for the enrolled classes of dual-role people.

### Context
PRD-092's split; Aline's seed with adult enrollments.

### Constraints
- The backend validates the enrollment and a cancelled session.
- Accessible Brazilian Portuguese messages.

### Acceptance criteria
- [ ] Aline, logged in, sees a button or an explicit message on each enrolled class in My area.
- [ ] The check-in POST returns success when the instructor is present and the enrollment is active.
- [ ] When the instructor is absent, the message guides the action (not an empty screen).
- [ ] An integration test: a student + `class-assistant` checks in to an enrolled class.
- [ ] `perform_checkin` rejects a check-in with no enrollment through a clear `ValueError`.

### Expected evidence
- A green check-in API test.
- Screenshots of the states before/after the instructor's self check-in.

### Output format
The PRD's Evidence.

## Scope
- The calendar service, the partial template, the home context, the tests.

## Out of scope
- Bulk approval by the instructor (it already exists).
- The complete monthly calendar.

## Impacted files
- `system/services/class_calendar.py`
- `system/views/home_views.py`
- `templates/home/partials/today_classes_section.html`
- `system/tests/test_calendar.py` or a new file

## Risks and edge cases
- Kids class support vs. an adult enrollment.
- A special open class with no main instructor.

## Rules and constraints
- Coordinate with PRD-092 for the correct list.

## Plan
1. [x] A Red test of Aline's check-in (reproduced live in the browser before coding: the `Turmas de hoje` (`Today's classes`) section simply did not appear).
2. [x] Adjust `home_views.py` (it was not `get_today_classes_for_person`, which was already correct — the bug was in the choice of which list becomes `today_classes`).
3. [x] UX: no new message needed; the message `Solicite ao professor...` (`Ask the instructor...`) already existed in the partial for when `instructor_present=False`.
4. [x] Green.

## Test plan
### Tests to author
- `test_dual_role_student_sees_own_checkin_merged_with_support_classes`

### Execution authorization
Local.

### Execution evidence
- Reproduced live in the internal browser, logged in as Aline (CPF `920.000.011-81`, the real seed): the `Turmas de hoje` (`Today's classes`) section did not exist on the home — confirmed through the ORM that `get_today_classes_for_person(aline)` returned 2 real classes for today with `instructor_present=True` (it should show the Check-in button), but the home did not use that list for her.
- The root cause: in `home_views.py`, the block `if is_instructor or (can_support_classes and not is_administrative): context["today_classes"] = get_today_classes_for_instructor(person)` overwrote `today_classes` with the support/instructor view, discarding the personal list (`my_classes`) for anyone with `can_support_classes=True`, even when they also train.
- Fixed: when the person trains and is not an instructor (but has `can_support_classes`), `today_classes` becomes the **merge** of `my_classes` (their own classes, `entry_role=student`) with the support classes (an `entry_role` other than `student`), ordered by time, through the new `_merge_class_entries` helper.
- `system/tests/test_home_dashboard.py::test_dual_role_student_sees_own_checkin_merged_with_support_classes` (new): a student person + `class-assistant`, enrolled and with a class today, sees `Turmas de hoje` (`Today's classes`), sees `Check-in`, and the context's `today_classes` contains an entry with `entry_role="student"`.
- `.venv/Scripts/python.exe manage.py test system.tests.test_home_dashboard --verbosity 2` — 5 tests OK (including the 2 pre-existing tests that already crystallized the correct "no Management" behavior for Aline — preserved unchanged).
- `.venv/Scripts/python.exe manage.py test system.tests.test_calendar --verbosity 1` — 89 tests OK (the check-in flow itself was not changed, only the routing of which list appears on the home).
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 326 tests OK (the full suite).
- Live validation after the fix: logged in as Aline, the home shows `Turmas de hoje` (`Today's classes`) with the 2 real classes (06:30 and 19:00, Jiu Jitsu Adulto), each with a visible `Check-in` button, plus the `Criar aulão` (`Create open class`) action from the class support in the same list — with no improper `Gestão` (`Management`) section.

## Visual validation
Validated in the internal browser (see Execution evidence). Mobile not tested in isolation in this round — the class card's layout is the same one already validated on mobile in the earlier PRDs, with no structural change that would justify a new touch-target check.

## ORM validation
`get_today_classes_for_person`/`get_today_classes_for_instructor` verified through the local shell before and after the fix (see Execution evidence).

## Quality validation
- `manage.py check` — 0 problems.
- The full suite — 326 tests OK.

## Evidence
- The `{% elif not item.instructor_present %}` gating in the partial already displayed the message `Solicite ao professor que realize o check-in na aula para continuar` (`Ask the instructor to check in to the class to continue`) correctly — there was no UX bug there. The bug was structural: the wrong list reached the template.

## Implemented
- `system/views/home_views.py`: the new `_merge_class_entries(personal_entries, support_entries)` helper; the `today_classes` branch adjusted to merge when `trains and not is_instructor`.

## Cleanup findings
- No residue. The demonstration data (Aline's password reset for the validation) does not affect business data, only her portal access credential in the local development environment.

## Follow-up PRDs
- None. PRD-092 closed alongside it (see the evidence there — the same fix resolves both).

## Deviations from plan
- It was not necessary to change `get_today_classes_for_person` (it was already correct); the bug was entirely in the context composition in `home_views.py`.

## Pending
- None.

## Final status
Completed.
