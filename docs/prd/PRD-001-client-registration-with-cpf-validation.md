# PRD-001: Client registration with CPF validation

## Summary

Implement the client registration flow with CPF validation, persistence through a service, and visual feedback for the user.

## Demand type

New feature

## Current problem

The system does not provide client registration. There is no CPF validation, structured persistence, or visual feedback for the user.

## Goal

Allow the user to register a client with a name, email address, and valid CPF while receiving success or error feedback. The flow must follow MVT with services, TDD, and complete validation.

---

## Context Ledger

### Files read in full
- `system/models/__init__.py`
- `system/models/client_models.py`
- `system/forms/__init__.py`
- `system/views/__init__.py`
- `system/urls.py`
- `templates/base.html`
- `settings.py`

### Adjacent files consulted
- `system/services/__init__.py`
- `system/tests/__init__.py`
- `static/system/css/`
- `static/system/js/`

### Internet / official documentation
- Django Forms: docs.djangoproject.com/en/4.1/topics/forms/
- CPF validation: official algorithm (mod 11)

### MCPs / tools verified
- Playwright — working — `python -c "from playwright.sync_api import sync_playwright; print('OK')"`
- Context7 — working — the Django Forms query returned a result

### Limitations found
- None

---

## Execution prompt

### Persona
Development agent specializing in Python + Django 4.1, following SDD + TDD + MVT with services.

### Action
Implement the complete client registration flow with CPF validation, including the model, form with `clean_cpf`, creation service, thin view, template extending `base.html`, namespaced CSS, tests by layer, and visual validation.

### Context
This is the system's first registration flow. The `Client` model does not exist yet. Registration will be available through the `/clientes/cadastrar/` route. The system uses the single `system/` app with an MVT + services architecture. The local SQLite database is disposable.

### Constraints
- No hardcoded validation rules — validate CPF through the algorithm
- No error masking — raise an explicit exception on failure
- No migrations — create the model without generating a migration
- Mandatory full reading of the flow's files
- Mandatory visual validation through Playwright
- No unnecessary comments or docstrings
- Clean code, small functions, and guard clauses

### Acceptance criteria
- [ ] When a valid CPF is submitted with a name and email address, the client is created and a success message is displayed (verifiable by: test + shell check + visual validation)
- [ ] When an invalid CPF is submitted, the form returns a specific error on the CPF field (verifiable by: test + visual validation)
- [ ] When a duplicate CPF is submitted, the form returns a uniqueness error (verifiable by: test + visual validation)
- [ ] When an empty form is submitted, required-field errors are displayed (verifiable by: test + visual validation)
- [ ] The `/clientes/cadastrar/` route returns 200 for GET and processes POST (verifiable by: test)
- [ ] The template extends `base.html` and uses `{% csrf_token %}` (verifiable by: inspection)
- [ ] CSS lives in `static/system/css/client_form.css`, with no inline CSS (verifiable by: inspection)
- [ ] The browser console has no JavaScript errors (verifiable by: Playwright)
- [ ] The terminal has no stack traces (verifiable by: inspection)

### Expected evidence
- `manage.py test --verbosity 2` → 0 failures, 0 errors
- `manage.py check` → no errors
- `manage.py collectstatic --noinput` → no errors
- Shell check: `Client.objects.filter(cpf='12345678909').exists()` → True
- Playwright screenshot of the registration screen
- Clean browser console

### Output format
Implemented code + tests by layer + validation evidence + final cleanup

---

## Scope

- Model `Client` (name, email, cpf)
- `ClientForm` form with `clean_cpf()`
- Service `create_client()`
- View `client_create_view`
- `/clientes/cadastrar/` URL
- Template `clients/client_form.html`
- CSS `static/system/css/client_form.css`
- Tests: `test_models`, `test_forms`, `test_services`, `test_views`

## Out of scope

- Client listing
- Client editing
- Client deletion
- Authentication
- Permissions

## Impacted files

| Action | File |
|---|---|
| Create | `system/models/client_models.py` |
| Create | `system/forms/client_forms.py` |
| Create | `system/services/client_service.py` |
| Create | `system/views/client_views.py` |
| Edit | `system/urls.py` |
| Create | `templates/clients/client_form.html` |
| Create | `static/system/css/client_form.css` |
| Create | `system/tests/test_models.py` |
| Create | `system/tests/test_forms.py` |
| Create | `system/tests/test_services.py` |
| Create | `system/tests/test_views.py` |

## Risks and edge cases

- Formatted CPF (periods and hyphen) versus digits only → accept both and normalize to digits only
- CPF with all digits equal (`111.111.111-11`) → reject
- Duplicate email address → allow it (the same email address may be associated with different CPFs)
- Brazilian Portuguese encoding in error messages → ensure UTF-8

---

## Rules and constraints

- SDD: this PRD is the specification — code is derived from it
- TDD: write failing tests (Red) → implement (Green) → refactor (Refactor)
- MVT: business logic in the service, thin view, form validates input
- No hardcoding — validate CPF through the algorithm
- No error masking — use explicit exceptions
- No migrations — project policy
- Mandatory full reading
- Mandatory visual validation

## Plan

- [ ] 1. Context and full reading of existing files
- [ ] 2. `Client` model with fields and constraints
- [ ] 3. Model tests (Red)
- [ ] 4. `ClientForm` form with `clean_cpf()`
- [ ] 5. Form tests (Red)
- [ ] 6. `create_client()` service with `@transaction.atomic`
- [ ] 7. Service tests (Red)
- [ ] 8. Minimum implementation needed for the tests to pass (Green)
- [ ] 9. `client_create_view` view + URL
- [ ] 10. View tests (Red → Green)
- [ ] 11. Template inheritance + namespaced CSS
- [ ] 12. Refactoring (Refactor)
- [ ] 13. Complete validation (tests + check + collectstatic + visual + ORM)
- [ ] 14. Final cleanup
- [ ] 15. Documentation update

---

## Visual validation

### Desktop
- [ ] The form renders correctly
- [ ] Labels are in Brazilian Portuguese
- [ ] Error messages appear on the fields
- [ ] A success message appears after registration

### Mobile
- [ ] Responsive layout works correctly

### Browser console
- [ ] No JavaScript errors
- [ ] No 404 responses for static assets

### Terminal
- [ ] No stack traces
- [ ] No critical warnings

## ORM validation

### Database
- [ ] `Client.objects.count()` returns the expected count after registration

### Shell checks
- [ ] `Client.objects.filter(cpf='12345678909').exists()` → True
- [ ] `Client.objects.filter(cpf='00000000000').exists()` → False

### Flow integrity
- [ ] Registration creates exactly one record
- [ ] CPF is stored without formatting (digits only)

## Quality validation

### No hardcoding
- [ ] CPF is validated through the algorithm, not a list

### No brittle conditional structures
- [ ] Guard clauses are used instead of cascades

### No `except: pass`
- [ ] Specific exceptions have clear messages

### No error masking
- [ ] Validation errors are propagated to the user

### No unnecessary comments or docstrings
- [ ] Code is self-explanatory

---

## Evidence
> (complete at the end with actual results)

## Implemented
> (complete at the end)

## Deviations from plan
> (complete at the end)

## Pending
> (complete at the end)
