# PRD-063: Person cascade deletion integrity

## Summary

Validate the deletion of a `Person` in LV end to end through the interface and safely handle the referential integrity failure modes. The `on_delete` map shows that `Person` is referenced with a mix of `CASCADE`, `SET_NULL`, and `PROTECT` across about ten models; `PersonDeleteView` is a standard `DeleteView` that does not handle `ProtectedError`, so deleting a person referenced by a `PROTECT` relation (e.g. an instructor in `ClassGroup.main_teacher`, an instructor in the calendar, a `TeacherPayout` payout) fails with no clear message to the administrator.

## Demand type

Integrity audit + view hardening + UI acceptance with authorized mutation.

## Current problem

- `system/views/person_views.py::PersonDeleteView` is a plain `DeleteView` (`AdministrativeRequiredMixin`), with no capture of `django.db.models.deletion.ProtectedError`.
- The `on_delete` map referencing `Person` (a sample confirmed by reading):
  - `person.py`: `PortalAccount` (OneToOne, CASCADE), `PersonRelationship.source/target` (CASCADE), `person_type` (PROTECT).
  - `class_membership.py`: `ClassEnrollment` (CASCADE), `ClassInstructorAssignment` (CASCADE).
  - `class_group.py`: `main_teacher` (PROTECT), and a second FK (PROTECT).
  - `asaas.py`: two CASCADE FKs, one PROTECT, one SET_NULL.
  - `registration_order.py`: CASCADE + SET_NULL + PROTECT.
  - `graduation.py`: CASCADE + PROTECT + SET_NULL.
  - `membership.py`: CASCADE + PROTECT.
  - `product_backorder.py`: CASCADE + PROTECT (the variant).
  - `calendar.py`: multiple CASCADE/SET_NULL/PROTECT, with the instructor as PROTECT.
  - `trial_access.py`: CASCADE.
- Unvalidated consequences:
  1. deleting a **student** with no PROTECT references should cascade cleanly (account, enrollments, pre-orders, graduation, charges), but that is not proven through the UI;
  2. deleting an **instructor** referenced by `PROTECT` must be **blocked** with a clear message — today it most likely results in an unhandled error;
  3. there is no defined behavior and no test for those two paths.

## Goal

1. Produce the complete, verified `on_delete` map of every reference to `Person`.
2. Define the expected behavior: a student with no PROTECT cascades; a person with a PROTECT reference is blocked with a Brazilian Portuguese message explaining what prevents it.
3. Harden `PersonDeleteView` to capture `ProtectedError` and show a friendly message (with no 500), preserving the administrative permission.
4. Cover both paths with tests (a successful cascade and a PROTECT block).
5. Accept through the UI the deletion of a test person on desktop and mobile, with visual evidence and a clean console.

## Context Ledger

### Files read in full

- `system/views/person_views.py` (partial: the `PersonDeleteView` signatures)
- `system/models/person.py`
- `system/models/class_membership.py`
- `system/models/class_group.py`

### Adjacent files consulted

- `system/models/asaas.py`, `registration_order.py`, `graduation.py`, `membership.py`, `product_backorder.py`, `calendar.py`, `trial_access.py` (the `on_delete` lines)
- `templates/people/person_confirm_delete.html`

### Internet / official documentation

