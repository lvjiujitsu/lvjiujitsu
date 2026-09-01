# PRD-015: Initial graduation during registration

## Summary of the implementation
Ensure that students registered without prior jiu jitsu experience automatically receive the initial belt applicable to their age, with a real graduation recorded in the graduation module.

## Demand type
Targeted fix of a registration rule with automated tests.

## Current problem
The form correctly clears the martial arts data when the student states they have never trained, but the registration service only creates a graduation when a legacy belt is provided. As a result, beginner students can end up with no recorded graduation.

## Goal
When registering a holder student, a dependent, or a test persona with no jiu jitsu history, create an initial graduation at degree 0 using the first active belt compatible with their age.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `system/services/graduation.py`
- `system/services/registration.py`
- `system/models/graduation.py`
- `system/models/person.py`
- `system/forms/registration_forms.py`
- `system/tests/test_graduation.py`
- `system/tests/test_forms.py`
- `system/services/registration_checkout.py`
- `system/forms/__init__.py`
- `system/constants.py`
- `system/models/category.py`
- `system/models/__init__.py`
- `system/management/commands/seed_test_personas.py`

### Adjacent files consulted
- `system/services/seeding.py`
- `system/tests/test_views.py`
- `system/tests/*.py`

### Internet / official documentation
- Not applicable. The change uses local Django contracts and existing models.

### MCPs / tools verified
- PowerShell — OK — read commands executed.
- `.venv` Python — OK — version verified earlier in preflight.
- Django — OK — version verified earlier in preflight.

### Limitations found
- `rg` failed with access denied in this environment; queries were done with PowerShell.
- `system/services/seeding.py` and `system/tests/test_views.py` are large and had their output truncated in the interface; the directly impacted sections were consulted through contextual search.

## Execution prompt
### Persona
Development agent specializing in Django, following SDD + TDD + MVT.

### Action
Implement automatic initial graduation for students with no prior experience.

### Context
Public registration and the persona seeds create people and portal accounts. The graduation module already has `BeltRank`, `Graduation`, and rules, with no migration needed.

### Constraints
- no hardcoded fixed belt when an age-compatible initial belt exists
- no error masking
- no migrations
- mandatory full reading
- mandatory validation

### Acceptance criteria
- [ ] When registering an adult holder student with no experience, there must be an initial graduation at the adult white belt / degree 0.
- [ ] When registering a kids dependent with no experience, there must be an initial kids graduation / degree 0.
- [ ] A student with a declared history must keep the graduation imported from that history.
- [ ] Test personas created by the seed must receive a compatible initial graduation when there is no history.
- [ ] The form must keep clearing the manual data when the answer is `Não` (`No`).

### Expected evidence
- Focused tests passing.
- `manage.py check` passing.
- The Django suite passing.

### Output format
Implemented code + tests + validation evidence.

## Scope
Graduation/registration/seeding services and the related automated tests.

## Out of scope
Visual changes, migrations, new belts, changes to the registration wizard, and changes to tuition rules.

## Impacted files
- `system/services/graduation.py`
- `system/services/registration.py`
- `system/services/seeding.py`
- `system/tests/test_graduation.py`
- `docs/prd/PRD-015-initial-graduation-in-registration.md`

## Risks and edge cases
- A missing birth date prevents resolving the age.
- The absence of active belts prevents creating an initial graduation.
- Kids and adult belts overlap at ages 16/17; the ordering must pick the first compatible belt on record.

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
Not applicable initially, since there is no visual change.

### Mobile
Not applicable initially, since there is no visual change.

### Browser console
Not applicable initially.

### Terminal
- `.\.venv\Scripts\python.exe manage.py check` — OK.
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_forms system.tests.test_graduation --verbosity 2` — 32 tests OK.
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_models --verbosity 2` — 11 tests OK.
- `.\.venv\Scripts\python.exe manage.py test --verbosity 2` — 312 tests OK.

## ORM validation
### Database
Validated through the in-memory Django test database during the suite.

### Shell checks
`manage.py check` executed with no issues.

### Flow integrity
The registration form, the registration service, the test persona seed, and graduation progress are covered by tests.

## Quality validation
### No hardcoding
The initial belt is resolved through a dynamic query on active `BeltRank` records, using age and `display_order`.

### No brittle conditional structures
Implementation with guard clauses and small helpers.

### No `except: pass`
No `except: pass` introduced.

### No error masking
When there is no compatible initial belt, the service raises an explicit `ValueError`.

### No unnecessary comments or docstrings
No new comment or docstring was needed.

## Evidence
- Initial Red: the tests failed due to the absence of `ensure_initial_graduation_for_beginner`.
- Focused Green: `InitialGraduationRegistrationTestCase` passed with 5 tests.
- Persona seed: `TestPersonaInitialGraduationTestCase` passed.
- Full regression: `manage.py test --verbosity 2` passed with 312 tests.

## Implemented
- An initial-belt-by-age helper in `system/services/graduation.py`.
- Idempotent creation of an initial graduation for beginners.
- A hook in the real registration flow for student/dependent.
- Hooks in the seeds for personas and test registrations.
- Tests for an adult holder, another martial art without jiu jitsu, a kids dependent, prior history, idempotency, and test personas.

## Deviations from plan
No functional deviations. It was necessary to seed belts into the old registration fixtures so the mandatory rule had a catalog available.

## Pending
No pending items identified.
