# PRD-112: A pending request for administrative access

## Summary
Implement a complete flow for a person to request administrative access without automatically gaining permission. The request can start in the public registration or inside the authenticated portal, stays pending in an administrative queue, and only becomes a `Person`, `PortalAccount`, `PersonOperationalRole`, or `administrative-assistant` after the explicit approval of a person with administrative capability.

## Demand type
A backend feature + UI + an approval workflow + permission security.

## Current problem
- The public wizard only offers `Aluno` (`Student`) and `Responsável` (`Guardian`).
- The internal person registration allows changing the `PersonType` and the roles, but that is a direct administrative action, not an auditable request.
- There is no pending request entity for administrative access.
- PRD-111 can create fixtures with back-office people and students with an administrative upgrade, but those possibilities do not exist as an end-to-end validatable product flow.

## Goal
- Add an administrative access request on the registration screen and in the authenticated portal.
- Persist the request with a pending status, the personal data, the justification, the requested roles, and the origin.
- Create an administrative queue to approve, reject, cancel, and audit the requests.
- On approval, promote the person transactionally:
  - an existing person: keep the main relationship and add the approved operational roles;
  - a new person: create `Person`/`PortalAccount` with only the permitted access;
  - a full back-office person: use `PersonTypeCode.ADMINISTRATIVE_ASSISTANT` only when the approver marks that level.
- Ensure that no management permission is granted before the approval.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/PRD-STANDARD.md`
- `docs/prd/README.md`
- `docs/prd/PRD-040-payment-before-person-creation-registration-flow.md`
- `docs/prd/PRD-074-cumulative-operational-roles-and-permissions.md`
- `docs/prd/PRD-091-operational-role-ui-on-person-form.md`
- `docs/prd/PRD-111-staging-seeds-registration-nn.md`
- `system/constants.py`
- `system/models/person.py`
- `system/models/pre_registration.py`
- `system/views/auth_views.py`
- `system/views/portal_mixins.py`
- `system/views/home_views.py`
- `system/forms/person_forms.py`
- `system/services/pre_registration.py`
- `system/services/portal_capabilities.py`
- `system/urls.py`
- `templates/login/register.html`

### Adjacent files consulted
- `static/system/js/auth/register.js`
- `templates/home/dashboard.html`
- `system/views/person_views.py`
- `system/services/operational_roles.py`
- `system/tests/test_person_operational_roles_form.py`
- `system/tests/test_home_dashboard.py`

### Internet / official documentation
- Django 5.2 auth and access control: `https://docs.djangoproject.com/en/5.2/topics/auth/default/`
- Django 5.2 transactions: `https://docs.djangoproject.com/en/5.2/topics/db/transactions/`
- Django 5.2 testing tools: `https://docs.djangoproject.com/en/5.2/topics/testing/tools/`

### Context7 / MCPs / tools verified
- Context7 `/websites/djangoproject_en_5_2`: `LoginRequiredMixin`, `PermissionRequiredMixin`, custom permissions, `transaction.atomic`, and `RequestFactory` for view tests.

### Limitations found
- The current public wizard is a payment-before-creating-`Person` flow; the administrative request must not reuse payment nor create a person before the approval.
- `Person.person_type` remains singular; partial administrative access must prefer `PersonOperationalRole` and capabilities.
- If there is a schema change, the single baseline `system/migrations/0001_initial.py` must be regenerated locally during the implementation, per the project's protocol.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved
Authorized by the current request: generate PRDs to implement the missing conceptual features before PRD-111's staging pass.

## Execution prompt
### Persona
A senior Django engineer focused on authorization, pending workflows, and server-rendered administrative UI.

### Action
Implement a pending administrative access request workflow, with entry points in the public registration and in the portal, an administrative queue, transactional approval, and visual validation.

### Context
The system already has `PersonType`, `OperationalRole`, `PersonOperationalRole`, `PortalCapability`, `PreRegistration`, and `PortalSessionMiddleware`. The new feature must add a pending workflow without granting permission until the approval.

### Constraints
- No administrative permission before the approval.
- Do not create a `Person` from a public request before the approval.
- Do not reuse checkout/payment.
- UI in pt-BR; code and technical names in English.
- The backend is the source of truth; JavaScript only controls the experience.
- Every approval/rejection write inside `transaction.atomic`.
- Rejecting does not erase history.
- Approving does not duplicate a person by CPF.

