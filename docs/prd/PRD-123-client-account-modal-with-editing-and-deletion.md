# PRD-123: The client account modal with editing and deletion

## Summary
Turn the `Dados do cliente` ("Client data") modal into a functional account area, allowing the user to view and edit their own registration data and to close their own registration with a confirmation.

## Demand type
Django MVT + the authenticated home's UI.

## Current problem
The current modal shows only the basic data, the plan, and the dependents. It offers no real action to edit or delete/deactivate the registration, contradicting the expectation of managing one's own account.

## Goal
Add account actions to the home's modal:
- view the main data;
- edit the permitted personal data;
- delete/close one's own registration safely, preserving the financial and operational history.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/PRD-STANDARD.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `system/views/home_views.py`
- `system/views/person_views.py`
- `system/forms/person_forms.py`
- `system/models/person.py`
- `system/views/dependent_views.py`
- `system/services/portal_auth.py`

### Adjacent files consulted
- `templates/home/dashboard.html`
- `templates/dependents/dependent_edit.html`
- `templates/dependents/dependent_registration_done.html`
- `static/system/js/home/dashboard.js`
- `static/system/css/home/dashboard.css`
- `system/tests/test_home_dependents_section.py`
- `system/urls.py`
- `system/forms/dependent_forms.py`

### Internet / official documentation
- The official Django 5.2 documentation via Context7: form handling, the class-based `View`, session handling, and the test client.

### Context7 / MCPs / tools verified
- The Context7 Django docs resolved as `/websites/djangoproject_en_5_2`.
- The internal browser available for validation at `http://127.0.0.1:8000/home/`.

### Limitations found
- The physical deletion of a `Person` is dangerous in self-service because it can remove or conflict with the financial history, the check-ins, the monthly fees, the orders, and the audit trail. The user's action will be `encerrar cadastro` ("close registration"): `Person.is_active=False`, `PortalAccount.is_active=False`, and a session logout.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-ui-delivery`
- `lv-django-delivery`
- `lv-cleanup-audit`
- `browser:control-in-app-browser`

## Understanding approved
The current request authorizes the implementation: "fix the screen, it should be possible to view, edit, and delete the registration if you want to".

## Execution prompt
### Persona
The LV JIU JITSU Django/UI agent.

### Action
Implement account self-service in the home's modal.

### Context
The authenticated user is resolved through `request.portal_person`. The home already has a static modal with the client's data and a modal pattern for dependents.

### Constraints
- Edit only the permitted registration fields of one's own record.
- Do not allow changing the CPF, the person type, the plan, the monthly fee, the classes, or the operational roles through self-service.
- Deleting by the user means deactivating the registration and the access, preserving the history.
- The backend decides the permission and the state.
- No `innerHTML` with user data.
- Do not edit `staticfiles/`.

### Acceptance criteria
- [x] The modal shows an edit-registration action.
- [x] The modal shows a destructive delete/close-registration action with a confirmation.
- [x] The edit POST saves the permitted fields and returns per-field errors when invalid.
- [x] A user cannot edit or delete another registration.
- [x] Closing the registration deactivates the `Person` and the `PortalAccount`, clears the session, and redirects to the login.
- [x] The UI updates the visible data after saving, without navigating to another screen.
- [x] Tests cover the rendering, the editing, and the deletion/deactivation.
- [x] The internal browser validates the happy path and the protected destructive state.

### Expected evidence
- `python manage.py test system.tests.test_home_dependents_section...`
- `python manage.py check`
- The internal browser: the modal opens, the edit saves, the delete confirmation is visible.

### Output format
A short closing note with what was implemented, the evidence, the limitations, and the status.

## Scope
- A restricted form for the client's account.
- Authenticated POST views to update and deactivate one's own account.
- The client account URLs.
- The home's context with the form and the URLs.
- The modal with reading, editing, and a delete zone.
- The JS to toggle the panels, submit the edit, render the errors, and confirm the deletion.
- Responsive/themed CSS.
- The focused tests.

## Out of scope
- The physical deletion of a `Person`.
- The automatic cancellation of the Stripe/Asaas subscription.
- Changing the plan, the monthly fee, the classes, the operational roles, or the CPF.
- The administrative People CRUD.

## Impacted files
- `docs/prd/README.md`
- `docs/prd/PRD-123-client-account-modal-with-editing-and-deletion.md`
- `system/forms/person_forms.py`
- `system/forms/__init__.py`
- `system/views/home_views.py`
- `system/views/__init__.py`
- `system/urls.py`
- `system/tests/test_home_dependents_section.py`
- `templates/home/dashboard.html`
- `static/system/js/home/dashboard.js`
- `static/system/css/home/dashboard.css`

## Risks and edge cases
- A user with an active monthly fee closes their access, but the history remains for management.
- An invalid e-mail must return a per-field error.
- A double submit must keep a coherent state.
- The session must be terminated after the deactivation.
- The interface must not suggest that the financial data was erased.

