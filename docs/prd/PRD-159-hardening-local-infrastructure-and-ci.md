# PRD-159: Local Infrastructure and CI Hardening

## Summary

Remove a dangerous temporary script, restrict destructive reset to the project itself, validate environment/targets before deletion, pin the declared Python version, and add Django CI without external credentials.

## Demand type

Architectural fix and operational-security review.

## Current problem

- `tmp_homolog_register.py` was tracked despite declaring that it should not be committed, contained a fixed password, and triggered Asaas/Stripe sandboxes.
- `clear_migrations.py` terminated every Windows Python process and validated only the presence of `manage.py` before destruction.
- `.python-version` did not pin the patch declared in contracts.
- The only existing workflow prepared Copilot tools without validating the application.

## Goal

Make the local lifecycle safe by construction and ensure every push/PR runs Django checks, migration verification, and tests.

## Context Ledger

### Files read in full

- `AGENTS.md`
- `CLAUDE.md`
- `clear_migrations.py`
- `system/tests/test_commands.py`
- `.github/workflows/copilot-setup-steps.yml`
- `.python-version`
- `.gitignore`

### Adjacent files consulted

- `docs/OPERACAO-BANCO-SEEDS.md`
- `docs/prd/PRD-154` through `PRD-158`
- `requirements.txt`
- `lvjiujitsu/settings.py`

### Internet / official documentation

- Not required: the change uses local standard-library, Django, and GitHub Actions APIs already adopted by the repository.

### Context7 / MCPs / tools verified

- Not applicable to the changed behavior.

### Limitations found

- The new workflow cannot run locally as GitHub Actions; its commands are validated locally.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved

The 2026-07-25 prompt explicitly authorized the four local fixes, proportionate tests, and documentation. Push, deployment, remote seeds, and external operations were prohibited.

## Execution prompt

### Persona

LV infrastructure and operational-security maintainer.

### Action

Remove the temporary script, harden reset, cover guards with tests, and add minimum CI.

### Context

The destructive local lifecycle uses SQLite, local `.env`, and explicit seeds.

### Constraints

- Never terminate another project’s Python process.
- Never accept a remote `DJANGO_ENVIRONMENT` or `DATABASE_URL` in the SQLite reset.
- Validate every precondition before any deletion.
- Do not execute gateways, remote seeds, push, or deployment.

### Acceptance criteria

- [x] `tmp_homolog_register.py` removed and `tmp_*.py` ignored.
- [x] Python processes are terminated only when their executable or command line belongs to the LV root.
- [x] Reset rejects an env file outside the project, a nonlocal environment, `DATABASE_URL`, empty required settings, and targets outside the root.
- [x] Unit tests cover process filtering and destructive guards.
- [x] `.python-version` contains `3.12.10`.
- [x] `.github/workflows/ci.yml` runs install, `check`, migration dry-run, and suite.
- [x] `manage.py check`, migration dry-run, and tests pass locally.

### Expected evidence

Diff, focused tests, suite, YAML parser, and residue search.

### Output format

Updated PRD and closure in English.

## Scope

- `clear_migrations.py`
- `system/tests/test_commands.py`
- `.github/workflows/ci.yml`
- `.python-version`
- `.gitignore`
- removal of `tmp_homolog_register.py`

## Out of scope

- HG, production, external payments, remote seeds, push, and deployment.
- Relaxing PRD-154 remote gates.

## Impacted files

Files listed under `Scope`, this PRD, and the index.

## Risks and edge cases

- LV process started with global Python: accepted when command line contains the project root.
- Another project using Python: rejected by root filter.
- Incomplete local `.env`: reset stops before destruction and lists only missing key names.

## Rules and constraints

- Smallest correct change.
- No real secret in code, logs, or workflow.
- TDD for destructive guards.

## Plan

- [x] Context and research
- [x] Tests authored
- [x] Implementation
- [x] Validation
- [x] Cleanup audit
- [x] Documentation

## Test plan

### Tests to author

- Positive and negative project-process filters.
- Guarantee that only the LV PID receives `taskkill`.
- Acceptance of complete local `.env`.
- Rejection of remote environment, incomplete configuration, and target traversal.

### Execution authorization

- Status: authorized by the current prompt.

### Execution evidence

- `ClearMigrationsCleanupTestCase`: nine tests, all passed.
- Complete suite: 719 tests in 226.840 s, all passed.
- `manage.py check`: no issues.
- `makemigrations --check --dry-run`: `No changes detected`.
- `py_compile clear_migrations.py`: passed.

## Visual validation

Not applicable.

## ORM validation

Not applicable.

## Quality validation

- Workflow YAML parser confirmed `name` and `django` job.
- Real preflight without destruction: `OK local=.env`.
- `git diff --check`: no whitespace errors.

## Evidence

- Tracked temporary script removed and `tmp_*.py` pattern ignored.
- Reset filters processes by root, validates local `.env`/SQLite/settings/targets before destruction, and waits only for LV PIDs.
- Minimum Django CI created for push and pull request.
- Python pinned to `3.12.10`.
- Local and Obsidian runbooks updated with the new preflight.

## Implemented

- Tracked temporary script removed and `tmp_*.py` pattern ignored.
- Reset restricted to LV processes and targets, with complete local preflight.
- Nine reset-security tests.
- Minimum Django CI and Python `3.12.10` pin.
- Local documentation and Obsidian runbook aligned.

## Cleanup findings

No temporary-script secret remains. No external call, remote seed, push, or deployment was executed.

## Follow-up PRDs

None planned.

## Deviations from plan

PRD-154 was not implemented because it relaxes remote environments and is outside authorized local hardening.

## Pending

Hosted workflow execution depends on the next push/PR and was not performed locally.

## Final status

**Completed with limitation**: every workflow command passed locally; hosted execution awaits a future push/PR.
