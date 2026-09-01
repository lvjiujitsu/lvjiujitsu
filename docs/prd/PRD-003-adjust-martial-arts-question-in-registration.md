# PRD-003: Adjust the martial arts question during registration

## Summary of the implementation
Separate, in the registration wizard, the binary answer to the question `Já praticou arte marcial?` (`Have you practiced a martial art?`) from the choice of the practiced discipline, so that the interface shows `Sim` (`Yes`) and `Não` (`No`) as the primary answer and only asks for the discipline when the answer is `Sim` (`Yes`).

## Demand type
Targeted fix

## Current problem
The current field uses the discipline itself as the answer to the question `Já praticou arte marcial?` (`Have you practiced a martial art?`). This makes the empty option appear as `Não possui` (`None`), mixes two different intents in the same selector, and produces incorrect UX for a binary question.

## Goal
Display `Sim` (`Yes`) and `Não` (`No`) as the answer to the question about prior martial arts experience, show the discipline only when applicable, and keep the current belt/graduation validation consistent with the chosen discipline.

## Context Ledger
### Files read in full
- `CLAUDE.md`
- `system/forms/registration_forms.py`
- `templates/login/register.html`
- `static/system/js/auth/registration-wizard-clean.js`
- `system/services/registration_validation.py`
- `system/services/registration.py`
- `system/views/auth_views.py`
- `system/models/person.py`
- `system/tests/test_views.py`
- `system/tests/test_forms.py`
- `system/tests/test_models.py`

### Adjacent files consulted
- `system/urls.py`

### Internet / official documentation
- Not applicable. Local fix in existing code, with no dependency on an external API or temporarily unstable behavior.

### MCPs / tools verified
- shell / PowerShell — ok — full reading of the files in the flow

### Limitations found
- None in the initial diagnosis.

## Execution prompt
### Persona
Development agent specializing in monolithic Django with server-rendered templates, following SDD + TDD.

### Action
Implement the separation between the binary answer (`Sim`/`Não` — `Yes`/`No`) and the practiced discipline in the registration wizard's health record.

### Context
Public registration in `templates/login/register.html` uses `PortalRegistrationForm`, incremental validation through `RegistrationStepValidationView`, and UI behavior in `registration-wizard-clean.js`.

### Constraints
- no brittle hardcoding
- no error masking
- no migrations
- mandatory full reading
- mandatory validation
- preserve existing persistence in `Person.martial_art`

### Acceptance criteria
- [ ] The question `Já praticou arte marcial?` (`Have you practiced a martial art?`) must expose `Sim` (`Yes`) and `Não` (`No`) in the wizard (verifiable by: view test and visual validation)
- [ ] The practiced discipline must appear only when the answer is `Sim` (`Yes`) (verifiable by: visual validation)
- [ ] If the answer is `Sim` (`Yes`) and the discipline is `Jiu Jitsu`, the medical step must require a belt (verifiable by: validation route test)
- [ ] If the answer is `Não` (`No`), the backend must not require a discipline, belt, or graduation and must clear that data from the final payload (verifiable by: form test)

### Expected evidence
- passing tests
- clean browser console
- terminal with no stack traces
- `manage.py check` with no errors

### Output format
Implemented code + tests + validation evidence

## Scope
- add a binary prior-experience field to `PortalRegistrationForm`
- adjust the registration template to reflect the binary question + conditional discipline selector
- adjust the wizard JavaScript to show/hide discipline, belt, and graduation correctly
- adjust incremental validation and data cleanup in the backend
- update the flow's tests

## Out of scope
- changing the administrative person CRUD
- schema changes
- reviewing copy outside the public registration wizard

## Impacted files
- `docs/prd/PRD-003-adjust-martial-arts-question-in-registration.md`
- `system/forms/registration_forms.py`
- `system/services/registration_validation.py`
- `templates/login/register.html`
- `static/system/js/auth/registration-wizard-clean.js`
- `system/tests/test_views.py`
- `system/tests/test_forms.py`

## Risks and edge cases
- draft saved with the wizard's old payload
- additional dependents need to serialize the new binary answer
- clearing derived fields must not erase data when the answer stays `Sim` (`Yes`)

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
- validate the `/register/` screen with the question showing `Sim` (`Yes`) and `Não` (`No`)

### Mobile
- validate the same flow in a mobile viewport

### Browser console
- no critical JavaScript errors

### Terminal
- no stack traces

## ORM validation
### Database
- no schema change

### Shell checks
- not required if the tests cover payload cleanup and persistence remains unchanged

### Flow integrity
- persist `martial_art` only when there is a positive answer

## Quality validation
### No hardcoding
- keep answers and decisions coupled to the form's contract

### No brittle conditional structures
- use cleanup helpers and prefix-based decisions

### No `except: pass`
- do not introduce any

### No error masking
- keep validation messages explicit

### No unnecessary comments or docstrings
- do not introduce any

## Evidence
- `.\.venv\Scripts\python.exe manage.py test --verbosity 2` — 189 tests OK
- `.\.venv\Scripts\python.exe manage.py check` — no errors
- `.\.venv\Scripts\python.exe manage.py collectstatic --noinput` — OK
- `.\.venv\Scripts\python.exe manage.py showmigrations` — only `system.0001_initial`
- Playwright at `http://127.0.0.1:8000/register/` — desktop and mobile with the options `Selecione` (`Select`), `Sim` (`Yes`), `Não` (`No`); discipline hidden on `Não` (`No`); graduation visible for a non-Jiu Jitsu discipline; belt visible for `Jiu Jitsu`; console with no errors and no warnings

## Implemented
- Binary field `*_has_martial_art` in `PortalRegistrationForm`
- Discipline field separated from the binary field in the registration template
- Cleanup/validation rules in the backend for `Sim`/`Não` (`Yes`/`No`)
- Defensive compatibility with a legacy draft when a discipline is filled in without the binary flag
- View and form tests covering the new contract

## Deviations from plan
- None so far

## Pending
- None
