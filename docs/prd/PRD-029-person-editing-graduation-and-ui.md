# PRD-029: Person editing with a proportional UI and graduation context

## Summary of the implementation
Rethink the person editing screen to remove stretched fields, improve the relationship/classes section, and display compact context for the official graduation and teaching activity without turning the screen into a full detail view. Update the instructor seed to load a fictional technical graduation history.

## Demand type
UI refactoring with a seed adjustment and documentation regeneration.

## Current problem
The editing screen uses overly wide sections, disproportionate fields, and a class list in long-form text. Instructors appear with no official technical history while editing, even though they are people with a graduation. The instructor seed does not record a complete graduation history.

## Goal
- Make the editing form more compact, sequential, and proportional.
- Keep editing focused on the person's data, without operating graduation/finance CRUDs inside the screen.
- Show compact context for the official graduation with a visual belt and a recent history.
- Show teaching context for instructors without mixing it with a student's enabled classes.
- Update the instructor seed with an idempotent graduation history.

## Context Ledger
### Files read in full
- `CLAUDE.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `docs/prd/PRD-028-home-and-people-in-full-screen.md`
- `system/forms/person_forms.py`
- `system/views/person_views.py`
- `system/models/graduation.py`
- `system/services/graduation.py`
- `system/management/commands/seed_system_initial_teacher.py`
- `system/management/commands/seed_system_initial_administrative.py`
- `static/initial_data/initial_teachers.json`
- `static/initial_data/initial_administrative.json`
- `system/management/commands/seed_system_initial_administrative.py`
- `static/initial_data/belt_ranks.json`
- `templates/people/person_form.html`
- `templates/people/_person_field.html`
- `templates/graduation/_belt_visual.html`
- `static/system/css/portal/people.css`
- `system/tests/test_views.py`
- `system/tests/test_graduation.py`

### Adjacent files consulted
- `system/constants.py`
- `system/urls.py`
- `templates/graduation/_progress_card.html`
- `templates/graduation/_history_modal.html`

### Internet / official documentation
- Not applicable; the change uses the existing Django templates, CSS, and models.

### MCPs / tools verified
- PowerShell — OK.
- Django test runner — OK.
- Browser/Playwright — OK.

### Limitations found
- No migrations.
- No new folders.
- The workspace already has many local changes; the implementation must preserve what is already there.

## Execution prompt
### Persona
Development agent specializing in Django MVT, following SDD + TDD + operational responsive CSS.

### Action
Reimplement the `people/person_form.html` screen for proportional editing and add an instructor graduation history to the seed.

### Context
Editing a person must change the record, health record, declared martial art, relationship, enabled classes, and payout. The official graduation history and teaching activity appear as compact context with links to their own flows.

### Constraints
- no hardcoded business rules in the template
- no migrations
- do not create folders
- do not remove existing fields
- CSS under `static/`
- templates under `templates/`
- an idempotent seed
- mandatory visual validation

### Acceptance criteria
- [ ] The editing screen must not duplicate a summary card with name/CPF/type/status/access when those data are already editable fields.
- [ ] Ordinary fields must have a proportional width on desktop and stack on a phone.
- [ ] Textareas and long lists must have a controlled width and an appropriate height.
- [ ] The relationship section must differentiate editing the type/status from selecting enabled classes.
- [ ] Enabled classes must appear as compact, readable options and not as disproportionate running text.
- [ ] Instructors must show teaching activity context when there is a class/schedule.
- [ ] People with a `Graduation` must show the current official graduation and a recent history while editing.
- [ ] Create/edit/remove graduation actions stay in the Graduation CRUD, reached through a link.
- [ ] The instructor seed must record an idempotent history up to the requested belt/degree.
- [ ] The light/dark theme must preserve contrast.
- [ ] Desktop and mobile must have no horizontal overflow.

## Scope
- `docs/UI-SCREEN-CONTRACT.md`
- `docs/prd/PRD-029-person-editing-graduation-and-ui.md`
- `templates/people/person_form.html`
- `static/system/css/portal/people.css`
- `system/views/person_views.py`
- `system/management/commands/seed_system_initial_teacher.py`
- `static/initial_data/initial_teachers.json`
- `system/tests/test_views.py`
- `system/tests/test_graduation.py`

## Out of scope
- Creating a new graduation screen.
- Changing the schema or migrations.
- Changing graduation rules.
- Changing permissions.

## Impacted files
- `docs/UI-SCREEN-CONTRACT.md`
- `docs/prd/PRD-029-person-editing-graduation-and-ui.md`
- `templates/people/person_form.html`
- `templates/plans/plan_form.html`
- `static/system/css/portal/people.css`
- `system/views/person_views.py`
- `system/management/commands/seed_system_initial_teacher.py`
- `static/initial_data/initial_teachers.json`
- `system/tests/test_views.py`
- `system/tests/test_graduation.py`

## Risks and edge cases
- Confusing a student's `class_groups` with an instructor's teaching activity.
- Duplicating the history when the seed is run again.
- Blowing out the layout with long class and schedule names.
- Hiding required fields on mobile.

## Rules and constraints
- SDD before code.
- TDD for the implementation.
- No hardcoded secrets.
- No migrations.
- Mandatory full reading.
- Mandatory validation.

## Plan
- [x] 1. Context and full reading.
- [x] 2. Update the screen's contract tests.
- [x] 3. Implement the graduation context in the view.
- [x] 4. Reimplement the editing template.
- [x] 5. Adjust the responsive CSS.
- [x] 6. Update the instructor seed.
- [x] 7. Validate tests/check/collectstatic.
- [x] 8. Validate the desktop/mobile browser.

## Visual validation
### Desktop
OK. `http://localhost:8000/people/6/edit/` at 1440x1000:
- no horizontal overflow;
- a layout with the form and a side context (`1004px 380px`);
- main fields with a controlled width of 420px;
- the official graduation displayed with 6 recent history items;
- console with no errors.

