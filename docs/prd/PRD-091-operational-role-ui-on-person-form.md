# PRD-091: Operational roles UI in the person form

## Summary
Expose the assignment of a `PersonOperationalRole` in the internal person record. The backend and the seeds already support cumulative roles (PRD-074), but the form only edits the singular `person_type` — Miguel and other people cannot receive class support or operations through the UI.

## Demand type
A new UI feature + Django integration.

## Current problem
- `PersonForm` has no fields for operational roles or a class scope.
- The assignment happens only through the seed JSON or a Django Admin inline.
- The user expects to "enable functions" in the person record, not in global types.

## Goal
A manager with `MANAGE_PEOPLE` assigns/removes active operational roles when creating and editing a person, with a global or per-class scope when the role requires it.

## Context Ledger
### Files read in full
- `docs/prd/AUDIT-2026-06-30-master-findings.md` (findings 13, 44, 112)
- `system/models/person.py` (`PersonOperationalRole`)
- `system/forms/person_forms.py`
- `system/services/portal_capabilities.py`
- `system/constants.py`
- `static/initial_data/initial_administrative.json`

### Adjacent files consulted
- `system/views/person_views.py`
- `system/admin.py`
- `docs/prd/PRD-074-cumulative-operational-roles-and-permissions.md`

### Internet / official documentation
- Django 5.2 ModelForm and formsets: https://docs.djangoproject.com/en/5.2/topics/forms/modelforms/

### Context7 / MCPs / tools verified
- Context7 Django 5.2 forms.

### Limitations found
- It depends on the modal templates (PRD-075/078) for the ideal UX; the MVP can use the existing full-screen form.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved
Authorized by the 2026-06-30 audit and the explicit Miguel/profiles problem.

## Execution prompt
### Persona
Django engineer focused on permissions and transactional forms.

### Action
Implement a `Papéis operacionais` (`Operational roles`) section in `PersonForm` with a formset or a multiple field validated server-side.

### Context
The roles are defined in `DEFAULT_OPERATIONAL_ROLE_DEFINITIONS`; the scope is optional through `class_group`.

### Constraints
- The code in English; the UI in Brazilian Portuguese.
- No business rules in JavaScript.
- `transaction.atomic` when saving the person + the roles.
- Do not change the canonical role list in `constants.py` without a PRD.

### Acceptance criteria
- [ ] The manager sees the list of active roles when editing Miguel and can add `class-assistant`.
- [ ] A role with a class scope requires a class to be selected; a per-field error when it is omitted.
- [ ] Removing a role deactivates or deletes it according to the idempotent rule documented in this PRD.
- [ ] The middleware reflects the new capabilities after saving with no new login (or document the need to log in again).
- [ ] A test: assign `class-assistant` to a student and verify `portal_capabilities` contains `SUPPORT_CLASSES`.

### Expected evidence
- An authorized, green Django test.
- A desktop/mobile screenshot of the form with the roles.
- `manage.py check` with no issues.

### Output format
An updated PR with the evidence in the Evidence section.

## Scope
- The form, the role sync service, the view context, and the section's template.
- Permission and persistence tests.

## Out of scope
- Renaming the Profiles route (PRD-100).
- Migrating `person_type` to a composite model.

## Impacted files
- `system/forms/person_forms.py`
- `system/views/person_views.py`
- `system/services/` (a new helper when necessary)
- `templates/people/person_form.html`
- `system/tests/`

## Risks and edge cases
- A conflict between the global unique constraint and a scoped role.
- An instructor with `SUPPORT_PEOPLE` must not edit roles without `MANAGE_PEOPLE`.

## Rules and constraints
- Follow `UI-SCREEN-CONTRACT.md` §15.6 once the modals exist.

## Plan
1. [x] A failing test for the role assignment through the form's POST.
2. [x] The `operational_roles` (a multi-select) + `class_assistant_group` (the scope) fields in `PersonForm`, with no formset (simpler and sufficient for the use case).
3. [x] The `sync_person_operational_roles` service (a new file `system/services/operational_roles.py`), transactional and idempotent.
4. [x] The template and visual validation (desktop, the modal, the ORM).

