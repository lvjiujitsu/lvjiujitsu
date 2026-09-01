# PRD-008: Adjust the instructor and student panels for schedule, check-in, and attendance history

## Summary of the implementation
Adjust the instructor panel to display the day's classes, access to the schedule, and a view of check-ins (including per-class history with a list of students present). Adjust the student panel to display the history of attendance confirmed by check-in.

## Demand type
Targeted fix with a functional dashboard improvement.

## Current problem
- The instructor panel does not display the day's classes or a useful attendance history.
- The instructor cannot see, from their own panel, which students checked in to the classes under their responsibility.
- The student panel does not display the history of attendance confirmed by check-in.

## Goal
- Display in the instructor panel: the day's classes, the list of students who checked in that day, per-class attendance history, and a working shortcut to the schedule.
- Display in the student panel: the history of classes with confirmed attendance.
- Allow an authenticated instructor to access the existing schedule route.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `system/views/home_views.py`
- `system/views/calendar_views.py`
- `system/views/portal_mixins.py`
- `system/views/__init__.py`
- `system/urls.py`
- `system/services/class_calendar.py`
- `system/models/calendar.py`
- `system/models/class_schedule.py`
- `system/models/class_group.py`
- `system/models/class_membership.py`
- `system/models/person.py`
- `system/models/__init__.py`
- `system/constants.py`
- `system/middleware.py`
- `templates/home/instructor/dashboard.html`
- `templates/home/student/dashboard.html`
- `templates/calendar/student_schedule.html`
- `templates/base.html`
- `static/system/css/portal/portal.css`
- `static/system/css/billing/billing.css`
- `system/tests/test_views.py`
- `system/tests/test_calendar.py`
- `system/tests/test_class_portal_views.py`

### Adjacent files consulted
- `system/services/class_overview.py` (search for instructor/class patterns)
- `system/services/class_catalog.py` (search for class/instructor query patterns)

### Internet / official documentation
- Not applicable to this demand (the behavior is internal to the project and the current domain).

### MCPs / tools verified
- `read` — ok
- `glob` — ok
- `grep` — ok
- `bash` — pending for final validation (test/check)

### Limitations found
- There is no dedicated attendance history screen; the delivery will be made on the existing dashboard.

## Execution prompt
### Persona
Django agent following SDD + TDD + MVT with services for business rules.

### Action
Implement schedule/classes/check-ins/history display for the instructor and attendance history for the student.

### Context
The portal already has check-in and a schedule for the student, but the instructor dashboard is incomplete and the student has no attendance history visible in the panel.

### Constraints
- no hardcoding
- no error masking
- no migrations
- mandatory full reading
- mandatory validation

### Acceptance criteria
- [ ] The instructor sees the day's classes on the dashboard (verifiable by view/template test)
- [ ] The instructor sees the students who checked in to the day's classes (verifiable by test)
- [ ] The instructor sees per-class attendance history (verifiable by test)
- [ ] The instructor can access the schedule through the agenda route (verifiable by test)
- [ ] The student sees the confirmed attendance history on the dashboard (verifiable by test)
- [ ] `manage.py test --verbosity 2` with no failures
- [ ] `manage.py check` with no errors

### Expected evidence
- passing view tests
- passing project checks
- dashboards rendering with the new sections

### Output format
Code + tests + validation evidence.

## Scope
- Calendar services for the instructor dashboard data and the student history.
- Context of `InstructorHomeView` and `StudentHomeView`.
- The instructor dashboard template.
- The student dashboard template.
- Authorization adjustment so the student schedule route is also available to the instructor.
- CSS styles needed for the readability of the new sections.
- View tests for the new behaviors.

## Out of scope
- A new dedicated reports page.
- Exports/CSV.
- Schema changes.

## Impacted files
- `system/services/class_calendar.py`
- `system/views/home_views.py`
- `system/views/calendar_views.py`
- `templates/home/instructor/dashboard.html`
- `templates/home/student/dashboard.html`
- `static/system/css/portal/portal.css`
- `templates/base.html`
- `system/tests/test_views.py`

## Risks and edge cases
- An instructor with a class that has no session created for the day must see the class with zero check-ins.
- Cancelled/holiday sessions must keep the correct signaling.
- Special classes (open sessions) need to appear in the history when linked to the instructor/student.

## Rules and constraints
- SDD before code
- TDD for the implementation
- no hardcoding
- no error masking
- no migrations
- mandatory full reading
- mandatory validation

## Plan
- [x] 1. Context and full reading
- [ ] 2. Tests (Red)
- [ ] 3. Implementation (Green)
- [ ] 4. Refactoring (Refactor)
- [ ] 5. Full validation
- [ ] 6. Final cleanup
- [ ] 7. Documentation update

## Visual validation
### Desktop
- The instructor and student dashboards render the new sections without errors.

### Mobile
- Check the readability of the history cards/table.

### Browser console
- No critical JavaScript errors.

### Terminal
- No stack trace when opening the dashboards.

## ORM validation
### Database
- There is no schema change.

### Shell checks
- Not applicable beyond the view and service tests.

### Flow integrity
- Existing check-ins are reflected in the dashboards without changing the model.

## Quality validation
### No hardcoding
Data comes from dynamic session/check-in queries.

### No brittle conditional structures
Use of guard clauses and service composition.

### No `except: pass`
Not used anywhere.

### No error masking
Reuses the explicit handling that already exists.

### No unnecessary comments or docstrings
Keep the code self-explanatory.

## Evidence
(fill in after running tests/checks)

## Implemented
(fill in at the end)

## Deviations from plan
(fill in at the end)

## Pending
- Visual validation in a real browser (Playwright/browser) after the technical work is complete.
