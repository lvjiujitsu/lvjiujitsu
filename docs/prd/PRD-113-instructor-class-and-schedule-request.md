# PRD-113: An instructor's class and schedule request

## Summary
Implement a flow for instructors to request the creation of a new class, a new schedule in an existing class, or the onboarding of a new instructor with an initial schedule proposal. The request stays pending until a person with class management approves it, and the approval promotes the data into `ClassGroup`, `ClassSchedule`, `ClassInstructorAssignment`, and, where necessary, an instructor's `Person`/`PortalAccount`.

## Demand type
A backend feature + UI + an approval workflow + the calendar/classes.

## Current problem
- The system has an administrative CRUD for `ClassGroup` and `ClassSchedule`, but only the back office creates/edits them directly.
- Instructors have no flow to request a new schedule or a new class.
- A new instructor, still without a registration, cannot propose an initial schedule without manual admin intervention.
- PRD-111 has fixtures with instructors and classes, but cannot validate the real creation of those cases through a request/approval.

## Goal
- Allow requesting:
  - a new schedule in an existing class;
  - a new class with one or more schedules;
  - the registration of a new instructor with an initial class/schedule proposal.
- Create an approval queue for class managers.
- Promote an approved request into the real class/schedule catalog transactionally.
- Reject or cancel while keeping the history and the reason.
- Expose the request's status to the instructor/requester.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/PRD-STANDARD.md`
- `docs/prd/README.md`
- `docs/prd/PRD-074-cumulative-operational-roles-and-permissions.md`
- `docs/prd/PRD-091-operational-role-ui-on-person-form.md`
- `docs/prd/PRD-111-staging-seeds-registration-nn.md`
- `system/constants.py`
- `system/models/person.py`
- `system/models/class_group.py`
- `system/models/class_schedule.py`
- `system/models/class_membership.py`
- `system/forms/class_forms.py`
- `system/views/class_views.py`
- `system/views/home_views.py`
- `system/views/portal_mixins.py`
- `system/services/class_management.py`
- `system/services/class_catalog.py`
- `system/services/class_calendar.py`
- `system/services/portal_capabilities.py`
- `system/urls.py`

### Adjacent files consulted
- `templates/classes/class_group_list.html`
- `templates/classes/class_group_form.html`
- `templates/class_schedules/class_schedule_list.html`
- `templates/class_schedules/class_schedule_form.html`
- `templates/home/dashboard.html`
- `system/tests/test_calendar.py`
- `system/tests/test_lv_foundation_classes.py`
- `static/initial_data/seed_system_initial_class_catalog.json`

### Internet / official documentation
- Django 5.2 auth and access control: `https://docs.djangoproject.com/en/5.2/topics/auth/default/`
- Django 5.2 transactions: `https://docs.djangoproject.com/en/5.2/topics/db/transactions/`
- Django 5.2 testing tools: `https://docs.djangoproject.com/en/5.2/topics/testing/tools/`

### Context7 / MCPs / tools verified
- Context7 `/websites/djangoproject_en_5_2`: the use of authentication/permission mixins, `transaction.atomic`, custom permissions, and view tests.

### Limitations found
- `ClassSchedule` already has a unique constraint per class/day/style/time; additional room/capacity conflicts do not exist in the model today.
- `ClassGroup.main_teacher` requires `PersonTypeCode.INSTRUCTOR`; a new instructor must be created or approved before becoming the main instructor.
- The current class and schedule CRUD is administrative; the new flow must not release direct writes to an instructor.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved
Authorized by the current request: generate PRDs to implement the complete behavior before the later staging pass.

## Execution prompt
### Persona
A senior Django engineer focused on the class catalog, the calendar, approval workflows, and operational UI.

### Action
Implement pending class/schedule requests by an existing instructor or a new instructor, with administrative approval and transactional promotion into the real catalog.

### Context
`ClassGroup`, `ClassSchedule`, `ClassGroupForm`, `ClassScheduleForm`, and `save_class_group_catalog` already exist. The new feature must add a request workflow without allowing direct writes to the catalog until the approval.

