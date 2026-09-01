# PRD-026: Responsive redesign of People

## Summary of the implementation
Reimplement the presentation of the People screens to make the list, detail, form, and deletion more readable on phones and computers, preserving every existing feature, per-profile permissions, and light/dark theme support.

## Demand type
UI refactoring with documentation regeneration and functional validation.

## Current problem
The People screens concentrate a lot of data in visual blocks with little hierarchy. In long forms, the identity, health, martial art, relationship, and payout fields appear as a single sequence, making them hard to use on phones and computers. The list also does not make clear the scope shown to back-office staff and instructors.

## Goal
- Present People with a modern, responsive visual hierarchy aligned with the LV standard.
- Preserve the light/dark theme through the existing variables.
- Split the form into functional blocks without hiding fields.
- Keep the list as a quick entry point to the modal view, editing, and deletion according to permission.
- Keep the detail with the summary, finance, classes, schedules, and teaching activity.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `docs/prd/PRD-025-responsive-redesign-of-the-lv-system.md`
- `system/views/person_views.py`
- `system/forms/person_forms.py`
- `system/models/person.py`
- `system/selectors/person_selectors.py`
- `templates/people/person_list.html`
- `templates/people/person_detail.html`
- `templates/people/person_form.html`
- `templates/people/person_confirm_delete.html`
- `templates/person_types/person_type_list.html`
- `templates/person_types/person_type_detail.html`
- `templates/person_types/person_type_form.html`
- `templates/person_types/person_type_confirm_delete.html`
- `templates/base.html`
- `static/system/css/portal/portal.css`
- `static/system/css/portal/class-catalog.css`
- `static/system/css/portal/person-detail.css`
- `system/tests/test_views.py`
- `system/tests/test_forms.py`

### Adjacent files consulted
- `system/tests/seed_helpers.py`
- The file listings under `static/`, `templates/`, and `system/tests/`

### Internet / official documentation
- Not applicable at this stage; the change uses the project's existing Django templates and CSS.

### MCPs / tools verified
- PowerShell — available — reading with `Get-Content`
- ripgrep — available — mapping files and tests with `rg`
- Django test runner — OK — `manage.py test`, `manage.py check`
- Browser/Playwright — OK — desktop/mobile visual validation at `http://127.0.0.1:8000/people/`

### Limitations found
- Do not create new folders; the PRD uses the existing `docs/prd/`, and the CSS will be created in the existing `static/system/css/portal/`.
- No migrations.
- Do not change permission rules, financial rules, or class rules at this stage.

## Execution prompt
### Persona
Development agent specializing in Django MVT, following SDD + TDD + mobile-first CSS.

### Action
Implement the responsive redesign of the People screens according to the spec below.

### Context
People and Types are the registration core of the LV Jiu Jitsu portal. A person may represent a student, dependent, instructor, or back-office member, and each profile must preserve its features without relying on fields hidden in the frontend.

### Constraints
- no hardcoded business rules
- no error masking
- no migrations
- do not create new folders
- do not move features into JavaScript
- CSS separated per screen/namespace under `static/`
- templates with no central business rules
- mandatory validation

### Acceptance criteria
- [ ] The People list must show a contextual header, filters, responsive cards, status, CPF, type, classes, and the permitted actions.
- [ ] The list's View action must open a modal on the screen itself, without navigating to an extra screen.
- [ ] Back-office staff must see every person and the View, Edit, and Delete actions.
- [ ] The instructor must see only the people permitted by the current contract and must not receive administrative actions.
- [ ] The form must group fields into Identity, Health, Martial art, Relationship, and Payout without removing existing fields.
- [ ] Payout must appear only when the view permits payout fields.
- [ ] The detail must keep the Summary, Finance for back-office staff, Enabled classes, Enabled schedules, and Teaching activity.
- [ ] The deletion screen must keep a POST confirmation with CSRF and an evident destructive action.
- [ ] The layout must work on mobile and desktop with no overlap or clipped text.
- [ ] The light/dark theme must keep using the global variables.

### Expected evidence
- passing automated tests
- `manage.py check` with no errors
- `collectstatic --noinput` with no errors
- a browser with no critical JavaScript errors
- desktop and mobile visual validation

### Output format
Implemented code + tests + validation evidence.

## Scope
- `PersonForm` only to expose field groups to the template.
- Templates in `templates/people/`.
- CSS in `static/system/css/portal/`.
- Contract tests in `system/tests/`.
- The PRD documentation.

## Out of scope
- Changing the data model.
- Changing existing permissions.
- Changing finance, payments, classes, or payouts.
- Redesigning every screen in the system at this stage.
- Creating migrations.

## Impacted files
- `docs/prd/PRD-026-responsive-redesign-of-people.md`
- `system/forms/person_forms.py`
- `system/tests/test_forms.py`
- `system/tests/test_views.py`
- `templates/people/person_list.html`
- `templates/people/person_detail.html`
- `templates/people/person_form.html`
- `templates/people/person_confirm_delete.html`
- `static/system/css/portal/people.css`
- `static/system/js/shared/people-list.js`

