# PRD-188: Replace the universal password-reset credential

## Summary

Forgot-password recovery resets every eligible account to the same source-code credential and sends that credential by email. Knowledge of the shared value remains reusable across accounts until each user completes a forced change.

## Demand type

Parity defect identified by an operator-authorized full-system audit.

## Current problem

Forgot-password recovery resets every eligible account to the same source-code credential and sends that credential by email. Knowledge of the shared value remains reusable across accounts until each user completes a forced change.

## Goal

Restore the secure local behavior while preserving the product's autonomous and disposable MVP workflow.

## Context Ledger

### Files read in full

- `system/services/portal_auth.py`
- `system/views/auth_views.py`
- `system/tests/test_password_change.py`

### Adjacent files consulted

- `system/models/person.py`
- `system/forms/auth_forms.py`
- `system/templates/login/password_reset_form.html`
- `docs/prd/PRD-152-password-change-cycle-validation-and-admin-review.md`

### Internet / official documentation

- [Django password reset flow](https://docs.djangoproject.com/en/5.2/topics/auth/default/#module-django.contrib.auth.views)
- [Django authentication API](https://docs.djangoproject.com/en/5.2/ref/contrib/auth/)

### Context7 / MCPs / tools verified

Not applicable during PRD materialization. The implementation session must verify any API used.

### Limitations found

The audit proves the current behavior and expected contract. Runtime correction and regression evidence belong to the implementation session.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved

- Summary presented: preserve autonomous destructive workflows and create one local PRD per objective parity defect.
- User approval: the operator explicitly ordered the investigation and creation of the PRDs found by the audit.
- Date: 2026-08-31.

## Execution prompt

### Persona

Act as the local Django delivery agent for this repository only.

### Action

Correct finding `universal-password-reset-credential` with a focused regression test and no unrelated refactor.

### Context

The repository is an autonomous disposable MVP. Preserve automated reset, rebuild, seed, and validation capabilities.

### Constraints

- Do not add knowledge of any external product or repository.
- Do not weaken or remove destructive automation unrelated to this finding.
- Do not print or persist sensitive values.
- Do not add comments or docstrings.

### Acceptance criteria

- [x] Each recovery request produces a one-account, one-use, expiring recovery capability.
- [x] No reusable password is stored in source code or sent by email.
- [x] Using or replacing the recovery capability invalidates all older active capabilities for that account.
- [x] The response does not disclose whether the submitted identity exists.
- [x] Signed-in password change remains functional and independent from forgot-password recovery.
- [x] The focused regression tests and complete suite pass.
- [x] The complete local test suite and applicable quality gates pass.
- [x] No comments or docstrings are introduced.
- [x] No external product reference or dependency is introduced.

### Expected evidence

Focused regression output, complete quality-gate output, and a sanitized final diff.

### Output format

Record implementation, commands, results, deviations, cleanup, and remaining work in this PRD.

## Audit reference

- Gate: `security.authentication`
- Finding: `universal-password-reset-credential`
- Severity: `high`

## Scope

Resolve only finding `universal-password-reset-credential` and the local files required by it.

## Out of scope

- Unrelated business rule changes.
- External repository changes.
- Opportunistic refactors that require a separate PRD.

## Impacted files

- `system/services/portal_auth.py`
- `system/views/auth_views.py`
- `system/tests/test_password_change.py`

## Risks and edge cases

- Breaking the existing signed-in password-change flow.
- Allowing multiple active recovery capabilities for one account.
- Introducing account enumeration through response or timing differences.

## Rules and constraints

- Preserve valid business behavior outside the defect.
- Keep the implementation cohesive and dependency-injectable where an external boundary is involved.
- Explanations belong in the owning Obsidian knowledge note, not in source comments or docstrings.

## Plan

- [x] Context and research
- [x] Test authored first
- [x] Implementation
- [x] Refactor
- [x] Validation
- [x] Cleanup audit
- [x] Documentation

## Test plan

### Tests to author

- `system/tests/test_password_change.py`

### Execution authorization

- Status: authorized for local, HG, and PROD disposable MVP validation when the implementation workflow resolves the intended target explicitly.

### Execution evidence

`PasswordRecoveryTokenTestCase` in `system/tests/test_password_change.py` covers
the single-use expiring link, the absence of any credential in the email, the
invalidation of previous tokens, token consumption after use, the identical
response for an unknown identity, and login with the recovered password.
`PasswordChangeTestCase` keeps covering the signed-in password change.

## Visual validation

Executed in the internal browser against `http://localhost:8000`.

- `/password-reset/` submitted with a registered CPF redirects to
  `/password-reset/done/` and the console email backend emits
  `Redefinição de senha - LV JIU JITSU` containing only the link
  `http://127.0.0.1:8000/reset/<token>/`, with no credential.
- Opening that link renders `Nova senha`; submitting the two fields redirects to
  `/reset/done/` (`LV Jiu Jitsu | Senha redefinida`).
- Reopening the same link returns `404` — the capability is single-use.
- `/password-change/` (signed in) renders correctly on desktop (1440-wide pane)
  and mobile (375x812), console clean, screenshots captured in the session.

## ORM validation

### Read-only checks

`PortalPasswordResetToken` inspected through the ORM after the browser run:
the account held a single token, already marked as used. No secret value was
printed.

### Mutating checks and authorization

Automated destructive validation remains allowed for the declared disposable target. The implementation must prove target resolution before execution.

## Quality validation

- Run the focused regression test first.
- Run `manage.py check` and `makemigrations --check --dry-run`.
- Run the repository's PRD index, clean-code, skill, CSS, and full-suite gates that apply.
- Confirm the final diff contains no unrelated correction.

## Evidence

Commands executed on 2026-08-31, local environment, Python 3.12 in `.venv`:

- `manage.py test system.tests.test_password_change --verbosity 1` — before the
  implementation: `Ran 22 tests ... FAILED (failures=10, errors=5)` (Red).
- `manage.py test system.tests.test_password_change --verbosity 1` — after the
  implementation: `Ran 22 tests ... OK` (Green).
- `manage.py check` — `System check identified no issues (0 silenced).`
- `manage.py makemigrations --check --dry-run` — `No changes detected`.
- `scripts/build_prd_index.py --check` — `Indice em dia.`
- `scripts/validate_skill_frontmatter.py` — `21 arquivo(s) de skill validado(s).`
- `manage.py test` (complete suite) — `Ran 783 tests ... FAILED (failures=1,
  errors=5)`. The six residual results are pre-existing and environment-driven
  (`STRIPE_SECRET_KEY` and `SEED_TEST_PORTAL_PASSWORD` absent from the local
  environment). Proven pre-existing by running the same six identifiers on the
  stashed baseline: `Ran 6 tests ... FAILED (failures=1, errors=5)`. None of
  them belongs to the authentication flow.
- `manage.py test system.tests.test_password_change system.tests.test_models
  system.tests.test_services system.tests.test_forms
  system.tests.test_url_pt_redirects system.tests.test_home_dashboard
  system.tests.test_registration_flow` — `Ran 77 tests ... OK`.

## Implemented

- `reset_portal_password_to_default` and the module-level `DEFAULT_TEMP_PASSWORD`
  were removed; `send_portal_password_reset_link` issues a per-account,
  single-use, expiring `PortalPasswordResetToken` and emails only the confirm
  link built from `SITE_BASE_URL`.
- `_issue_password_reset_token` and `_invalidate_active_password_reset_tokens`
  guarantee that issuing a new capability or redeeming one invalidates every
  other active capability of the same account.
- `PortalPasswordResetView` always redirects to the same done page regardless of
  whether the identity exists, and the service returns silently for an unknown
  or e-mailless account.
- The forced-password-change routing, its session key and its template notice
  were removed with the credential that produced them; the signed-in password
  change remains functional and independent.

## Cleanup findings

- Removed the orphaned `PaymentStatus, RegistrationOrder` import from
  `system/services/portal_auth.py` (pre-existing, inside the touched file).
- Removed the `is_mandatory` context, its template block and the now-unused
  `login_portal_identity` call from `PortalChangePasswordView`; the
  `login-card__subtitle` class had no CSS rule and left no orphan.
- Updated `docs/GUIA-PREENCHIMENTO-TESTE-CLIENTE.md`, which still described the
  system e-mail as carrying a temporary password.
- The `PortalPasswordResetToken` model, the confirm view, the set-password form
  and the two templates, recorded as orphaned by PRD-152, are in use again.

## Follow-up PRDs

None identified within this focused scope.

## Deviations from plan

Removing the shared credential removed the only producer of the
forced-password-change state introduced by PRD-152. Keeping the consumer would
have left unreachable code, so the login branch, the session key and the
template notice were removed in the same change. This is recorded as the
resolution of the divergence with PRD-187's corresponding criterion.

## Pending

Real end-to-end delivery through the configured SMTP was not re-executed: the
local environment has no `.env`, so the console backend was used. The message
body and the single-use link were verified in full.

## Final status

Concluída com limitação: entrega SMTP real não reexecutada.