### Acceptance criteria
- [x] The `/register/` screen shows a clear "Solicitar acesso administrativo" ("Request administrative access") option, separate from Student/Guardian.
- [x] A public request only writes a pending entity, without creating a `Person`, a `PortalAccount`, or an operational role.
- [x] A logged-in person can request administrative access through the portal without changing their current permission.
- [x] The request requires a name, CPF, e-mail, phone, justification, origin, and the requested roles.
- [x] An already-registered CPF links the request to the existing person, without duplicating the registration.
- [x] The administrative queue lists the pending requests with filters by origin, CPF, status, and date.
- [x] Only a person with `MANAGE_PEOPLE` or `MANAGE_ACADEMY` approves/rejects.
- [x] The approval allows choosing between specific operational roles and full administrative access.
- [x] Approving operational roles creates/updates `PersonOperationalRole` without improperly switching the `person_type` of a student/guardian/instructor.
- [x] Approving full administrative access creates or updates `Person.person_type=administrative-assistant` only when explicitly chosen.
- [x] A rejection records a reason and does not grant access.
- [x] The history appears in the person's detail and in the request queue.
- [ ] PRD-111 can visually validate a student with an administrative upgrade, a back-office-only person, and a back-office person who trains, using the real flow.

### Expected evidence
- Model/service/view tests for requesting, approving, and rejecting.
- Security tests ensuring the absence of permission before the approval.
- `manage.py check`.
- Desktop/mobile visual validation of the public registration, the requester's home, and the administrative queue.
- Local ORM proving the before/after of the approval.

### Output format
The implemented code, the tests, browser screenshots/evidence, and the PRD updated with the real results.

## Scope
- A new administrative request model, for example `AdministrativeAccessRequest`.
- Status enums: `pending`, `approved`, `rejected`, `canceled`.
- Origin: `public_registration`, `portal`, `admin_created`.
- Minimum fields: an optional existing person, personal data, a snapshot, the requested roles, the justification, the decider, the dates, the decision reason.
- Server-side forms for the public request, the authenticated request, and the administrative decision.
- Services to create, approve, reject, and cancel.
- Views/templates:
  - the entry point in the public registration;
  - the entry point in the portal/home;
  - the administrative queue;
  - the request detail;
  - the approve/reject modal/action.
- Operational auditing where available.
- Proportional tests and visual validation.

## Out of scope
- Approving a payment, a plan, or an enrollment.
- Real e-mail/WhatsApp delivery.
- Writing to staging/production.
- A general refactor of the public wizard.
- Creating a per-instructor class/schedule flow; that belongs to PRD-113.

## Impacted files
- `system/models/person.py` or a new model in `system/models/access_request.py`
- `system/models/__init__.py`
- `system/constants.py`
- `system/forms/access_request_forms.py`
- `system/services/access_requests.py`
- `system/views/access_request_views.py`
- `system/views/auth_views.py`
- `system/views/home_views.py`
- `system/urls.py`
- `templates/login/register.html`
- `static/system/js/auth/register.js`
- `templates/home/dashboard.html`
- `templates/access_requests/*`
- `system/tests/test_administrative_access_requests.py`
- `system/migrations/0001_initial.py` if there is a new schema

## Risks and edge cases
- Self-approval: the requester cannot approve their own request if they do not have the capability in force.
- A duplicate CPF: a public request must locate the existing person by normalized CPF.
- An existing person with a pending payment must not gain management by working around the financial block.
- A repeated pending request for the same CPF and type must be blocked or consolidated.
- A rejection must preserve the history for auditing.
- Partial administrative access must use an operational role; switching the `person_type` can break the student's personal area.
- Approving a new person with no password set requires a clear `PortalAccount` creation/activation flow.

## Rules and constraints
- MVT: the models persist, the forms validate the input, the services write, the views stay thin.
- `transaction.atomic` on approval/rejection.
- `select_for_update` when approving a pending request.
- Permission always in the backend, through `PortalCapability`.
- No business rule in the template/JS.
- No `except: pass`.
- Do not edit `staticfiles/`.

## Visual hierarchy
- The public registration: the new option must appear as a third functional card, but visually indicate "pendente de aprovação" ("pending approval"), not "acesso imediato" ("immediate access").
- The portal/home: a compact "Solicitações" ("Requests") block below the personal/management areas, with the current status.
- The administrative queue: a dense, operational table/list, with the status, the requester, the origin, the requested roles, the date, and the actions.
- The detail: the person's summary, the justification, the requested roles, the history, and the decision.

## Wireframe
### The public registration
```text
Como voce vai se cadastrar?
[Aluno] [Responsavel] [Solicitar acesso administrativo]

Solicitar acesso administrativo
- Nome completo
- CPF
- E-mail
- Telefone
- Area desejada: Pessoas / Turmas / Financeiro / Estoque / Graduacao / Gestao completa
- Justificativa
[Enviar solicitacao]
```