### Constraints
- An instructor does not create `ClassGroup`/`ClassSchedule` directly.
- The approval is the only transition that writes to the real catalog.
- A manager with `MANAGE_CLASSES` or `MANAGE_ACADEMY` decides.
- A new instructor does not gain the instructor area before the approval.
- The request data must be auditable and preserved after the decision.
- UI in pt-BR, code in English.
- Server-side validation is mandatory.

### Acceptance criteria
- [x] A logged-in instructor sees a `Solicitar turma/horário` ("Request a class/schedule") action on the home.
- [x] A logged-in instructor can request a new schedule for a class where they act as the main/assistant instructor, or propose a new class.
- [x] A requester with no registration can submit a new-instructor proposal with personal data and an initial schedule.
- [x] A pending request neither creates nor changes a `ClassGroup` or a `ClassSchedule`.
- [x] The administrative queue lists the requests with the status, the instructor, the category, the class, the days/times, and the date.
- [x] The approver can adjust the payload before approving without editing the original request directly and untraceably.
- [x] Approving a new schedule creates a `ClassSchedule` linked to the correct class.
- [x] Approving a new class creates the `ClassGroup`, the schedule, and the teaching staff according to the approved payload.
- [x] Approving a new instructor creates the `Person` as an `instructor`, the `PortalAccount`, and the approved class/schedule links.
- [x] Rejecting records a reason and does not create a class/schedule/instructor.
- [x] Duplicate/conflicting requests show a clear error.
- [ ] PRD-111 can validate an instructor, an instructor with a dependent, and a new schedule request using the real flow.

### Expected evidence
- Service, form, and view tests.
- The local ORM before/after the approval.
- Desktop/mobile screenshots of the request and the queue.
- `manage.py check`.

### Output format
The implemented code, the tests, the visual validation, and the PRD updated with the real evidence.

## Scope
- A new request model, for example `ClassCatalogRequest`.
- Types:
  - `new_schedule`
  - `new_class_group`
  - `new_teacher_with_schedule`
- Statuses:
  - `pending`
  - `approved`
  - `rejected`
  - `canceled`
- A versioned JSON payload and normalized fields for the filters.
- Forms for an existing instructor, a new instructor, and the administrative decision.
- Services:
  - create the request;
  - validate the conflicts;
  - approve a new schedule;
  - approve a new class;
  - approve a new instructor;
  - reject/cancel.
- Views/templates:
  - the instructor's request form;
  - the public/protected new-instructor form;
  - my requests;
  - the administrative queue;
  - the detail/decision.
- Tests and visual validation.

## Out of scope
- Managing physical rooms.
- Real e-mail/WhatsApp notifications.
- Automatic payment/payout for the new instructor.
- Changing the check-in rules.
- The administrative access flow; that belongs to PRD-112.

## Impacted files
- `system/models/class_request.py` or `system/models/class_group.py`
- `system/models/__init__.py`
- `system/forms/class_request_forms.py`
- `system/services/class_requests.py`
- `system/views/class_request_views.py`
- `system/views/home_views.py`
- `system/views/class_views.py`
- `system/urls.py`
- `templates/class_requests/*`
- `templates/home/dashboard.html`
- `templates/classes/class_group_detail.html`
- `static/system/css/classes/*` if necessary
- `static/system/js/lv/*` or specific JS if necessary
- `system/tests/test_class_catalog_requests.py`
- `system/migrations/0001_initial.py` if there is a new schema

## Risks and edge cases
- An assistant instructor with `class-assistant` can request for a scoped class; they must not be able to request for any class.
- A new instructor may provide a CPF that already exists as a student/guardian; the approval must decide whether to promote the existing person to `instructor` or deny it.
- An already-existing schedule must be blocked before approving.
- The approver can change the schedule into a conflict; the final service must re-validate.
- Creating an active class with no active schedule must be forbidden, preserving the current `BaseClassGroupScheduleFormSet` rule.
- The partial approval of multiple schedules must be defined: either all enter, or none do.
- Cancelling cannot remove an already-approved class/schedule.

