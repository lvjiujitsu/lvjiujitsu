# PRD-055: Check-in with instructor approval + parity in schedule management

## Summary of the implementation
Introduce an approval flow into check-in: the student checks in from their panel and the record stays in an `Aguardando aprovação` (`Awaiting approval`) state; the class's instructor sees the pending check-ins in their panel and confirms them, or already sees them as `Confirmado` (`Confirmed`). The confirmed attendance history for the student and the instructor now considers only approved check-ins.

**Expansion (2026-05-06):** give the instructor parity with the admin in the schedule — they can now cancel/reactivate sessions of the classes they are responsible for, create and remove open classes on any day/time (always linking themselves as the teacher), and the admin must now link a responsible instructor when creating an open class.

## Demand type
New feature with a schema change (check-in) + a new feature with no schema change (the instructor's schedule management).

## Current problem
- The instructor's panel lists those present but has no approval action.
- The student's check-in is recorded as already confirmed, with no instructor mediation.
- There is no visual distinction between "awaiting approval" and "confirmed" in the student's panel.
- The student's attendance history mixes check-ins of any state, with no guarantee of real approval.

## Goal
- The student checks in → the record stays `pending` (Awaiting approval).
- The class's/open class's instructor sees the day's check-ins with an **Aprovar** (**Approve**) button, and the ones they already approved appear as confirmed.
- The student's panel shows an `Aguardando aprovação` (`Awaiting approval`) pill until approved and `Confirmado` (`Confirmed`) afterwards.
- The student's and the instructor's attendance history shows only `approved` check-ins.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/prd/PRD-008-adjust-instructor-and-student-panels-for-schedule-check-in-and-attendance-history.md`
- `system/models/calendar.py`
- `system/models/class_group.py`
- `system/models/__init__.py`
- `system/services/class_calendar.py`
- `system/views/calendar_views.py`
- `system/views/home_views.py`
- `system/views/portal_mixins.py`
- `system/views/__init__.py`
- `system/urls.py`
- `system/constants.py`
- `system/tests/test_calendar.py`
- `system/tests/test_views.py` (the relevant sections of the instructor/student dashboard)
- `templates/home/instructor/dashboard.html`
- `templates/home/student/dashboard.html`
- `static/system/css/portal/portal.css` (the `today-class-*` and `attendance-history-*` sections)
- `system/admin.py` (the `ClassCheckin` registration)
- `clear_migrations.py`

### Adjacent files consulted
- `system/migrations/0001_initial.py`
- `feedback_migrations_policy.md` (memory)

### Internet / official documentation
- Not applicable: behavior internal to the domain.

### MCPs / tools verified
- `read`, `glob`, `grep` — ok
- `bash` — pending for `manage.py test` and the destructive cycle
- browser/Playwright — pending for visual validation

### Limitations found
- The change requires a schema change → the destructive cycle authorized by the user on 2026-05-05.

## Execution prompt
### Persona
Django agent following SDD + TDD + MVT, with a service layer for business rules.

### Action
Add a status (pending/approved) to `ClassCheckin` and `SpecialClassCheckin`, create the approval services and views, and update the templates and tests.

### Context
The portal already has check-in for regular classes and open classes. The instructor's dashboard already lists those present, but with no action. The flow needs to mediate the confirmation to ensure the history only covers classes actually attended and validated by the person responsible for the class.

### Constraints
- no hardcoding
- no error masking
- the destructive cycle is authorized for this change
- mandatory full reading
- mandatory validation

### Acceptance criteria
- [ ] `ClassCheckin` and `SpecialClassCheckin` have `status`, `approved_at`, `approved_by` (verifiable through a model test).
- [ ] `perform_checkin` creates the check-in as `pending` (verifiable through a test).
- [ ] `approve_class_checkin(instructor, checkin_id)` requires the instructor to belong to the class; if so, it marks it `approved` and fills in `approved_at`/`approved_by` (verifiable through a service test).
- [ ] `approve_special_checkin(instructor, checkin_id)` validates that the instructor is the open class's teacher (verifiable through a test).
- [ ] The instructor's panel shows a list of the day's check-ins with a status badge and an Approve button for the pending ones (verifiable through a view test + visually).
- [ ] The student's panel shows an `Aguardando aprovação` (`Awaiting approval`) pill for the pending ones and `Confirmado` (`Confirmed`) for the approved ones in the day's classes (verifiable through a view test + visually).
- [ ] The student's attendance history includes only `approved` records (verifiable through a test).
- [ ] `manage.py test --verbosity 2` with no failures.
- [ ] `manage.py check` with no errors.

### Expected evidence
- passing tests
- the destructive cycle executed successfully
- a visual capture of the panels after in-browser validation

### Output format
Code + tests + evidence.

## Scope

### Check-in approval
- `system/models/calendar.py` — add `CheckinStatus` and the `status`, `approved_at`, `approved_by` fields to `ClassCheckin` and `SpecialClassCheckin`.
- `system/services/class_calendar.py` — `perform_checkin` creates pending; new `approve_class_checkin` and `approve_special_checkin`; `get_today_classes_for_instructor` exposes check-in IDs/statuses; `get_student_checkin_history` filters approved; `get_today_classes_for_person` exposes the person's own check-in status.
- `system/views/calendar_views.py` — the new `InstructorApproveCheckinView` and `InstructorApproveSpecialCheckinView` views.
- `system/urls.py` — the `instructor-approve-checkin` and `instructor-approve-special-checkin` routes.
- `templates/home/instructor/dashboard.html` — list those present with a badge and an Approve button.
- `templates/home/student/dashboard.html` — an `Aguardando aprovação`/`Confirmado` (`Awaiting approval`/`Confirmed`) pill on the card and a history filter.
- `static/system/css/portal/portal.css` — the pills, the instructor's check-in list, the Approve button; bump `?v=`.
- `system/admin.py` — include the new fields in `ClassCheckinAdmin`.

### Instructor schedule management (the expansion)
- `system/services/class_calendar.py` — `assert_instructor_owns_schedule(person, schedule_id)`, `assert_instructor_owns_special(person, special_id)`.
- `system/views/calendar_views.py` — `InstructorCalendarView`, `InstructorToggleSessionView`, `InstructorSpecialClassCreateView` (forcing `teacher=person`), `InstructorSpecialClassDeleteView`.
- `system/views/calendar_views.py` — `AdminCalendarView` passes `instructors` in the context; the `_get_instructor_choices` helper.
- `system/urls.py` — the `instructor-calendar`, `instructor-calendar-month`, `instructor-toggle-session`, `instructor-special-class-create`, `instructor-special-class-delete` routes.
- `templates/calendar/instructor_calendar.html` — a functional clone of the admin one with its own endpoints and buttons gated by schedule/open class ownership.
- `templates/calendar/admin_calendar.html` — a required `teacher` field in the modal and the payload.
- `templates/home/instructor/dashboard.html` — the `Gerir cronograma` (`Manage schedule`) link now points to `instructor-calendar`.

### Tests
- `system/tests/test_calendar.py` — cover the new status/approval services + the ownership helpers.
- `system/tests/test_views.py` — update the existing tests and add scenarios for approval, the instructor's schedule (loads, toggle, special create/delete), and the admin (a required teacher on the open class).

## Out of scope
- Notifying the student after approval.
- An approval history with detailed auditing beyond `approved_at`/`approved_by`.
- A "rejection" workflow (only pending → approved in this delivery).
- The administrative flow (only the instructor portal).

## Impacted files
See the "Scope" section.

## Risks and edge cases
- Check-ins created before the migration: since the destructive cycle recreates the database, there is no legacy.
- An instructor who is not the `main_teacher` but is a `ClassInstructorAssignment`: they must be able to approve — use `_get_instructor_class_group_ids`.
- An open class with no teacher (a nullable FK): approval is only unlocked for the open class's teacher; with no teacher, nobody can approve — explicit behavior.
- Approving twice: idempotent, it changes nothing if it is already `approved`.

## Rules and constraints
- SDD before code
- TDD when introducing new behavior
- no hardcoding
- no error masking
- the destructive cycle is authorized
- mandatory full reading
- mandatory validation

## Plan
- [x] 1. Context and full reading
- [x] 2. The model (`status`, `approved_at`, `approved_by`)
- [x] 3. Services (perform_checkin pending + approve_*)
- [x] 4. Approval views/URLs
- [x] 5. Templates (instructor + student)
- [x] 6. CSS + `?v=` bump
- [x] 7. Approval tests (updated + new)
- [x] 8. Instructor ownership helpers (services)
- [x] 9. The instructor's schedule views/URLs
- [x] 10. The `instructor_calendar.html` template + the dashboard link
- [x] 11. The admin modal with a required `teacher`
- [x] 12. Tests for the expansion (the instructor's schedule + the admin teacher)
- [x] 13. `manage.py check` (0 issues)
- [ ] 14. The destructive cycle + seeds (pending — authorized by the user, blocked by the local hook)
- [ ] 15. `manage.py test --verbosity 2`
- [ ] 16. In-browser visual validation
- [ ] 17. Final cleanup + PRD update

## Visual validation
### Desktop
- The instructor's panel: the day's class card shows the list of those present with a `Pendente` (`Pending`) pill + an Approve button; after approval, it becomes `Confirmado` (`Confirmed`).
- The student's panel: the day's class card shows an `Aguardando aprovação` (`Awaiting approval`) pill after check-in; it becomes `Confirmado` (`Confirmed`) after approval.

### Mobile
- The cards and pills must stay readable with an appropriate touch target.

### Browser console
- No critical JavaScript errors.

### Terminal
- No stack trace when opening the dashboards and when approving.

## ORM validation
### Database
- The schema regenerated by the destructive cycle after editing the models.

### Shell checks
- Check `ClassCheckin.objects.values_list("status", flat=True)` after the migration.

### Flow integrity
- Check-in is created as pending; the service changes it to approved; the history lists only approved.

## Quality validation
### No hardcoding
The statuses and copy come from `TextChoices`/templates.

### No brittle conditional structures
Guard clauses; the services validate authorization and idempotency.

### No `except: pass`
Unauthorized errors are explicit `PermissionError`s.

### No error masking
The views return JSON with an appropriate status code and a clear message.

### No unnecessary comments or docstrings
Keep the code self-explanatory.

## Evidence
(fill in after execution)

## Implemented
(fill in at the end)

## Deviations from plan
(fill in at the end)

## Pending
(fill in at the end)