- [Django 5.2 — on_delete / ProtectedError](https://docs.djangoproject.com/en/5.2/ref/models/fields/#django.db.models.ForeignKey.on_delete)
- [Django 5.2 — deletion / collector](https://docs.djangoproject.com/en/5.2/topics/db/queries/#deleting-objects)
- [Django 5.2 — DeleteView](https://docs.djangoproject.com/en/5.2/ref/class-based-views/generic-editing/#deleteview)
- [Django 5.2 — messages framework](https://docs.djangoproject.com/en/5.2/ref/contrib/messages/)

### Context7 / MCPs / tools verified

- Context7 to be consulted for Django deletion/ProtectedError during execution.
- The internal browser available at `http://127.0.0.1:8000` for acceptance.
- PowerShell, Git, and `rg` available.

### Limitations found

- Deletion is a real mutation; it requires explicit authorization and a dedicated test person.
- The exact set of PROTECT relations that block must be confirmed during execution, not presumed from a sample.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved

- Summary presented: validate and harden the deletion of a `Person`, handling `ProtectedError` and accepting it through the UI.
- User approval: an explicit request for complete PRDs for sequential implementation.
- Date: 2026-06-28.

## Execution prompt

### Persona

Django engineer responsible for referential integrity and the administrative person flow.

### Action

Map `on_delete`, define the expected behavior, harden the view, write the tests, and accept the deletion through the UI.

### Context

LV is a Django 5.2 monolith; `Person` is the central aggregate referenced by enrollments, payouts, graduation, the calendar, orders, and charges, with a heterogeneous `on_delete`.

### Constraints

- Do not create migrations (do not change `on_delete` without a schema decision from the user).
- Do not run a deletion without authorization and a test person.
- Do not mask an error; the message must be specific and in Brazilian Portuguese.
- Preserve `AdministrativeRequiredMixin`.

### Acceptance criteria

- [x] A complete, verified map of every reference to `Person` with its `on_delete`.
- [x] The expected behavior documented for both paths (cascade vs. block).
- [x] `PersonDeleteView` captures `ProtectedError` and renders a Brazilian Portuguese message with no 500.
- [ ] A student with no PROTECT reference is deleted and the cascade covers the account, enrollments, relationships, and expected derived records.
- [ ] A person with a PROTECT reference is blocked with a message naming the impediment.
- [x] Tests cover both paths.
- [ ] UI acceptance on desktop and mobile with a screenshot and a clean console.

### Expected evidence

- The `on_delete` map.
- The tests' output (after authorization).
- A screenshot of the successful deletion and of the blocking message.
- A read-only ORM snapshot confirming the cascade and the absence of orphans.

### Output format

A short summary, the map, evidence, limitations, and status.

## Scope

- `system/views/person_views.py` (`PersonDeleteView`)
- `templates/people/person_confirm_delete.html` (the blocking message, when necessary)
- `system/tests/test_person_delete.py` (new)
- this PRD.

## Out of scope

- Changing `on_delete` in the models (a schema change; the user's decision).
- Redesigning the person list/detail.
- Deleting instructors in production/HG.

## Impacted files

- `system/views/person_views.py`
- `templates/people/person_confirm_delete.html`
- `system/tests/test_person_delete.py` (new)
- this PRD.

## Risks and edge cases

- An excessive cascade: deleting a student may remove financial/graduation history that should be preserved — assess whether some CASCADE should be SET_NULL (record it as a schema follow-up, do not change it here).
- `PROTECT` on `person_type` never blocks deleting a person (it is the inverse side), but `main_teacher`/instructor/payout do.
- The blocking message must not leak technical model names to the end user.
- Bulk deletion from the list, if it exists, needs the same handling.

## Rules and constraints

- The smallest correct change; the root cause.
- No migration; no unauthorized mutation.
- A specific message, with no masked error.
- Permission in the backend.

## Plan

- [x] Context and research (the complete on_delete map)
- [x] Define the expected behavior of both paths
- [x] Write the tests (test-first)
- [x] Harden `PersonDeleteView`
- [ ] Request authorization and run the tests
- [ ] Accept it through the desktop/mobile UI
- [x] Cleanup audit
- [x] Documentation

## Test plan

### Tests to author

- `test_person_delete.py`: deleting a student with no PROTECT (the expected cascade, with no orphans); deleting a person with a PROTECT reference (a block + a message); the view's response with no 500.

### Execution authorization

- Status: not authorized in this run. The tests were written before the code and not run, per policy.

### Execution evidence

The test was written, not run, per policy. There is no Red/Green claim.

## Visual validation

- The local server at `127.0.0.1:8000`.
- Delete a test person with no PROTECT → confirm the removal and the redirect.
- Try to delete a person with a PROTECT → confirm the blocking message.
- Desktop and mobile, light and dark themes, a console with no errors, screenshots.

## ORM validation

- A read-only introspection performed to map the FKs of `Person`.
- A before/after snapshot of a real deletion was not performed because it would require mutating a test person.

## Quality validation

- `manage.py check` (after authorization).
- A review of the diff and the map.
- `git diff --check`.

## Evidence

A read-only map through Django introspection:

| Reference | Field | `on_delete` |
|---|---|---|
| `ClassCheckin` | `approved_by` | `SET_NULL` |
| `ClassCheckin` | `person` | `CASCADE` |
| `ClassEnrollment` | `person` | `CASCADE` |
| `ClassGroup` | `main_teacher` | `PROTECT` |
| `ClassInstructorAssignment` | `person` | `CASCADE` |
| `Graduation` | `awarded_by` | `SET_NULL` |
| `Graduation` | `person` | `CASCADE` |
| `Membership` | `person` | `CASCADE` |
| `PersonRelationship` | `source_person` | `CASCADE` |
| `PersonRelationship` | `target_person` | `CASCADE` |
| `PortalAccount` | `person` | `CASCADE` |
| `PreRegistration` | `finalized_person` | `SET_NULL` |
| `ProductBackorder` | `person` | `CASCADE` |
| `RegistrationOrder` | `person` | `CASCADE` |
| `SpecialClass` | `teacher` | `PROTECT` |
| `SpecialClassCheckin` | `approved_by` | `SET_NULL` |
| `SpecialClassCheckin` | `person` | `CASCADE` |
| `TeacherBankAccount` | `person` | `CASCADE` |
| `TeacherPayout` | `person` | `PROTECT` |
| `TeacherPayrollConfig` | `person` | `CASCADE` |
| `TrialAccessGrant` | `person` | `CASCADE` |

Validations executed:

- `python manage.py check` returned `System check identified no issues (0 silenced).`
- `python -m py_compile system/tests/test_person_delete.py system/tests/test_register_wizard_contract.py` returned exit code 0.
- `system/tests/test_person_delete.py` was created with the student cascade and the `ClassGroup.main_teacher` block scenarios, but it was not run.

## Implemented

- `PersonDeleteView.form_valid()` now captures `ProtectedError`, redirects to the preserved person's detail, and shows a Brazilian Portuguese message with the type of protected relation.
- A deletion with no block keeps redirecting to the list and now shows a success message.
- `_format_person_delete_blockers()` translates the known blockers: the main class, the special class, and the financial payout.
- `system/tests/test_person_delete.py` covers the student cascade contract with account/enrollment/relationship and the block for an instructor linked to a class.

## Cleanup findings

- The person list and detail already displayed Django messages; no template change was necessary for this adjustment.
- No migration or schema change was created.
- No test person was created in the local database.

## Follow-up PRDs

- A possible schema PRD to reassess CASCADE vs. SET_NULL where the cascade deletes history that should be preserved (the user's decision, the destructive cycle).

## Deviations from plan

- The UI acceptance and the test execution were not done because they require explicit authorization for mutation/tests.

## Pending

- Authorization to run `system.tests.test_person_delete`.
- Authorization to create/delete a test person and validate the flow in the desktop/mobile browser.

## Final status

**Completed with limitations** — the implementation and the tests were written; the real test/UI/mutation validation remains pending under the authorization policy.
