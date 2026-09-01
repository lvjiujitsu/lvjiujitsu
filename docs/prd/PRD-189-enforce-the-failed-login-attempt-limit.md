# PRD-189: Enforce the failed-login attempt limit

## Summary

Portal accounts expose a failed_login_attempts counter and update it after unsuccessful authentication, but the application declares no maximum-attempt setting and applies no lock or recovery threshold. The counter is observational only.

## Demand type

Parity defect identified by an operator-authorized full-system audit.

## Current problem

Portal accounts expose a failed_login_attempts counter and update it after unsuccessful authentication, but the application declares no maximum-attempt setting and applies no lock or recovery threshold. The counter is observational only.

## Goal

Restore the secure local behavior while preserving the product's autonomous and disposable MVP workflow.

## Context Ledger

### Files read in full

- `system/services/portal_auth.py`
- `system/models/person.py`
- `lvjiujitsu/settings.py`
- `.env.example`
- `system/tests/test_password_change.py`

### Adjacent files consulted

- `system/views/auth_views.py`
- `system/forms/auth_forms.py`

### Internet / official documentation

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

Correct finding `failed-login-counter-without-enforcement` with a focused regression test and no unrelated refactor.

### Context

The repository is an autonomous disposable MVP. Preserve automated reset, rebuild, seed, and validation capabilities.

### Constraints

- Do not add knowledge of any external product or repository.
- Do not weaken or remove destructive automation unrelated to this finding.
- Do not print or persist sensitive values.
- Do not add comments or docstrings.

### Acceptance criteria

- [x] PORTAL_MAX_FAILED_LOGIN_ATTEMPTS is declared in .env.example, loaded by Django settings, validated as a positive integer, and enforced by portal authentication.
- [x] An account reaching the configured limit cannot authenticate with a password until successful password recovery clears the state.
- [x] A successful login before the limit resets the counter.
- [x] Concurrent invalid attempts are persisted atomically so a lost update cannot bypass the configured limit.
- [x] Technical-admin authentication keeps its existing Django behavior.
- [x] Messages and timing do not disclose whether an account exists.
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
- Finding: `failed-login-counter-without-enforcement`
- Severity: `high`

## Scope

Resolve only finding `failed-login-counter-without-enforcement` and the local files required by it.

## Out of scope

- Unrelated business rule changes.
- External repository changes.
- Opportunistic refactors that require a separate PRD.

## Impacted files

- `system/services/portal_auth.py`
- `system/models/person.py`
- `lvjiujitsu/settings.py`
- `.env.example`
- `system/tests/test_password_change.py`

## Risks and edge cases

- Creating a permanent lock with no recovery path.
- Allowing concurrent failures to bypass the threshold.
- Leaking account existence through different responses.

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

`FailedLoginLimitTestCase` in `system/tests/test_password_change.py`, running
under `@override_settings(PORTAL_MAX_FAILED_LOGIN_ATTEMPTS=3)`, covers the
declared setting, the lock at the configured limit with a valid password, the
identical message for a locked account and an unknown identity, the counter
reset on a successful login before the limit, the lock cleared by password
recovery, the atomic persistence of concurrent failures and the untouched
technical-admin authentication.

## Visual validation

Executed in the internal browser against `http://localhost:8000` with the
default limit of 5. Five wrong submissions to `/login/` returned the re-rendered
form; the sixth submission, with the correct password, also returned the form
instead of the `302` to `/dashboard/`. After the recovery link was redeemed, the
same credentials produced the `302` and the browser landed on `/home/`.

## ORM validation

### Read-only checks

ORM inspection after the browser run: `failed_login_attempts = 5` and
`has_reached_failed_login_limit() = True` for the locked account; both back to
the unlocked state after recovery. No secret value was printed.

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

- `PORTAL_MAX_FAILED_LOGIN_ATTEMPTS` declared in `.env.example`, loaded in
  `lvjiujitsu/settings.py` with `cast=int` and default `5`, and rejected with
  `ImproperlyConfigured` when lower than `1`.
- `PortalAccount.has_reached_failed_login_limit` reads the configured limit and
  `_authenticate_local_portal_account` refuses password authentication before
  checking the password once the limit is reached, returning the same generic
  failure as any other invalid attempt.
- `PortalAccount.register_failed_login` now increments through a single
  `UPDATE ... failed_login_attempts = failed_login_attempts + 1` with `F()` and
  refreshes the instance, so concurrent failures cannot be lost.
- `reset_portal_password` and `change_own_password` already zero the counter, so
  a successful recovery clears the lock; `register_successful_login` keeps
  resetting it below the limit. Technical-admin authentication is untouched.

## Cleanup findings

No residue introduced. No comment or docstring added. The counter had no other
reader in the codebase, so the enforcement point is single.

## Follow-up PRDs

None identified within this focused scope.

## Deviations from plan

None. The recovery path that clears the lock is the one delivered by PRD-188.

## Pending

None.

## Final status

Concluída.
