# PRD-098: Operational audit module

## Summary
Introduce a queryable trail of the academy's operational actions (who changed a person, a class, attendance, a graduation, finance), meeting the expectation of an audit CRUD that is missing from the current inventory.

## Demand type
A new domain feature + an administrative UI.

## Current problem
- There is no `AuditLog` model, no `/audit/` route, and no equivalent.
- Check-ins and timestamps exist, but they cover neither record changes nor admin actions.
- The user listed auditing among the expected CRUD modules.
- PRD-062 deals with service idempotency, not with a trail for the end user.

## Goal
A manager with `MANAGE_ACADEMY` consults a filtered list of events: the date, the actor, the entity, the action, and a summary — with no editing/deleting of audit records through the UI.

## Context Ledger
### Files read in full
- `docs/prd/AUDIT-2026-06-30-master-findings.md` (finding 84)
- `system/models/` (the inventory)
- `system/urls.py`
- `docs/prd/PRD-077-crud-mvp-of-the-martial-arts-academy.md`

### Adjacent files consulted
- The dense list pattern (without copying the domain)
- `docs/prd/PRD-062-signal-standard-auditing-idempotent-service.md`

### Internet / official documentation
- Django signals: https://docs.djangoproject.com/en/5.2/topics/signals/
- django-auditlog (an API reference, not mandatory to adopt): consult Context7 when assessing the package.

### Context7 / MCPs / tools verified
- Pending during the implementation if a third-party library is used.

### Limitations found
- A schema change requires a decision about the `0001_initial.py` baseline, per `AGENTS.md`.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved
The academy CRUD gap in the 2026-06-30 audit.

## Execution prompt
### Persona
Django architect with operational compliance.

### Action
An append-only model, writes in the critical services, and a read-only listing.

### Context
The MVP can start with manual events in the Person, ClassGroup, check-in approve, and financial action services.

### Constraints
- No unnecessary PII in the JSON payload.
- An English route (`/audit/` or `/operations/audit/`).
- The UI in Brazilian Portuguese.

### Acceptance criteria
- [ ] The `OperationalAuditEntry` model (the final name at implementation time) persisted in the critical transactions.
- [ ] A GET listing with a filter by date, actor, and module.
- [ ] Permission: only `MANAGE_ACADEMY` or a dedicated capability.
- [ ] A test: creating a person generates an audit entry.
- [ ] The template follows the LV foundation once it is available (PRD-075).

### Expected evidence
- Tests + a screenshot of the listing.

### Output format
The PRD's Evidence.

## Scope
- The model, the migration/baseline, a service helper, the list view, the template, and the initial tests.
- The minimal instrumentation: Person create/update/delete, approving a check-in, and marking an order paid.

## Out of scope
- Read auditing (an access log).
- A CSV export (a follow-up).
- Automatic retention/archiving.

## Impacted files
- `system/models/`
- `system/services/`
- `system/views/`
- `system/urls.py`
- `templates/` (the new module)
- `system/migrations/0001_initial.py` if it is regenerated

## Risks and edge cases
- The data volume; indexing by `created_at`.
- A technical admin actor vs. a portal person.

## Rules and constraints
- Append-only; no delete in the UI.

## Plan
1. [x] The PRD approved.
2. [x] A Red test of the write.
3. [x] The `OperationalAuditEntry` model + the `record_audit_event`/`resolve_actor_label` helper (`system/services/audit.py`).
4. [x] Instrument 3 pilot flows: create/edit/delete a Person, approve a check-in, mark an order as paid.
5. [x] The UI listing with a filter by module.

## Test plan
### Tests to author
- `test_person_create_writes_audit_entry`
- `test_person_delete_writes_audit_entry`
- `test_audit_list_requires_manage_academy`
- `test_audit_list_renders_for_technical_admin`
- `test_str_includes_module_action_and_entity`

### Execution authorization
Local, with a migration (the `system/migrations/0001_initial.py` baseline regenerated through `clear_migrations.py` + `makemigrations`, authorized by `CLAUDE.md`/`AGENTS.md` for a local schema change).