## Risks and edge cases
- Long forms on a phone may hide fields when the grouping is wrong.
- The list may lose teaching context if it removes labels hydrated by the view.
- Administrative actions must not appear for the instructor.
- Class checkboxes must remain usable by touch.
- Financial tables must preserve horizontal scrolling when necessary.

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
- [x] 2. UI contracts and modeling
- [x] 3. Tests (Red)
- [x] 4. Implementation (Green)
- [x] 5. Refactoring (Refactor)
- [x] 6. Full validation
- [x] 7. Final cleanup
- [x] 8. Documentation update

## Visual validation
### Desktop
OK. Playwright at 1622x1411 confirmed:
- usable `.content-shell` width: 1480px;
- the filter at 101px tall;
- the filter with 6 columns in the main row;
- 4 cards in the first row;
- no horizontal overflow.

### Mobile
OK. Playwright at 390x900 confirmed a screen with no horizontal overflow and card metadata in compact rows.

### Browser console
OK. No console errors captured during the Playwright validation.

### Terminal
OK. The validation commands ran with no stack traces.

## ORM validation
### Database
There is no schema change.

### Shell checks
`manage.py showmigrations system` confirmed `0001_initial` applied; no migration was created.

### Flow integrity
OK. The People list, detail, and form opened with a real back-office user from the local environment.

## Quality validation
### No hardcoding
OK. The change only adds visual structure and field groups derived from existing `PersonForm` names.

### No brittle conditional structures
OK. No new business rule was introduced.

### No `except: pass`
OK. No `except: pass` introduced.

### No error masking
OK. No new silent handling.

### No unnecessary comments or docstrings
OK.

## Evidence
- Initial Red:
  - `manage.py test system.tests.test_forms.PersonFormLayoutContractTestCase --verbosity 2` failed due to the absence of `identity_fields`.
  - `manage.py test system.tests.test_views.PortalViewTestCase.test_people_screens_render_responsive_contract_sections --verbosity 2` failed due to the absence of `people.css`.
- Green:
  - `manage.py test system.tests.test_forms.PersonFormLayoutContractTestCase system.tests.test_views.PortalViewTestCase.test_people_screens_render_responsive_contract_sections --verbosity 2` — OK.
  - `manage.py test system.tests.test_forms system.tests.test_views --verbosity 2` — 76 tests OK.
  - `manage.py test --verbosity 2` — 263 tests OK before the final visual refinement.
  - `manage.py check` — OK.
  - `manage.py showmigrations system` — OK.
  - `manage.py collectstatic --noinput` — OK.
  - `git diff --check` — OK.
  - Playwright desktop/mobile — OK.

## Implemented
- Field groups in `PersonForm` for Identity, Health, Martial art, Relationship, and Payout.
- A reusable partial template for Person fields.
- A list with a wider desktop width, a compact filter, and responsive cards.
- Quick Person viewing in a modal opened from the list itself.
- A detail with its own hero, preserved administrative actions, and an operational summary.
- Deletion with a dedicated confirmation panel.
- Dedicated CSS in `static/system/css/portal/people.css`.
- Person editing reviewed as an editing flow, not a lookup:
  - removed the duplicated person summary, LV progression, and technical history from the editing screen;
  - kept only the fields the Person form edits directly;
  - the Tatame flow restored with the question `Já praticou arte marcial?` (`Have you practiced a martial art?`) and, when the answer is yes, the discipline, graduation/level, belt, degrees, jiu jitsu start date, previous last graduation, and previous academy in the same block;
  - the official graduation, technical history, finance, and other related CRUDs remain in their own flows.
  - the form sections follow a sequential expandable pattern, with no side-by-side layout.

## Additional evidence on 2026-05-16
- Red:
  - `manage.py test system.tests.test_forms.PersonFormLayoutContractTestCase system.tests.test_views.PortalViewTestCase.test_people_screens_render_responsive_contract_sections --verbosity 2` failed because editing exposed neither the martial history nor the recorded progression.
- Green:
  - `manage.py test system.tests.test_forms.PersonFormLayoutContractTestCase system.tests.test_views.PortalViewTestCase.test_people_screens_render_responsive_contract_sections --verbosity 2` — OK.
  - `manage.py test system.tests.test_forms system.tests.test_views.PortalViewTestCase.test_people_screens_render_responsive_contract_sections system.tests.test_views.PortalViewTestCase.test_person_update_saves_payroll_config_for_instructor --verbosity 2` — 5 tests OK.
  - `manage.py check` — OK.
  - `manage.py collectstatic --noinput` — OK.
- Browser at `http://localhost:8000/people/6/edit/` authenticated as a technical admin:
    - desktop: 6 expandable sections, a single-column form, no duplicated summary, no duplicated progression panel, no horizontal overflow, no console errors;
    - mobile 390x900: 6 expandable sections, a single-column form, a visible expand/collapse icon, no horizontal overflow, no console errors.
- Browser at `http://localhost:8000/people/6/edit/`:
    - the Tatame section contains the martial experience question and the 7 detail fields in the same block;
    - when `Não` (`No`) is selected, the 7 detail fields become hidden and disabled;
    - no console errors.

## Deviations from plan
The final visual refinement compacted the filters and card metadata after the user's annotation in the browser.
A new user annotation required extending the editing screen with martial history and recorded progression topics, without changing the schema.

## Pending
No known technical pending items at this stage.