## Rules and constraints
- `Person.is_active=False` makes the login invalid through the middleware.
- `PortalAccount.is_active=False` blocks a new local login.
- Self-service editing does not touch `person_type`, `cpf`, `class_enrollments`, `Membership`, `RegistrationOrder`, or `OperationalRole`.

## Visual hierarchy
- The header: the avatar, the name, the profiles, close.
- Block 1: the current data and the editing actions.
- Block 2: a collapsible edit form.
- Block 3: a delete zone with the impact text and a confirmation.

## Wireframe
### The modal
- The header: the avatar + the name + the badges + close.
- The `Dados atuais` ("Current data") region: CPF, e-mail, phone, date of birth, a short address, the plan, the dependents.
- The actions: `Editar cadastro` ("Edit registration") secondary, `Excluir cadastro` ("Delete registration") destructive.
- The `Editar cadastro` ("Edit registration") region: the fields in a grid; the `Salvar alterações` ("Save changes") and `Cancelar` ("Cancel") buttons.
- The `Excluir cadastro` ("Delete registration") region: a warning + a checkbox/textual confirmation + a destructive button.

## State machine
### The account modal
- `closed` -> `viewing` -> `editing` -> `saving` -> `saved` or `error`.
- `viewing` -> `delete-confirm` -> `deleting` -> `logged-out` or `error`.

## Plan
- [x] Create the focused tests.
- [x] Implement the restricted form.
- [x] Implement the POST views.
- [x] Update the URLs and the exports.
- [x] Update the modal, the CSS, and the JS.
- [x] Run the tests and the internal browser.

## Test plan
### Tests to author
- The home renders the account actions in the modal.
- The edit POST updates the name/e-mail/phone and preserves the CPF.
- An invalid POST returns a JSON 400 with a field error.
- The delete POST deactivates the person and the portal account and clears the session.

### Execution authorization
Authorized by the current operational request.

### Execution evidence
- The initial Red: the focused tests failed because of the missing modal routes/actions.
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_home_dependents_section.HomeDependentsSectionTestCase.test_home_uses_client_profile_modal_instead_of_large_header system.tests.test_home_dependents_section.HomeDependentsSectionTestCase.test_client_profile_update_changes_allowed_fields_and_preserves_cpf system.tests.test_home_dependents_section.HomeDependentsSectionTestCase.test_client_profile_update_returns_field_errors system.tests.test_home_dependents_section.HomeDependentsSectionTestCase.test_client_profile_deactivate_disables_person_account_and_session` -> OK, 4 tests.
- `.\.venv\Scripts\python.exe manage.py check` -> OK, no issues.
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_home_dependents_section system.tests.test_calendar` -> OK, 111 tests.

## Visual validation
- The internal browser at `http://127.0.0.1:8000/home/`.
- The modal opened with `Editar cadastro` ("Edit registration") and `Excluir cadastro` ("Delete registration").
- The editing opened inside the modal itself with the fields filled in.
- Saving the phone `(11) 97777-4455` updated the view without navigating and with no field errors.
- The delete zone opened a textual confirmation with `ENCERRAR` ("CLOSE"), the local route `/account/profile/deactivate/`, and a history-preservation notice; the real deletion was not executed in the visual validation.
- The internal browser's console with no errors.
- The mobile viewport `390x844`: the modal visible, 358px wide, with no horizontal overflow.
- After restarting the local server, the home loaded `dashboard.js?v=18`; the modal opened with the edit/delete actions and was closed without leaving `body.modal-open`.

## ORM validation
- `manage.py shell`: `Person(email='aluno.local.stripe.445521@example.com')` persisted the phone `(11) 97777-4455` and stayed `is_active=True` after the validation with no deletion.

## Quality validation
- `manage.py check`: OK.
- The focused account test: OK.
- The proportional suite `test_home_dependents_section` + `test_calendar`: OK.

## Evidence
- The restricted `ClientProfileForm` does not include the CPF, the roles, the plan, the monthly fee, or the classes.
- The POST views require a portal session and use only `request.portal_person`.
- The self-service deactivation uses `Person.is_active=False`, `PortalAccount.is_active=False`, and clears the session.
- The JS uses `textContent`/FormData/fetch and does not inject user data through `innerHTML`.

## Implemented
- The account modal with reading, editing, and a delete zone.
- The `account/profile/update/` and `account/profile/deactivate/` endpoints.
- Tests for the rendering, a valid edit, a field error, and the deactivation/logout.
- Responsive CSS for desktop/mobile and the themes.

## Cleanup findings
- The physical deletion and the automatic subscription cancellation remain out of scope for operational safety.

## Follow-up PRDs
None so far.

## Deviations from plan
None so far.

## Pending
- No pending item within this scope.
- A recommended follow-up, if desired: an administrative flow to reactivate a closed registration and to handle an active subscription after a self-service closure.

## Final status
Completed.