### The authenticated portal
```text
Solicitacoes
Status atual: nenhuma / pendente / aprovada / recusada
[Solicitar acesso administrativo]
```

### The administrative queue
```text
Solicitacoes administrativas
Filtros: status, origem, CPF, periodo
Linha: solicitante | CPF | origem | papeis | status | data | [Ver]
Detalhe: [Aprovar] [Reprovar] [Cancelar]
```

## State machine
```text
draft -> pending -> approved
draft -> pending -> rejected
pending -> canceled
approved/rejected/canceled -> terminal
```

### State rules
- `pending` grants no capability.
- `approved` requires a decider, a date, and an approved payload.
- `rejected` requires a reason.
- `canceled` is only allowed for the requester before the decision, or for a manager.

## Plan
1. [ ] Confirm the request's final modeling.
2. [ ] Write the Red tests for public creation without a `Person`.
3. [ ] Write the Red tests for an authenticated request without changing capabilities.
4. [ ] Write the Red tests for approval with `PersonOperationalRole`.
5. [ ] Write the Red tests for approval as a full back-office person.
6. [ ] Implement the model/forms/services.
7. [ ] Implement the views/templates/urls.
8. [ ] Adjust the wizard JS without displacing the student/guardian payment flow.
9. [ ] Visually validate the registration, the portal, and the queue.
10. [ ] Update the PRD with the real evidence.

## Test plan
### Tests to author
- `test_public_administrative_request_does_not_create_person`
- `test_existing_person_request_links_by_cpf_without_duplicate`
- `test_pending_request_does_not_add_capabilities`
- `test_approve_operational_roles_grants_expected_capabilities`
- `test_approve_full_administrative_sets_person_type_when_selected`
- `test_reject_request_keeps_person_unchanged`
- `test_only_manage_people_or_manage_academy_can_decide`
- `test_duplicate_pending_request_for_same_cpf_is_rejected`
- `test_cancel_pending_request_by_requester`
- `test_cannot_cancel_already_decided_request`
- `test_manager_can_open_queue_and_detail` / `test_non_manager_is_blocked_from_queue_and_detail` / `test_non_manager_cannot_approve_via_post`
- `test_requester_can_self_cancel` / `test_unrelated_person_cannot_self_cancel`
- `test_date_filter_narrows_queue`

### Execution authorization
Local, in Django's isolated test database. Local migrations authorized if the implementation requires a schema change.

### Execution evidence
- `2026-07-01`: `.\.venv\Scripts\python.exe manage.py test system.tests.test_administrative_access_requests system.tests.test_class_catalog_requests --verbosity 2` => 14 tests OK.
- `2026-07-01`: `.\.venv\Scripts\python.exe manage.py test system.tests.test_home_dashboard system.tests.test_register_wizard_contract system.tests.test_registration_flow system.tests.test_lv_foundation_classes system.tests.test_admin_hubs_contract --verbosity 2` => 21 tests OK.
- `2026-07-01`: `.\.venv\Scripts\python.exe manage.py makemigrations system --check --dry-run` => no changes detected.
- `2026-07-01`: `.\.venv\Scripts\python.exe manage.py check` => no issues.
- `2026-07-01` (fixing the limitations): `.\.venv\Scripts\python.exe clear_migrations.py` + `.\.venv\Scripts\python.exe manage.py makemigrations` (regenerated `0001_initial.py` with `extra_schedules` in `ClassCatalogRequest`; `AdministrativeAccessRequest` with no schema change).
- `2026-07-01`: `.\.venv\Scripts\python.exe manage.py test system.tests.test_administrative_access_requests system.tests.test_class_catalog_requests system.tests.test_administrative_access_request_views system.tests.test_class_catalog_request_views --verbosity 2` => 30 tests OK.
- `2026-07-01`: `.\.venv\Scripts\python.exe manage.py test --verbosity 1` => 391 tests OK (the full suite).
- `2026-07-01`: `.\.venv\Scripts\python.exe manage.py check` => no issues.
- `2026-07-01`: `.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run` => no changes detected.

## Visual validation
### Desktop
- [x] The public registration shows the third option without breaking the layout.
- [x] Submitting shows the pending request confirmation (the success message and the status change validated through real approve/cancel actions in the internal browser).
- [x] The portal shows the requests block and the queue links for a person with management.
- [x] The administrative queue renders the filters (status, origin, CPF, date) and the approval/rejection/cancellation detail.

### Mobile
- [x] The registration cards do not overlap the text.
- [x] The administrative queue becomes a scannable list (validated in the card generated in this delivery, a single-line layout per request).
- [x] The form and the home validated with no horizontal overflow; the "Cancelar" ("Cancel") button in the home's requests block validated at 375x812.