## Rules and constraints
- MVT: the forms validate, the services write, the views stay thin.
- `transaction.atomic` on the approval.
- `select_for_update` on the pending request during the decision.
- Reuse the existing validators/forms (`ClassGroupForm`, `ClassScheduleForm`) whenever possible.
- Do not duplicate an already-existing constraint rule.
- No `innerHTML` with user data if there is JS.
- Do not edit `staticfiles/`.

## Visual hierarchy
- The instructor's home: a small, operational action near the `Turmas de hoje` ("Today's classes") area, not a hero card.
- The request form: a dense layout with radios/a segmented control for the request type.
- The administrative queue: an operational list, filters at the top, the status in badges.
- The detail: the request's original data and the approved payload side by side when there is an adjustment.

## Wireframe
### The instructor's home
```text
Turmas de hoje
[Solicitar novo horario] [Solicitar nova turma]
Minhas solicitacoes: Pendente / Aprovada / Recusada
```

### An existing instructor's request
```text
Tipo de solicitacao
( ) Novo horario em turma existente
( ) Nova turma

Turma/Categoria
Dia, horario, estilo, duracao, capacidade
Justificativa operacional
[Enviar solicitacao]
```

### A new instructor
```text
Dados do professor
Nome, CPF, e-mail, telefone, faixa/experiencia
Proposta inicial
Categoria, turma, dia, horario, estilo, duracao
Justificativa
[Enviar proposta]
```

### The administrative queue
```text
Solicitacoes de turmas/horarios
Filtros: status, tipo, professor, categoria
Linha: tipo | professor | turma/categoria | horarios | status | data | [Ver]
Detalhe: [Aprovar] [Ajustar e aprovar] [Reprovar]
```

## State machine
```text
draft -> pending -> approved
draft -> pending -> rejected
pending -> canceled
approved/rejected/canceled -> terminal
```

### Promotion state
```text
pending request
  -> validate payload
  -> lock request
  -> create/update Person when needed
  -> create ClassGroup when needed
  -> create ClassSchedule(s)
  -> create ClassInstructorAssignment(s)
  -> mark approved
```

## Plan
1. [ ] Confirm the `ClassCatalogRequest`'s final modeling.
2. [ ] Write the Red tests for an existing instructor requesting a new schedule without changing the catalog.
3. [ ] Write the Red tests for approving a new schedule.
4. [ ] Write the Red tests for requesting/approving a new class with schedules.
5. [ ] Write the Red tests for a new instructor with an initial proposal.
6. [ ] Write the Red tests for the permissions and the conflicts.
7. [ ] Implement the models/forms/services.
8. [ ] Implement the views/templates/urls.
9. [ ] Integrate the call on the home/calendar.
10. [ ] Visually validate on desktop/mobile.
11. [ ] Update the PRD with the real evidence.

## Test plan
### Tests to author
- `test_instructor_request_new_schedule_does_not_create_schedule`
- `test_approve_new_schedule_creates_class_schedule`
- `test_instructor_cannot_request_for_unscoped_class_group`
- `test_new_class_group_request_approval_creates_group_and_schedules`
- `test_new_teacher_request_does_not_create_person_before_approval`
- `test_new_teacher_request_approval_creates_instructor_and_schedule`
- `test_reject_request_creates_no_catalog_records`
- `test_duplicate_schedule_conflict_is_blocked`
- `test_only_manage_classes_or_manage_academy_can_approve`
- `test_cancel_pending_request_by_requester`
- `test_cannot_cancel_already_decided_request`
- `test_new_class_group_request_with_extra_schedules_creates_all_slots`
- `test_extra_schedule_duplicate_within_request_is_blocked`
- `test_extra_schedules_not_allowed_for_new_schedule_request`
- `test_manager_can_open_queue_and_detail` / `test_instructor_without_manage_capability_is_blocked_from_queue_and_detail` / `test_instructor_cannot_approve_via_post`
- `test_requester_can_self_cancel` / `test_unrelated_person_cannot_self_cancel`