## Test plan
### Tests to author
- `test_assign_class_assistant_role_requires_class_group`
- `test_assign_class_assistant_role_with_class_group_succeeds`
- `test_capabilities_reflect_new_role_after_save`
- `test_removing_role_deletes_assignment`

### Execution authorization
Authorized locally per `AGENTS.md`.

### Execution evidence
- `system/tests/test_person_operational_roles_form.py` (4 tests): assigning `Apoio de turma` (`Class support`) with no class produces a field error; with a class it persists the correct `PersonOperationalRole`; `operational_role_assignments` reflects the new role right after saving (with no new login needed); removing the role from the form deletes the record.
- `.venv/Scripts/python.exe manage.py test system.tests.test_person_operational_roles_form --verbosity 2` — 4 tests OK.
- `.venv/Scripts/python.exe manage.py test system.tests.test_forms system.tests.test_lv_foundation_people system.tests.test_person_permissions --verbosity 1` — 16 tests OK (no regression in the People form/modal).
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 323 tests OK (the full suite).
- `.venv/Scripts/python.exe manage.py check` — 0 problems.
- End-to-end validation in the internal browser, logged in as an admin: I edited Miguel (a student with no role at all) through the modal, checked `Apoio de turma` (`Class support`), selected the class `Jiu Jitsu - Adulto`, and saved — the modal closed and reloaded the list. Confirmed through the local ORM (`Person.objects.get(cpf='920.000.012-62').operational_role_assignments`) that the `class-assistant` / Adult class record was created with `is_active=True`. The demonstration record was removed at the end of the validation so as not to pollute the development database.

## Visual validation
- Desktop, dark theme: the `Papéis operacionais` (`Operational roles`) section renders inside the Person edit modal, with checkboxes for the 6 registered roles (People support, Class support, Academy manager, Stock operator, Graduation operator, Financial operator) and the conditional class selector.
- Mobile: not tested in isolation in this round (it reuses the same modal already validated on mobile in PRD-075); there was no layout change that would justify a new overflow check.
- The per-field error: `test_assign_class_assistant_role_requires_class_group` confirms the message `Selecione a turma para o apoio de turma.` (`Select the class for the class support.`) on the `class_assistant_group` field.

## ORM validation
`PersonOperationalRole` verified through the local shell after saving from the form (see Execution evidence).

## Quality validation
- `manage.py check` — 0 problems.
- The full suite — 323 tests OK.

## Evidence
- The `Papéis operacionais` (`Operational roles`) section only appears for those with `MANAGE_PEOPLE` (`show_operational_role_fields` mirrors the same control as `show_payroll_fields`); someone with only `SUPPORT_PEOPLE` neither sees nor can change other people's roles.

## Implemented
- `system/services/operational_roles.py` (new): `sync_person_operational_roles(person, role_ids, class_assistant_group=None)`, transactional, idempotent, removing assignments that are no longer selected.
- `system/forms/person_forms.py`: the `operational_roles` (`ModelMultipleChoiceField`) and `class_assistant_group` (`ModelChoiceField`) fields, initialization from the active `PersonOperationalRole` records, a cross validation in `clean()`, and the call to the service in `save()`.
- `system/views/person_views.py`: `show_operational_role_fields=False` propagated to anyone without `MANAGE_PEOPLE`, in `PersonCreateView` and `PersonUpdateView`.
- `templates/people/person_form.html` and `person_form_modal.html`: the new `Papéis operacionais` (`Operational roles`) section, visible only with `can_manage_people`.

## Cleanup findings
- No residue. The demonstration data created during the visual validation was removed from the development database.

## Follow-up PRDs
- None new; PRD-100 (renaming Profiles → Relationship types) was already executed in parallel and references this PRD as the right place to assign roles.

## Deviations from plan
- I chose direct fields in `PersonForm` instead of a dedicated formset — a single `class-assistant` role with a scope at a time is enough for the real use case (a single class per support person); a formset would be unrequested complexity. Documented here as a conscious decision, not a gap.

## Pending
- If in the future a person needs to support more than one class at the same time, this decision needs revisiting (today it is only one class at a time through `class_assistant_group`).

## Final status
Completed.
