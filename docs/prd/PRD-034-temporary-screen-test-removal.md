# PRD-034: Temporary removal of screen tests

## Summary of the implementation
Temporarily remove the automated tests coupled to screens/templates that are being reimplemented.

## Demand type
Targeted fix

## Current problem
The suite was failing with 5 failures and 109 errors due to old UI contracts, missing templates, and screen routes that are being reimplemented.

## Goal
Keep the domain, services, models, forms, commands, and seeds suite green while the screens are recreated.

## Context Ledger
### Files read in full
- `CLAUDE.md`
- `system/urls.py`
- `system/views/home_views.py`
- `system/views/person_views.py`
- `templates/login/login_form.html`
- `system/tests/test_views.py`
- `system/tests/test_plan_views.py`
- `system/tests/test_product_views.py`
- `system/tests/test_class_portal_views.py`

### Adjacent files consulted
- `system/tests/test_calendar.py`
- `system/tests/test_graduation.py`
- the `templates/` listing

### Internet / official documentation
- Not applicable.

### MCPs / tools verified
- PowerShell — status ok — running tests and checks.

### Limitations found
- Automated screen coverage was temporarily removed by the user's decision.

## Execution prompt
### Persona
Django development agent following SDD + test-based validation.

### Action
Remove the old UI/view tests and preserve the domain tests.

### Context
The screens will be reimplemented; the old tests validated HTML, templates, and routes that no longer represent the current contract.

### Constraints
- no migrations
- do not delete the services/models/forms/commands tests
- validate the suite after the removal

### Acceptance criteria
- [x] The old screen tests removed.
- [x] The domain tests preserved.
- [x] `python manage.py test --verbosity 2` passes.
- [x] `python manage.py check` passes.

### Expected evidence
- A green suite.
- A green check.

### Output format
A summary of the removed tests and the evidence.

## Scope
- Remove test files exclusively covering views/screens.
- Remove the view/dashboard classes in mixed files.

## Out of scope
- Reimplementing screens.
- Creating new UI tests.
- Changing views/templates.

## Impacted files
- `system/tests/test_views.py`
- `system/tests/test_plan_views.py`
- `system/tests/test_product_views.py`
- `system/tests/test_class_portal_views.py`
- `system/tests/test_calendar.py`
- `system/tests/test_graduation.py`

## Risks and edge cases
- Visual regressions will not be caught until the new screen tests are recreated.
- HTTP flows have less coverage temporarily.

## Rules and constraints
- no migrations
- mandatory validation
- preserve the tests unrelated to the UI

## Plan
- [x] 1. Capture the suite's current failures.
- [x] 2. Identify the tests coupled to the UI.
- [x] 3. Remove the screen tests.
- [x] 4. Run the full suite.
- [x] 5. Run the check.

## Visual validation
Not applicable; a test removal.

## ORM validation
Not applicable.

## Quality validation
### No hardcoding
Not applicable.

### No brittle conditional structures
Not applicable.

### No `except: pass`
Not introduced.

### No error masking
The old failures were removed by the user's explicit decision during the reimplementation of the screens.

### No unnecessary comments or docstrings
Not introduced.

## Evidence
- `python manage.py test --verbosity 2`: 157 tests, OK.
- `python manage.py check`: no issues.

## Implemented
- Removed the view/screen test files.
- Removed the view/dashboard classes in `test_calendar.py` and `test_graduation.py`.

## Deviations from plan
- None.

## Pending
- Recreate new screen tests after the screens are reimplemented.