### Console
- [x] No critical JS error.
- [x] No relevant asset 404 on the screens navigated.

## ORM validation
- [x] Before the approval: the request exists, the person/roles were not created or changed.
- [x] After the operational approval: an active `PersonOperationalRole` exists.
- [x] After the full approval: `Person.person_type.code == administrative-assistant` only when chosen.
- [x] After the rejection: no new capability appears.

## Quality validation
- [x] `manage.py test system.tests.test_administrative_access_requests --verbosity 2`
- [x] `manage.py check`
- [x] A visual test with the internal browser.
- [x] A search for improper `person_type` comparisons in the new views (reviewed; the operational approval preserves `person_type` and only changes it when `grant_full_administrative` is explicit).

## Evidence
- The PRD was created on 2026-07-01 after reading the local contracts, mapping the current registration/roles flow, and consulting the official Django documentation recorded in the Context Ledger.
- `2026-07-01`: implemented the `AdministrativeAccessRequest` model, the forms, the transactional services, the views, the URLs, the templates, and the integration into the public registration and the authenticated home.
- `2026-07-01`: `makemigrations --check --dry-run` with no changes; the schema consolidated in `system/migrations/0001_initial.py`.
- `2026-07-01`: `manage.py check` OK.
- `2026-07-01`: 14 focused PRD-112/113 tests OK and 21 adjacent tests OK.
- `2026-07-01`: the internal browser validated `/register/admin-access/`, `/register/`, `/home/`, `/requests/admin-access/`, and `/requests/admin-access/create/` with no console errors.
- The visual evidence saved in `docs/prd/evidence/PRD-112-113-home-mobile.png`.
- `2026-07-01` (fixing the limitations): implemented `cancel_administrative_access_request`, `can_cancel_administrative_access_request`, the `AdministrativeAccessRequestSelfCancelView` view, the `requests/admin-access/<pk>/cancel/` route, and the "Cancelar" ("Cancel") button in the detail (the manager) and in the home (the requester).
- `2026-07-01`: the `date_from`/`date_to` filter added to `AdministrativeAccessRequestQueueView` and to the `access_requests/request_list.html` template.
- `2026-07-01`: `PersonDetailView` passes `access_request_history`/`class_request_history`; a new "Solicitações" ("Requests") section in `templates/people/person_detail.html`, visible only to `can_manage_people`.
- `2026-07-01`: a new file `system/tests/test_administrative_access_request_views.py` with 6 permission/cancellation/date-filter tests; all OK.
- `2026-07-01`: the internal browser validated the queue with the date filter, a real request cancellation (pending -> canceled status), the history in the person's detail (`/people/1/view/`), and the mobile "Solicitações" ("Requests") block (375x812) with a working "Cancelar" ("Cancel") button.
- `2026-07-01`: the full `manage.py test` suite (391 tests) OK after regenerating the migrations baseline.

## Implemented
- A persistent administrative request model with a status, an origin, the linked person, the decider, the requested/approved roles, and a pending-CPF constraint.
- A creation, approval, and rejection service with `transaction.atomic`, `select_for_update`, CPF normalization, and `person_type` preservation for the operational upgrade.
- The public `/register/admin-access/` flow, with no `Person` creation before the approval.
- The authenticated `/requests/admin-access/create/` flow.
- An administrative queue and detail with filters by status/origin/CPF/date and the approve/reject/cancel decision.
- The card integrated into `/register/` and the requests block into `/home/`.
- Controlled cancellation: by the requester themselves (a matching CPF) or by a manager with `MANAGE_PEOPLE`/`MANAGE_ACADEMY`, preserving the history through `decided_by`/`decided_at`/`decision_notes`.
- The history of administrative and class requests in the person's detail, restricted to `can_manage_people`.

## Cleanup findings
- A partial review run on 2026-07-01. No `staticfiles/` file was edited.
- The automated click on form buttons still does not fire a native POST in this internal browser (the same limitation recorded in the previous delivery); the fix was validated with `form.submit()` through `preview_eval` and with `system.tests.test_administrative_access_request_views`/`test_class_catalog_request_views` using the Django test client, which cover the real POST.

## Follow-up PRDs
- PRD-113 covers the class/schedule requests.
- PRD-111 must be used afterwards to run the staging pass on the administrative upgrade scenarios.

## Deviations from plan
- No material deviation in this fix; the items pending from the previous delivery were implemented within the PRD's original scope.

## Pending
- PRD-111 still needs to run the full visual staging pass for a student with an administrative upgrade, a back-office-only person, and a back-office person who trains, using the real flow (outside this fix's scope).

## Final status
Completed.