### Execution authorization
Local, in Django's isolated test database. Local migrations authorized if the implementation requires a schema change.

### Execution evidence
- `2026-07-01`: `.\.venv\Scripts\python.exe manage.py test system.tests.test_administrative_access_requests system.tests.test_class_catalog_requests --verbosity 2` => 14 tests OK.
- `2026-07-01`: `.\.venv\Scripts\python.exe manage.py test system.tests.test_home_dashboard system.tests.test_register_wizard_contract system.tests.test_registration_flow system.tests.test_lv_foundation_classes system.tests.test_admin_hubs_contract --verbosity 2` => 21 tests OK.
- `2026-07-01`: `.\.venv\Scripts\python.exe manage.py makemigrations system --check --dry-run` => no changes detected.
- `2026-07-01`: `.\.venv\Scripts\python.exe manage.py check` => no issues.
- `2026-07-01` (fixing the limitations): `.\.venv\Scripts\python.exe clear_migrations.py` followed by `.\.venv\Scripts\python.exe manage.py makemigrations` to add `extra_schedules` (a `JSONField`) to `ClassCatalogRequest`; the `0001_initial.py` baseline regenerated.
- `2026-07-01`: `.\.venv\Scripts\python.exe manage.py test system.tests.test_class_catalog_requests system.tests.test_class_catalog_request_views --verbosity 2` => 19 tests OK.
- `2026-07-01`: `.\.venv\Scripts\python.exe manage.py test --verbosity 1` => 391 tests OK (the full suite, after the migrations regeneration).
- `2026-07-01`: `.\.venv\Scripts\python.exe manage.py check` => no issues.
- `2026-07-01`: `.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run` => no changes detected.

## Visual validation
### Desktop
- [x] An existing instructor has an entry point on the home when they have the teaching/support area.
- [x] The admin sees the queue and the decision form, including the `Cancelar` ("Cancel") button.
- [x] An approved class/schedule is created by the service and is covered by the ORM/the test.
- [x] The new-instructor form and the existing-class form show up to 4 `Horários adicionais` ("Additional schedules") rows with a per-row label, without breaking the layout.
- [x] The `Solicitar novo horário` ("Request a new schedule") button appears on the schedule page (`/calendar/`) next to `Criar aulão` ("Create open class") when the user has `SUPPORT_CLASSES`.

### Mobile
- [x] The request form has no horizontal overflow.
- [x] The administrative queue in a mobile list shows a clear status and clear actions (validated at 375x812).

### Console
- [x] No critical JS error.
- [x] No relevant asset 404 on the screens navigated.

## ORM validation
- [x] Before the schedule approval: no `ClassSchedule` exists for the payload.
- [x] After the schedule approval: the `ClassSchedule` exists and the request is `approved`.
- [x] Before the new-instructor approval: no `Person` exists for the given CPF.
- [x] After the new-instructor approval: `Person.person_type.code == instructor`, the `PortalAccount` exists, and the class/schedule exist.
- [x] A rejection creates no catalog records.

## Quality validation
- [x] `manage.py test system.tests.test_class_catalog_requests --verbosity 2`
- [x] `manage.py check`
- [x] The internal browser on desktop/mobile.
- [x] A search for direct catalog writes in a request view outside the service (reviewed; `ClassGroup`/`ClassSchedule` are still written only in `system/services/class_requests.py`).

