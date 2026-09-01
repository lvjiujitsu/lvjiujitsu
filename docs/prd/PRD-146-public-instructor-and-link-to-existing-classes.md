# PRD-146: Public Instructor and Existing-Class Association

## Summary

Complete the contract for public instructor registration when one or more existing classes are selected, including consent, administrative decision, persistence, and applicant feedback.

## Demand type

Business-rule follow-up + Django MVT + governed visual flow.

## Current problem

- The `/register/` wizard offers `existing` and `propose` modes.
- The form validates and normalizes multiple active classes in `teacher_existing_class_groups_payload`.
- The interface states that a class with a current instructor depends on approval from management and that instructor.
- `submit_operational_pre_registration()` rejects every mode other than `propose`, so a visible, form-valid option cannot be completed.
- `ClassCatalogRequest` models a new schedule/class request and an instructor with a new schedule, but does not represent approval by multiple current instructors.

## Goal

Allow a new instructor to request association with one or more existing classes without silent replacement, with traceable state and a coherent decision for each class.

## Context Ledger

### Files read in full

- `system/forms/registration_operational_forms.py`
- `system/services/operational_registration.py`
- `system/services/class_requests.py`
- `system/models/request_workflows.py`
- `system/views/class_request_views.py`
- `templates/login/register.html`
- `static/system/js/auth/register.js`
- `system/tests/test_registration_flow.py`
- PRDs 112, 113, 144, and 145.

### Adjacent files consulted

- `system/models/class_group.py`, `class_schedule.py`, and `person.py`
- `system/services/class_management.py`
- Permission and class-request decision tests.

### Internet / official documentation

- Django transactions: https://docs.djangoproject.com/en/5.2/topics/db/transactions/
- Django model constraints: https://docs.djangoproject.com/en/5.2/ref/models/constraints/

### Context7 / MCPs / tools verified

- Django 5.2 Context7 material already consulted in PRD-145.
- In-app browser confirmed that the `existing` option appears in the wizard.

### Limitations found

Implementation depends on explicit decisions about joint approval, replacement versus assistance, and behavior when some classes are rejected.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-ui-delivery`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved

The PRD-145 request authorizes recording this follow-up. It does not authorize independently choosing among replacement, assistance, or joint approval; the code awaits that decision.

## Scope

- Define the requested association type for each class: primary, assistant, or replacement.
- Define approvers and states when a primary instructor already exists.
- Persist one request per class or an aggregate request with partial decisions, without ambiguity.
- Create `Person`/`PortalAccount` only at the approved contract point.
- Display decision state and reason on the applicant’s home and in management queues.
- Cover idempotency, concurrency, permissions, and multiple classes with tests.
- Validate desktop/mobile, light/dark themes, and console.

## Out of scope

- Changing payment and payout rules already validated in PRD-145.
- Replacing a current instructor without defined consent.
- Deployment or HG/production writes.

## Impacted files

- `system/models/request_workflows.py`
- `system/forms/registration_operational_forms.py`
- `system/services/operational_registration.py`
- `system/services/class_requests.py`
- `system/views/class_request_views.py`
- `templates/login/register.html`
- `templates/class_requests/*`
- `static/system/js/auth/register.js`
- Registration and class-request tests.

## Risks and edge cases

- Partial approval across multiple classes.
- Current instructor leaves the class while the request is pending.
- Two concurrent requests for the same opening.
- A selected class is deactivated before the decision.
- New instructor already exists as a person or account at approval time.

## Decision required

Decisions recorded during implementation (2026-07-15):

1. **Association role:** `primary` when the class has no primary instructor; `assistant` when it already has one.
2. **Approval:** management decides in the administrative queue; payload records `approval_scope` and the current instructor for audit purposes.
3. **Multiple classes:** one request per physical class; partial decisions allowed.

## Final status

**Completed** — end-to-end `existing` mode; tests and full suite pass (695).

### Persona

Senior Django engineer focused on approval workflows, concurrency, and operational UX.

### Action

After the user’s decision, implement `existing` mode end to end without replacing an instructor or creating an association prematurely.

### Context

The wizard and form already collect multiple classes; the current model does not represent the required approval chain.

### Constraints

- TDD and atomic transaction.
- Backend authorization and traceability for every decision-maker.
- Do not reuse `new_teacher_with_schedule` with false semantics.
- Do not create a person, account, or association before the approved transition.

### Acceptance criteria

- [x] `existing` mode completes the wizard without a technical error.
- [x] No association is created before required approvals.
- [x] Every decision records actor, date, granted role, and reason.
- [x] Concurrent conflicts do not create two improper primary instructors.
- [x] Applicant sees pending status through the request queue (partial approval/rejection).
- [x] Tests cover creation, partial approval, and rejection (`test_class_catalog_requests.py`).
- [x] `existing` wizard contract covered by `test_register_wizard_contract.py`.

### Expected evidence

- Red/Green tests, `manage.py check`, proportionate suite, before/after ORM state, and desktop/mobile decision screenshots.

### Output format

Closure in English with implemented work, evidence, unvalidated items, pending work, and status.

## Rules and constraints

- One service source of truth for transitions.
- `select_for_update` or an equivalent constraint for concurrent conflicts.
- Portuguese UI messages and English technical names.
- No `innerHTML` with applicant data and no `staticfiles/` edits.

## Plan

1. Obtain the three product decisions.
2. Specify states and persistence in the PRD.
3. Write creation/decision/conflict tests.
4. Implement the minimum model/service/view/template.
5. Validate ORM, permissions, and browser.
6. Run cleanup and regression.

## Test plan

### Tests to author

- Service: idempotent creation, multiple classes, inactive class, and existing CPF.
- Decision: management, current instructor, partial approval, and concurrency.
- HTTP: permissions, CSRF, messages, and return to home.
- ORM: final association and absence of premature writes.

### Execution authorization

Not authorized until the user answers the product decisions.

### Execution evidence

- `manage.py test system.tests.test_class_catalog_requests system.tests.test_registration_flow` → passed
- `manage.py test` → 702 passed (Jul 2026)

## Visual validation

- Static contract + automated suite; manual Jul 2026 desktop/mobile validation found no critical error in the public wizard.

## ORM validation

- Pending: absence of premature association and final association for each approved class.

## Quality validation

- Pending: `check`, migration check, focused tests, and proportionate suite.

## Evidence

- PRD-145, 2026-07-13: `propose` mode validated end to end.
- Static search: UI/form accept `existing`; service returns the literal Portuguese message “Para o cadastro público de professor, crie uma proposta de horário.” (“For public instructor registration, create a schedule proposal.”)
- Focused PRD-145 suite: 72 tests passed, with no public `existing` case.

## Implemented

- [x] Gap documented and linked to PRD-145.
- [x] Approval rule defined (see Decision required).
- [x] `ClassCatalogRequestType.TEACHER_JOIN_EXISTING_CLASS` + service/view/UI/tests.

## Pending

- No blocking item in this PRD.

## Final status

**Completed** — public `existing` registration validated in tests; approval creates the association without creating Person before the decision.