### Mobile
OK. `http://localhost:8000/people/6/edit/` at 390x900:
- no horizontal overflow;
- the graduation context moves above the form;
- main fields with a controlled width of 336px;
- console with no errors.

### Browser console
OK. 0 errors in the validated mobile and desktop scenarios.

### Terminal
OK. No stack trace during the seeds, tests, and validation.

## ORM validation
### Database
OK. The `seed_system_initial_teacher` seed was run locally after `seed_system_initial_belt_ranks`, creating a graduation history for the 5 instructors.

### Shell checks
OK. An automated test confirms the seed's idempotency and each instructor's current belt/degree.

### Flow integrity
OK. The form preserves the existing POST, and the graduation context is read-only.

## Quality validation
### No hardcoding
OK. The fictional histories live in the seed's JSON; the template consumes data from the model.

### No brittle conditional structures
OK. The view uses the existing graduation services and relationship hydration.

### No `except: pass`
OK.

### No error masking
OK. The seed fails explicitly when the required belt does not exist.

## Evidence
- Initial Red:
  - `test_people_screens_render_responsive_contract_sections` failed due to the absence of `Acesso e turmas` (`Access and classes`).
  - `test_teacher_seed_creates_requested_graduation_histories_idempotently` failed because the instructors had no official graduation.
- Focused Green:
  - `manage.py test system.tests.test_views.PortalViewTestCase.test_people_screens_render_responsive_contract_sections system.tests.test_graduation.InitialTeacherSeedGraduationTestCase.test_teacher_seed_creates_requested_graduation_histories_idempotently --verbosity 2` — OK.
- Full validation:
  - `manage.py test --verbosity 2` — 276 tests OK.
  - `manage.py check` — OK.
  - `manage.py collectstatic --noinput` — OK.
  - `git diff --check` — OK, only CRLF warnings.

## Implemented
- A Person editing screen with a proportional layout and no duplicated summary card.
- Compact context for the current official graduation and a recent history.
- Compact teaching activity context for instructors.
- `Turmas liberadas` (`Enabled classes`) rendered as a compact options panel.
- An instructor seed with an idempotent history:
  - Lauro: black belt, degree 2.
  - Andre: black belt, degree 1.
  - Layon: black belt, degree 1.
  - Vanessa: brown belt, degree 4.
  - Vinicius: black belt, degree 0.
- The instructor and back-office seeds now fill in record data consistent with manual editing: blood type, allergies, previous injuries, emergency contact, martial art, jiu jitsu start date, previous last graduation, and previous academy.
- A regression contract adjustment in `templates/plans/plan_form.html` to keep `Cadastrar plano` (`Register plan`).

## Deviations from plan
During the full suite, an existing `plan_form.html` contract failed because the template rendered `Novo plano` (`New plan`) where the test requires `Cadastrar plano` (`Register plan`). The fix was applied without changing any business rule.

## Pending
No known pending items for this stage.
