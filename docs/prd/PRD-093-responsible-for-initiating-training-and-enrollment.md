# PRD-093: A guardian starting training and enrollment

## Summary
Allow a person with a `guardian` relationship to start training: enrolling in classes, an initial belt, and check-in as a holder student, without forcing a change of `person_type` to `student` when the business rule allows accumulation.

## Demand type
A business rule fix + the form.

## Current problem
- `PersonForm.clean` rejects `class_groups` when the type is neither `student` nor `dependent` (`person_forms.py:460-466`).
- `CLASS_ENROLLMENT_PERSON_TYPE_CODES` does not include `guardian`.
- The middleware marks `portal_is_student=True` for a guardian through `ACCESS_STUDENT_AREA`, but with no classes the user does not train.
- The user's explicit problem: a guardian cannot start training.

## Goal
An active guardian can:
- receive classes and an enrollment through the internal record or an approved flow;
- see the student area on the home when enrolled;
- check in to the classes they are enrolled in.

## Context Ledger
### Files read in full
- `system/forms/person_forms.py`
- `system/constants.py`
- `system/models/person.py` (`can_enroll_in_class_group`)
- `docs/prd/PRD-040-payment-before-person-creation-registration-flow.md` (adjacent)

### Adjacent files consulted
- `system/services/membership.py`
- `docs/prd/AUDIT-2026-06-30-master-findings.md`

### Internet / official documentation
- Django 5.2 validation: https://docs.djangoproject.com/en/5.2/ref/forms/validation/

### Context7 / MCPs / tools verified
- Context7 Django 5.2.

### Limitations found
- A product decision: the guardian trains as a holder with the same CPF, or a separate `student` profile is required — the PRD must record the decision chosen during the implementation.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved
Authorized by the user's explicit problem.

## Execution prompt
### Persona
Academy domain engineer.

### Action
Extend the enrollment eligibility and the form's validation for a guardian starting training.

### Context
The cumulative roles of PRD-074; the billing may stay with the guardian.

### Constraints
- Validate the age/IBJJF category the same way as for the other types.
- Do not break the dependent vs. holder flow.

### Acceptance criteria
- [ ] A manager assigns classes to a `guardian` person with no form error.
- [ ] `can_enroll_in_class_group()` aligned with the form.
- [ ] The home shows `Minha área` (`My area`) when the guardian has an active enrollment.
- [ ] Check-in works for an enrolled guardian (with PRD-094's rules).
- [ ] A test covers the happy path and the block with no class.

### Expected evidence
- Green tests.
- The local ORM with an enrolled guardian.

### Output format
An updated PRD.

## Scope
- `constants.py` when necessary.
- `person_forms.py`, `person.py`.
- Form and home tests.

## Out of scope
- The public wizard for a holder guardian (PRD-040 has its own scope).
- The guardian-student's billing/plan.

## Impacted files
- `system/constants.py`
- `system/forms/person_forms.py`
- `system/models/person.py`
- `system/tests/test_forms.py`
- `system/tests/test_home_dashboard.py`

## Risks and edge cases
- A guardian with dependents: the billing and the home tabs.
- A minor as a guardian (unlikely).

## Rules and constraints
- An explicit rule in the PRD before the code when there are two interpretations.

## Plan
1. [x] The documented decision: a guardian may enroll and train while keeping the `guardian` relationship (with no forced change to `student`); the billing stays with the guardian, as already implemented by `get_membership_owner`/`get_guardian_billing_tabs`.
2. [x] A Red test.
3. [x] An adjustment in `constants.py` (`CLASS_ENROLLMENT_PERSON_TYPE_CODES` now includes `PersonTypeCode.GUARDIAN`).
4. [x] Green + a home test.

## Test plan
### Tests to author
- `test_guardian_can_receive_class_groups_on_update`
- `test_guardian_with_enrollment_has_personal_home_area`

### Execution authorization
Local.

### Execution evidence
- `system/tests/test_guardian_can_train.py` (2 tests): a manager edits a guardian and assigns a class with no form error, creating an active `ClassEnrollment`; a guardian with an active enrollment sees `has_personal_area=True` and the label `Responsável` (`Guardian`) on the home.
- `.venv/Scripts/python.exe manage.py test system.tests.test_guardian_can_train --verbosity 2` — 2 tests OK.
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 325 tests OK (the full suite, with no regression in the other uses of `CLASS_ENROLLMENT_PERSON_TYPE_CODES`: the people list, the graduation overview, the initial graduation seed in the public registration).
- `.venv/Scripts/python.exe manage.py check` — 0 problems.

## Visual validation
Not run in isolation in this round (the change concerns data eligibility and reuses the same form/modal already validated visually in PRD-075/091).

## ORM validation
An active `ClassEnrollment` confirmed through the test (see Execution evidence).

## Quality validation
- `manage.py check` — 0 problems.
- The full suite — 325 tests OK.

## Evidence
- `get_class_group_eligibility_error` (used in the form's validation) was already neutral regarding `person_type` — it validates only the age/biological sex against the class's category. The only real block was the explicit check in `PersonForm.clean()` against `CLASS_ENROLLMENT_PERSON_TYPE_CODES`, which did not include `guardian`.
- `CLASS_ENROLLMENT_PERSON_TYPE_CODES` is used at 7 points in the code (the person list/detail, the graduation overview, the initial graduation seed in the checkout, the home's "student" context) — every use makes semantic sense for including guardians who also train; none of them is a billing/payment lock that could have an undesired side effect.

## Implemented
- `system/constants.py`: `CLASS_ENROLLMENT_PERSON_TYPE_CODES` now includes `PersonTypeCode.GUARDIAN`.

## Cleanup findings
- No residue. A minimal, surgical change in a single, widely reused constant, with no duplicated logic.

## Follow-up PRDs
- PRD-040 (the public wizard) was not changed in this PRD — it remains a separate product decision if the public registration needs to offer direct enrollment to a holder guardian.

## Deviations from plan
- No functional deviation.

## Pending
- No code pending items. The product decision about the guardian-student's plan/tuition remains open (the billing already flows to the guardian through `get_membership_owner`, but no new plan screen was created specifically for this case).

## Final status
Completed.
