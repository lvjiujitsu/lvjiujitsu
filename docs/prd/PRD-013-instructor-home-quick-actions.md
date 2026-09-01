# PRD-013: Instructor quick actions on the home

## Summary of the implementation
Add quick actions to the `Aulas do dia` (`Today's classes`) card on the instructor home to:
- cancel or reactivate a regular class linked to the authenticated instructor
- create an open class for the current day without opening the schedule screen

## Demand type
New UI/flow feature.

## Current problem
The instructor has to open `Gerir cronograma` (`Manage schedule`) to cancel a class for the day or to create an open class. This adds unnecessary navigation to an operational and urgent task.

## Goal
Allow the instructor to perform the most frequent daily actions directly on the home, preserving the permissions and services the schedule already has.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `lvjiujitsu/settings.py`
- `templates/home/instructor/dashboard.html`
- `templates/calendar/instructor_calendar.html`
- `templates/calendar/admin_calendar.html`
- `templates/base.html`
- `system/views/home_views.py`
- `system/views/calendar_views.py`
- `system/views/__init__.py`
- `system/urls.py`
- `system/services/class_calendar.py`
- `system/forms/class_forms.py`
- `system/models/calendar.py`
- `system/tests/test_calendar.py`
- `system/tests/test_views.py`
- `static/system/css/portal/portal.css`

### Adjacent files consulted
- `docs/prd/`
- `system/models/category.py`
- `system/models/class_catalog.py` through existing imports
- `system/services/__init__.py` through existing tests

### Internet / official documentation
- Not applicable. The implementation reuses Django endpoints and native JavaScript already present in the project.

### MCPs / tools verified
- PowerShell — ok — file reading and local commands.
- `.venv` — ok — Python 3.12.10.
- Django — ok — 4.1.13.
- Browser Use — limited — `node_repl` returned "No active Codex browser pane available".
- Playwright — ok — desktop/mobile functional validation run at `http://127.0.0.1:8000/home/instructor/`.

### Limitations found
- The worktree already carries many unrelated changes; this delivery must preserve that state.
- `rg` was not used because it failed on permissions in a previous run in this environment; inspection was done with PowerShell.
- The full suite did not end 100% green due to 3 errors outside this flow: the payout rules seed and payroll tests blocked by birth-date validation.

## Execution prompt
### Persona
Development agent specializing in Django 4.1, following SDD + TDD + server-rendered MVT.

### Action
Implement quick actions in the `Aulas do dia` (`Today's classes`) card on the instructor home.

### Context
The project already has:
- `InstructorToggleSessionView` to cancel/reactivate the instructor's own class session
- `InstructorSpecialClassCreateView` to create an open class linked to the authenticated instructor
- `get_today_classes_for_instructor` as the source of the home's listing

### Constraints
- no new migration
- no hardcoded duration/title; use `settings`
- no error masking
- do not create business rules in the template
- preserve the server-side permissions of the existing endpoints
- validate in a browser

### Acceptance criteria
- [x] The instructor home must show a `Criar aulão` (`Create open class`) button in the `Aulas do dia` (`Today's classes`) card.
- [x] Clicking `Criar aulão` (`Create open class`) must open a compact form with today's date, title, time, duration, and notes.
- [x] Submitting the form must create the open class for the authenticated instructor.
- [x] A regular class linked to the instructor must show a `Cancelar` (`Cancel`) button when it is active.
- [x] A cancelled regular class must show a `Reativar` (`Reactivate`) button.
- [x] A class cancelled by a holiday must not expose `Reativar` (`Reactivate`) as though it were a manual cancellation.
- [x] The actions must use CSRF and the existing authenticated endpoints.
- [x] The JavaScript must live in a separate static file, versioned in the template.
- [x] The versioned `portal.css` must be updated when there is a visual change.

### Expected evidence
- an automated test of the home rendering with quick actions
- an automated test of the data required in the home service
- `manage.py test --verbosity 2`
- `manage.py check`
- `manage.py collectstatic --noinput`
- `manage.py showmigrations`
- visual/functional validation in a desktop and mobile browser
- browser console with no critical JavaScript errors

### Output format
Implemented code + tests + validation evidence.

## Scope
- `system/services/class_calendar.py`
- `system/views/home_views.py`
- `templates/home/instructor/dashboard.html`
- `static/system/js/home/instructor-dashboard.js`
- `static/system/css/portal/portal.css`
- `templates/base.html`
- `system/tests/test_calendar.py`
- `docs/prd/PRD-013-instructor-home-quick-actions.md`

## Out of scope
- Changing calendar rules outside the current day.
- Creating editing/removal of an open class from the home.
- Changing the schedule CRUD.
- Creating migrations.

## Impacted files
- `system/services/class_calendar.py`
- `system/views/home_views.py`
- `templates/home/instructor/dashboard.html`
- `static/system/js/home/instructor-dashboard.js`
- `static/system/css/portal/portal.css`
- `templates/base.html`
- `system/tests/test_calendar.py`
- `docs/prd/PRD-013-instructor-home-quick-actions.md`