## Evidence
- The PRD was created on 2026-07-01 after reading the local contracts, mapping the current class/schedule CRUD, and consulting the official Django documentation recorded in the Context Ledger.
- `2026-07-01`: implemented the `ClassCatalogRequest` model, the forms, the transactional services, the views, the URLs, the templates, the public instructor proposal, and the authenticated class/schedule request.
- `2026-07-01`: `makemigrations --check --dry-run` with no changes; the schema consolidated in `system/migrations/0001_initial.py`.
- `2026-07-01`: `manage.py check` OK.
- `2026-07-01`: 14 focused PRD-112/113 tests OK and 21 adjacent tests OK.
- `2026-07-01`: the internal browser validated `/register/teacher-proposal/`, `/home/`, `/requests/classes/`, and `/requests/classes/create/` on desktop and mobile with no console errors.
- The visual evidence saved in `docs/prd/evidence/PRD-112-113-home-mobile.png`.
- `2026-07-01` (fixing the limitations): implemented `cancel_class_catalog_request`, `can_cancel_class_catalog_request`, the `ClassCatalogRequestSelfCancelView` view, the `requests/classes/<pk>/cancel/` route, and the `Cancelar` ("Cancel") button in the detail (the manager) and on the home (the instructor/requester).
- `2026-07-01`: implemented the `extra_schedules` (JSON) field on `ClassCatalogRequest`; `create_existing_teacher_class_request`/`create_new_teacher_class_request` accept up to 4 additional schedules, validated for duplicates and blocked for `NEW_SCHEDULE`; `_approve_new_class_group` creates one `ClassSchedule` per additional schedule, re-validating the conflict at approval time.
- `2026-07-01`: the `ClassCatalogExtraScheduleFormSet` formset integrated into `ExistingTeacherClassCatalogRequestCreateView` and `PublicNewTeacherClassCatalogRequestCreateView`; the `class_requests/request_form.html` and `class_requests/new_teacher_form.html` templates render the labeled extra rows.
- `2026-07-01`: the `Solicitar novo horário` ("Request a new schedule") button added in `templates/calendar/calendar.html`, conditioned on `show_instructor_area` (which already requires `SUPPORT_CLASSES`, the same capability required by the creation view).
- `2026-07-01`: a new file `system/tests/test_class_catalog_request_views.py` with 5 permission/cancellation tests; all OK.
- `2026-07-01`: the internal browser validated the queue/detail with a real cancellation and approval, the new-instructor form with 4 additional schedule rows rendered and labeled, the button on the schedule page, and the mobile queue (375x812) legible.
- `2026-07-01`: the full `manage.py test` suite (391 tests) OK after regenerating the migrations baseline.

## Implemented
- A persistent catalog request model with the type, the origin, the status, the instructor/created person, the target/created class, the approved payload, the decider, the dates, and the additional schedules (`extra_schedules`).
- Creation, approval, rejection, and cancellation services with `transaction.atomic`, `select_for_update`, teaching-scope validation, and schedule conflict blocking (including between the additional schedules).
- An existing-instructor flow for a new schedule in an existing class or a new class, with up to 4 additional schedules in the same new-class request.
- The public `/register/teacher-proposal/` flow for a new instructor with an initial schedule and optional additional schedules.
- An administrative queue and detail with payload adjustment before approving/rejecting/cancelling.
- The public card integrated into `/register/`, the authenticated action into `/home/`, and a shortcut on the schedule page (`/calendar/`).
- Controlled cancellation: by the request's instructor/requester or by a manager with `MANAGE_CLASSES`/`MANAGE_ACADEMY`.

## Cleanup findings
- A partial review run on 2026-07-01. No `staticfiles/` file was edited.
- The automated click on form buttons still does not fire a native POST in this internal browser (the same limitation recorded in the previous delivery); the fix was validated with `form.submit()` through `preview_eval` and with `system.tests.test_class_catalog_request_views` using the Django test client, which covers the real approval/rejection/cancellation POST.
- The approver still cannot edit the additional schedules at decision time (only the main schedule is editable); documented as intentional scope to keep the decision simple in this fix.

## Follow-up PRDs
- PRD-112 covers the administrative access request.
- PRD-111 must validate the scenarios after the implementation.

## Deviations from plan
- No material deviation in this fix; the items pending from the previous delivery were implemented within the PRD's original scope.
- The additional schedules are limited to 4 per request (5 in total including the main one) and are not individually editable by the approver in this delivery; adjusting them requires rejecting and resubmitting.

## Pending
- Allow the approver to edit/remove the additional schedules individually before approving (today only the main schedule is adjustable in the decision).
- PRD-111 still needs to run the full visual staging pass for an instructor, an instructor with a dependent, and a new schedule request using the real flow (outside this fix's scope).

## Final status
Completed.
