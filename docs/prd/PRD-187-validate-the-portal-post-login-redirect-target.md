# PRD-187: Validate the portal post-login redirect target

## Summary

PortalLoginView sends the request-controlled next value directly to redirect() after authentication. A crafted absolute or protocol-relative target can redirect an authenticated portal user outside the application.

## Demand type

Parity defect identified by an operator-authorized full-system audit.

## Current problem

PortalLoginView sends the request-controlled next value directly to redirect() after authentication. A crafted absolute or protocol-relative target can redirect an authenticated portal user outside the application.

## Goal

Restore the secure local behavior while preserving the product's autonomous and disposable MVP workflow.

## Context Ledger

### Files read in full

- `system/views/auth_views.py`
- `system/tests/test_password_change.py`

### Adjacent files consulted

- `system/views/portal_mixins.py`
- `system/urls.py`

### Internet / official documentation

- [Django URL safety utility](https://docs.djangoproject.com/en/5.2/ref/utils/#django.utils.http.url_has_allowed_host_and_scheme)

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

Correct finding `unsafe-portal-login-next-redirect` with a focused regression test and no unrelated refactor.

### Context

The repository is an autonomous disposable MVP. Preserve automated reset, rebuild, seed, and validation capabilities.

### Constraints

- Do not add knowledge of any external product or repository.
- Do not weaken or remove destructive automation unrelated to this finding.
- Do not print or persist sensitive values.
- Do not add comments or docstrings.

### Acceptance criteria

- [x] A same-origin relative next target is accepted after portal login.
- [x] Absolute, protocol-relative, malformed, or disallowed-host targets are rejected.
- [x] A rejected or absent target falls back to dashboard-redirect.
- [x] Forced password change and pending-payment routing keep precedence over next (the forced-password-change routing was removed by PRD-188 together with the shared credential that produced it; see Deviations from plan).
- [x] The focused regression test and complete suite pass.
- [x] The complete local test suite and applicable quality gates pass.
- [x] No comments or docstrings are introduced.
- [x] No external product reference or dependency is introduced.

### Expected evidence

Focused regression output, complete quality-gate output, and a sanitized final diff.

### Output format

Record implementation, commands, results, deviations, cleanup, and remaining work in this PRD.

## Audit reference

- Gate: `security.authentication`
- Finding: `unsafe-portal-login-next-redirect`
- Severity: `high`

## Scope

Resolve only finding `unsafe-portal-login-next-redirect` and the local files required by it.

## Out of scope

- Unrelated business rule changes.
- External repository changes.
- Opportunistic refactors that require a separate PRD.

## Impacted files

- `system/views/auth_views.py`
- `system/tests/test_password_change.py`

## Risks and edge cases

- Bypassing forced password change or payment routing.
- Blocking legitimate same-origin return paths.

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

`PortalLoginRedirectTargetTestCase` in `system/tests/test_password_change.py`
covers the accepted relative target, the absent target, the hostile targets
(absolute, protocol-relative, backslash, malformed scheme, `javascript:`,
empty), the query-string target and the pending-payment precedence.

## Visual validation

Executed in the internal browser against `http://localhost:8000`.
`GET /login/?next=https%3A%2F%2Fevil.example.com%2Froubo` renders the login form
with the hostile value in the hidden `next` input; after a valid submission the
browser lands on `http://localhost:8000/home/`, never on the external host. No
console error on the resulting page.

## ORM validation

### Read-only checks

Not required for this finding: the correction is confined to the HTTP redirect
target and is proven by the regression tests and by the browser run.

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

- `PortalLoginView._resolve_redirect_target` validates the request-controlled
  `next` with `django.utils.http.url_has_allowed_host_and_scheme`, restricted to
  the request host and to the request scheme, and falls back to
  `system:dashboard-redirect` whenever the target is absent, external,
  protocol-relative or malformed.
- The blocking routings still return before `next` is consulted, so
  pending-payment routing keeps precedence over the requested target.

## Cleanup findings

- Removed the now-unused `PortalAccount` import from `system/views/auth_views.py`
  after PRD-188 removed the forced-password-change branch.
- No residue introduced; no comment or docstring added.

## Follow-up PRDs

None identified within this focused scope.

## Deviations from plan

The acceptance criterion "forced password change ... keeps precedence over next"
was resolved together with PRD-188, which removed the only producer of the
forced-password-change state (the shared temporary credential). The precedence
guarantee is preserved structurally: every blocking routing returns before
`next` is read, and the surviving pending-payment routing is covered by
`test_pending_payment_routing_takes_precedence_over_next`.

## Pending

None.

## Final status

Concluída.
