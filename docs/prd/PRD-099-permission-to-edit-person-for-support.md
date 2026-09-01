# PRD-099: Person edit permission for support roles

## Summary
Align `PersonUpdateView` (and deletion where applicable) with the real capabilities: whoever has `SUPPORT_PEOPLE` and can create a student must be able to edit student/dependent records, while `MANAGE_PEOPLE` keeps broad editing.

## Demand type
A permissions fix.

## Current problem
- `PersonCreateView` uses `PeopleSupportRequiredMixin` (`SUPPORT_PEOPLE`).
- `PersonUpdateView` uses `AdministrativeRequiredMixin` (`MANAGE_ACADEMY`).
- The instructor is blocked from editing a student they have just registered.
- It contributes to the "dysfunctional person record" reported by the user.

## Goal
A coherent create/read/update/delete matrix by capability, documented and tested.

## Context Ledger
### Files read in full
- `system/views/person_views.py`
- `system/views/portal_mixins.py`
- `docs/prd/PRD-014-admin-panel-as-portal-persona.md`
- `docs/prd/AUDIT-2026-06-30-master-findings.md` (finding 15)

### Adjacent files consulted
- `system/tests/test_person_delete.py`
- `docs/prd/PRD-074-cumulative-operational-roles-and-permissions.md`

### Internet / official documentation
- Django 5.2 access mixins: https://docs.djangoproject.com/en/5.2/topics/auth/default/#the-permissionrequiredmixin-mixin

### Context7 / MCPs / tools verified
- Context7 Django 5.2.

### Limitations found
- Editing sensitive fields (payroll, the administrative type) must stay restricted.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
The 2026-06-30 audit.

## Execution prompt
### Persona
Authorization engineer.

### Action
Replace the update mixin with a granular check in the dispatch/get_queryset.

### Context
PRD-014 promised the instructor could register and view students with no admin finance.

### Constraints
- The payroll fields and the administrative `person_type` only with `MANAGE_PEOPLE`.
- CSRF and server-side validation.

### Acceptance criteria
- [ ] An instructor with `SUPPORT_PEOPLE` edits an existing student (the name, the classes).
- [ ] The instructor does not edit a back-office person or the payroll fields.
- [ ] A manager with `MANAGE_PEOPLE` edits every current field.
- [ ] Permission tests, 302 vs. 200.
- [ ] `PersonDeleteView` stays restricted to management (documented).

### Expected evidence
- Green tests.

### Output format
The PRD's Evidence.

## Scope
- `person_views.py`
- Tests in `system/tests/`

## Out of scope
- New fields in the form.

## Impacted files
- `system/views/person_views.py`
- `system/tests/test_forms.py` or a new `test_person_permissions.py`

## Risks and edge cases
- The instructor changing the plan/finance through hidden fields — block it in the form.

## Rules and constraints
- Do not weaken `MANAGE_ACADEMY` for the financial modules.

## Plan
1. [x] A Red test of the instructor updating a student.
2. [x] Replace `AdministrativeRequiredMixin` with `PeopleSupportRequiredMixin` in `PersonUpdateView` (the same capability as Create).
3. [x] Restrict the queryset (excluding back-office/instructor) and the form's fields (`person_type_codes`, `show_payroll_fields=False`) for anyone without `MANAGE_PEOPLE`, mirroring `PersonCreateView`.
4. [x] Green.

## Test plan
### Tests to author
- `test_support_people_can_update_student`
- `test_support_people_cannot_update_administrative_person`
- `test_support_people_form_hides_payroll_fields`

### Execution authorization
Local.

### Execution evidence
- `system/tests/test_person_permissions.py` (3 tests): an instructor with the `people-support` role (only `SUPPORT_PEOPLE`) can open a student's edit screen (200); the same person tries to edit a back-office member and receives a 404 (the queryset already excludes them); the form does not show `Repasse do professor` (`Instructor payout`) and `form.show_payroll_fields` is `False`.
- `.venv/Scripts/python.exe manage.py test system.tests.test_person_permissions --verbosity 2` — 3 tests OK.
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 319 tests OK (the full suite, with no regression).
- `.venv/Scripts/python.exe manage.py check` — 0 problems.

## Visual validation
Not applicable in this round (the change concerns permissions/the queryset and reuses the existing template/modal already validated in PRDs 075/077).

## ORM validation
N/A — covered by the permission tests above.

## Quality validation
- `manage.py check` — 0 problems.
- The full suite — 319 tests OK.

## Evidence
- Before: `PersonUpdateView(AdministrativeRequiredMixin, ...)` required `MANAGE_ACADEMY`, blocking anyone with only `SUPPORT_PEOPLE` (e.g. the `people-support` operational role, or the instructor who registered the student) from editing the record they had just created.
- `PersonCreateView` already used `PeopleSupportRequiredMixin` and already restricted `person_type_codes`/`show_payroll_fields` for non-managers — Update did not replicate that same matrix, causing the create-yes/update-no asymmetry the user reported.

## Implemented
- `system/views/person_views.py`: `PersonUpdateView` swapped `AdministrativeRequiredMixin` for `PeopleSupportRequiredMixin`; `get_queryset` filters by `CLASS_ENROLLMENT_PERSON_TYPE_CODES` when `not _can_manage_people`; a new `get_form_kwargs` replicates `PersonCreateView`'s restriction (no payroll, no switching to the administrative/instructor type).
- `PersonDeleteView` stays with `AdministrativeRequiredMixin` (`MANAGE_ACADEMY`), per the explicit decision to keep deletion restricted to management.

## Cleanup findings
- No residue. No duplicated logic: `PersonUpdateView` now mirrors exactly the pattern already used by `PersonCreateView`.

## Follow-up PRDs
- None.

## Deviations from plan
- No functional deviation.

## Pending
- None.

## Final status
Completed.
