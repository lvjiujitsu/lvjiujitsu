# PRD-122: Undoing a student's pending check-in

## Summary
Allow a student to undo a check-in made by mistake while the attendance is still pending the instructor's approval.

## Demand type
Django MVT + the student home's UI.

## Current problem
On the home, after the student clicks `Check-in`, the card switches to `Aguardando aprovação` ("Awaiting approval") and offers no action to undo it. That creates an incorrect pending attendance when the click was accidental.

## Goal
Add the cancellation of one's own pending check-in for a regular class and an open class, keeping the block for an approved attendance.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/PRD-STANDARD.md`
- `docs/UI-SCREEN-CONTRACT.md`

### Adjacent files consulted
- `system/services/class_calendar.py`
- `system/views/calendar_views.py`
- `system/urls.py`
- `system/views/__init__.py`
- `system/tests/test_calendar.py`
- `templates/home/dashboard.html`
- `templates/home/partials/today_classes_section.html`
- `static/system/js/home/dashboard.js`
- `static/system/css/home/dashboard.css`
- `system/services/trial_access.py`
- `system/models/trial_access.py`

### Internet / official documentation
- The official Django 5.2 documentation via Context7: class-based views, `JsonResponse`, a test client JSON POST, and session-based tests.

### Context7 / MCPs / tools verified
- The Context7 Django docs resolved as `/websites/djangoproject_en_5_2`.
- The internal browser available for validation at `http://127.0.0.1:8000/home/`.

### Limitations found
- There is no persisted link between a check-in and the trial class grant it consumed; restoring the trial when undoing would require additional modeling and stays out of this patch.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`
- `browser:control-in-app-browser`

## Understanding approved
The user's current request authorizes the fix: "fix it because on the screen it's not possible to undo the check-in, sometimes the student may have clicked by accident".

## Execution prompt
### Persona
The LV JIU JITSU Django/UI agent.

### Action
Implement the cancellation of a pending check-in by the student themselves on the home.

### Context
The student's check-in creates a `ClassCheckin` or a `SpecialClassCheckin` with the `PENDING` status. Instructors approve it later. The student needs to undo it only while it is pending.

### Constraints
- The backend decides the permission and the state.
- Do not allow cancelling an approved attendance.
- Do not edit `staticfiles/`.
- Do not use `innerHTML` with user data.
- UI in pt-BR.

### Acceptance criteria
- [x] A pending regular class shows the undo action next to the status.
- [x] A pending open class shows the same action.
- [x] Cancelling removes only the logged-in student's pending check-in.
- [x] An approved attendance returns an error and stays intact.
- [x] The absence of a check-in returns a clean response with no 500 error.
- [x] The UI allows `Check-in` again after a successful cancellation.
- [x] A focused test covers the service and the endpoint.
- [ ] The internal browser validates the real flow.

### Expected evidence
- `python manage.py test system.tests.test_calendar...`
- `python manage.py check`
- The internal browser: before/after the `Desfazer` ("Undo") button.

### Output format
A short closing note with what was implemented, the evidence, the limitations, and the status.

## Scope
- A pending cancellation service for a regular class and an open class.
- Authenticated JSON views for the student.
- The canonical URLs.
- The data exposed by the home's selector.
- The home's template, CSS, and JS.
- The focused tests.

## Out of scope
- Cancelling an already-approved attendance.
- Editing an approved history.
- Restoring a consumed trial class.
- Changing the instructor's approval flow.

## Impacted files
- `docs/prd/README.md`
- `docs/prd/PRD-122-undo-pending-student-checkin.md`
- `system/services/class_calendar.py`
- `system/views/calendar_views.py`
- `system/views/__init__.py`
- `system/urls.py`
- `system/tests/test_calendar.py`
- `templates/home/dashboard.html`
- `templates/home/partials/today_classes_section.html`
- `static/system/js/home/dashboard.js`
- `static/system/css/home/dashboard.css`

## Risks and edge cases
- An approved check-in cannot be removed by the student.
- The endpoint must not accept cancelling another person's check-in.
- If the session does not exist yet, the response must be clean.
- A double click on undo must be idempotent.

## Rules and constraints
- `PENDING` is cancellable.
- `APPROVED` is immutable for the student.
- A cancelled class does not change the rule for cancelling a pending attendance.

## Plan
- [x] Create the focused tests.
- [x] Implement the transactional service.
- [x] Implement the views and the URLs.
- [x] Expose the flags in the selector.
- [x] Adjust the UI and the JS.
- [x] Validate the tests and the rendering in the internal browser.

## Test plan
### Tests to author
- The service cancels a pending `ClassCheckin`.
- The service blocks an approved `ClassCheckin`.
- The service cancels a pending `SpecialClassCheckin`.
- The regular class view returns success.
- The view for an approved attendance returns a 400 error.
- The home renders `js-cancel-checkin` for a pending one.

### Execution authorization
Authorized by the current operational request.

### Execution evidence
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_calendar` -> OK, 100 tests.
- `.\.venv\Scripts\python.exe manage.py check` -> OK, no issues.
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_home_dependents_section system.tests.test_calendar` -> OK, 111 tests.

## Visual validation
- The internal browser at `http://127.0.0.1:8000/home/`: the confirmed row did not show `Desfazer` ("Undo"); two pending rows showed `Aguardando aprovação Desfazer` ("Awaiting approval Undo").
- A real cancellation click in the internal browser was not completed in this round because the visual interaction was interrupted/slow after the account modal's validation; the backend and the rendering are covered by tests.

## ORM validation
- The service tests confirm the removal of pending `ClassCheckin` and `SpecialClassCheckin` records and the block on an approved attendance.

## Quality validation
- `manage.py check`: OK.
- `system.tests.test_calendar`: OK.
- The proportional suite `test_home_dependents_section` + `test_calendar`: OK.

## Evidence
- The `cancel_student_checkin` and `cancel_student_special_class_checkin` services remove only the logged-in student's pending attendance.
- The JSON views return success for a pending one and a 400 error for an approved one.
- The template renders `js-cancel-checkin` only when the check-in is pending and cancellable.

## Implemented
- The `Desfazer` ("Undo") button for pending check-ins in regular classes and open classes.
- The `aulas/checkin/cancelar/` and `aulas/aulao/checkin/cancelar/` endpoints.
- A JS update of the row so it returns to the `Check-in` state after a success.
- Service, view, and rendering tests.

## Cleanup findings
- Restoring a consumed trial class remains out of scope and stays as a follow-up.

## Follow-up PRDs
- The traceable restoration of a consumed trial class when a pending check-in is undone.

## Deviations from plan
None so far.

## Pending
- A real cancellation click in the internal browser still needs to be repeated in a dedicated visual round.

## Final status
Completed, with a visual limitation.