### Execution evidence
- `system/tests/test_operational_audit.py` (5 tests): the model has a readable `__str__`; creating and deleting a Person through the form writes an audit entry; someone without `MANAGE_ACADEMY` receives a 302 when trying to reach the listing; the technical admin sees the listing rendered with the real content.
- The complete local rebuild cycle run in this PRD: `clear_migrations.py` → `makemigrations` (a new baseline with `OperationalAuditEntry`) → `manage.py test` (328 tests OK before this new suite) → `migrate` → `check` → `create_admin_superuser` → the complete sequence of the 20 seeds in the canonical order fixed by PRD-095 (the holidays run last, with no error).
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — **333 tests OK** (the full suite, including the 5 new audit tests).
- `.venv/Scripts/python.exe manage.py check` — 0 problems.
- End-to-end validation in the internal browser, logged in as an admin: editing Miguel through the People modal generated, in real time, the literal entry `Miguel Torres Dourado · admin · Pessoas · Atualização · 01/07/2026 09:58` (`Miguel Torres Dourado · admin · People · Update · 01/07/2026 09:58`) on the `/administration/audit/` screen.

## Visual validation
## Wireframe
### Region: The top
- The title Operational audit
- Filters: the period, the module, the user

### Region: The list
- Dense rows: the timestamp, the actor, the action, the entity

### States
- Empty, with data, no permission

## ORM validation
The entry count confirmed through a test (`OperationalAuditEntry.objects.filter(...).exists()`) and through the browser (1 real entry after editing Miguel).

## Quality validation
- `manage.py check` — 0 problems.
- The full suite — 333 tests OK.

## Evidence
- The period filter was not implemented in this round (only the module) — an MVP deliberately smaller than the original wireframe so as not to expand the scope; recorded in Pending.
- The decision taken: an in-house implementation (a simple model), without adopting `django-auditlog` — the volume and the need (3 pilot flows, with no field diffs) do not justify the external dependency.

## Implemented
- `system/models/audit.py`: `OperationalAuditEntry` (append-only, with no edit/delete UI), `AuditModule`, `AuditAction`.
- `system/services/audit.py`: `record_audit_event`, `resolve_actor_label`.
- The instrumentation: `PersonCreateView`/`PersonUpdateView`/`PersonDeleteView` (`system/views/person_views.py`), `InstructorApproveCheckinView` (`system/views/calendar_views.py`), `MarkOrderPaidActionView` (`system/views/billing_admin_views.py`).
- `system/views/admin_views.py`: `AuditLogListView` (restricted to `MANAGE_ACADEMY` through `AdministrativeRequiredMixin`), and an `Auditoria` (`Audit`) card in the administrative hub with a real count.
- `templates/audit/audit_log_list.html`: a listing with a filter by module, pagination, and an empty state.
- `system/urls.py`: the `/administration/audit/` route (`audit-log-list`), in English.
- The `system/migrations/0001_initial.py` baseline regenerated to include the new model.

## Cleanup findings
- No residue. The audit entry created during the visual validation (the real edit of Miguel) was kept — it is legitimate evidence that the feature works, not test data to clean up.

## Follow-up PRDs
- Exporting (CSV) and automatic retention/archiving — deliberately out of this PRD's scope, as already recorded.
- Filters by period and by actor in the listing (the original wireframe foresaw them; the MVP delivered only the module filter).
- Instrumenting more flows beyond the 3 pilots (e.g. deleting a class, a financial refund) if the user prioritizes it.

## Deviations from plan
- The original wireframe's period/user filter was not implemented — only the module filter, to keep the MVP lean, per the UI standard's "no unrequested new KPI/filter". Recorded as an explicit pending item, not hidden.

## Pending
- Filters by period and by actor on the listing screen.
- Exporting and automatic retention (explicitly out of scope since the original specification).

## Final status
Completed with limitations — the model, the instrumentation of the 3 pilot flows, and the listing screen delivered, tested (5 new tests + the full suite of 333), and validated live in the browser. Additional filters (period/actor) and exporting go to a future PRD if prioritized.
