# PRD-081: Extract the registration and payment services from the wizard

## Summary
Reduce the concentration of business rules in `auth_views.py`, moving persistence, snapshots, payment, and finalization into transactional services.

## Demand type
Django MVT refactoring + transactional safety.

## Current problem
`system/views/auth_views.py` concentrates the HTTP view, ORM writes, pre-registration snapshots, order creation, payment integration, and finalization. That violates the MVT contract and makes tests/maintenance fragile.

## Goal
Leave the views thin:
- HTTP/form validation in the view;
- business rules in services;
- writes with `transaction.atomic`;
- tests per service and per view.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/AGENT-WORKFLOW.md`
- `system/views/auth_views.py`
- `system/services/registration.py`
- `system/services/pre_registration.py`
- `system/services/registration_checkout.py`
- `system/services/registration_validation.py`

### Adjacent files consulted
- `docs/prd/PRD-040-payment-before-person-creation-registration-flow.md`
- `docs/GUIA-PREENCHIMENTO-TESTE-CLIENTE.md`
- `system/tests/test_registration_flow.py`
- `system/tests/test_register_wizard_contract.py`

### Internet / official documentation
- Django transactions: https://docs.djangoproject.com/en/5.2/topics/db/transactions/

### Context7 / MCPs / tools verified
- Context7 Django 5.2 transactions.

### Limitations found
- The real payment flow depends on Asaas/Stripe and cannot be validated as a success without a gateway/tunnel where applicable.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
Authorized by the current request to fix the large views and the legacy.

## Scope
- Extract services for the pre-registration, the snapshot, order creation, and finalization.
- Keep the existing public behavior.
- Cover it with focused tests.

## Out of scope
- A visual redesign of the wizard.
- Changing gateways.

## Impacted files
- `system/views/auth_views.py`
- `system/services/pre_registration.py`
- `system/services/registration.py`
- `system/services/registration_checkout.py`
- `system/tests/test_registration_flow.py`
- `system/tests/test_register_wizard_contract.py`

## Risks and edge cases
- The pre-payment/post-payment flow is sensitive; a regression may create a person too early.
- The webhooks and the redirects need to stay separate.

## Plan
- [x] Map the current responsibilities.
- [x] Write tests for the critical behavior.
- [x] Extract the services in small steps.
- [x] Validate the wizard locally.

## Test plan
### Tests to author
- The pre-registration does not create a `Person` before the finalization.
- The finalization creates the person/membership in a transaction.
- A payment error does not finish the registration.

### Execution authorization
Authorized locally.

### Execution evidence
Commands run locally in `C:\Users\whsf\Documents\GitHub\lvjiujitsu` with `.venv\Scripts\python.exe`.

1. Baseline (before the extraction), the full suite:
   `manage.py test --verbosity 1` → `Ran 261 tests in 74.918s` → `OK`.
2. Focused baseline (before the extraction):
   `manage.py test system.tests.test_registration_flow system.tests.test_register_wizard_contract --verbosity 2` → `Ran 4 tests in 0.927s` → `OK`.
3. After extracting the services, a new per-service regression test created in
   `system/tests/test_pre_registration_service.py` (5 tests covering
   `finalize_pre_registration`, `mark_pre_registration_trial_requested`, and
   `create_pre_registration_plan_payment`):
   `manage.py test system.tests.test_pre_registration_service --verbosity 2` → `Ran 5 tests in 1.179s` → `OK`.
4. `manage.py check` → `System check identified no issues (0 silenced).`
5. The full suite after the extraction:
   `manage.py test --verbosity 1` → `Ran 267 tests in 68.720s` → `OK` (and a new final run in
   `55.083s` → `OK`).
6. The wizard's contract tests (including the one that instantiates
   `PortalRegisterView()._get_pending_person_summary()` directly) stay green after the
   extraction: `manage.py test system.tests.test_register_wizard_contract.PendingRegistrationSummaryContractTestCase --verbosity 2` → `Ran 1 test in 0.022s` → `OK`.

Visual validation of the public wizard in the internal browser **was not performed** in this delivery —
the `PortalRegisterView`/`FinalizeRegistrationView`/`MaterialsCheckoutView` HTTP views were changed
only to delegate calls to services (the same URL signature, the same `template_name`,
the same context contract), with no template/CSS/JS change. The automated suite (including the
`test_register_wizard_contract.py` contract test that checks the script's `?v=36` and the function
markers in the JavaScript) covers the static contract with no regression.

## Visual validation
Necessary for the wizard when the view is touched.

## ORM validation
Mandatory in the test database.

## Quality validation
- Focused tests
- `manage.py check`

## Evidence
- The subagent pointed at the concentration in `PortalRegisterView` and `FinalizeRegistrationView`.

## Implemented
- `system/services/pre_registration.py` gained the business rule functions that lived in
  `PortalRegisterView`/`FinalizeRegistrationView`:
  - `build_wizard_form_snapshot`, `snapshot_scalar`, `resolve_primary_cpf`, `resolve_primary_email`,
    `save_pre_registration_from_form` (creating/updating a `PreRegistration` from the wizard's POST).
  - `mark_pre_registration_trial_requested` (the "pay later" flow).
  - `get_pending_person_summary`, `build_pending_summary_from_pre_registration`,
    `build_snapshot_student_summary`, `build_extra_dependent_summary`,
    `get_extra_dependents_from_snapshot`, `build_person_class_group_summary`,
    `build_snapshot_class_group_summary`, `build_class_group_summary_from_groups`
    (the pending person summary displayed in the wizard).
  - `get_order_summary`, `get_registration_order_or_pre_registration_summary`
    (the plan/materials order summary).
  - `normalize_snapshot_for_form`, `grant_trial_for_pre_registration`, and
    `finalize_pre_registration` (the transactional finalization: it creates the `Person`/`PortalAccount` through
    `PortalRegistrationForm.save()`, activates the accounts, synchronizes the confirmed payment with the
    `RegistrationOrder`, and grants the trial class where applicable). `finalize_pre_registration`
    returns a dict (`ok`, `error`, `person`, `portal_account`, `already_finalized`) so the view can
    decide the redirect/message without reimplementing the rule.
- `system/services/registration_checkout.py` gained the payment functions that lived in the view:
  `ensure_pre_registration_asaas_customer`, `parse_selected_plan_payload`,
  `create_pre_registration_plan_payment` (Asaas PIX/card and a Stripe subscription, with a coupon), and
  `create_pre_registration_materials_payment` (Asaas PIX/card for materials).
- `system/views/auth_views.py` became thin: `PortalRegisterView.form_valid`,
  `MaterialsCheckoutView._post_for_pre_registration`, and
  `FinalizeRegistrationView._finalize_pre_registration` now call the services above instead of
  containing the logic directly. The file went from 1,104 to 538 lines. No URL, template,
  public context, or externally referenced method signature (`_get_pending_person_summary`
  remains as a thin wrapper over the service, since it is used directly by
  `test_register_wizard_contract.py`) was changed.
- A new test `system/tests/test_pre_registration_service.py` covering finalization (success,
  idempotency, and a validation error with no `Person` created), the trial class marking, and a plan
  payment error with no plan selected.

## Cleanup findings
- Removed the duplicated logic between `PortalRegisterView._ensure_pre_registration_asaas_customer`
  and the copy used by `MaterialsCheckoutView` through `PortalRegisterView()._ensure_pre_registration_asaas_customer(...)`
  (instantiating a view just to call a helper method) — both views now call the same
  `ensure_pre_registration_asaas_customer` service function.
- The duplicated local `import re`/`from decimal import Decimal` inside `ValidateCouponView.post`
  (around line 211 of `auth_views.py`) is pre-existing legacy, outside this PRD's scope; recorded here
  for a possible future cleanup, not removed in this delivery so as not to expand the diff.
- Confirmed (through `git grep` on the `HEAD` before this change) that `build_form_snapshot`,
  `create_or_update_pre_registration`, `get_pre_registration_for_session`, and `restore_form_initial`
  in `system/services/pre_registration.py` were already orphaned code before this PRD — there was no
  caller in `system/` beyond the module itself. They were not removed in this delivery so as not to expand the
  scope (the PRD asks for extraction, not the deletion of unrelated legacy); recorded here as
  pre-existing debt for a future audit.

## Follow-up PRDs
None opened in this delivery. The duplicated import item in `ValidateCouponView` may become a
minor cleanup follow-up if desired, but it does not justify its own PRD.

## Deviations from plan
No relevant deviation. The Plan foresaw "extract the services in small steps" — the extraction was
done in a single work commit (with no git commit created, per the instruction not to commit),
but internally divided by responsibility (the snapshot/summary/finalization in
`pre_registration.py`; the payment in `registration_checkout.py`) and validated with focused tests before
the full suite.

## Pending
- Manual visual validation of the wizard in the internal browser (desktop/mobile, the happy path, and an edge
  case) was not performed in this delivery. Recommended before promoting to HG, especially the
  PIX/card/Stripe payment flows, which depend on an external gateway and are not exercised by the
  automated suite (the tests cover only the validation error paths that do not call the real
  Asaas/Stripe API).
- A real payment (Asaas/Stripe) was not validated end to end — it depends on an HTTPS tunnel and a gateway,
  per the limitation already recorded in this PRD's Context Ledger.

## Final status
Completed with limitations (the extraction core tested and green; the visual/real-payment validation
pending, per the Pending section).