## Risks and edge cases
- A regular class without a `ClassSession` yet must still be cancellable; the endpoint creates the session when cancelling.
- A class cancelled by a holiday must not be reactivated from the home.
- An assistant instructor linked through `ClassInstructorAssignment` must remain authorized.
- Permission errors must keep being blocked in the backend.
- If an open class is created with an invalid time, the form must show the error without masking it.

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
- [x] 2. Contracts and modeling
- [x] 3. Tests (Red)
- [x] 4. Implementation (Green)
- [x] 5. Refactoring (Refactor)
- [x] 6. Full validation
- [x] 7. Final cleanup
- [x] 8. Documentation update

## Visual validation
### Desktop
Playwright in a 1366x900 viewport:
- login with a temporary instructor
- the home opened at `/home/instructor/`
- the `Criar aulão` (`Create open class`) button visible
- the collapsible form opened
- an open class created from the home
- the `Cancelar` (`Cancel`) and `Reativar` (`Reactivate`) buttons visible according to state
- console with no critical errors

### Mobile
Playwright in a 390x844 viewport:
- the `Criar aulão` (`Create open class`) button visible
- the collapsible panel opened
- `scrollWidth` smaller than `innerWidth`, no horizontal overflow
- console with no critical errors

### Browser console
No `error` or `pageerror` entries in the Playwright validations.

### Terminal
The local server responded `200` at `http://127.0.0.1:8000/home/instructor/`.

## ORM validation
### Database
No schema change. No migration created.

### Shell checks
Temporary validation data created and removed through the ORM:
- `Person.cpf='920.000.800-01'`
- `ClassGroup.code='codex-home-actions-group'`
- `ClassCategory.code='codex-home-actions'`
- a `SpecialClass` linked to the temporary instructor

Cleanup confirmed `False False False False` for residual existence.

### Flow integrity
Creating an open class uses `InstructorSpecialClassCreateView`, which links `teacher` to the authenticated instructor.
Cancellation/reactivation uses `InstructorToggleSessionView`, preserving `assert_instructor_owns_schedule`.

## Quality validation
### No hardcoding
The open class's default title and duration come from `settings.SPECIAL_CLASS_DEFAULT_TITLE` and `settings.SPECIAL_CLASS_DEFAULT_DURATION_MINUTES`.

### No brittle conditional structures
The template only decides whether to expose actions, using flags coming from the service (`is_special`, `is_holiday_cancelled`, `is_cancelled`).

### No `except: pass`
Not introduced.

### No error masking
The JavaScript shows the error returned by the backend when the response is not `ok`; the endpoints keep returning an explicit HTTP status.

### No unnecessary comments or docstrings
No comments/docstrings were added to the feature's code.

## Evidence
- `manage.py test system.tests.test_calendar.CheckinApprovalServiceTestCase.test_today_classes_for_instructor_exposes_quick_action_identifiers --verbosity 2` — passed.
- `manage.py test system.tests.test_calendar.InstructorHomeQuickActionsViewTestCase.test_instructor_dashboard_exposes_quick_schedule_actions --verbosity 2` — passed.
- `manage.py test system.tests.test_calendar --verbosity 2` — 46 tests, passed.
- `manage.py check` — no issues.
- `node --check static/system/js/home/instructor-dashboard.js` — passed.
- `manage.py showmigrations` — migrations applied up to `system.0001_initial`.
- `git diff --check` — no whitespace errors; only Windows LF/CRLF warnings.
- `manage.py collectstatic --noinput` — 3 files copied, 161 unchanged.
- `manage.py test --verbosity 2` — 298 tests run, 295 ok, 3 errors outside the flow.

## Implemented
- `get_today_classes_for_instructor` now exposes `schedule_id`, `session_date`, `is_holiday_cancelled`, and `special_id`.
- The instructor home received a `Criar aulão` (`Create open class`) button and a collapsible form in the `Aulas do dia` (`Today's classes`) card.
- Active regular classes show `Cancelar` (`Cancel`); manually cancelled classes show `Reativar` (`Reactivate`).
- Classes cancelled by a holiday do not show the reactivation action.
- The home's inline JavaScript was replaced by `static/system/js/home/instructor-dashboard.js`.
- CSS for the quick panel and buttons was added to `portal.css`, with the versioning updated in `base.html`.
- A service test and a home rendering test were added to `system/tests/test_calendar.py`.

## Deviations from plan
- The JavaScript file ended up at `static/system/js/home/instructor-dashboard.js`, following the existing home scripts folder, instead of `static/system/js/portal/instructor-home.js`.
- Visual validation used Playwright MCP because Browser Use did not find an active pane in Codex.
- The full suite failed with 3 payroll/seed errors outside the flow that was changed.

## Pending
- Fix the 3 global errors outside this scope if the goal is a 100% green full suite:
  - `test_seed_class_catalog_creates_default_payroll_rules`
  - `test_calculates_fixed_monthly_plus_student_percentage_rules`
  - `test_calculates_per_class_attendance_rule`
